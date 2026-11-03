"""Pydantic request/response models matching DATABASE_SCHEMA.md."""
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class Project(ProjectCreate):
    id: str
    path_root: str
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    user_request: str
    task_type: str = "geometry"
    domain: str = "naval_architecture"
    risk_level: str = "L0"


class Task(TaskCreate):
    id: str
    project_id: str
    state: str
    plan_json: Optional[str] = None
    verification_json: Optional[str] = None
    errors_json: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class VerifyRequest(BaseModel):
    """Payload for POST /tasks/{id}/verify."""
    connector_result: dict[str, Any]
    software_version: str
    length: float
    width: float
    height: float


ALLOWED_ACTIONS = {
    "rhino.create_box_test",
    "rhino.inspect_objects",
    "rhino.get_document_info",
}


class ExecuteRequest(BaseModel):
    """Payload for POST /tasks/{id}/execute."""
    action: str
    params: dict[str, Any] = {}
