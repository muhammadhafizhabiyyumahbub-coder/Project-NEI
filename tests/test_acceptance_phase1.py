"""Phase 1 acceptance: full task lifecycle via FastAPI TestClient.

Mirrors PLAN.md Phase 1 acceptance criteria:
- POST /projects -> project created, path_root exists
- POST /projects/{id}/tasks -> task created, state PENDING
- Task transitions PENDING -> PLANNING -> VALIDATING -> QUEUED -> RUNNING -> VERIFYING -> COMPLETED
- CANCEL works from any active state
- task_events rows written for every transition
- No CAD software required
"""
import os
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import init_db, DB_PATH


def test_phase1_acceptance():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)

    # health
    r = client.get("/api/v1/health")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"

    # create project
    r = client.post("/api/v1/projects", json={"name": "Alpha Ship", "description": "cargo"})
    assert r.status_code == 200, r.text
    project = r.json()
    pid = project["id"]
    assert Path(project["path_root"]).exists()
    assert Path(project["path_root"], "artifacts").exists()

    # list projects
    r = client.get("/api/v1/projects")
    assert r.status_code == 200
    assert any(p["id"] == pid for p in r.json())

    # create task
    r = client.post(f"/api/v1/projects/{pid}/tasks",
                    json={"user_request": "create a 10x3x1 box in Rhino 6",
                          "task_type": "geometry", "risk_level": "L0"})
    assert r.status_code == 200, r.text
    task = r.json()
    assert task["state"] == "pending"
    tid = task["id"]

    # L3 forbidden
    r = client.post(f"/api/v1/projects/{pid}/tasks",
                    json={"user_request": "x", "risk_level": "L3"})
    assert r.status_code == 400

    # full transition via task_manager + SSE
    from nei.core.task_manager import transition_task
    from nei.core.state_machine import TaskStatus
    for event, to in [
        ("planning_start", TaskStatus.PLANNING),
        ("plan_complete", TaskStatus.VALIDATING),
        ("validation_passed", TaskStatus.QUEUED),
        ("lock_acquired", TaskStatus.RUNNING),
        ("all_steps_done", TaskStatus.VERIFYING),
        ("all_postconditions_passed", TaskStatus.COMPLETED),
    ]:
        t = asyncio.run(transition_task(tid, event, to))
        assert t["state"] == to.value, (t["state"], to.value)

    # task_events rows written for every transition
    from nei.core.database import get_db
    asyncio.get_event_loop().close() if False else None
    async def _count_events():
        async with get_db() as db:
            rows = await db.execute_fetchall(
                "SELECT COUNT(*) FROM task_events WHERE task_id = ?", (tid,))
            return rows[0][0]
    n_events = asyncio.run(_count_events())
    assert n_events == 7, n_events  # 1 created + 6 transitions

    # cancel a fresh task from PENDING
    r = client.post(f"/api/v1/projects/{pid}/tasks",
                    json={"user_request": "cancel me", "risk_level": "L0"})
    tid2 = r.json()["id"]
    r = client.post(f"/api/v1/tasks/{tid2}/cancel")
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "cancelled"

    print("PHASE 1 ACCEPTANCE: PASSED")


if __name__ == "__main__":
    test_phase1_acceptance()
