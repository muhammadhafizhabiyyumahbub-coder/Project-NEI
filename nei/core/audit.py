"""Audit logging: every notable action is recorded in audit_events."""
import json
from datetime import datetime, timezone
from typing import Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def log_event(db, task_id, event_type: str, detail_json: Optional[dict] = None,
                    step_id: Optional[str] = None, model_id: Optional[str] = None,
                    tool_name: Optional[str] = None, script_hash: Optional[str] = None):
    """Write one audit_events row."""
    await db.execute(
        """INSERT INTO audit_events (timestamp, task_id, step_id, event_type, detail_json,
           model_id, tool_name, script_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (_now(), task_id, step_id, event_type, json.dumps(detail_json or {}),
         model_id, tool_name, script_hash),
    )
