# NEI — Architecture Decisions (Tahap 2)

**Date:** 2026-11-02
**Status:** PROPOSED — awaiting approval before Tahap 3
**Supersedes:** `Arsitektur.py` embedded content (to be extracted to `ARCHITECTURE.md` in Tahap 3)

---

## D1. System boundary and module direction

**Decision:** Modular monolith, single Python process, FastAPI + Uvicorn.

```
┌─────────────────────────────────────────────────────────────────┐
│  NEI Backend (Python 3.12, FastAPI)                            │
│                                                               │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │  API     │  │  Orchestrator│  │  Execution Policy       │   │
│  │  layer   │→ │  (Planner +  │→ │  (policy gate, approvals│   │
│  │  (routes)│  │   Router)    │  │   + resource manager)   │   │
│  └────┬─────┘  └──────┬───────┘  └───────────┬────────────┘   │
│       │               │                      │                │
│       ▼               ▼                      ▼                │
│  ┌─────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│  │Storage  │  │Evidence Engine│ │  Connector Registry      │   │
│  │(SQLite  │  │(Phase 4+)    │  │  (capability-driven)    │   │
│  │+ art.)  │  └──────────────┘  └──────────┬──────────────┘   │
│  └─────────┘                                │                │
│                                             ▼                │
│                              ┌──────────────────────────┐    │
│                              │  Verification Engine     │    │
│                              │  (postcondition checks)  │    │
│                              └──────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   Rhino 6 (COM/IPC)  SOLIDWORKS 2022 (COM)  Maxsurf 20 V8i (file)
```

**Repository structure (authoritative, replaces `Arsitektur.py` §5):**

```
NEI/
├── README.md
├── PLAN.md
├── ARCHITECTURE.md
├── ARCHITECTURE_AUDIT.md
├── FRONTEND_SPEC.md
├── API_SPEC.md
├── DATABASE_SCHEMA.md
├── STATE_MACHINE_SPEC.md
├── RHINO6_INTEGRATION_SPIKE.md
├── CONNECTOR_SPEC.md
├── VERIFICATION_SPEC.md
├── ENGINEERING_EVIDENCE_PROTOCOL.md
├── SECURITY.md
├── DATA_GOVERNANCE.md
├── IMPLEMENTATION_GUIDE.md
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.lock
│
├── apps/
│   ├── api/
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── projects.py
│   │       ├── tasks.py
│   │       ├── approvals.py
│   │       ├── evidence.py
│   │       ├── calculations.py
│   │       └── connectors.py
│   └── ui/          # React + Vite + TypeScript; built and served by FastAPI in production
│
├── nei/
│   ├── config/
│   │   ├── settings.py       # pydantic-settings; loads .env
│   │   └── logging_config.py # structured JSON logging
│   ├── core/
│   │   ├── orchestrator.py
│   │   ├── planner.py
│   │   ├── task_manager.py
│   │   ├── state_machine.py
│   │   ├── tool_router.py
│   │   └── prompt_templates/
│   ├── contracts/
│   │   ├── task.py
│   │   ├── plan.py
│   │   ├── tool.py
│   │   ├── connector.py
│   │   ├── evidence.py
│   │   ├── calculation.py
│   │   ├── artifact.py
│   │   └── events.py
│   ├── evidence/
│   │   ├── ingestion/
│   │   ├── extraction/
│   │   ├── indexing/
│   │   ├── retrieval.py
│   │   ├── authority.py
│   │   ├── applicability.py
│   │   └── citation_builder.py
│   ├── knowledge/
│   │   ├── source_registry.py
│   │   ├── formula_registry.py
│   │   ├── method_registry.py
│   │   ├── unit_registry.py
│   │   └── schemas/
│   ├── engineering/
│   │   ├── units/
│   │   ├── geometry/
│   │   ├── hydrostatics/
│   │   ├── stability/
│   │   ├── resistance/
│   │   ├── propulsion/
│   │   ├── structures/
│   │   └── validation/
│   ├── connectors/
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── discovery.py
│   │   ├── rhino6/
│   │   ├── solidworks2022/
│   │   └── maxsurf_v8i/
│   ├── automation/
│   │   ├── desktop_session.py
│   │   ├── ui_automation.py
│   │   ├── screen_capture.py
│   │   ├── visual_observer.py
│   │   └── safety.py
│   ├── execution/
│   │   ├── policy.py
│   │   ├── approvals.py
│   │   ├── script_validator.py
│   │   ├── sandbox.py
│   │   ├── scheduler.py
│   │   └── resource_manager.py
│   ├── verification/        # NEW — resolves audit H5
│   │   ├── engine.py
│   │   ├── postconditions.py
│   │   ├── geometry_check.py
│   │   └── record.py
│   ├── storage/
│   │   ├── database.py
│   │   ├── repositories/
│   │   ├── artifact_store.py
│   │   ├── project_store.py
│   │   └── migrations/
│   ├── reporting/
│   │   ├── engineering_report.py
│   │   ├── calculation_report.py
│   │   └── export.py
│   └── observability/
│       ├── audit.py
│       ├── metrics.py
│       └── event_bus.py
│
├── data/                  # NOT committed; .gitignore'd
│   ├── documents/
│   ├── indexes/
│   ├── formulas/
│   ├── projects/
│   ├── artifacts/
│   ├── logs/
│   └── backups/
│
├── scripts/
│   ├── preflight_windows.ps1
│   ├── check_environment.py
│   └── dev_start.ps1
│
├── docs/
│   └── archive/           # Arsitektur.py and FrontEnd.py move here
│
└── tests/
    ├── unit/
    ├── integration/
    ├── fixtures/
    ├── engineering_reference_cases/
    └── security/
```

