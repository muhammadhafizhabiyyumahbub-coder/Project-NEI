"""API routes matching PLAN.md Phase 1 acceptance criteria.

Endpoints:
  GET    /health
  GET    /projects
  POST   /projects
  POST   /projects/{project_id}/tasks
  GET    /tasks/{task_id}
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

    created = await create_task(
        project_id=project_id,
        user_request=task.user_request,
        task_type=task.task_type,
        domain=task.domain,
        risk_level=task.risk_level,
    )
    async with get_db() as db:
        await log_event(db, task_id=created["id"], event_type="TASK_CREATED",
                        detail_json={"request": task.user_request, "risk": task.risk_level})
        await db.commit()
    return created


@router.get("/tasks/{task_id}", response_model=models.Task)
async def get_task_endpoint(task_id: str):
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/cancel", response_model=models.Task)
async def cancel_task_endpoint(task_id: str):
    cancelled = await cancel_task(task_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Task not found")
    return cancelled
