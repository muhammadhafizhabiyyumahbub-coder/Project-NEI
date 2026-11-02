# NEI — State Machine Specification

**Scope:** Task lifecycle states and all legal transitions.
**Source of truth:** `STATE_MACHINE_SPEC.md` (this file). Implementation: `nei/core/state_machine.py`.

---

## States

### Active states (task can progress forward)
| State | Meaning |
|-------|---------|
| `PLANNING` | Planner is building/validating the execution plan |
| `NEEDS_INPUT` | Waiting for user to supply missing engineering inputs |
| `VALIDATING` | Policy gate checking paths, risk, preconditions |
| `WAITING_APPROVAL` | Waiting for human approval (L2+ actions) |
| `QUEUED` | Approved, waiting for connector lock / resource |
| `RUNNING` | Actively executing tool calls in software |
| `VERIFYING` | Postcondition checks against software result |
| `RECOVERING` | Software hung or crashed; attempting graceful detach |

### Terminal states (no forward transition)
| State | Meaning |
|-------|---------|
| `COMPLETED` | All postconditions verified; artifact saved |
| `FAILED` | Irrecoverable error; user must create new task or retry |
| `CANCELLED` | User explicitly cancelled; no retry from this state |
| `NEEDS_REVIEW` | Verification or execution completed but result requires human review before acceptance |

---

## Transition table

| From | Event | Guard | To | Side effect |
|------|-------|-------|----|
| *(task created)* | `created` | — | `PENDING` | `task_events` row written; `created_at` set |
| `PENDING` | `planning_start` | plan schema valid | `PLANNING` | `started_at` set |
| `PLANNING` | `plan_needs_input` | planner found missing fields | `NEEDS_INPUT` | `plan_json` saved with `required_inputs` |
| `PLANNING` | `plan_complete` | all required inputs present | `VALIDATING` | `plan_json` finalized |
| `NEEDS_INPUT` | `input_provided` | user submitted valid inputs | `PLANNING` | inputs merged into plan |
| `NEEDS_INPUT` | `user_cancelled` | — | `CANCELLED` | `task_events` row |
| `VALIDATING` | `validation_passed` | policy gate: paths OK, risk known | `WAITING_APPROVAL` (if L2+) **or** `QUEUED` (if L0/L1) | `approval` row created if L2+ |
| `VALIDATING` | `validation_failed` | path forbidden / risk too high | `FAILED` | `errors_json` set |
| `WAITING_APPROVAL` | `approved` | `approvals.status=APPROVED` and `payload_hash` matches | `QUEUED` | `approval_ids` updated |
| `WAITING_APPROVAL` | `rejected` | `approvals.status=REJECTED` | `CANCELLED` | `task_events` row |
| `WAITING_APPROVAL` | `payload_changed` | plan/params modified after approval request | `WAITING_APPROVAL` | old approval invalidated; new approval requested |
| `WAITING_APPROVAL` | `user_cancelled` | — | `CANCELLED` | |
| `QUEUED` | `lock_acquired` | resource manager grants app lock | `RUNNING` | lock held until task terminal |
| `QUEUED` | `user_cancelled` | — | `CANCELLED` | lock released |
| `RUNNING` | `all_steps_done` | every tool call returned | `VERIFYING` | raw results in memory |
| `RUNNING` | `timeout` | connector op exceeded `timeout_seconds` | `RECOVERING` | attempt graceful detach |
| `RUNNING` | `connector_error` | unrecoverable connector failure | `FAILED` | `errors_json` set |
| `RUNNING` | `user_cancelled` | — | `CANCELLED` | release lock; detach if needed |
| `VERIFYING` | `all_postconditions_passed` | every check PASSED within tolerance | `COMPLETED` | artifact saved; `completed_at` set |
| `VERIFYING` | `postcondition_failed` | one or more checks FAILED | `NEEDS_REVIEW` | verification record saved with failed checks |
| `RECOVERING` | `software_back` | connector `health_check` returns OK (automatic, no user action needed) | `QUEUED` | re-acquire lock; re-execute from last step |
| `RECOVERING` | `emergency_timeout` | > 300s (configurable) | `FAILED` | `errors_json` set with incident detail |
| `RECOVERING` | `user_cancelled` | — | `CANCELLED` | |
| `NEEDS_REVIEW` | `user_retry` | — | *(new task)* | new task created with `parent_task_id`; original stays terminal |

---

## Rules

1. **COMPLETED requires verification.** A script returning exit code 0 does NOT transition to `COMPLETED`. The verification engine must run all declared postconditions and report PASSED.

2. **Every transition is audited.** Each transition writes exactly one `task_events` row: `from_state`, `to_state`, `event`, `timestamp`, and any relevant `metadata_json`.

3. **Illegal transitions are rejected.** If an event is not in the table for the current state, the API returns `STATE_TRANSITION_INVALID` (409) and no state change occurs.

4. **Retries create new tasks.** `FAILED` and `NEEDS_REVIEW` tasks are terminal. A retry creates a new task linked via `parent_task_id`. The original task record is preserved for audit.

5. **Cancellation is immediate.** `user_cancelled` is legal from any active state. The task transitions directly to `CANCELLED`; no intermediate states.

6. **Locks released on all terminal transitions.** `CANCELLED`, `FAILED`, and `COMPLETED` release the app lock. `NEEDS_REVIEW` holds the lock until the user explicitly cancels or retries (new task acquires lock).

7. **RECOVERING is not a retry.** It is the same task continuing after a software fault. The last completed step is recorded in `tool_calls_json`; execution resumes from the next step.

---

## Timeout configuration

| Timeout | Default | Configurable | Notes |
|---------|---------|-------------|-------|
| Connector operation | 300s | `NEI_CONNECTOR_TIMEOUT_S` | Per tool action `timeout_seconds` in plan |
| Emergency recovery | 300s | `NEI_EMERGENCY_TIMEOUT_S` | After this in RECOVERING → FAILED |
| LLM call | 60s | `NEI_LLM_TIMEOUT_S` | On timeout: task → NEEDS_INPUT |
| SSE keepalive | 30s | fixed | No configuration |

---

## State diagram (text)

```
PENDING
  │ planning_start
  ▼
PLANNING ◄────────────────────────┐
  │ plan_complete                  │ input_provided
  ▼                                │
VALIDATING                         │
  │ validation_passed              │
  ▼ (L2+)                          │
WAITING_APPROVAL ── rejected ──► CANCELLED
  │ approved                       │
  ▼ (L0/L1 direct)                 │
QUEUED ◄───────────────────────────┘
  │ lock_acquired
  ▼
RUNNING
  │ all_steps_done          timeout
  ▼                         ▼
VERIFYING              RECOVERING
  │ all_passed            │ software_back
  ▼                      ▼
COMPLETED             QUEUED (resume)
  │
  │ postcondition_failed
  ▼
NEEDS_REVIEW  (terminal; retry → new task)

FAILED  (terminal; retry → new task)
CANCELLED (terminal)
```
