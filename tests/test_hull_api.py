"""HTTP-level Hull Preview workflow tests."""
import asyncio
import json
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import DB_PATH, init_db


def reset_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    for suffix in ("-wal", "-shm"):
        path = DB_PATH.with_name(DB_PATH.name + suffix)
        if path.exists():
            path.unlink()
    asyncio.run(init_db())


def test_hull_preview_persists_trace_and_completes():
    reset_db()
    client = TestClient(app)
    project = client.post("/api/v1/projects", json={"name": "Hull E2E"}).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "user_request": "tugboat preview",
        "task_type": "hull_design",
        "hull_design": {
            "vessel_type": "tugboat", "loa": 30, "beam": 8,
            "depth": 5, "draft": 2.5, "speed": 12,
        },
    })
    assert task.status_code == 200
    task = task.json()
    assert json.loads(task["hull_design_json"])["vessel_type"] == "tugboat"

    result = client.post(f"/api/v1/tasks/{task['id']}/run")
    assert result.status_code == 200, result.text
    completed = result.json()
    assert completed["state"] == "completed"
    run_ids = json.loads(completed["calc_run_ids"])
    assert len(run_ids) == 1

    trace = client.get(f"/api/v1/calculations/{run_ids[0]}")
    assert trace.status_code == 200
    body = trace.json()
    assert body["formula_id"] == "hull_preview"
    assert body["status"] == "UNVERIFIED"
    assert body["result"]["status"] == "PREVIEW_ONLY"
    assert body["result"]["connector_status"] == "NOT_GENERATED"
    assert body["result"]["calculations"]["displacement_volume_m3"] == 468.0


def test_hull_task_rejects_invalid_geometry():
    reset_db()
    client = TestClient(app)
    project = client.post("/api/v1/projects", json={"name": "Hull Invalid"}).json()
    response = client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "user_request": "invalid hull", "task_type": "hull_design",
        "hull_design": {"vessel_type": "tugboat", "loa": 30, "beam": 8,
                         "depth": 3, "draft": 3, "speed": 12},
    })
    assert response.status_code == 422


def test_hull_task_cannot_run_twice():
    reset_db()
    client = TestClient(app)
    project = client.post("/api/v1/projects", json={"name": "Hull Repeat"}).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "user_request": "preview", "task_type": "hull_design",
        "hull_design": {"vessel_type": "tugboat", "loa": 30, "beam": 8,
                         "depth": 5, "draft": 2.5, "speed": 12},
    }).json()
    assert client.post(f"/api/v1/tasks/{task['id']}/run").status_code == 200
    assert client.post(f"/api/v1/tasks/{task['id']}/run").status_code == 400


def test_hull_preview_verification_summary():
    reset_db()
    client = TestClient(app)
    project = client.post("/api/v1/projects", json={"name": "Hull Summary"}).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "user_request": "preview", "task_type": "hull_design",
        "hull_design": {"vessel_type": "tugboat", "loa": 30, "beam": 8,
                        "depth": 5, "draft": 2.5, "speed": 12},
    }).json()
    assert client.post(f"/api/v1/tasks/{task['id']}/run").status_code == 200
    summary = client.get(f"/api/v1/tasks/{task['id']}/verification-summary").json()
    assert summary["verification_status"] == "PASSED"
    assert summary["hydrostatics_status"] == "passed"
    assert summary["stability_status"] == "passed"
    assert summary["fairness_status"] == "not_verified"
    assert summary["overall_status"] == "not_ready"
