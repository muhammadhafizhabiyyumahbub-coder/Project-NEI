# NEI — Implementation Guide

**Scope:** Concrete build instructions for Phase 0–2. Later phases are decision-level (see `PLAN.md`).

**Audience:** Coding agent (OpenCode) and the developer.
**Rule:** Stop at the end of each phase and report before continuing. Do not start Phase N+1 before Phase N is accepted.

---

## Phase 0 — Environment audit and spikes

### Step 0.1 — Environment discovery

Create `scripts/check_environment.py`:
- Detect Python version and path
- Detect Rhino 6: registry key + exe path, version, bitness (UNVERIFIED until confirmed)
- Detect SOLIDWORKS 2022: registry + exe path, version, service pack
- Detect Maxsurf 20 V8i: exe path, version
- Detect ANSYS: report not found (deferred)
- Measure RAM, CPU model, GPU model
- Write `data/environment.json` with all findings. Use `UNVERIFIED` for unknowns.

**Output:** `data/environment.json` (human-readable + machine-readable)

### Step 0.2 — Rhino 6 spike

Follow `RHINO6_INTEGRATION_SPIKE.md`. For each of the 5 candidate methods:
1. Detect if the method is available in the installed Rhino 6
2. Run the box test: open/create disposable document, create 10×3×1 box, read bounding box, verify dimensions
3. Record: success/fail, time taken, fragility notes
4. Do NOT touch any production Rhino file

**Output:** Rhino spike report (write to `docs/rhino_spike_report.md`)

### Step 0.3 — SOLIDWORKS + Maxsurf probe

- SOLIDWORKS: registry detect, version, COM class accessibility (`SldWorks.ApplicationPm`). No document operations.
- Maxsurf: exe detect, version, supported file formats from installed docs. No automation.

**Output:** Probe results appended to `data/environment.json`

### Step 0.4 — License check

For each software: check edition (academic/student/full) and whether automation is permitted by the license. Document in `data/environment.json` as `license_status: "UNVERIFIED"` or specific finding. No bypass.

### Phase 0 done when:
- `data/environment.json` exists with all hardware fields filled
- Rhino spike report: at least one transport method passed or all 5 failed (document why)
- SW/Maxsurf probe: detection + version recorded
- License status documented (UNVERIFIED allowed)

**Stop. Report to user. Wait for "lanjut" before Phase 1.**

---

## Phase 1 — Backend foundation

### 1.1 Project setup

```bash
cd D:\Project NEI
python -m venv .venv
.venv\Scripts\activate
pip install fastapi uvicorn pydantic pydantic-settings httpx sqlite3
# SQLite is in the standard library
```

Create `pyproject.toml`:
```toml
[project]
name = "nei"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.100",
    "uvicorn[standard]",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "httpx>=0.24",
]
```

### 1.2 Database

Create `nei/storage/database.py`:
- `initialize_database(path: Path) -> None` — creates `nei.db` if not exists, enables WAL
- `query(db_path, sql, params) -> list` — read-only
- `execute(db_path, sql, params) -> int` — single write (caller manages transaction)
- `connect(db_path) -> sqlite3.Connection` — with `PRAGMA journal_mode=WAL`, `PRAGMA foreign_keys=ON`, `PRAGMA synchronous=NORMAL`

Create migration `nei/storage/migrations/001_initial.sql` with all Phase 1 tables from `DATABASE_SCHEMA.md`.

### 1.3 Pydantic contracts

Create files in `nei/contracts/`:
- `task.py` — `Task`, `TaskState` (enum), `TaskEvent`
- `plan.py` — `Plan`, `PlanStep`, `RequiredInput`
- `tool.py` — `ToolAction`, `ToolResult`
- `connector.py` — `BaseConnector` (ABC), `DetectionResult`, `Capability`, `HealthResult`, `InspectionResult`
- `artifact.py` — `Artifact`
- `events.py` — `SSEEvent`

All use Pydantic v2 (`BaseModel`, `Field`, `model_validator`).

### 1.4 State machine

Create `nei/core/state_machine.py`:
- Implement the full transition table from `STATE_MACHINE_SPEC.md`
- `can_transition(current: TaskState, event: str) -> bool`
- `transition(task, event) -> Task` — raises `IllegalTransition` if not allowed
- Writes a `task_events` row on every valid transition

Unit test: `tests/unit/test_state_machine.py` — every legal + illegal transition.

### 1.5 Task manager

Create `nei/core/task_manager.py`:
- `create_task(project_id, user_request, task_type, domain) -> Task`
- `get_task(project_id, task_id) -> Task`
- `cancel_task(project_id, task_id) -> Task`
- `provide_input(project_id, task_id, inputs: dict) -> Task`
- `retry_task(project_id, task_id) -> Task`

### 1.6 Policy gate

