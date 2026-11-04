"""Verification engine tests: PASSED/FAILED paths via /tasks/{id}/verify."""
import json
import asyncio
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import init_db, DB_PATH, get_db
from nei.core.state_machine import TaskStatus
from nei.core.task_manager import transition_task


def _make_task(client, request="create a 10x3x1 box in Rhino 6"):
    r = client.post("/api/v1/projects", json={"name": "Verify Test", "description": "test"})
    pid = r.json()["id"]
    r = client.post(f"/api/v1/projects/{pid}/tasks",
                    json={"user_request": request, "task_type": "geometry", "risk_level": "L0"})
    return r.json()["id"]


def _advance_to_verifying(task_id):
    for to, event in [
        (TaskStatus.PLANNING, "planning_start"),
        (TaskStatus.VALIDATING, "plan_complete"),
        (TaskStatus.QUEUED, "validation_passed"),
        (TaskStatus.RUNNING, "lock_acquired"),
        (TaskStatus.VERIFYING, "all_steps_done"),
    ]:
        asyncio.run(transition_task(task_id, event, to))


def test_verification_passed():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)

    tid = _make_task(client)
    _advance_to_verifying(tid)

    connector_result = {
        "status": "ok",
        "object_ids": ["box1"],
        "objects": [{"id": "box1", "type": "Brep",
                     "bounding_box": {"length": 10.0, "width": 3.0, "height": 1.0}}],
        "document": {"units": "millimeter"},
    }
    r = client.post(f"/api/v1/tasks/{tid}/verify", json={
        "connector_result": connector_result,
        "software_version": "Rhino 6.0",
        "length": 10.0, "width": 3.0, "height": 1.0,
    })
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "completed"

    record = asyncio.run(_get_verification_json(tid))
    assert record["status"] == "PASSED"
    assert len(record["checks"]) == 4
    assert all(c["result"] == "PASSED" for c in record["checks"])


def test_verification_failed_dimension():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)

    tid = _make_task(client)
    _advance_to_verifying(tid)

    connector_result = {
        "status": "ok",
        "object_ids": ["box1"],
        "objects": [{"id": "box1", "type": "Brep",
                     "bounding_box": {"length": 10.5, "width": 3.0, "height": 1.0}}],
        "document": {"units": "millimeter"},
    }
    r = client.post(f"/api/v1/tasks/{tid}/verify", json={
        "connector_result": connector_result,
        "software_version": "Rhino 6.0",
        "length": 10.0, "width": 3.0, "height": 1.0,
    })
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "needs_review"

    record = asyncio.run(_get_verification_json(tid))
    assert record["status"] == "FAILED"
    bbox_check = next(c for c in record["checks"] if c["target"] == "bounding_box")
    assert bbox_check["result"] == "FAILED"


async def _get_verification_json(task_id):
    import json
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT verification_json FROM tasks WHERE id = ?", (task_id,))
    return json.loads(rows[0][0])
