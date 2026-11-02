"""Pydantic request/response models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str
    vessel_type: Optional[str] = None
    description: Optional[str] = None


class Project(ProjectCreate):
    id: str
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    project_id: str
    action: str
    target: Optional[str] = None
    params: Optional[Any] = None
    risk_level: str = "L0"


class Task(TaskCreate):
    id: str
    status: str
    result: Optional[str] = None
    verification_json: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
