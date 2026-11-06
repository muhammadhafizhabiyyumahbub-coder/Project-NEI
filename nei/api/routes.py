"""API routes matching PLAN.md Phase 1 acceptance criteria + Phase 2 needs.

Endpoints:
  GET    /health
  GET    /projects
  POST   /projects
  POST   /projects/{project_id}/tasks
  GET    /projects/{project_id}/tasks
  GET    /tasks/{task_id}
  GET    /tasks/{task_id}/events_raw
  POST   /tasks/{task_id}/cancel
"""
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from nei.core.database import get_db
from nei.core.state_machine import TaskStatus
from nei.core.task_manager import create_task, get_task, cancel_task
from nei.core.audit import log_event
from nei.core.policy import risk_forbidden
from nei.api import models
from typing import Optional

router = APIRouter()

PROJECTS_ROOT = Path("data/projects")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/health")
async def health():
    """Health endpoint: DB reachable + app_state readable."""
    async with get_db() as db:
        row = await db.execute_fetchall("SELECT 1")
    return {"status": "ok", "db": bool(row), "timestamp": _now()}


@router.get("/projects", response_model=list[models.Project])
async def list_projects():
    async with get_db() as db:
        rows = await db.execute_fetchall("SELECT * FROM projects ORDER BY created_at DESC")
    return [
        {"id": r[0], "name": r[1], "description": r[2],
         "created_at": r[3], "updated_at": r[4], "path_root": r[5]}
        for r in rows
    ]


@router.post("/projects", response_model=models.Project)
async def create_project(project: models.ProjectCreate):
    pid = str(uuid.uuid4())
    now = _now()
    path_root = (PROJECTS_ROOT / pid).resolve().as_posix()
    Path(path_root).mkdir(parents=True, exist_ok=True)
    Path(path_root, "artifacts").mkdir(exist_ok=True)
    async with get_db() as db:
        await db.execute(
            "INSERT INTO projects (id, name, description, created_at, updated_at, path_root) VALUES (?, ?, ?, ?, ?, ?)",
            (pid, project.name, project.description, now, now, path_root),
        )
        await db.commit()
    return {"id": pid, "name": project.name, "description": project.description,
            "created_at": now, "updated_at": now, "path_root": path_root}


