"""Phase 1 self-checks: state machine, policy gate, task manager."""
import pytest
import asyncio
from pathlib import Path
from nei.core.state_machine import TaskStatus, TaskStateTransition
from nei.core.policy import risk_allows_autopass, risk_requires_approval, risk_forbidden, validate_sandbox_path
from nei.core.task_manager import create_task, get_task, transition_task, cancel_task, retry_task
from nei.core.artifact_store import save_artifact, load_artifact, verify_artifact


async def _make_task():
    await create_task(project_id="test-project", user_request="test box", risk_level="L0")
    task = await get_task("test-project:test box:2026-01-01T00:00:00+00:00")
    return task


def test_valid_transitions():
    assert TaskStateTransition.can_transition(TaskStatus.PENDING, TaskStatus.PLANNING)
    assert TaskStateTransition.can_transition(TaskStatus.PLANNING, TaskStatus.VALIDATING)
    assert TaskStateTransition.can_transition(TaskStatus.VALIDATING, TaskStatus.QUEUED)
    assert TaskStateTransition.can_transition(TaskStatus.QUEUED, TaskStatus.RUNNING)
    assert TaskStateTransition.can_transition(TaskStatus.RUNNING, TaskStatus.VERIFYING)
    assert TaskStateTransition.can_transition(TaskStatus.VERIFYING, TaskStatus.COMPLETED)
    assert TaskStateTransition.can_transition(TaskStatus.RUNNING, TaskStatus.RECOVERING)
    assert TaskStateTransition.can_transition(TaskStatus.RECOVERING, TaskStatus.QUEUED)
    assert TaskStateTransition.can_transition(TaskStatus.RUNNING, TaskStatus.CANCELLED)


def test_invalid_transitions():
    assert not TaskStateTransition.can_transition(TaskStatus.PENDING, TaskStatus.COMPLETED)
    assert not TaskStateTransition.can_transition(TaskStatus.COMPLETED, TaskStatus.PENDING)
    assert not TaskStateTransition.can_transition(TaskStatus.PENDING, TaskStatus.VERIFYING)


def test_terminal_states():
    assert TaskStateTransition.is_terminal(TaskStatus.COMPLETED)
    assert TaskStateTransition.is_terminal(TaskStatus.FAILED)
    assert TaskStateTransition.is_terminal(TaskStatus.CANCELLED)
    assert not TaskStateTransition.is_terminal(TaskStatus.NEEDS_REVIEW)


def test_policy_autopass_l0_l1():
    assert risk_allows_autopass("L0")
    assert risk_allows_autopass("L1")
    assert not risk_allows_autopass("L2")
    assert not risk_allows_autopass("L3")


def test_policy_l2_needs_approval():
    assert risk_requires_approval("L2")
    assert not risk_requires_approval("L0")
    assert not risk_requires_approval("L1")


def test_policy_l3_forbidden():
    assert risk_forbidden("L3")
    assert not risk_forbidden("L0")
    assert not risk_forbidden("L2")


def test_sandbox_path():
    root = "D:/Project NEI/data/projects/test"
    assert validate_sandbox_path(f"{root}/artifacts/box.3dm", root)
    assert not validate_sandbox_path("C:/Windows/System32", root)


@pytest.mark.asyncio
async def test_task_lifecycle():
    from nei.core.database import init_db, DB_PATH
    if DB_PATH.exists():
        DB_PATH.unlink()
    await init_db()
    task = await create_task(
        project_id="test-project",
        user_request="create a 10x3x1 box in Rhino 6",
        risk_level="L0",
    )
    assert task["state"] == TaskStatus.PENDING.value

    task = await transition_task(task["id"], "planning_done", TaskStatus.PLANNING)
    assert task["state"] == TaskStatus.PLANNING.value

    task = await transition_task(task["id"], "plan_complete", TaskStatus.VALIDATING)
    assert task["state"] == TaskStatus.VALIDATING.value

    task = await transition_task(task["id"], "validation_passed", TaskStatus.QUEUED)
    assert task["state"] == TaskStatus.QUEUED.value

    task = await transition_task(task["id"], "lock_acquired", TaskStatus.RUNNING)
    assert task["state"] == TaskStatus.RUNNING.value

    task = await transition_task(task["id"], "all_steps_done", TaskStatus.VERIFYING)
    assert task["state"] == TaskStatus.VERIFYING.value

    task = await transition_task(task["id"], "all_postconditions_passed", TaskStatus.COMPLETED)
    assert task["state"] == TaskStatus.COMPLETED.value
