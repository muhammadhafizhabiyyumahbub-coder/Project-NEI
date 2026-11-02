# NEI — Database Schema

**Engine:** SQLite, WAL mode, single writer (FastAPI process).
**File:** `data/nei.db`
**Migrations:** Sequential SQL in `nei/storage/migrations/`, tracked in `schema_migrations`.

> After Phase 1, the Pydantic models and migration files in code are the source of truth.
> This document records the planned schema and rationale.

---

## Phase 1–2 tables (FULL spec)

### `projects`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | TEXT(36) | PK, UUIDv4 | |
| name | TEXT | NOT NULL | |
| description | TEXT | | nullable |
| created_at | TEXT | NOT NULL, DEFAULT | ISO 8601 UTC |
| updated_at | TEXT | NOT NULL, DEFAULT | |
| path_root | TEXT | NOT NULL | Absolute path to `data/projects/<id>/` |

```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    path_root TEXT NOT NULL
);
```

**Why:** One project = one workspace. `path_root` enables artifact sandboxing.

---

### `tasks`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | TEXT(36) | PK, UUIDv4 | |
| project_id | TEXT(36) | NOT NULL, FK→projects.id | |
| parent_task_id | TEXT(36) | FK→tasks.id, nullable | retry link |
| user_request | TEXT | NOT NULL | original NL request |
| task_type | TEXT | NOT NULL | e.g. `geometry`, `hydrostatics` |
| domain | TEXT | NOT NULL | engineering domain |
| risk_level | TEXT | NOT NULL | `L0`/`L1`/`L2`/`L3` |
| state | TEXT | NOT NULL | see `STATE_MACHINE_SPEC.md` |
| plan_json | TEXT | | serialized Plan (Pydantic) |
| tool_calls_json | TEXT | | array of executed tool calls |
| input_artifact_ids | TEXT | | JSON array of UUIDs |
| output_artifact_ids | TEXT | | JSON array of UUIDs |
| evidence_ref_ids | TEXT | | JSON array of source IDs (Phase 4+) |
| calc_run_ids | TEXT | | JSON array of calculation run IDs (Phase 5+) |
| approval_ids | TEXT | | JSON array of approval UUIDs |
| software_versions_json | TEXT | | `{"rhino6": "6.x", ...}` |
| errors_json | TEXT | | array of error objects |
| warnings_json | TEXT | | array of warning strings |
| connector_id | TEXT | nullable | which connector was used |
| schema_version | INTEGER | NOT NULL, DEFAULT 1 | |
| created_at | TEXT | NOT NULL | |
| started_at | TEXT | | nullable |
| completed_at | TEXT | | nullable |

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    parent_task_id TEXT REFERENCES tasks(id),
    user_request TEXT NOT NULL,
    task_type TEXT NOT NULL,
    domain TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    state TEXT NOT NULL,
    plan_json TEXT,
    tool_calls_json TEXT,
    input_artifact_ids TEXT,
    output_artifact_ids TEXT,
    evidence_ref_ids TEXT,
    calc_run_ids TEXT,
    approval_ids TEXT,
    software_versions_json TEXT,
    errors_json TEXT,
    warnings_json TEXT,
    connector_id TEXT,
    schema_version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT
);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_state ON tasks(state);
CREATE INDEX idx_tasks_parent ON tasks(parent_task_id);
```

**Why:** Task is the central unit. JSON columns for multi-valued refs avoid join tables in a local single-writer DB. `plan_json` stores the full structured plan for audit.

---

### `task_events`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PK, AUTOINCREMENT | |
| task_id | TEXT(36) | NOT NULL, FK→tasks.id | |
| from_state | TEXT | | nullable (first event: NULL) |
| to_state | TEXT | NOT NULL | |
| event | TEXT | NOT NULL | trigger, e.g. `planning_done`, `approval_granted` |
| metadata_json | TEXT | | extra context |
| timestamp | TEXT | NOT NULL | |

```sql
CREATE TABLE task_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    from_state TEXT,
    to_state TEXT NOT NULL,
    event TEXT NOT NULL,
    metadata_json TEXT,
    timestamp TEXT NOT NULL
);
CREATE INDEX idx_task_events_task ON task_events(task_id, timestamp);
```

**Why:** Audit trail of every state transition. Required by `STATE_MACHINE_SPEC.md`.

---

### `approvals`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | TEXT(36) | PK, UUIDv4 | |
| task_id | TEXT(36) | NOT NULL, FK→tasks.id | |
| payload_hash | TEXT | NOT NULL | SHA-256 of exact action payload |
| approved_by | TEXT | NOT NULL | `user` (local, no password) |
| status | TEXT | NOT NULL | `PENDING`/`APPROVED`/`REJECTED` |
| reason | TEXT | | reject reason |
| requested_at | TEXT | NOT NULL | |
| decided_at | TEXT | | nullable |

```sql
CREATE TABLE approvals (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    payload_hash TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT,
    requested_at TEXT NOT NULL,
    decided_at TEXT
);
CREATE INDEX idx_approvals_task ON approvals(task_id);
```

**Why:** Approval is bound to exact payload. If payload changes, old approval is invalid.

---

### `artifacts`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | TEXT(36) | PK, UUIDv4 | |
| project_id | TEXT(36) | NOT NULL, FK→projects.id | |
| task_id | TEXT(36) | FK→tasks.id, nullable | |
| filename | TEXT | NOT NULL | |
| path | TEXT | NOT NULL | relative to `data/` root |
| sha256 | TEXT | NOT NULL | computed on write |
| size_bytes | INTEGER | NOT NULL | |
| status | TEXT | NOT NULL | `ACTIVE`/`CORRUPT`/`DELETED` |
| created_at | TEXT | NOT NULL | |

```sql
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    task_id TEXT REFERENCES tasks(id),
    filename TEXT NOT NULL,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_artifacts_project ON artifacts(project_id);
