"""Policy gate: risk levels + path sandbox enforcement.

Alpha 0.1 (Phase 1-3): L0/L1 auto-approved; L2 requires human approval (WAITING_APPROVAL);
L3 disallowed entirely.
"""
from pathlib import Path, PureWindowsPath
import os
from typing import Set

ALLOWED_RISK = {"L0", "L1"}
REQUIRES_APPROVAL = {"L2"}
FORBIDDEN = {"L3"}


def risk_allows_autopass(risk_level: str) -> bool:
    """True if risk_level can skip WAITING_APPROVAL."""
    return risk_level in ALLOWED_RISK


def risk_requires_approval(risk_level: str) -> bool:
    return risk_level in REQUIRES_APPROVAL


def risk_forbidden(risk_level: str) -> bool:
    return risk_level in FORBIDDEN


def validate_sandbox_path(path: str, project_root: str) -> bool:
    """Check a path stays within the project's sandbox root.

    Both paths are normalized (``..``, symlinks) before comparison, which is
    case-insensitive on Windows. Invalid roots and other drives are rejected.
    """
    try:
        root = Path(project_root).resolve(strict=False)
        target = Path(path)
        if not target.is_absolute():
            target = root / target
        target = target.resolve(strict=False)
    except (OSError, ValueError):
        return False

    if not root.exists():
        return False
    if os.path.normcase(root.drive) != os.path.normcase(target.drive):
        return False

    root_s = os.path.normcase(str(root))
    target_s = os.path.normcase(str(target))
    try:
        return os.path.commonpath([root_s, target_s]) == root_s
    except ValueError:
        return False
