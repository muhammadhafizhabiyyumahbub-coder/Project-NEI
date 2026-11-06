-- NEI migration 007: explicit engineering approval state.
-- Approval is separate from connector capability and automated verification.

CREATE TABLE IF NOT EXISTS engineering_approvals (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    artifact_sha256 TEXT,
    status TEXT NOT NULL CHECK (status IN ('not_performed', 'pending', 'approved', 'rejected')),
    reviewed_by TEXT,
    reason TEXT,
    created_at TEXT NOT NULL,
    reviewed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_engineering_approvals_task ON engineering_approvals(task_id);
CREATE INDEX IF NOT EXISTS idx_engineering_approvals_status ON engineering_approvals(status);
