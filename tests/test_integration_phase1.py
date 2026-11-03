"""Phase 1 happy-path integration test: full project → task → state flow."""
import asyncio
import uuid
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from nei.main import app
    with TestClient(app, base_url="http://testserver") as c:
        # Auth: in dev mode the middleware bypasses cookie check, so just use the client directly
        yield c


def test_phase1_happy_path(client: TestClient):
    # 1. Health
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["db"] is True

    # 2. Create project
    project_name = f"it_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/v1/projects", json={"name": project_name, "description": "it test"})
    assert r.status_code == 200, r.text
    project = r.json()
    assert project["name"] == project_name
    assert "id" in project

    # 3. List projects — new project visible
    r = client.get("/api/v1/projects")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert project_name in names

    # 4. Create task under project
    r = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"user_request": "create a test box", "risk_level": "L0"},
    )
    assert r.status_code == 200, r.text
    task = r.json()
    assert task["state"] == "pending"
    assert task["project_id"] == project["id"]
    assert task["user_request"] == "create a test box"
    assert task["risk_level"] == "L0"

    # 5. List tasks for project — new task visible
    r = client.get(f"/api/v1/projects/{project['id']}/tasks")
    assert r.status_code == 200
    task_ids = [t["id"] for t in r.json()]
    assert task["id"] in task_ids

    # 6. Get task by ID
    r = client.get(f"/api/v1/tasks/{task['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == task["id"]
    assert r.json()["state"] == "pending"

    # 7. Events raw (empty for new task)
    r = client.get(f"/api/v1/tasks/{task['id']}/events_raw")
    assert r.status_code == 200

    # 8. Cancel task — terminal transition
    r = client.post(f"/api/v1/tasks/{task['id']}/cancel")
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "cancelled"

    # 9. Verify task state changed
    r = client.get(f"/api/v1/tasks/{task['id']}")
    assert r.json()["state"] == "cancelled"
