"""Tests for built-in formula seeding (fixes Calculations page being unusable)."""
import asyncio
from fastapi.testclient import TestClient
from nei.core.database import DB_PATH, init_db


from fastapi.testclient import TestClient
from nei.core.database import DB_PATH, init_db
from nei.main import app


def setup_function():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())


def test_built_in_formulas_seeded_and_calculatable():
    from nei.engineering.seed import ensure_built_in_formulas
    asyncio.run(ensure_built_in_formulas())
    client = TestClient(app)

    # Seeding runs on startup; formulas available in production mode.
    r = client.get("/api/v1/formulas")
    assert r.status_code == 200
    names = {f["name"] for f in r.json()}
    assert {"box_volume", "displacement_volume"} <= names

    box = next(f for f in r.json() if f["name"] == "box_volume")
    fid = box["id"]

    # Production mode: APPROVED_FOR_USE formula accepted, unit strings parsed.
    r = client.post("/api/v1/calculations", json={
        "formula_id": fid,
        "inputs": {"length": "10 m", "width": "3 m", "height": "1 m"},
        "research": False,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["result"] == 30.0
    assert body["evidence_status"] == "VERIFIED"
    assert body["formula_review_status"] == "APPROVED_FOR_USE"

    # Research mode also runs on approved formulas but labels UNVERIFIED.
    r = client.post("/api/v1/calculations", json={
        "formula_id": fid,
        "inputs": {"length": "10 m", "width": "3 m", "height": "1 m"},
        "research": True,
    })
    assert r.status_code == 200, r.text
    assert r.json()["evidence_status"] == "UNVERIFIED"
