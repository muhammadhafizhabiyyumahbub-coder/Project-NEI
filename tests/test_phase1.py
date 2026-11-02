"""Phase 1 self-checks: state machine and policy gate."""
import pytest
from nei.core.state_machine import TaskStatus, TaskStateTransition
from nei.core.policy import check_policy


def test_valid_transitions():
    assert TaskStateTransition.can_transition(TaskStatus.PENDING, TaskStatus.PLANNING)
    assert TaskStateTransition.can_transition(TaskStatus.PENDING, TaskStatus.POLICY_CHECK)
    assert TaskStateTransition.can_transition(TaskStatus.EXECUTING, TaskStatus.VERIFYING)
    assert TaskStateTransition.can_transition(TaskStatus.VERIFYING, TaskStatus.COMPLETED)
    assert TaskStateTransition.can_transition(TaskStatus.FAILED, TaskStatus.RECOVERING)


def test_invalid_transitions():
    assert not TaskStateTransition.can_transition(TaskStatus.PENDING, TaskStatus.COMPLETED)
    assert not TaskStateTransition.can_transition(TaskStatus.COMPLETED, TaskStatus.PENDING)
    assert not TaskStateTransition.can_transition(TaskStatus.PENDING, TaskStatus.EXECUTING)


def test_policy_allows_l0_l1():
    assert check_policy("create_box", "L0")
    assert check_policy("create_box", "L1")


def test_policy_blocks_l2_l3():
    assert not check_policy("delete_all", "L2")
    assert not check_policy("delete_all", "L3")


def test_policy_blocks_unknown_risk():
    assert not check_policy("mystery", "L9")
