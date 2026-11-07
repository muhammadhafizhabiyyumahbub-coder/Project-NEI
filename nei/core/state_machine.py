"""Task lifecycle state machine.

Implements the transition table from STATE_MACHINE_SPEC.md.
"""
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    PLANNING = "planning"
    NEEDS_INPUT = "needs_input"
    VALIDATING = "validating"
    WAITING_APPROVAL = "waiting_approval"
    QUEUED = "queued"
    RUNNING = "running"
    VERIFYING = "verifying"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NEEDS_REVIEW = "needs_review"


class TaskStateTransition:
    """Legal transitions and their side effects."""

    VALID = {
        TaskStatus.PENDING: [TaskStatus.PLANNING, TaskStatus.CANCELLED],
        TaskStatus.PLANNING: [TaskStatus.NEEDS_INPUT, TaskStatus.VALIDATING, TaskStatus.CANCELLED],
        TaskStatus.NEEDS_INPUT: [TaskStatus.PLANNING, TaskStatus.CANCELLED],
        TaskStatus.VALIDATING: [TaskStatus.WAITING_APPROVAL, TaskStatus.QUEUED, TaskStatus.FAILED, TaskStatus.CANCELLED],
        TaskStatus.WAITING_APPROVAL: [TaskStatus.QUEUED, TaskStatus.CANCELLED, TaskStatus.NEEDS_REVIEW],
        TaskStatus.QUEUED: [TaskStatus.RUNNING, TaskStatus.CANCELLED],
        TaskStatus.RUNNING: [TaskStatus.VERIFYING, TaskStatus.RECOVERING, TaskStatus.FAILED, TaskStatus.CANCELLED],
        TaskStatus.VERIFYING: [TaskStatus.COMPLETED, TaskStatus.NEEDS_REVIEW, TaskStatus.FAILED],
        TaskStatus.RECOVERING: [TaskStatus.QUEUED, TaskStatus.FAILED, TaskStatus.CANCELLED],
        TaskStatus.COMPLETED: [],
        TaskStatus.FAILED: [],
        TaskStatus.CANCELLED: [],
        TaskStatus.NEEDS_REVIEW: [],
    }

    @classmethod
    def can_transition(cls, from_status: TaskStatus, to_status: TaskStatus) -> bool:
        return to_status in cls.VALID[from_status]

    @classmethod
    def is_terminal(cls, status: TaskStatus) -> bool:
        return status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
