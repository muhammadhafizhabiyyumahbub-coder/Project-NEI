"""Policy gate: risk levels + path sandbox enforcement.

Alpha 0.1 (Phase 1-3): L0/L1 auto-approved; L2 requires human approval (WAITING_APPROVAL);
L3 disallowed entirely.
"""
from pathlib import PureWindowsPath
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
    """Check a path stays within the project's sandbox root."""
    root = PureWindowsPath(project_root)
    target = PureWindowsPath(path)
    if not target.is_absolute():
        target = root / target
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False
