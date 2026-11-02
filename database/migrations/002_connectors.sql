-- NEI migration 002: connectors + probes (Phase 3).
-- Registered connector metadata and probe history.

CREATE TABLE IF NOT EXISTS connectors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    version TEXT,
    exe_path TEXT,
    bitness TEXT,
    last_probe_ts TEXT
);

CREATE TABLE IF NOT EXISTS connector_probes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connector_id TEXT NOT NULL REFERENCES connectors(id),
    probe_type TEXT NOT NULL,
    result_json TEXT,
    timestamp TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_connector_probes_connector ON connector_probes(connector_id, timestamp);