**Key changes from old structure:**
- Added `nei/verification/` module — resolves audit H5 (Verification Engine had no location)
- `apps/ui/` is now "Vite React app, built and served by FastAPI in production" (not "optional later") — resolves audit H1
- `data/` is explicitly gitignored
- `docs/archive/` for retired files

---

## D2. Process model and session

**Decision: OQ1 resolved — backend runs in the user's interactive desktop session.**

Rationale:
- Rhino 6, SOLIDWORKS 2022, and Maxsurf 20 V8i are desktop GUI applications.
- COM automation (SOLIDWORKS) and RhinoPython/RhinoCommon (Rhino 6) require the same Windows desktop session (Session 1), not the Windows service session (Session 0).
- A Windows service cannot reach COM objects in the user's interactive session without complex cross-session marshalling.
- This is a single-user laptop. There is no need for a service.

**Consequences:**
- Backend is started by the user (or `dev_start.ps1`) in their desktop session.
- `desktop_session.py` must verify it is running in an interactive session before COM calls.
- If the user locks the machine or logs off, COM automation stops working. Document this clearly.
- No Windows service, no scheduled task that runs as SYSTEM.

**Thread/apartment model (UNVERIFIED until Phase 0 spike):**
- Python `pywin32` COM calls require `CoInitialize` with `MTC` (Multi-Threaded) or `STA` (Single-Threaded).
- FastAPI runs on uvicorn's event loop (async). COM calls are blocking → must run in a thread pool (`asyncio.to_thread`) with per-connector lock.
- Rhino 6 bitness (32-bit vs 64-bit) affects which Python interpreter can load RhinoCommon. UNVERIFIED — probe in Phase 0.

**Per-application lock:**
- One NEI operation at a time per software application. `resource_manager.py` enforces this with a named Windows mutex (`\\NEI\{connector_id}`).
- If Rhino is already locked by NEI task A, task B requesting Rhino waits or is queued.
- No concurrent writes to the same software document.

**Recovery on software hang:**
- Each connector operation has a `timeout_seconds` from the tool action schema.
- On timeout: mark task `RECOVERING`, attempt graceful detach (`Connector.detach()`), do NOT force-kill the software process.
- If the software is unresponsive beyond a longer "emergency timeout" (configurable, default 300s): mark task `FAILED`, log incident, prompt user to manually close the software.
- `RECOVERING` state is entered, not `CANCELLED` — the task can be retried once the software is back.