@router.post("/projects/{project_id}/tasks", response_model=models.Task)
async def create_task_endpoint(project_id: str, task: models.TaskCreate):
    """Create a task under a project. Enforces L3 ban per Alpha 0.1."""
    async with get_db() as db:
        rows = await db.execute_fetchall("SELECT id FROM projects WHERE id = ?", (project_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Project not found")
    if risk_forbidden(task.risk_level):
        raise HTTPException(status_code=400, detail="L3 risk level disallowed in Alpha 0.1")
    if task.task_type == "hull_design":
        from nei.engineering.hull import HullDesignRequest
        try:
            hull = HullDesignRequest.model_validate(task.hull_design or {})
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Invalid hull design: {exc}") from exc
        task.user_request = f"Design {hull.vessel_type} hull: LOA {hull.loa} m, beam {hull.beam} m, depth {hull.depth} m, draft {hull.draft} m, speed {hull.speed} kn."

    created = await create_task(
        project_id=project_id,
        user_request=task.user_request,
        task_type=task.task_type,
        domain=task.domain,
        risk_level=task.risk_level,
        hull_design=task.hull_design,
    )
    async with get_db() as db:
        await log_event(db, task_id=created["id"], event_type="TASK_CREATED",
                        detail_json={"request": task.user_request, "risk": task.risk_level})
        await db.commit()
    return created


@router.get("/projects/{project_id}/tasks", response_model=list[models.Task])
async def list_project_tasks(project_id: str):
    """All tasks under a project, newest first. 404 if project does not exist."""
    async with get_db() as db:
        rows = await db.execute_fetchall("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not rows:
            raise HTTPException(status_code=404, detail="Project not found")
        rows = await db.execute_fetchall(
            "SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,))
    return [row_to_task(r) for r in rows]


def row_to_task(row: tuple) -> dict:
    """Map a tasks table row (24 cols) to the Task response shape."""
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


@router.get("/tasks/{task_id}", response_model=models.Task)
async def get_task_endpoint(task_id: str):
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/tasks/{task_id}/artifacts")
async def task_artifacts(task_id: str):
    """List sandbox artifacts with current SHA-256 values."""
    from nei.core.artifact_store import list_artifacts
    async with get_db() as db:
        if not await db.execute_fetchall("SELECT id FROM tasks WHERE id = ?", (task_id,)):
            raise HTTPException(status_code=404, detail="Task not found")
    return await list_artifacts(task_id)


@router.get("/tasks/{task_id}/artifacts/{filename:path}")
async def download_task_artifact(task_id: str, filename: str):
    """Download artifact. Only task-owned files. No path traversal."""
    async with get_db() as db:
        if not await db.execute_fetchall("SELECT id FROM tasks WHERE id = ?", (task_id,)):
            raise HTTPException(status_code=404, detail="Task not found")
    # Prevent path traversal
    if ".." in filename or filename.startswith("/") or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    from nei.core.artifact_store import get_artifact_path
    try:
        full_path = get_artifact_path(task_id, filename)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    if not full_path.exists() or not full_path.is_file():
        # Check if it was a traversal attempt that got sanitized or just missing
        if ".." in filename or filename.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid filename")
        raise HTTPException(status_code=404, detail="Artifact not found")
        
    from fastapi.responses import FileResponse
    return FileResponse(full_path, filename=Path(filename).name)


@router.get("/tasks/{task_id}/evidence")
async def task_evidence(task_id: str):
    """Return connector evidence linked to task execution."""
    async with get_db() as db:
        task = await db.execute_fetchall("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        rows = await db.execute_fetchall(
            """SELECT id, connector_id, capability_name, evidence_type, artifact_path,
                      artifact_sha256, metadata_json, verified_at, verified_by, notes
               FROM connector_evidence WHERE json_extract(metadata_json, '$.task_id') = ?
               ORDER BY verified_at DESC""", (task_id,))
    from nei.core import artifact_store
    records = []
    for r in rows:
        metadata = json.loads(r[6]) if r[6] else None
        artifact_verified = None
        if metadata and metadata.get("task_id") == task_id and r[4]:
            filename = Path(r[4]).name
            artifact_verified = await artifact_store.verify_artifact(task_id, filename, r[5]) if r[5] else None
        records.append({
            "id": r[0], "connector_id": r[1], "capability_name": r[2],
            "evidence_type": r[3], "artifact_path": Path(r[4]).name if r[4] else None, "artifact_sha256": r[5],
            "metadata": metadata, "verified_at": r[7], "verified_by": r[8],
            "notes": r[9], "artifact_verified": artifact_verified,
        })
    return records


@router.get("/tasks/{task_id}/events_raw")
async def task_events_raw(task_id: str):
    """State timeline for task detail page (reads task_events)."""
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT from_state, to_state, event, metadata_json, timestamp FROM task_events WHERE task_id = ? ORDER BY timestamp ASC",
            (task_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Task not found")
    return [{
        "from_state": r[0], "to_state": r[1], "event": r[2],
        "metadata": json.loads(r[3]) if r[3] else None, "timestamp": r[4]
    } for r in rows]


@router.post("/tasks/{task_id}/approval")
async def create_engineering_approval(task_id: str, body: models.EngineeringApprovalRequest):
    """Record explicit engineering review; never inferred from automated checks."""
    if body.status not in {"not_performed", "pending", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid approval status")
    if body.status in {"approved", "rejected"}:
        if not body.reviewed_by or not body.reviewed_by.strip():
            raise HTTPException(status_code=400, detail="reviewed_by required for final approval status")
        if not body.reason or not body.reason.strip():
            raise HTTPException(status_code=400, detail="reason required for final approval status")
    if body.status == "approved" and not body.artifact_sha256:
        raise HTTPException(status_code=400, detail="artifact_sha256 required for approval")
    async with get_db() as db:
        if not await db.execute_fetchall("SELECT id FROM tasks WHERE id = ?", (task_id,)):
            raise HTTPException(status_code=404, detail="Task not found")
        if body.status == "approved":
            artifact = await db.execute_fetchall(
                "SELECT 1 FROM connector_evidence WHERE json_extract(metadata_json, '$.task_id') = ? AND artifact_sha256 = ? LIMIT 1",
                (task_id, body.artifact_sha256),
            )
            if not artifact:
                raise HTTPException(status_code=400, detail="artifact_sha256 does not match task evidence")
        approval_id = str(uuid.uuid4())
        now = _now()
        await db.execute(
            """INSERT INTO engineering_approvals
               (id, task_id, artifact_sha256, status, reviewed_by, reason, created_at, reviewed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (approval_id, task_id, body.artifact_sha256, body.status,
             body.reviewed_by, body.reason, now, now if body.status in {"approved", "rejected"} else None),
        )
        await db.commit()
    return {"id": approval_id, "task_id": task_id, "artifact_sha256": body.artifact_sha256,
            "status": body.status, "reviewed_by": body.reviewed_by, "reason": body.reason,
            "created_at": now, "reviewed_at": now if body.status in {"approved", "rejected"} else None}


@router.get("/tasks/{task_id}/verification-summary")
async def task_verification_summary(task_id: str):
    """Return one conservative engineering-readiness summary for a task."""
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    verification = json.loads(task["verification_json"]) if task.get("verification_json") else None
    approvals = await get_engineering_approval(task_id)
    approval = approvals[0] if approvals else None
    if approval and approval["status"] == "approved":
        matching_artifact = False
        async with get_db() as db:
            rows = await db.execute_fetchall(
                "SELECT artifact_path, artifact_sha256, metadata_json FROM connector_evidence WHERE json_extract(metadata_json, '$.task_id') = ? AND artifact_sha256 = ?",
                (task_id, approval["artifact_sha256"]),
            )
        for artifact_path, artifact_sha, metadata_json in rows:
            filename = Path(artifact_path).name if artifact_path else None
            if filename:
                from nei.core import artifact_store
                matching_artifact = await artifact_store.verify_artifact(task_id, filename, artifact_sha)
            else:
                matching_artifact = True
            if matching_artifact:
                break
        if not matching_artifact:
            approval = {**approval, "status": "stale"}
    checks = verification.get("checks", []) if verification else []
    stability_metrics = await _task_stability_metrics(task)
    return {
        "task_id": task_id,
        "artifact_integrity": all(c.get("result") == "PASSED" for c in checks if c.get("target") == "artifact_saved") if any(c.get("target") == "artifact_saved" for c in checks) else "not_verified",
        "verification_status": verification.get("status") if verification else "not_verified",
        "reopen_verified": any((e.get("metadata") or {}).get("reopen_verified") is True for e in await _task_evidence_rows(task_id)),
        "hydrostatics_status": _hydrostatics_status(checks),
        "volume_consistency": await _task_volume_consistency(task),
        "stability_status": stability_metrics["status"] if stability_metrics["status"] in {"stable", "unstable", "neutral"} else _stability_status(checks),
        "metacentric_height_m": stability_metrics["gm"],
        "loading_conditions": stability_metrics["loading_conditions"],
        "loading_status": stability_metrics["loading_status"],
        "mass_status": stability_metrics["mass_status"],
        "longitudinal_status": stability_metrics["longitudinal_status"],
        "fairness_status": _fairness_status(checks, await _task_evidence_rows(task_id)),
        "watertight_status": _watertight_status(checks, await _task_evidence_rows(task_id)),
        "engineering_approval": approval["status"] if approval else "not_performed",
        "approval_artifact_sha256": approval.get("artifact_sha256") if approval else None,
        "overall_status": "approved" if approval and approval["status"] == "approved" and stability_metrics["loading_status"] != "failed" and stability_metrics["mass_status"] != "failed" and stability_metrics["longitudinal_status"] != "failed" and await _task_volume_consistency(task) != "failed" else "not_ready",
    }


async def _task_volume_consistency(task: dict) -> str:
    """Read volume consistency from latest calculation without upgrading approval."""
    raw_ids = task.get("calc_run_ids")
    if not raw_ids:
        return "not_verified"
    try:
        run_ids = json.loads(raw_ids)
    except (TypeError, json.JSONDecodeError):
        return "not_verified"
    if not run_ids:
        return "not_verified"
    async with get_db() as db:
        rows = await db.execute_fetchall("SELECT result_json FROM calculation_runs WHERE id = ?", (run_ids[-1],))
    if not rows or not rows[0][0]:
        return "not_verified"
    calculations = json.loads(rows[0][0]).get("calculations", {})
    return calculations.get("volume_consistency", "not_verified")


async def _task_stability_metrics(task: dict) -> dict:
    """Read explicit stability result from latest deterministic calculation."""
    raw_ids = task.get("calc_run_ids")
    if not raw_ids:
        return {"status": None, "gm": None, "loading_conditions": [], "loading_status": "not_verified", "mass_status": "not_verified", "longitudinal_status": "not_verified"}
    try:
        run_ids = json.loads(raw_ids)
    except (TypeError, json.JSONDecodeError):
        return {"status": None, "gm": None, "loading_conditions": [], "loading_status": "not_verified", "mass_status": "not_verified", "longitudinal_status": "not_verified"}
    if not run_ids:
        return {"status": None, "gm": None, "loading_conditions": [], "loading_status": "not_verified", "mass_status": "not_verified", "longitudinal_status": "not_verified"}
    async with get_db() as db:
        rows = await db.execute_fetchall("SELECT result_json FROM calculation_runs WHERE id = ?", (run_ids[-1],))
    if not rows or not rows[0][0]:
        return {"status": None, "gm": None, "loading_conditions": [], "loading_status": "not_verified", "mass_status": "not_verified", "longitudinal_status": "not_verified"}
    result = json.loads(rows[0][0])
    calculations = result.get("calculations", {})
    loading = calculations.get("loading_conditions", [])
    return {
        "status": calculations.get("stability_status"),
        "gm": calculations.get("metacentric_height_m"),
        "loading_conditions": loading,
        "loading_status": "failed" if any(c.get("status") == "unstable" for c in loading) else "passed" if loading and all(c.get("status") == "stable" for c in loading) else "not_verified",
        "mass_status": "failed" if any(c.get("mass_status") == "failed" for c in loading) else "passed" if loading and all(c.get("mass_status") == "passed" for c in loading) else "not_verified",
        "longitudinal_status": "failed" if any(c.get("longitudinal_status") == "failed" for c in loading) else "passed" if loading and all(c.get("longitudinal_status") == "passed" for c in loading) else "not_verified",
    }


def _hydrostatics_status(checks: list[dict]) -> str:
    """Conservative hydrostatics check from available verification data."""
    dim = [c for c in checks if c.get("target") == "dimensions"]
    vol = [c for c in checks if c.get("target") == "volume"]
    if not dim or not vol:
        return "not_verified"
    if any(c.get("result") == "FAILED" for c in dim + vol):
        return "failed"
    if any(c.get("result") == "PASSED" for c in dim + vol):
        return "passed"
    return "not_verified"


def _stability_status(checks: list[dict]) -> str:
    """Conservative stability check from available verification data."""
    stab = [c for c in checks if c.get("target") == "stability"]
    if not stab:
        return "not_verified"
    if any(c.get("result") == "FAILED" for c in stab):
        return "failed"
    if any(c.get("result") == "PASSED" for c in stab):
        return "passed"
    return "not_verified"


def _fairness_status(checks: list[dict], evidence: list[dict]) -> str:
    """Fairness requires explicit CAD evidence, never preview geometry."""
    fair = [c for c in checks if c.get("target") == "fairness"]
    if not fair:
        fair = [{"result": (e.get("metadata") or {}).get("fairness_status")} for e in evidence
                if (e.get("metadata") or {}).get("fairness_status")]
    if not fair:
        return "not_verified"
    if any(c.get("result") in {"FAILED", "failed"} for c in fair):
        return "failed"
    if any(c.get("result") in {"PASSED", "passed", "verified"} for c in fair):
        return "passed"
    return "not_verified"


def _watertight_status(checks: list[dict], evidence: list[dict]) -> str:
    """Watertightness requires explicit CAD inspection evidence."""
    water = [c for c in checks if c.get("target") == "watertight"]
    if not water:
        water = [{"result": (e.get("metadata") or {}).get("watertight_status")} for e in evidence
                 if (e.get("metadata") or {}).get("watertight_status")]
    if not water:
        return "not_verified"
    if any(c.get("result") in {"FAILED", "failed"} for c in water):
        return "failed"
    if any(c.get("result") in {"PASSED", "passed", "verified"} for c in water):
        return "verified"
    return "not_verified"


async def _task_evidence_rows(task_id: str) -> list[dict]:
    async with get_db() as db:
        rows = await db.execute_fetchall("SELECT metadata_json FROM connector_evidence WHERE json_extract(metadata_json, '$.task_id') = ?", (task_id,))
    return [{"metadata": json.loads(r[0]) if r[0] else None} for r in rows]


@router.get("/tasks/{task_id}/approval")
async def get_engineering_approval(task_id: str):
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT id, task_id, artifact_sha256, status, reviewed_by, reason, created_at, reviewed_at FROM engineering_approvals WHERE task_id = ? ORDER BY created_at DESC",
            (task_id,),
        )
        if not rows and not await db.execute_fetchall("SELECT id FROM tasks WHERE id = ?", (task_id,)):
            raise HTTPException(status_code=404, detail="Task not found")
    return [{"id": r[0], "task_id": r[1], "artifact_sha256": r[2], "status": r[3],
             "reviewed_by": r[4], "reason": r[5], "created_at": r[6], "reviewed_at": r[7]} for r in rows]


@router.post("/tasks/{task_id}/cancel", response_model=models.Task)
async def cancel_task_endpoint(task_id: str):
    cancelled = await cancel_task(task_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Task not found")
    return cancelled


@router.post("/tasks/{task_id}/verify", response_model=models.Task)
async def verify_task_endpoint(task_id: str, body: models.VerifyRequest):
    """Run verification checks against connector result. Task must be in VERIFYING state."""
    from nei.core.task_manager import verify_task
    from nei.verification.postconditions import rhino_box_postconditions, rhino_export_copy_postconditions
    # Choose postconditions based on which task type this is:
    # export_copy: artifact path comes from connector_result
    # box: default box postconditions
    connector_result = body.connector_result or {}
    artifact_path = connector_result.get("artifact_path", "")
    if artifact_path:
        filename = artifact_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        pcs = rhino_export_copy_postconditions(filename=filename)
    else:
        pcs = rhino_box_postconditions(body.length, body.width, body.height)
    try:
        return await verify_task(
            task_id,
            connector_result,
            body.software_version,
            postconditions=pcs,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/execute")
async def execute_task_endpoint(task_id: str, body: models.ExecuteRequest):
    """Execute connector action for a RUNNING task, return connector result.

    Security:
    - Action must be in the connector allowlist (no arbitrary commands/scripts)
    - Params validated: numeric ranges for dimensions, sandbox check for artifact_path
    - Policy gate enforced by risk level; L2 requires human approval
    - Audit event written for every attempt
    """
    import json as _json

    from nei.connectors.rhino6 import Rhino6Connector
    from nei.core.task_manager import get_task, transition_task
    from nei.core.state_machine import TaskStatus
    from nei.core.policy import risk_requires_approval, risk_forbidden, validate_sandbox_path
    from nei.core.audit import log_event
    from nei.core.database import get_db

    if body.action not in models.ALLOWED_ACTIONS:
        async with get_db() as db:
            await log_event(
                db, task_id=task_id, event_type="EXECUTE_REJECTED",
                detail_json={"reason": "action_not_allowlisted", "action": body.action,
                             "params": body.params},
            )
            await db.commit()
        raise HTTPException(status_code=400, detail=f"Action not allowed: {body.action}")

    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    state = TaskStatus(task["state"])
    if state != TaskStatus.RUNNING:
        raise HTTPException(status_code=400, detail=f"Task must be in RUNNING state, got {state.value}")

    risk_level = task["risk_level"]
    if risk_forbidden(risk_level):
        raise HTTPException(status_code=400, detail=f"Risk level {risk_level} is forbidden")

    # Validate numeric params for box creation (prevents injection-ish values)
    if body.action == "rhino.create_box_test":
        params = body.params or {}
        for dim in ("length", "width", "height"):
            if dim in params:
                val = params[dim]
                if not isinstance(val, (int, float)) or isinstance(val, bool) or val <= 0:
                    raise HTTPException(status_code=400,
                                        detail=f"Parameter {dim} must be a positive number, got {val!r}")
        if "artifact_path" in params and params["artifact_path"]:
            ap = str(params["artifact_path"])
            project_root = task.get("path_root") or str(PROJECTS_ROOT / task["project_id"])
            if not validate_sandbox_path(ap, project_root):
                raise HTTPException(status_code=400,
                                    detail=f"artifact_path outside sandbox: {ap}")

    # Validate artifact_path sandbox for export_copy
    if body.action == "rhino.export_copy":
        params = body.params or {}
        if "artifact_path" in params and params["artifact_path"]:
            ap = str(params["artifact_path"])
            project_root = task.get("path_root") or str(PROJECTS_ROOT / task["project_id"])
            if not validate_sandbox_path(ap, project_root):
                raise HTTPException(status_code=400,
                                    detail=f"artifact_path outside sandbox: {ap}")

    connector = Rhino6Connector()
    result = connector.execute(body.action, body.params, timeout_s=60)

    # If a .3dm was produced, ingest it into the artifact store + write a manifest
    artifact_sha: str | None = None
    artifact_filename: str | None = None
    artifact_path = str((body.params or {}).get("artifact_path", ""))
    if result.success and artifact_path:
        from pathlib import Path
        from nei.core import artifact_store
        src = Path(artifact_path)
        if src.exists():
            artifact_filename = src.name
            content = src.read_bytes()
            async with get_db() as db:
                artifact_sha = await artifact_store.save_artifact(task_id, artifact_filename, content)
                await artifact_store.write_manifest(
                    task_id, artifact_filename,
                    {"source_action": body.action, "source_path": str(src)},
                )
            # Reflect the artifact in the connector result so verify can find it
            result.data["artifact_path"] = str(src)
            result.data["artifact_sha256"] = artifact_sha
            # Link artifact evidence to the task so the audit trail is traceable
            from nei.connectors.evidence import record_connector_evidence
            await record_connector_evidence(
                connector_id="rhino6",
                capability_name=body.action,
                evidence_type="artifact_exchange",
                artifact_path=str(src),
                artifact_sha256=artifact_sha,
                metadata={"task_id": task_id, "action": body.action},
                notes=f"Rhino action {body.action} produced artifact for task {task_id}",
            )

    async with get_db() as db:
        await db.execute(
            "UPDATE tasks SET tool_calls_json = ?, software_versions_json = ? WHERE id = ?",
            (
                _json.dumps({"action": body.action, "params": body.params, "result": result.__dict__}),
                _json.dumps({"rhino6": connector.get_version() or "unknown"}),
                task_id,
            ),
        )
        await log_event(db, task_id=task_id, event_type="EXECUTE_ACTION",
                        detail_json={"action": body.action, "params": body.params,
                                     "success": result.success,
                                     "artifact_sha256": artifact_sha})
        await db.commit()

    return {
        "success": result.success,
        "object_ids": result.object_ids,
        "data": result.data,
        "error": result.error,
    }


@router.post("/tasks/{task_id}/approve", response_model=models.Task)
async def approve_task_endpoint(task_id: str):
    """Approve a task in WAITING_APPROVAL state, transition to QUEUED."""
    from nei.core.task_manager import transition_task
    from nei.core.state_machine import TaskStatus
    from nei.core.audit import log_event
    from nei.core.database import get_db

    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if TaskStatus(task["state"]) != TaskStatus.WAITING_APPROVAL:
        raise HTTPException(status_code=400, detail=f"Task must be in WAITING_APPROVAL state, got {task['state']}")

    approved = await transition_task(task_id, "human_approved", TaskStatus.QUEUED)
    async with get_db() as db:
        await log_event(db, task_id=task_id, event_type="TASK_APPROVED",
                        detail_json={"risk_level": task["risk_level"]})
        await db.commit()
    return approved


@router.post("/tasks/{task_id}/provide-input", response_model=models.Task)
async def provide_input_endpoint(task_id: str, body: models.InputRequest):
    """Provide missing inputs for a task in NEEDS_INPUT state, re-enter PLANNING."""
    from nei.core.task_manager import transition_task
    from nei.core.state_machine import TaskStatus
    from nei.core.audit import log_event
    from nei.core.database import get_db
    import json

    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if TaskStatus(task["state"]) != TaskStatus.NEEDS_INPUT:
        raise HTTPException(status_code=400, detail=f"Task must be in NEEDS_INPUT state, got {task['state']}")

    # Store inputs in task metadata
    async with get_db() as db:
        await db.execute(
            "UPDATE tasks SET plan_json = ? WHERE id = ?",
            (json.dumps(body.inputs), task_id),
        )
        await db.commit()

    updated = await transition_task(task_id, "input_provided", TaskStatus.PLANNING)
    async with get_db() as db:
        await log_event(db, task_id=task_id, event_type="INPUT_PROVIDED",
                        detail_json=body.inputs)
        await db.commit()
    return updated


@router.post("/tasks/{task_id}/retry", response_model=models.Task)
async def retry_task_endpoint(task_id: str):
    """Retry a failed/needs-review task, create a new child task."""
    from nei.core.task_manager import retry_task
    from nei.core.state_machine import TaskStatus
    from nei.core.audit import log_event
    from nei.core.database import get_db

    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if TaskStatus(task["state"]) not in (TaskStatus.FAILED, TaskStatus.NEEDS_REVIEW):
        raise HTTPException(status_code=400, detail=f"Task must be in FAILED or NEEDS_REVIEW state, got {task['state']}")

    retried = await retry_task(task_id)
    async with get_db() as db:
        await log_event(db, task_id=task_id, event_type="TASK_RETRIED",
                        detail_json={"retry_task_id": retried["id"]})
        await db.commit()
    return retried


@router.post("/tasks/{task_id}/run", response_model=models.Task)
async def run_task_endpoint(task_id: str):
    """Drive a PENDING task through planning → validating → queued → running → verifying.

    Uses the template planner to pick the connector action, then executes it
    via registered connector and runs postcondition verification.
    """
    from nei.core.task_manager import get_task, transition_task
    from nei.core.state_machine import TaskStatus
    from nei.core.planner import plan_task
    from nei.core.policy import risk_requires_approval
    from nei.core.audit import log_event
    from nei.core.database import get_db
    from nei.connectors.registry import get_connector_class
    from nei.core.resource_manager import acquire_app_lock, release_app_lock
    from nei.core.config import settings
    from nei.verification.postconditions import rhino_box_postconditions, rhino_export_copy_postconditions
    from nei.engineering.handoff import save_handoff_file, write_provenance_manifest, validate_handoff_artifact, HandoffHop
    import json as _json

    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    state = TaskStatus(task["state"])
    if state != TaskStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Task must be in PENDING state, got {state.value}")

    # Step 1: PENDING → PLANNING
    await transition_task(task_id, "start_planning", TaskStatus.PLANNING)

    # Step 2: Run planner
    hull_design = None
    if task["task_type"] == "hull_design" and task.get("hull_design_json"):
        hull_design = json.loads(task["hull_design_json"])
    plan = plan_task(task["user_request"], task["task_type"], hull_design)
    if not plan.steps:
        await transition_task(task_id, "needs_input", TaskStatus.NEEDS_INPUT)
        raise HTTPException(status_code=400,
                            detail=f"Planner needs input: {plan.required_inputs}")

    # Step 2b: Hull design preview — deterministic calculation, no connector claim.
    if task["task_type"] == "hull_design" and hull_design:
        from nei.engineering.hull import HullDesignRequest, hull_preview, record_hull_run
        hull = HullDesignRequest.model_validate(hull_design)
        preview = hull_preview(hull)
        run_id = await record_hull_run(task_id, hull, preview)
        plan.notes = f"Preview recorded {run_id}: {preview['calculations']}"


    # Step 3: Validate complete plan before executing any step.
    for planned_step in plan.steps:
        if not planned_step.action or "." not in planned_step.action:
            await transition_task(task_id, "plan_invalid", TaskStatus.FAILED,
                                  {"error": "Invalid action in plan"})
            raise HTTPException(status_code=400, detail="Invalid action in plan")
        if not isinstance(planned_step.params, dict):
            await transition_task(task_id, "plan_invalid", TaskStatus.FAILED,
                                  {"error": "Step parameters must be an object"})
            raise HTTPException(status_code=400, detail="Step parameters must be an object")

    # Step 4: PLANNING → VALIDATING
    await transition_task(task_id, "plan_validated", TaskStatus.VALIDATING,
                          {"plan": [s.action for s in plan.steps], "params": [s.params for s in plan.steps]})

    # Step 5: policy check
    for step in plan.steps:
        if risk_requires_approval(step.risk_level):
            await transition_task(task_id, "approval_required", TaskStatus.WAITING_APPROVAL)
            raise HTTPException(status_code=400,
                                detail=f"Risk level {step.risk_level} requires approval. "
                                       "Approve via POST /tasks/{id}/approve, then re-run.")

    # Step 5: VALIDATING → QUEUED
    await transition_task(task_id, "validating_complete", TaskStatus.QUEUED)

    # Initialize handoff chain
    handoff_chain: list[HandoffHop] = []
    handoff_artifact: Optional[bytes] = None
    handoff_filename: Optional[str] = None

    # Execute all steps in sequence
    for step_idx, step in enumerate(plan.steps):
        action = step.action
        params = dict(step.params)

        # Step 6: QUEUED → RUNNING (acquire app lock first per resource policy)
        connector_id = "hull_preview" if action == "hull.preview_calculation" else action.split(".")[0]
        connector_id = {"rhino": "rhino6"}.get(connector_id, connector_id)
        lock_acquired = True if action == "hull.preview_calculation" else acquire_app_lock(connector_id, task_id, timeout_s=60.0)
        if not lock_acquired:
            # Task stays in QUEUED; user can retry or cancel. No state corruption.
            raise HTTPException(
                status_code=503,
                detail=f"Another task is using {connector_id}. Task remains in QUEUED. Retry or cancel.",
            )

        try:
            # Step 6b: QUEUED → RUNNING once; later steps remain RUNNING.
            if step_idx == 0:
                await transition_task(task_id, "start_execution", TaskStatus.RUNNING)

            # Hull preview calculation: deterministic calc, no connector claim
            if action == "hull.preview_calculation":
                from nei.engineering.hull import HullDesignRequest, hull_preview, record_hull_run
                hull = HullDesignRequest.model_validate(hull_design)
                result = hull_preview(hull)
                from nei.engineering.report import build_hull_report
                from nei.core import artifact_store
                report = build_hull_report(
                    task_id=task_id,
                    hull=hull.model_dump(),
                    preview=result,
                )
                report_content = _json.dumps(report, indent=2, sort_keys=True).encode()
                report_sha = await artifact_store.save_artifact(task_id, "hull_engineering_report.json", report_content)
                result["report_artifact"] = {
                    "filename": "hull_engineering_report.json",
                    "sha256": report_sha,
                    "status": report["status"],
                }
                run_id = await record_hull_run(task_id, hull, result)
                async with get_db() as db:
                    await db.execute("UPDATE tasks SET calc_run_ids = ? WHERE id = ?", (_json.dumps([run_id]), task_id))
                    await db.commit()
                continue

            # Step 7: Resolve connector from registry
            cls = get_connector_class(connector_id)
            if cls is None:
                await transition_task(task_id, "connector_unknown", TaskStatus.FAILED,
                                      {"action": action, "connector": connector_id})
                raise HTTPException(status_code=400, detail=f"Unknown connector: {connector_id}")

            # Step 8: Instantiate connector with optional exe_path
            kwargs = {}
            if connector_id == "solidworks2022":
                kwargs["exe_path"] = settings.solidworks_exe_path
            elif connector_id == "rhino6":
                kwargs["rhino_exe"] = settings.rhino_exe_path
            conn = cls(**kwargs)

            # Step 9: Validate advertised capability before execution.
            capabilities = {cap.name: cap.status.value for cap in conn.get_capabilities()}
            capability = capabilities.get(action)
            if capability in {"UNSUPPORTED", "UNAVAILABLE"}:
                await transition_task(task_id, "capability_unavailable", TaskStatus.FAILED,
                                      {"action": action, "capability": capability})
                raise HTTPException(status_code=400, detail=f"Capability unavailable: {action}")
            if capability is None:
                await transition_task(task_id, "capability_unknown", TaskStatus.FAILED,
                                      {"action": action})
                raise HTTPException(status_code=400, detail=f"Capability unknown: {action}")
            parameter_error = conn.validate_parameters(action, params)
            if parameter_error:
                await transition_task(task_id, "parameters_invalid", TaskStatus.FAILED,
                                      {"action": action, "error": parameter_error})
                raise HTTPException(status_code=400, detail=parameter_error)

            # Resolve validated input artifact before connector execution.
            if step_idx > 0 and handoff_chain:
                params.setdefault("input_artifact", handoff_chain[-1].file_path)
                validate_handoff_artifact(
                    handoff_chain[-1], task.get("path_root") or str(PROJECTS_ROOT), task["project_id"]
                )

            # Step 10: Execute connector action; unexpected connector errors fail task.
            try:
                result = conn.execute(action, params, timeout_s=60)
            except TimeoutError as exc:
                await transition_task(task_id, "execution_timeout", TaskStatus.FAILED,
                                      {"action": action, "error": str(exc) or "connector timeout"})
                raise HTTPException(status_code=504, detail="Connector execution timed out") from exc
            except Exception as exc:
                await transition_task(task_id, "execution_exception", TaskStatus.FAILED,
                                      {"action": action, "error": type(exc).__name__})
                raise HTTPException(status_code=500, detail="Connector execution failed") from exc

            async with get_db() as db:
                await db.execute(
                    "UPDATE tasks SET tool_calls_json = ?, software_versions_json = ? WHERE id = ?",
                    (_json.dumps({"action": action, "params": params, "result": result.__dict__}),
                     _json.dumps({connector_id: conn.get_version() or "unknown"}), task_id),
                )
                await log_event(db, task_id=task_id, event_type="EXECUTE_ACTION",
                                detail_json={"action": action, "params": params,
                                            "success": result.success})
                await db.commit()

            if not result.success:
                await transition_task(task_id, "execution_failed", TaskStatus.FAILED,
                                      {"action": action, "error": result.error})
                raise HTTPException(status_code=500, detail=result.error or "Connector execution failed")

            # Step 10: Record handoff artifact if this step produces one
            if action.endswith(".export_copy"):
                handoff_artifact = result.data.get("artifact_bytes")
                handoff_filename = result.data.get("artifact_filename")
                if handoff_artifact and handoff_filename:
                    hop = save_handoff_file(
                        project_root=task.get("path_root") or str(PROJECTS_ROOT / task["project_id"]),
                        project_id=task["project_id"],
                        source_bytes=handoff_artifact,
                        filename=handoff_filename,
                        software=connector_id,
                        software_version=conn.get_version() or "unknown",
                        unit=params.get("unit", "mm"),
                        file_format=params.get("format", "STEP"),
                    )
                    validate_handoff_artifact(
                        hop, task.get("path_root") or str(PROJECTS_ROOT), task["project_id"]
                    )
                    handoff_chain.append(hop)

            # Keep task RUNNING until all plan steps finish. Final verification is below.

        finally:
            if action != "hull.preview_calculation":
                release_app_lock(connector_id, task_id)

    # Final verification runs once after every step, preserving multi-step state flow.
    await transition_task(task_id, "execution_complete", TaskStatus.VERIFYING, {"steps": len(plan.steps)})
    from nei.core.task_manager import verify_task
    if plan.steps[-1].action == "hull.preview_calculation":
        final_result = result
        inputs = result.get("inputs", {}) or {}
        volume = (result.get("calculations") or {}).get("displacement_volume_m3")
        from nei.verification.postconditions import DimensionsCheck, VolumeCheck, StabilityCheck
        hull_conditions = [
            DimensionsCheck(loa=inputs.get("loa", 0), beam=inputs.get("beam", 0),
                            depth=inputs.get("depth", 0), draft=inputs.get("draft", 0)),
            StabilityCheck(beam=inputs.get("beam", 0), draft=inputs.get("draft", 0)),
        ]
        if volume is not None:
            hull_conditions.append(VolumeCheck(expected_volume=volume))
        await verify_task(task_id, final_result, "NEI deterministic preview", hull_conditions)
        return await get_task(task_id)
    final_result = result.data
    if plan.steps[-1].action == "rhino.create_box_test":
        final_conditions = rhino_box_postconditions(
            plan.steps[-1].params.get("length", 10.0),
            plan.steps[-1].params.get("width", 3.0),
            plan.steps[-1].params.get("height", 1.0),
        )
    elif plan.steps[-1].action == "rhino.export_copy":
        final_conditions = rhino_export_copy_postconditions(
            filename=final_result.get("artifact_filename", ""),
            expected_sha256=final_result.get("artifact_sha256"),
        )
    else:
        final_conditions = []
    # Persist provenance before final verification can terminate execution.
    if handoff_chain:
        write_provenance_manifest(
            project_root=task.get("path_root") or str(PROJECTS_ROOT / task["project_id"]),
            project_id=task["project_id"],
            task_id=task_id,
            chain=handoff_chain,
        )

    await verify_task(task_id, final_result, conn.get_version() or "unknown", final_conditions)
    return await get_task(task_id)
