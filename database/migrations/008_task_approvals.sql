-- NEI migration 008: task-level approval decisions (Phase 2 spec).
-- Records explicit approve/reject actions for a task so the decision trail is auditable.

CREATE TABLE IF NOT EXISTS task_approvals (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    action TEXT NOT NULL CHECK (action IN ('approve', 'reject')),
    reason TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_task_approvals_task ON task_approvals(task_id);