---

## D3. Local server security

**Decision: local-only binding, no public interface.**

| Control | Decision |
|---------|----------|
| Bind address | `127.0.0.1` only. Never `0.0.0.0`. Uvicorn `--host 127.0.0.1`. |
| Auth | No password auth for localhost. Session token issued on first browser visit, stored in `app_state` table. Token is a random UUID, httpOnly cookie, bound to the process lifetime. |
| DNS rebinding | FastAPI middleware checks `Host` header; reject requests where `Host` is not `localhost` or `127.0.0.1`. |
| CORS | Allow only `http://localhost:5173` (Vite dev) and `http://127.0.0.1:8000` (production static). No `*`. |
| CSRF | Same-origin only; no cross-site cookies. Session token is `SameSite=Strict`. |
| File access | Backend only reads/writes inside `data/` root. All path arguments are canonicalised and checked against the root. Reject `..`, UNC paths, device paths. |
| Secrets | `.env` file, gitignored. `NEI_SESSION_TOKEN` (auto-generated), `LLM_API_KEY`, `LLM_BASE_URL`. Never logged. |

---

## D4. API conventions

| Convention | Decision |
|------------|----------|
| Protocol | REST for commands/CRUD; SSE (`/events`) for task state streaming to UI. |
| Versioning | URL prefix `/api/v1/`. Breaking changes → `/api/v2/`. |
| Envelope | All responses: `{"ok": true, "data": {...}}` or `{"ok": false, "error": {"code": "...", "message": "...", "details": {...}}}`. No bare HTTP codes for app errors. |
| Error codes | Machine-readable: `TASK_NOT_FOUND`, `STATE_TRANSITION_INVALID`, `APPROVAL_REQUIRED`, `CONNECTOR_UNAVAILABLE`, `TIMEOUT`, `PATH_FORBIDDEN`, `VALIDATION_FAILED`. |
| Pagination | Cursor-based: `?cursor=<opaque>&limit=<int>`. Default limit 50, max 200. |
| Idempotency | `Idempotency-Key` header on all POST endpoints. Server stores hash for 24h. Duplicate returns original result. |
| Timeouts | Client-configurable per request; server default 30s for API, 300s for connector operations. |
| Retry | No automatic retry on 4xx. Client-side retry with exponential backoff for 5xx and `TIMEOUT`. |
| Timestamps | ISO 8601 UTC, millisecond precision: `2026-11-02T05:00:00.123Z`. |
| IDs | UUIDv4 for all entity IDs. No auto-increment integers exposed. |
| OpenAPI | FastAPI auto-generates `/openapi.json`. TypeScript types generated from this via `openapi-typescript`. |

---

## D5. Database and artifact strategy

**SQLite, WAL mode, single writer.**

| Aspect | Decision |
|--------|----------|
| File | `data/nei.db`. One file. WAL mode enabled on every connection (`PRAGMA journal_mode=WAL`). |
| Writer | Single FastAPI process. No multi-process writes. Uvicorn `--workers 1`. |
| Read concurrency | Multiple readers OK in WAL mode. |
| Backups | `VACUUM INTO` to `data/backups/nei_<YYYYMMDD_HHMM>.db` on user action + daily if `data/` size changed. No automated cron. |
| Migration | Sequential SQL files in `nei/storage/migrations/`, tracked in `schema_migrations` table. No ORM. Raw `sqlite3` + Pydantic contracts. |
| Artifact integrity | On write: SHA-256 hash stored in `artifacts` table. On read: hash verified. Mismatch → `artifact_corrupt` error. |
| Retention | No automatic deletion. User deletes projects. `audit_events` and `artifacts` retained indefinitely. |

