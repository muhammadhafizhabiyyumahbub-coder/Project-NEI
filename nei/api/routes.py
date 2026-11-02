"""API routes."""
import uuid
import json
import datetime
from fastapi import APIRouter, HTTPException
from nei.core.database import get_db
from nei.core.state_machine import TaskStatus, TaskStateTransition
from nei.api import models

router = APIRouter()


@router.get("/projects", response_model=list[models.Project])
async def list_projects():
    async with await get_db() as db:
        rows = await db.execute_fetchall("SELECT * FROM projects ORDER BY created_at DESC")
    return [{
        "id": r[0], "name": r[1], "vessel_type": r[2],
        "description": r[3], "created_at": r[4], "updated_at": r[5]
    } for r in rows]


@router.post("/projects", response_model=models.Project)
async def create_project(project: models.ProjectCreate):
    pid = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat()
    async with await get_db() as db:
        await db.execute(
            "INSERT INTO projects (id, name, vessel_type, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (pid, project.name, project.vessel_type, project.description, now, now)
        )
        await db.commit()
    return {**project.model_dump(), "id": pid, "created_at": now, "updated_at": now}


@router.post("/tasks", response_model=models.Task)
async def create_task(task: models.TaskCreate):
    tid = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat()
    async with await get_db() as db:
        await db.execute(
            """INSERT INTO tasks (id, project_id, action, target, params, risk_level, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (tid, task.project_id, task.action, task.target,
             json.dumps(task.params) if task.params else None,
             task.risk_level, TaskStatus.PENDING.value, now)
        )
        await db.commit()
    return {**task.model_dump(), "id": tid, "status": TaskStatus.PENDING.value,
            "created_at": now, "started_at": None, "completed_at": None,
            "result": None, "verification_json": None, "error": None}


@router.get("/tasks/{task_id}", response_model=models.Task)
async def get_task(task_id: str):
    async with await get_db() as db:
        rows = await db.execute_fetchall("SELECT * FROM tasks WHERE id = ?", (task_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Task not found")
    row = rows[0]
    return {
        "id": row[0], "project_id": row[1], "status": row[2],
        "action": row[3], "target": row[4],
        "params": json.loads(row[5]) if row[5] else None,
        "risk_level": row[6], "result": row[7],
        "verification_json": json.loads(row[8]) if row[8] else None,
        "error": row[9], "created_at": row[10],
        "started_at": row[11], "completed_at": row[12]
    }
