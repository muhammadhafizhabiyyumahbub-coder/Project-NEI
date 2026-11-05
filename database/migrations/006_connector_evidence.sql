-- NEI migration 006: connector evidence audit trail.
-- Records verified probe artifacts and inspection results for traceability.

CREATE TABLE IF NOT EXISTS connector_evidence (
    id TEXT PRIMARY KEY,
    connector_id TEXT NOT NULL,
    capability_name TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    artifact_path TEXT,
    artifact_sha256 TEXT,
    metadata_json TEXT,
    verified_at TEXT NOT NULL,
    verified_by TEXT DEFAULT 'system',
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_connector_evidence_connector ON connector_evidence(connector_id);
CREATE INDEX IF NOT EXISTS idx_connector_evidence_capability ON connector_evidence(capability_name);
CREATE INDEX IF NOT EXISTS idx_connector_evidence_verified ON connector_evidence(verified_at);