Create `nei/execution/policy.py`:
- `check_path(path: str, data_root: Path) -> None` — raises `PathForbidden`
- `check_risk(risk_level: str, requires_approval: bool) -> None`
- `validate_plan(plan: Plan) -> list[Issue]`

### 1.7 Artifact store

Create `nei/storage/artifact_store.py`:
- `save_artifact(project_id, task_id, filename, content: bytes) -> Artifact`
  - Writes to `data/projects/<project_id>/artifacts/<timestamp>_<uuid8>_<filename>`
  - Computes SHA-256, stores in DB
- `read_artifact(artifact_id) -> bytes`
  - Verifies SHA-256; raises `ArtifactCorrupt` on mismatch
- `get_manifest(project_id) -> list[Artifact]`

### 1.8 Audit logging

Create `nei/observability/audit.py`:
- `record_event(db_path, event_type, task_id=None, detail: dict = {}) -> None`
- Writes to `audit_events` table
- Redacts secrets via `logging_config.SecretRedactor`

### 1.9 FastAPI app

Create `apps/api/main.py`:
- FastAPI app, title="NEI API", version="0.1.0"
- CORS: `http://localhost:5173`, `http://127.0.0.1:8000`
- Host check middleware (reject non-localhost Host header)
- Session token middleware (check `nei_session` cookie against `app_state.session_token`)
- Include routers: `health`, `projects`, `tasks`, `approvals`
- SSE endpoint: `/api/v1/events`
- Run with: `uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 1`

### 1.10 Mock tool router

Create `nei/core/tool_router.py`:
- `MockToolRouter` — for Phase 1, all tool calls return a canned `ToolResult` with `success=True`
- This lets the full task lifecycle run without any CAD software

### Phase 1 done when:
- [ ] `pytest tests/unit/` passes
- [ ] `POST /api/v1/projects` creates a project with `path_root`
- [ ] `POST /api/v1/projects/{id}/tasks` creates task in PENDING
- [ ] Task transitions PENDING→PLANNING→VALIDATING→QUEUED→RUNNING→VERIFYING→COMPLETED with mock tools
- [ ] Every transition has a `task_events` row
- [ ] `POST .../cancel` works from QUEUED, RUNNING, VERIFYING
- [ ] `POST .../provide-input` works from NEEDS_INPUT
- [ ] `POST .../retry` creates a new task with `parent_task_id`
- [ ] `GET /api/v1/events` streams task state changes via SSE
- [ ] Artifact save + read + SHA-256 verification works
- [ ] No CAD software required

**Stop. Run tests. Report to user. Wait for "lanjut" before Phase 2.**

---

## Phase 2 — Frontend foundation

### 2.1 Scaffold

```bash
cd D:\Project NEI
npm create vite@latest apps/ui -- --template react-ts
cd apps/ui
npm install
npm install tailwindcss @tailwindcss/vite lucide-react @tanstack/react-query
# shadcn/ui: follow official setup for Vite + Tailwind
```

### 2.2 Design tokens

Add to `apps/ui/src/styles/globals.css` (Tailwind config):
- Colors from `FRONTEND_SPEC.md` "Design tokens" section
- Dark theme as default

### 2.3 App shell

Create:
- `AppShell.tsx` — sidebar + main content layout
- `Sidebar.tsx` — collapsible, Lucide icons, route links
- `TopBar.tsx` — project name + connector health dots

### 2.4 Pages

Create all pages from `FRONTEND_SPEC.md` Phase 2 section:
- `Dashboard.tsx`
- `Projects.tsx`
- `ProjectDetail.tsx` (tabs: Overview, Tasks, Artifacts, Audit)
- `TaskDetail.tsx` (state timeline + detail panel)
- `Connectors.tsx`
- `Settings.tsx`

### 2.5 API layer

- `api/client.ts` — `fetch` wrapper with session token, error envelope parsing
- `api/hooks/` — one TanStack Query hook per endpoint group
- `api/types.ts` — generated from `/openapi.json` via `openapi-typescript`

### 2.6 SSE

- `hooks/useSse.ts` — `EventSource` subscription with reconnect backoff
- Live update task state in Dashboard and TaskDetail without page reload

## Phase 2 — Frontend foundation

### 2.0 Status (as of commit `e636f9f`)

- [x] `npm run build` in `apps/ui` — zero TypeScript errors
- [x] Dashboard loads and shows `/health` data
- [x] Create project via UI → appears in project list
- [x] Create task via UI → task detail shows state
- [x] SSE updates task state live
- [x] Cancel task via UI → state updates
- [x] Connector health page shows probe results
- [x] All API types from OpenAPI
- [x] **Phase 2 accepted: 2026-11-04** — Playwright e2e `e2e/happy-path.spec.ts` passed (6.7s); 99/99 pytest passing

