"""Route-level Phase 8 orchestration tests using mocked connectors only."""
import asyncio
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from nei.connectors.base import Capability, CapabilityStatus, ToolResult
from nei.core.database import DB_PATH, init_db
from nei.core.task_manager import get_task
from nei.core.planner import Plan, PlanStep
from nei.main import app


class FakeConnector:
    connector_id = "fake"
    calls = []
    fail_on = None

    def __init__(self, **kwargs):
        pass

    def get_capabilities(self):
        return [Capability("fake.create", CapabilityStatus.SUPPORTED),
                Capability("fake.finish", CapabilityStatus.SUPPORTED)]

    def validate_parameters(self, action, parameters):
        return None

    def get_version(self):
        return "test"

    def execute(self, action, parameters, *, timeout_s):
        type(self).calls.append((action, dict(parameters)))
        if action == type(self).fail_on:
            return ToolResult(success=False, error="middle failure")
        return ToolResult(success=True, data={"status": "ok"})


def setup_function():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    FakeConnector.calls = []
    FakeConnector.fail_on = None


def make_pending_task(client):
    project = client.post("/api/v1/projects", json={"name": "Phase 8"}).json()
    return client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"user_request": "test", "task_type": "test"},
    ).json()


@patch("nei.core.resource_manager.acquire_app_lock", lambda *args, **kwargs: True)
@patch("nei.core.resource_manager.release_app_lock", lambda *args, **kwargs: None)
@patch("nei.connectors.registry.get_connector_class", lambda _: FakeConnector)
def test_multistep_success_and_order():
    client = TestClient(app)
    task = make_pending_task(client)
    plan = Plan("test", [PlanStep("fake.create", "L0"), PlanStep("fake.finish", "L0")])
    
    with patch("nei.core.planner.plan_task", return_value=plan):
        response = client.post(f"/api/v1/tasks/{task['id']}/run")
    assert response.status_code == 200, response.text
    assert [call[0] for call in FakeConnector.calls] == ["fake.create", "fake.finish"]
    assert asyncio.run(get_task(task["id"]))["state"] == "completed"


@patch("nei.core.resource_manager.acquire_app_lock", lambda *args, **kwargs: True)
@patch("nei.core.resource_manager.release_app_lock", lambda *args, **kwargs: None)
@patch("nei.connectors.registry.get_connector_class", lambda _: FakeConnector)
def test_middle_failure_stops_next_step():
    client = TestClient(app)
    task = make_pending_task(client)
    FakeConnector.fail_on = "fake.finish"
    plan = Plan("test", [
        PlanStep("fake.create", "L0"), PlanStep("fake.finish", "L0"),
        PlanStep("fake.create", "L0"),
    ])
    
    with patch("nei.core.planner.plan_task", return_value=plan):
        response = client.post(f"/api/v1/tasks/{task['id']}/run")
    assert response.status_code == 500
    assert [call[0] for call in FakeConnector.calls] == ["fake.create", "fake.finish"]
    assert asyncio.run(get_task(task["id"]))["state"] == "failed"


@patch("nei.core.resource_manager.acquire_app_lock", lambda *args, **kwargs: True)
@patch("nei.core.resource_manager.release_app_lock", lambda *args, **kwargs: None)
@patch("nei.connectors.registry.get_connector_class", lambda _: FakeConnector)
def test_timeout_stops_execution():
    client = TestClient(app)
    task = make_pending_task(client)
    plan = Plan("test", [PlanStep("fake.create", "L0"), PlanStep("fake.finish", "L0")])
    
    def timeout_execute(self, action, parameters, *, timeout_s):
        FakeConnector.calls.append((action, dict(parameters)))
        raise TimeoutError("slow")
    
    with patch("nei.core.planner.plan_task", return_value=plan):
        with patch.object(FakeConnector, "execute", timeout_execute):
            response = client.post(f"/api/v1/tasks/{task['id']}/run")
    assert response.status_code == 504
    assert len(FakeConnector.calls) == 1
    assert asyncio.run(get_task(task["id"]))["state"] == "failed"

