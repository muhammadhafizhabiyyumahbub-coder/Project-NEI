import asyncio
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import DB_PATH, init_db
from nei.core.state_machine import TaskStatus
from nei.core.task_manager import transition_task


def _task_to_waiting(client, project_id, task_id, risk="L2"):
    """Advance an L2 task to WAITING_APPROVAL using the transition table."""
    asyncio.run(transition_task(task_id, "planning_done", TaskStatus.PLANNING))
    asyncio.run(transition_task(task_id, "plan_complete", TaskStatus.VALIDATING))
    asyncio.run(transition_task(task_id, "validation_passed", TaskStatus.WAITING_APPROVAL))


def test_approve_task_decision_moves_to_queued():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)
    project = client.post("/api/v1/projects", json={"name": "p"}).json()
    task = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"user_request": "hull", "risk_level": "L2"},
    ).json()
    _task_to_waiting(client, project["id"], task["id"])

    r = client.post(
        f"/api/v1/projects/{project['id']}/tasks/{task['id']}/approvals",
        json={"action": "approve", "reason": "ok"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["task_state"] == "queued"
    assert r.json()["approval_id"] is not None

    listed = client.get(f"/api/v1/projects/{project['id']}/tasks/{task['id']}/approvals")
    assert listed.status_code == 200
    assert listed.json()[0]["action"] == "approve"


def test_reject_task_decision_moves_to_needs_review():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)
    project = client.post("/api/v1/projects", json={"name": "p"}).json()
    task = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"user_request": "hull", "risk_level": "L2"},
    ).json()
    _task_to_waiting(client, project["id"], task["id"])

    r = client.post(
        f"/api/v1/projects/{project['id']}/tasks/{task['id']}/approvals",
        json={"action": "reject", "reason": "insufficient evidence"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["task_state"] == "needs_review"


def test_task_approval_rejects_bad_action():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)
    project = client.post("/api/v1/projects", json={"name": "p"}).json()
    task = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"user_request": "hull", "risk_level": "L2"},
    ).json()
    _task_to_waiting(client, project["id"], task["id"])
    r = client.post(
        f"/api/v1/projects/{project['id']}/tasks/{task['id']}/approvals",
        json={"action": "maybe"},
    )
    assert r.status_code == 422


def test_task_approval_rejects_wrong_state():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)
    project = client.post("/api/v1/projects", json={"name": "p"}).json()
    task = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"user_request": "hull", "risk_level": "L0"},
    ).json()
    # Task is PENDING, not WAITING_APPROVAL
    r = client.post(
        f"/api/v1/projects/{project['id']}/tasks/{task['id']}/approvals",
        json={"action": "approve"},
    )
    assert r.status_code == 409