CREATE INDEX idx_artifacts_task ON artifacts(task_id);
```

**Why:** SHA-256 integrity check on every read. `status=CORRUPT` triggers re-download or user action.

---

### `audit_events`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PK, AUTOINCREMENT | |
| timestamp | TEXT | NOT NULL | |
| task_id | TEXT(36) | nullable | |
| step_id | TEXT | nullable | |
| event_type | TEXT | NOT NULL | `TASK_CREATED`, `TOOL_CALL`, `ARTIFACT_SAVED`, ... |
| detail_json | TEXT | | full event payload |
| model_id | TEXT | | LLM model if called |
| prompt_template_version | TEXT | | |
| tool_name | TEXT | | |
| tool_version | TEXT | | |
| connector_version | TEXT | | |
| script_hash | TEXT | | SHA-256 of executed script |
| token_usage | TEXT | | `{"prompt":123,"completion":456}` |
| est_cost | TEXT | | |

```sql
CREATE TABLE audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    task_id TEXT,
    step_id TEXT,
    event_type TEXT NOT NULL,
    detail_json TEXT,
    model_id TEXT,
    prompt_template_version TEXT,
    tool_name TEXT,
    tool_version TEXT,
    connector_version TEXT,
    script_hash TEXT,
    token_usage TEXT,
    est_cost TEXT
);
CREATE INDEX idx_audit_ts ON audit_events(timestamp);
CREATE INDEX idx_audit_task ON audit_events(task_id);
```

**Why:** Observability and reproducibility. No secrets in this table.

---

### `model_usage`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PK, AUTOINCREMENT | |
| task_id | TEXT(36) | nullable | |
| provider | TEXT | NOT NULL | |
| model | TEXT | NOT NULL | |
| prompt_tokens | INTEGER | NOT NULL | |
| completion_tokens | INTEGER | NOT NULL | |
| est_cost | REAL | | |
| latency_ms | INTEGER | | |
| timestamp | TEXT | NOT NULL | |

```sql
CREATE TABLE model_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    est_cost REAL,
    latency_ms INTEGER,
    timestamp TEXT NOT NULL
);
CREATE INDEX idx_model_usage_task ON model_usage(task_id);
CREATE INDEX idx_model_usage_ts ON model_usage(timestamp);
```

**Why:** Cost tracking and daily cap enforcement.

---

### `app_state`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| key | TEXT | PK | |
| value | TEXT | NOT NULL | |

```sql
CREATE TABLE app_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

**Keys used in Phase 1–2:**
- `session_token` — random UUID, regenerated on each backend start
- `last_backup_ts` — ISO timestamp of last `VACUUM INTO`
- `schema_version` — current migration version (redundant with `schema_migrations`)

---

### `schema_migrations`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| version | INTEGER | PK | 1, 2, 3... |
| applied_at | TEXT | NOT NULL | |

```sql
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
```

---

## Phase 4+ tables (DEFERRED — list only)

| Table | Phase | Purpose | Key columns |
|-------|-------|---------|-------------|
| `evidence_sources` | 4 | Source document metadata | `id, title, source_type, authority_level, edition, verification_status, checksum_sha256, local_file_path` |
| `evidence_chunks` | 4 | Extracted text with provenance | `id, source_id, page, section, text, checksum` |
| `formulas` | 5 | Formula records with lifecycle | `id, name, domain, equation_text, canonical_units, source_refs, review_status, version` |
| `calculation_runs` | 5 | Deterministic calc execution | `id, task_id, formula_id, inputs_json, result_json, status, trace_json, timestamp` |
| `connectors` | 1 | Registered connector metadata | `id, name, status, version, exe_path, bitness, last_probe_ts` |
| `connector_probes` | 1 | Probe history | `id, connector_id, probe_type, result_json, timestamp` |
| `settings` | 1 | User-configurable settings | `key, value, updated_at` |

> These tables are created when their phase starts. Do not create them in Phase 1.

---

## Migration sequence (Phase 1)

| Version | File | Contents |
|---------|------|----------|
| 1 | `001_initial.sql` | `projects`, `tasks`, `task_events`, `approvals`, `artifacts`, `audit_events`, `model_usage`, `app_state`, `schema_migrations` |
| 2 | `002_connectors.sql` | `connectors`, `connector_probes` |
| 3 | `003_evidence.sql` | `evidence_sources`, `evidence_chunks` |
| 4 | `004_formulas.sql` | `formulas`, `calculation_runs` |
| 5 | `005_settings.sql` | `settings` |

WAL enabled in `database.py` on every connection:
```python
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA foreign_keys=ON")
conn.execute("PRAGMA synchronous=NORMAL")
```