**Core tables (Phase 1–2, full spec in `DATABASE_SCHEMA.md`):**
- `projects(id, name, created_at, updated_at, path_root)`
- `tasks(id, project_id, user_request, task_type, domain, risk_level, state, plan_json, created_at, started_at, completed_at, connector_id, tool_calls_json, input_artifact_ids, output_artifact_ids, evidence_ref_ids, calc_run_ids, approval_ids, software_versions_json, errors_json, warnings_json, schema_version)`
- `task_events(id, task_id, from_state, to_state, event, timestamp, metadata_json)`
- `approvals(id, task_id, payload_hash, approved_by, approved_at, status)`
- `artifacts(id, project_id, task_id, filename, path, sha256, size_bytes, created_at, status)`
- `audit_events(id, timestamp, task_id, step_id, event_type, detail_json, model_id, prompt_template_version, tool_name, tool_version, connector_version, script_hash, token_usage, est_cost)`
- `model_usage(id, task_id, provider, model, prompt_tokens, completion_tokens, est_cost, latency_ms, timestamp)`
- `app_state(key TEXT PRIMARY KEY, value TEXT)` — for `telegram_update_offset` equivalent: `session_token`, `last_backup_ts`
- `schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT)`

**Deferred tables (Phase 4+):** `evidence_sources`, `evidence_chunks`, `formulas`, `calculation_runs`, `calculation_inputs`, `calculation_results`, `connectors`, `connector_probes`, `settings`.

---

## D6. State machine (full transition table in `STATE_MACHINE_SPEC.md`)

**States:** PENDING, PLANNING, NEEDS_INPUT, VALIDATING, WAITING_APPROVAL, QUEUED, RUNNING, VERIFYING, COMPLETED, FAILED, CANCELLED, NEEDS_REVIEW, RECOVERING.

**Active states:** PLANNING, NEEDS_INPUT, VALIDATING, WAITING_APPROVAL, QUEUED, RUNNING, VERIFYING, RECOVERING.
**Terminal states:** COMPLETED, FAILED, CANCELLED, NEEDS_REVIEW.

**Key rules (full table in spec):**
- `COMPLETED` is reached only after `VERIFYING` passes all postconditions. Script exit 0 alone is not sufficient.
- `RECOVERING` → back to `QUEUED` if software is back; → `FAILED` if user cancels or emergency timeout exceeded.
- `NEEDS_INPUT` → `PLANNING` when user provides missing data.
- `NEEDS_REVIEW` is terminal but a user can create a new task linked to the original.
- Every transition writes a `task_events` row with timestamp and triggering event.
- Retries create a new execution attempt linked to the original task via `parent_task_id`.

---

## D7. Roadmap (replaces old 8-phase roadmap in `Arsitektur.py`)

Principle: **highest risk proved earliest; visible features do not sacrifice dependencies.**

| Phase | Name | Depends on | Deliverable | Acceptance |
|-------|------|-----------|-------------|-----------|
| 0 | Audit & spikes | — | `environment.json`, Rhino 6 spike report, SW/Maxsurf probe, license check | All UNVERIFIED items resolved or marked |
| 1 | Backend foundation | 0 | FastAPI, SQLite, Pydantic contracts, state machine, audit logging, artifact store, health endpoint | Create task, view state, cancel task, persist audit, no CAD needed |
| 2 | Frontend foundation | 1 | React shell, Dashboard, health integration, OpenAPI types, basic navigation | Dashboard loads, shows health, creates project via UI |
| 3 | Verification + Rhino 6 connector | 1, 2, 0-spike | `verification/` module, Rhino 6 connector (spike method), disposable box test, artifact `.3dm` manifest | **Alpha 0.1** |
| 4 | Evidence engine + EEP | 3 | Source registry, PDF ingestion, lexical search, formula registry, citation builder | Ingest doc, retrieve passage with page, mark UNVERIFIED source |
| 5 | Engineering core | 4 | Unit-safe calc framework, formula lifecycle, reference cases, calculation verification | Same inputs → same result; wrong units rejected |
| 6 | SOLIDWORKS connector | 3, 5 | SW 2022 probe, read-only inspection, disposable test part | No unsupported API assumed; version-tested |
| 7 | Maxsurf connector | 3, 5 | Maxsurf 20 V8i probe, file exchange, GUI fallback | Every claim has reproducible test |
| 8 | Cross-software workflow | 6, 7 | Artifact handoff, unit mapping, import/export validation | Test artifact moves between 2 apps; geometry/units verified |
| 9 | Advanced domains | 5, 8 | More formulas, stability/resistance methods, report export | Each method has source + reference case |

