"""Artifact store: SHA-256 integrity, path sandboxing, status tracking."""
import os
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional

from nei.core.config import settings

ARTIFACTS_ROOT = Path("data/artifacts")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_path(task_id: str, filename: str) -> Path:
    """Task-specific sandbox under data/artifacts/<task_id>/<filename>.

    Defense-in-depth: even if _sanitize_name is bypassed, the resolved path
    must stay inside ARTIFACTS_ROOT.
    """
    base = (ARTIFACTS_ROOT / task_id / filename).resolve()
    root = ARTIFACTS_ROOT.resolve()
    try:
        base.relative_to(root)
    except ValueError:
        raise ValueError(f"Path traversal rejected: {filename!r}")
    return base


def _sanitize_name(name: str, kind: str = "filename") -> str:
    """Reject filenames containing path separators or traversal sequences."""
    if not name or "/" in name or "\\" in name or ".." in name or name in (".", ".."):
        raise ValueError(f"Invalid {kind}: {name!r}")
    return name


async def save_artifact(task_id: str, filename: str, content: bytes) -> str:
    """Save artifact, return sha256. Rejects path traversal in filename."""
    _sanitize_name(task_id, "task_id")
    _sanitize_name(filename, "filename")
    path = _safe_path(task_id, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    return _sha256(content)


async def load_artifact(task_id: str, filename: str) -> bytes | None:
    """Load artifact by task_id + filename. Rejects path traversal."""
    _sanitize_name(task_id, "task_id")
    _sanitize_name(filename, "filename")
    path = _safe_path(task_id, filename)
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return f.read()


async def verify_artifact(task_id: str, filename: str, expected_sha: str) -> bool:
    """Verify SHA-256 matches. Rejects path traversal."""
    _sanitize_name(task_id, "task_id")
    _sanitize_name(filename, "filename")
    path = _safe_path(task_id, filename)
    if not path.exists():
        return False
    with open(path, "rb") as f:
        actual = _sha256(f.read())
    return actual == expected_sha


async def list_artifacts(task_id: str) -> List[Dict]:
    """List artifacts for a task."""
    task_dir = ARTIFACTS_ROOT / task_id
    if not task_dir.exists():
        return []
    return [
        {
            "filename": p.name,
            "path": str(p),
            "sha256": _sha256(p.read_bytes()),
            "size_bytes": p.stat().st_size,
            "created_at": datetime.fromtimestamp(p.stat().st_ctime).isoformat(),
        }
        for p in task_dir.iterdir() if p.is_file()
    ]