"""Policy engine for action gates."""
from nei.core.state_machine import TaskStatus

RISK_LEVELS = ["L0", "L1", "L2", "L3"]

def check_policy(action: str, risk_level: str) -> bool:
    """Verify if action is allowed by policy."""
    # Placeholder: Alpha 0.1 only allows L0/L1
    if risk_level not in ["L0", "L1"]:
        return False
    return True