**Alpha 0.1 = end of Phase 3.** Definition (unchanged from V2 prompt):
User opens dashboard → creates project → requests 10×3×1 box in Rhino 6 → planner (template, not LLM free-code) → policy gate → connector creates object in disposable doc → verification checks bounding box + object count + units from Rhino result (not stdout) → artifact `.3dm` + manifest saved → dashboard shows result, script hash, execution log. No original file overwritten. Does NOT require evidence engine or engineering core.

**Change from old roadmap:** Evidence Engine and Engineering Core moved AFTER Alpha 0.1. The old roadmap placed them before Rhino, which blocked the first visible milestone.

---

## D8. Spike list (Phase 0)

| # | Spike | Pass criteria | Fail criteria |
|---|-------|--------------|---------------|
| S1 | Rhino 6 detect + version + bitness | `environment.json` records exact version, 32/64-bit, exe path | Cannot detect or version unknown |
| S2 | Rhino 6 transport method test | One of: RhinoCommon .NET plugin, RhinoPython, command-line, IPC — successfully creates a box in a disposable doc and reads back bounding box | All 5 methods fail or are unavailable |
| S3 | SOLIDWORKS 2022 COM detect | `swProcess` accessible via `GetObject`, version reported | No running instance and launch fails, or COM not available |
| S4 | Maxsurf 20 V8i file format probe | Identify supported import/export formats from installed docs | No automation interface found |
| S5 | License check | Each software's edition + automation permission documented | Cannot confirm; mark UNVERIFIED |
| S6 | Resource budget measurement | Concurrent memory usage of all software + backend + browser recorded | Machine OOMs; policy "one heavy software at a time" confirmed |

---

## D9. LLM provider strategy (OQ2 resolved)

**Decision: External API provider by default.**

| Setting | Value |
|---------|-------|
| Provider | OpenAI-compatible endpoint (configurable base URL) |
| Model | User-configured; default: a strong model for planning, smaller for classification |
| API key | In `.env`, never logged, redacted in all output |
| Data sent | Only structured plan requests, relevant document chunks, and tool schemas. Never full PDFs, never CAD files, never project files. |
| Privacy mode | `NEI_LLM_PRIVACY=on` disables all external calls; planner falls back to template-only mode (no LLM). |
| Budget | `NEI_LLM_DAILY_TOKEN_CAP` in settings; exceeded → tasks marked `NEEDS_REVIEW` with reason "LLM budget exceeded". |
| Timeout | 60s per LLM call. No retry on 4xx. |
| Structured output | Planner must return JSON matching a Pydantic schema. Unknown tool names or invalid parameters → reject, do not pass to execution. |

---

## D10. Ansys — remains DEFERRED

No connector, no probe, no placeholder code. Documented in `CONNECTOR_SPEC.md` as:
> ANSYS: **DEFERRED**. No integration work until the user confirms an installed ANSYS product, version, and license. At that point, spike PyMechanical/PyFluent compatibility for the exact release.

---

## Open questions remaining after Tahap 2

| # | Question | Resolution |
|---|----------|-----------|
| OQ3 | License type for Rhino/SW/Maxsurf | **UNVERIFIED** — Phase 0 spike S5. Document in `environment.json`. |
| OQ4 | Rhino 6 bitness | **UNVERIFIED** — Phase 0 spike S1. Affects transport method choice (S2). |
| OQ6 | `data/` root path | Default: `<project_root>/data/`. Overridable via `NEI_DATA_ROOT` in `.env`. Confirm with user. |
| OQ7 | Which OpenAI-compatible provider and model? | User decision at setup time. `.env` configurable. No default model name in code. |

---

**Tahap 2 complete. Awaiting "lanjut" before writing Tahap 3 documents.**
