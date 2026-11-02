"""Artifact store service."""
import os
import shutil
from pathlib import Path
from datetime import datetime
import hashlib

from nei.core.config import settings

ARTIFACTS_DIR = settings.artifacts_path


def get_artifact_path(task_id: str, filename: str) -> Path:
    """Get secure path for artifact."""
    target_dir = ARTIFACTS_DIR / task_id
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / filename


def save_artifact(task_id: str, filename: str, content: bytes) -> str:
    """Save artifact and return hash."""
    path = get_artifact_path(task_id, filename)
    with open(path, "wb") as f:
        f.write(content)
        
    # Generate hash
    sha256 = hashlib.sha256()
    sha256.update(content)
    return sha256.hexdigest()