**Phase 2 selesai, semua acceptance criteria terpenuhi.**

---

## Phase 3 — Verification + Rhino 6 connector = Alpha 0.1

**Goal:** First visible engineering workflow: create box in Rhino 6, verify from Rhino result.  
**Status:** Core infrastructure complete, live Rhino 6 integration terbukti di mesin ini (Rhino listener).

### 3.0 Status (as of commit `dbe16b0` — 2026-11-07)

| Item | Status | Bukti |
|---|---|---|
| `nei/verification/` module (engine, postconditions, geometry check, record) | ✅ **terbukti** | `tests/test_verification.py` (PASSED/FAILED via API) |
| Rhino 6 connector (spike‑selected transport Method 2, passive listener) | ✅ **terbukti** | `tests/test_rhino_connector.py` + `tests/test_rhino_hull_proxy.py` (live Rhino via listener) |
| `rhino.detect`, `health_check`, `get_version`, `get_document_info`, `list_objects` | ✅ **terbukti** | `tests/test_rhino_connector.py` (mock) + live listener |
| `rhino.create_box_test` | ✅ **terbukti** | `tests/test_rhino_connector.py` + live Rhino via listener |
| `rhino.inspect_objects` | ✅ **terbukti** | `tests/test_rhino_connector.py` + live Rhino via listener |
| `rhino.export_copy` (new `.3dm` under `data/projects/<id>/artifacts/`) | ✅ **terbukti** | `tests/test_rhino_hull_proxy.py` (live artifact write) |
| Verification: bounding box, object count, units from **Rhino result** | ✅ **terbukti** | verification engine + postconditions (box) |
| Artifact manifest for `.3dm` | ✅ **terbukti** | `write_manifest` + `save_artifact` (test round‑trip) |
| LLM planner wired (external provider, privacy mode) | ✅ **terbukti** | `tests/test_planner.py` (template match, LLM fallback) |
| Script hash surfaced in UI + audit log | ✅ **terbukti** | `tests/test_rhino_connector.py` (`script_sha256` in result data) |

### ✅ **Yang sudah dijalankan dan lulus** (189/189 tests passing)

| Test suite | Jumlah passed | Bukti |
|---|---|---|
| `python -m pytest tests/` | 189 | semua unit, integration, artifact, verification, planner |
| Playwright `npm run test:e2e` | 1 | `e2e/happy-path.spec.ts` (phase 1–2 happy path) |
| Oxlint | 0 error | `npx oxlint` |

### ❌ **Yang sengaja di‑skip / belum terbukti**

| Item | Alasan |
|---|---|
| SOLIDWORKS 2022 connector | Belum diimplementasi (Phase 6). |
| Maxsurf 20 V8i connector | Belum diimplementasi (Phase 7). |
| ANSYS | Tidak ada kode, tidak ada probe, tidak ada placeholder (sesuai konvensi). |

**Stop. Phase 3 selesai. Alpha 0.1 terpenuhi: dashboard + Rhino live + script hash + verification.**

---

## Phase 4 — Evidence engine + EEP

**Goal:** Traceable technical evidence with provenance.
**Status:** Implemented, tests passing.

### 4.0 Status (as of commit `5877de1` — 2026-11-07)

| Item | Status | Bukti |
|---|---|---|
| `evidence_sources` + `evidence_chunks` tables (migrations 003) | ✅ **terbukti** | `tests/test_evidence.py` |
| Source registry (metadata, checksum, status) | ✅ **terbukti** | `tests/test_evidence.py::test_checksum_detects_tampering` |
| PDF ingestion with page provenance | ✅ **terbukti** | `tests/test_evidence.py::test_ingest_and_list_source` |
| Lexical search (SQLite FTS5) | ✅ **terbukti** | `tests/test_evidence.py::test_search` |
| Formula registry + lifecycle enforcement | ✅ **terbukti** | `tests/test_evidence.py::test_formula_lifecycle` |
| Citation builder | ✅ **terbukti** | `tests/test_citation_builder.py` |
| Evidence status assignment (VERIFIED/CONDITIONAL/UNVERIFIED/INVALID) | ✅ **terbukti** | `tests/test_evidence.py::test_source_status` |

### ✅ **Yang sudah dijalankan dan lulus** (189/189 tests passing)

| Test suite | Jumlah passed | Bukti |
|---|---|---|
| `python -m pytest tests/` | 189 | semua unit, integration, artifact, verification, planner, evidence |

**Phase 4 selesai, semua acceptance criteria terpenuhi.**

---

---

## Conventions for all phases

- One commit per logical change, message: `<phase>: <what>`
- Tests before feature is marked done
- No new dependency without written justification in commit message
- No hardcoded paths, keys, or personal data
- ANSYS: no code, no probe, no placeholder in any phase
- Do not mark a capability SUPPORTED without a working test on this machine

