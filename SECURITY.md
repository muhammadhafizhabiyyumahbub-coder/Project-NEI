# NEI — Security

**Scope:** Local security model for a single-user, single-machine deployment.
**Threat model:** Local user is trusted. Network attackers are the threat. LLM provider is an external party.

---

## 1. Network binding

| Control | Value |
|---------|-------|
| Listen address | `127.0.0.1` only. Never `0.0.0.0`. |
| Port | `8000` (configurable via `NEI_API_PORT`) |
| Uvicorn flag | `--host 127.0.0.1` (hardcoded in `dev_start.ps1` and production entry point) |

**DNS rebinding protection:**
FastAPI middleware inspects the `Host` header on every request. Requests where `Host` is not `localhost` or `127.0.0.1` are rejected with `403 FORBIDDEN_HOST`.

---

## 2. Authentication

| Control | Value |
|---------|-------|
| Mechanism | Session token (random UUID, 128-bit) |
| Storage | `app_state.session_token` in SQLite; regenerated on every backend start |
| Cookie | `nei_session`, `HttpOnly=True`, `SameSite=Strict`, `Secure=False` (localhost), `Path=/` |
| Lifetime | Process lifetime. Cleared when backend restarts. |
| First visit | Browser GET `/api/v1/health` without cookie → `UNAUTHENTICATED` (401). UI calls POST `/api/v1/auth/session` to get a token, stores it in memory (not localStorage). |

**No password, no user database.** Single local user.

---

## 3. CORS

| Origin | Allowed |
|--------|---------|
| `http://localhost:5173` | Yes (Vite dev server) |
| `http://127.0.0.1:8000` | Yes (production static) |
| All others | No |

`Access-Control-Allow-Credentials: true` for the two allowed origins only. `*` is never used.

---

## 4. File system sandbox

| Rule | Enforcement |
|------|-------------|
| All file I/O is under `data/` root (`NEI_DATA_ROOT`, default `<project_root>/data/`) | `storage/artifact_store.py` canonicalises every path and checks `path.is_relative_to(data_root)` |
| Reject `..` traversal | Path canonicalisation before any filesystem call |
| Reject UNC paths (`\\server\share`) | Check first two characters |
| Reject device paths (`\\.\` etc.) | Check first three characters |
| Reject symlinks / reparse points | `os.path.islink()` check on every file operation |
| Read-only source files | Originals in `data/documents/` are opened with `O_RDONLY` only |
| Output always to new path | Generated artifacts get a unique name (`<timestamp>_<uuid8>.<ext>`) |

**Any path that fails sandbox check → `PATH_FORBIDDEN` (403), no filesystem operation is performed.**

---

## 5. Script execution safety

| Rule | Enforcement |
|------|-------------|
| LLM never writes scripts directly | Planner produces a structured plan with tool names + parameters; scripts are generated from approved templates |
| Scripts run in a sandboxed working directory | `data/projects/<project_id>/artifacts/scripts/` |
| No arbitrary imports | AST validation: only allowlisted modules (`math`, `numpy`, `rhino.*` for Rhino scripts, etc.) |
| No network access from scripts | Scripts run in a subprocess with no network if applicable; or in-process with no `socket` access |
| No file deletion | `os.remove`, `shutil.rmtree`, `Path.unlink` are forbidden in the AST allowlist |
| No registry access | `winreg` is forbidden |
| Script hash recorded before execution | SHA-256 of the exact script file → `audit_events.script_hash` |
| Script preserved after execution | Never deleted; stored at `data/projects/<id>/artifacts/scripts/<task_id>_<step_id>.py` |

---

## 6. LLM data exposure

| Setting | Behaviour |
|---------|-----------|
| `NEI_LLM_PRIVACY=off` (default) | Structured plan requests, relevant document chunks, and tool schemas are sent to the configured LLM endpoint. Full PDFs, CAD files, and project files are **never** sent. |
| `NEI_LLM_PRIVACY=on` | No external LLM calls. Planner uses template-only mode (pre-defined plan templates with parameter substitution). No `model_usage` rows written. |
| API key | Stored in `.env` (`NEI_LLM_API_KEY`). Never logged, never in responses, redacted in all output via `logging_config.SecretRedactor`. |
| Data minimisation | Only the fields declared in the plan's `required_inputs` are sent. No project history, no other tasks, no audit log. |

---

## 7. Secret management

| Secret | Storage | Notes |
|--------|---------|-------|
| `NEI_LLM_API_KEY` | `.env` file, gitignored | Redacted in all logs and API responses |
| `NEI_SESSION_TOKEN` | `app_state` table in SQLite | Regenerated on backend start; not in `.env` |
| Software license credentials | Not stored by NEI | NEI never reads, stores, or transmits software license keys |

`.env` file:
```
NEI_LLM_PROVIDER=openai-compatible
NEI_LLM_BASE_URL=https://api.example.com/v1
NEI_LLM_API_KEY=sk-...          # never committed
NEI_LLM_MODEL=...
NEI_LLM_PRIVACY=off
NEI_LLM_DAILY_TOKEN_CAP=500000
NEI_DATA_ROOT=./data
NEI_CONNECTOR_TIMEOUT_S=300
NEI_EMERGENCY_TIMEOUT_S=300
```

`.env` is in `.gitignore`. `.env.example` (no real values) is committed.

---

## 8. Audit log

- All state transitions, tool calls, approval decisions, and artifact writes are recorded in `audit_events`.
- `audit_events` is append-only. No UPDATE or DELETE in application code.
- Secrets are redacted before writing to `audit_events` via `SecretRedactor`.
- Audit log retention: indefinite (no automatic deletion).
- Export: user-initiated via `POST /api/v1/audit/export` (Phase 5+).

---

## 9. Recovery and emergency stop

| Action | Effect |
|--------|--------|
| Cancel task | Task → `CANCELLED`. App lock released. No force-kill of software. |
| Emergency stop (NEI) | All queued/running tasks → `CANCELLED`. Connectors call `detach()`. No software is force-killed. |
| Software crash | Task → `RECOVERING`. Graceful detach attempted. If software doesn't recover within `NEI_EMERGENCY_TIMEOUT_S` → `FAILED`. |
| NEI process crash | No lock is held (process death releases OS locks). On restart, tasks in `RUNNING` are set to `RECOVERING` by a startup reconciliation step. |

---

## 10. Software license boundary

- NEI does not bypass, crack, or circumvent any software license.
- NEI does not store, transmit, or display software license keys.
- If a software feature requires a license module that is not installed or activated, the connector reports `UNAVAILABLE` and the capability is marked accordingly.
- Academic/student license restrictions are documented as UNVERIFIED (OQ3) and checked in Phase 0 spike S5.
