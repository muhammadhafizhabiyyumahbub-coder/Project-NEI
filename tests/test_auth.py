"""Security: auth middleware + DNS rebinding host check (SECURITY.md §1, §2)."""
import asyncio
import os
from pathlib import Path
from fastapi.testclient import TestClient
from nei.main import app, _session_token
from nei.core.database import init_db, DB_PATH
from nei.core import config


def _reset(env="dev"):
    if DB_PATH.exists():
        DB_PATH.unlink()
    for suffix in ("-wal", "-shm"):
        p = DB_PATH.with_name(DB_PATH.name + suffix)
        if p.exists():
            p.unlink()
    config.settings.environment = env
    config.settings.session_secret = "insecure-change-me" if env == "dev" else "test-secret"
    asyncio.run(init_db())
    # Re-enter lifespan to generate token + enforce mode
    return TestClient(app)


def test_dev_mode_no_auth_required():
    """Dev mode bypasses auth (single-user local workflow)."""
    _reset("dev")
    client = TestClient(app)
    r = client.get("/api/v1/projects")
    assert r.status_code == 200, r.text


def test_prod_mode_requires_auth():
    _reset("prod")
    client = TestClient(app)
    r = client.get("/api/v1/projects")
    assert r.status_code == 401, r.text
    assert "UNAUTHENTICATED" in r.json()["detail"]


def test_prod_mode_with_valid_cookie():
    _reset("prod")
    client = TestClient(app)
    r = client.post("/api/v1/auth/session")
    assert r.status_code == 200, r.text
    token = r.cookies["nei_session"]
    client.cookies.set("nei_session", token)
    r = client.get("/api/v1/projects")
    assert r.status_code == 200, r.text


def test_auth_session_mint_cookie():
    _reset("prod")
    client = TestClient(app)
    r = client.post("/api/v1/auth/session")
    assert r.status_code == 200, r.text
    assert "nei_session" in r.cookies


def test_health_no_auth_required():
    _reset("prod")
    client = TestClient(app)
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dns_rebinding_host_check():
    _reset("prod")
    client = TestClient(app)
    # Simulate external host header
    r = client.get("/api/v1/projects", headers={"Host": "evil.example.com"})
    assert r.status_code == 403, r.text
    assert "FORBIDDEN_HOST" in r.json()["detail"]


def test_env_restored_to_dev():
    """Ensure subsequent test modules run in dev mode (auth bypass)."""
    _reset("dev")
    client = TestClient(app)
    r = client.get("/api/v1/projects")
    assert r.status_code == 200
