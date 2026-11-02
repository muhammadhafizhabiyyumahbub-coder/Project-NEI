"""State machine for task lifecycle."""
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    PLANNING = "planning"
    POLICY_CHECK = "policy_check"
    APPROVED = "approved"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERING = "recovering"


class TaskStateTransition:
    """Valid state transitions for tasks."""
    
    VALID = {
        TaskStatus.PENDING: [TaskStatus.PLANNING, TaskStatus.POLICY_CHECK],
        TaskStatus.PLANNING: [TaskStatus.POLICY_CHECK, TaskStatus.PENDING],
        TaskStatus.POLICY_CHECK: [TaskStatus.APPROVED, TaskStatus.PENDING],
        TaskStatus.APPROVED: [TaskStatus.EXECUTING, TaskStatus.PENDING],
        TaskStatus.EXECUTING: [TaskStatus.VERIFYING, TaskStatus.FAILED],
        TaskStatus.VERIFYING: [TaskStatus.COMPLETED, TaskStatus.FAILED],
        TaskStatus.COMPLETED: [],
        TaskStatus.FAILED: [TaskStatus.RECOVERING],
        TaskStatus.RECOVERING: [TaskStatus.PENDING, TaskStatus.FAILED],
    }

    @classmethod
    def can_transition(cls, from_status: TaskStatus, to_status: TaskStatus) -> bool:
        """Check if transition is valid."""
        return to_status in cls.VALID[from_status]
