"""Task manager: create, transition, cancel, retry with audit trail."""
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from nei.core.state_machine import TaskStatus, TaskStateTransition
from nei.core.database import get_db
from nei.core.audit import log_event


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


async def create_task(
    project_id: str,
    user_request: str,
    task_type: str = "geometry",
    domain: str = "naval_architecture",
    risk_level: str = "L0",
) -> dict:
    """Create a task in PENDING state and record the transition."""
    task_id = _sha256(f"{project_id}:{user_request}:{_now()}")
    now = _now()
    async with get_db() as db:
        await db.execute(
            """INSERT INTO tasks (id, project_id, user_request, task_type, domain, risk_level, state, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, project_id, user_request, task_type, domain, risk_level,
             TaskStatus.PENDING.value, now),
        )
        await db.execute(
            """INSERT INTO task_events (task_id, from_state, to_state, event, metadata_json, timestamp)
               VALUES (?, NULL, ?, ?, ?, ?)""",
            (task_id, TaskStatus.PENDING.value, "created", json.dumps({}), now),
        )
        await db.commit()
    return await get_task(task_id)


async def get_task(task_id: str) -> Optional[dict]:
    async with get_db() as db:
        rows = await db.execute_fetchall("SELECT * FROM tasks WHERE id = ?", (task_id,))
    if not rows:
        return None
    row = rows[0]
    return {
        "id": row[0], "project_id": row[1], "parent_task_id": row[2],
        "user_request": row[3], "task_type": row[4], "domain": row[5],
        "risk_level": row[6], "state": row[7], "plan_json": row[8],
        "tool_calls_json": row[9], "input_artifact_ids": row[10],
        "output_artifact_ids": row[11], "evidence_ref_ids": row[12],
        "calc_run_ids": row[13], "approval_ids": row[14],
        "software_versions_json": row[15], "errors_json": row[16],
        "warnings_json": row[17], "connector_id": row[18],
        "verification_json": row[19], "schema_version": row[20],
        "created_at": row[21], "started_at": row[22], "completed_at": row[23],
    }


async def transition_task(task_id: str, event: str, to_status: TaskStatus,
                          metadata: Optional[Dict] = None) -> dict:
    """Apply a state transition, writing the task_events row and audit log."""
    async with get_db() as db:
        row = await db.execute_fetchall("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not row:
            raise ValueError(f"Task {task_id} not found")
        row = row[0]
        current = TaskStatus(row[7])
        if not TaskStateTransition.can_transition(current, to_status):
            raise ValueError(f"Illegal transition {current.value} -> {to_status.value}")

        now = _now()
        await db.execute(
            """UPDATE tasks SET state = ?, started_at = ? WHERE id = ?""",
            (to_status.value, now, task_id),
        )
        await db.execute(
            """INSERT INTO task_events (task_id, from_state, to_state, event, metadata_json, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (task_id, current.value, to_status.value, event, json.dumps(metadata or {}), now),
        )
        await db.commit()
        await log_event(db, task_id=task_id, event_type=f"TASK_{event.upper()}",
                        detail_json=json.dumps({"from": current.value, "to": to_status.value}))
    # Push live update to SSE subscribers
    try:
        from nei.api.sse import publish_event
        publish_event(task_id, "state", {"from": current.value, "to": to_status.value, "event": event})
    except Exception:
        pass
    return await get_task(task_id)


async def cancel_task(task_id: str) -> dict | None:
    """Cancel from any active state (immediate). Returns updated task or None if not found."""
    task = await get_task(task_id)
    if not task:
        return None
    if TaskStateTransition.is_terminal(TaskStatus(task["state"])):
        return task  # already terminal, nothing to cancel
    return await transition_task(task_id, "user_cancelled", TaskStatus.CANCELLED)


async def retry_task(task_id: str) -> dict:
    """Retry a FAILED/NEEDS_REVIEW task: create a new task with parent link."""
    parent = await get_task(task_id)
    if not parent:
        raise ValueError(f"Task {task_id} not found")
    if TaskStatus(parent["state"]) not in (TaskStatus.FAILED, TaskStatus.NEEDS_REVIEW):
        raise ValueError("Only FAILED/NEEDS_REVIEW tasks can be retried")
    new_task = await create_task(
        parent["project_id"],
        parent["user_request"],
        task_type=parent["task_type"],
        domain=parent["domain"],
        risk_level=parent["risk_level"],
    )
    async with get_db() as db:
        await db.execute(
            "UPDATE tasks SET parent_task_id = ? WHERE id = ?",
            (new_task["id"], task_id),
        )
        await db.commit()
    return new_task
