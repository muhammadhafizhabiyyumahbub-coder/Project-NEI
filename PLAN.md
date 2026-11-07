# NEI — Plan & Roadmap

**Source of truth for phase deliverables and acceptance criteria.**
Supersedes the 8-phase roadmap in the old `Arsitektur.py`.

Principle: **highest risk proved earliest; visible features do not sacrifice dependencies.**

---

## Phase 0 — Audit, environment, and risk spikes

**Status:** `data/environment.json` now resolves GPU, SOLIDWORKS/Maxsurf/Rhino versions, SOLIDWORKS COM availability, Maxsurf registry installation, file formats, and COM automation status. `scripts/measure_resource_budget.py` records current process working sets and enforces one-heavy-CAD-app-at-a-time policy for the 8GB host. `data/license_policy.json` documents license/automation policy as UNVERIFIED without accessing credentials or claiming permission. Hardware fields are verified; license status remains UNVERIFIED pending vendor documentation.

**Goal:** Resolve all UNVERIFIED items before writing integration code.

### Deliverables
- `environment.json` — Python version, Rhino/SW/Maxsurf exact versions, paths, bitness, OS
- Measured resource budget: `data/resource_budget.json` from `scripts/measure_resource_budget.py`; current CAD processes and serialized execution policy recorded
- Rhino 6 spike report (transport method selection, see `RHINO6_INTEGRATION_SPIKE.md`)
- SOLIDWORKS 2022 probe: detected? version? COM available? license state?
- Maxsurf 20 V8i probe: detected? version? file formats? automation interface?
- License policy check for each software (automation permitted?)

### Acceptance criteria
- `environment.json` exists with no `UNVERIFIED` hardware fields
- Rhino 6 spike: at least one transport method passes the box test
- SW/Maxsurf: probe reports (read-only, no document operations)
- License state documented (UNVERIFIED allowed if vendor doc unavailable)

### Not included
- No backend code
- No database
- No UI
- No document operations on production files

### Risks
- Rhino 6 bitness may force a different transport method than expected
- License may restrict automation; spike S5 may block Phase 3
- Resource budget may force "one heavy software at a time" policy

---

## Phase 1 — Backend foundation

**Status:** FastAPI backend with task lifecycle, policy gate, artifact store, audit logging, SSE, and mock tool router is implemented and covered by tests. The policy gate now rejects unknown or malformed risk levels as forbidden in addition to explicitly banning L3. Phase 2 spec task-approval decision endpoints are implemented: `POST /projects/{id}/tasks/{id}/approvals` (approve → QUEUED, reject → NEEDS_REVIEW) and `GET` listing; state machine now allows WAITING_APPROVAL → NEEDS_REVIEW on reject. New migration 008 (`task_approvals`) and 4 route tests added.

**Goal:** Runnable backend with task lifecycle, no CAD needed.

### Deliverables
- FastAPI app with health endpoint
- SQLite DB (WAL) + migration 001
- Pydantic contracts for Task, Plan, ToolAction, Approval, Artifact
- State machine (all transitions from `STATE_MACHINE_SPEC.md`)
- Task manager: create, view, cancel, provide-input, retry
- Policy gate (risk level, path sandbox)
- Audit logging (structured JSON)
- Artifact store (SHA-256 on write/read)
- SSE endpoint
- Mock tool router (template plans, no real connector calls)

### Acceptance criteria
- `POST /projects` → project created, `path_root` exists
- `POST /projects/{id}/tasks` → task created, state PENDING
- Task transitions through PLANNING → VALIDATING → QUEUED → RUNNING → VERIFYING → COMPLETED with mock tools
- `CANCEL` works from any active state
- `task_events` rows written for every transition
- Artifact SHA-256 verified on read
- No CAD software required to run the full test

### Depends on
- Phase 0 (environment confirmed)

### Not included
- Real connector calls
- Evidence engine
- Engineering calculations
- LLM calls (template-only planner in this phase)

---

## Phase 2 — Frontend foundation

**Status:** Vite/React UI is implemented under `apps/ui/` with generated API types, dashboard/task workflows, SSE updates, connector health, and static build path `apps/ui/dist/`. Production TypeScript build passes. Lint reports one intentional React effect warning for resetting SSE state when task ID changes. E2E selectors match rendered task and calculation controls. Playwright config now starts/reuses UI and API servers automatically before browser tests; task E2E selectors match nested project-task routes and rendered task-row markup. All 6 Playwright E2E tests now pass (fixed task-state class, calculation result panel selectors, dashboard heading text, task-creation/run selectors, server orchestration).

**Goal:** Dashboard usable for task management.

### Deliverables
- Vite + React + TypeScript scaffold
- App shell (sidebar, topbar, routing)
- Dashboard (system status, active tasks, connector health)
- Project list + create
- Task list + detail (state timeline, plan, errors)
- SSE live update
- Connector health page
- Settings page (read-only LLM config display)
- OpenAPI → TypeScript types
- Design tokens (dark theme)

### Acceptance criteria
- Dashboard loads and shows `/health` data
- Create project via UI → appears in project list
- Create task via UI → task detail shows live state via SSE
- Cancel task via UI → state updates without reload
- No TypeScript build errors
- All types from OpenAPI, no hand-written API interfaces

### Depends on
- Phase 1 (backend API live)

### Not included
- AI Workspace (chat input)
- Calculation Center
- Evidence browser
- Report export

---

## Phase 3 — Verification + Rhino 6 connector = **Alpha 0.1**

**Goal:** First visible engineering workflow: create box in Rhino 6, verify from Rhino result.

### Deliverables
- `nei/verification/` module (engine, postconditions, geometry check, record)
- Rhino 6 connector (spike-selected transport method)
- `rhino.detect`, `rhino.health_check`, `rhino.get_version`, `rhino.get_document_info`, `rhino.list_objects`
- `rhino.create_box_test` (disposable document only)
- `rhino.inspect_object`
- `rhino.export_copy` (new `.3dm` under `data/projects/<id>/artifacts/`)
- Verification: bounding box, object count, units from **Rhino result** (not stdout)
- Artifact manifest for `.3dm`
- LLM planner wired (external provider, privacy mode available)

### **Alpha 0.1 definition (acceptance):**
1. User opens dashboard
2. User creates a project
3. User requests a 10×3×1 box in Rhino 6
4. Planner produces a structured plan (template; LLM does not write free code)
5. Policy gate checks action and path
6. Rhino connector executes the script in a **disposable document**
7. Rhino creates the box object
8. Connector inspects object ID and bounding box from Rhino
9. Verification engine checks dimensions, object count, and units **from the Rhino result, not script stdout**
10. Artifact store saves the new `.3dm` and manifest
11. Dashboard displays result, script hash, and execution log
12. No original file is overwritten

**Alpha 0.1 does NOT require:** evidence engine, engineering core, SOLIDWORKS, Maxsurf, or ANSYS.

### Depends on
- Phase 0 (Rhino spike S2 transport selected)
- Phase 1 (backend + state machine)
- Phase 2 (dashboard UI)

### Not included
- SOLIDWORKS or Maxsurf connectors
- Engineering calculations
- Evidence retrieval
- Report export
- L3 risk level (disallowed in Alpha 0.1; L0–L2 only)

---

## Phase 4 — Evidence engine + EEP

**Status:** Source ingestion with sandbox validation, SHA-256 provenance, PDF/text extraction, page-aware chunks, SQLite FTS5 search, formula lifecycle enforcement, citations, and UNVERIFIED status handling are implemented and covered by tests. Ingestion is idempotent on checksum: repeated calls with the same file body return the canonical source record instead of duplicating the row. A duplicate ingest now re-verifies the stored document against its recorded SHA-256 and reports `intact` so integrity drift is visible even before the explicit checksum endpoint is called. Production evidence remains dependent on permitted authoritative source documents.

**Goal:** Traceable technical evidence with provenance.

### Deliverables
- `evidence_sources` + `evidence_chunks` tables (migrations 003)
- Source registry (metadata, checksum, status)
- PDF ingestion with page provenance
- Lexical search (SQLite FTS5)
- Formula registry + lifecycle enforcement
- Citation builder
- Evidence status assignment (VERIFIED/CONDITIONAL/UNVERIFIED/INVALID)

### Acceptance criteria
- Ingest a permitted sample document → `evidence_sources` row + chunks
- Search returns passage with correct page/section
- Citation has no invented metadata
- Incomplete source → `UNVERIFIED`

### Depends on
- Phase 3 (Alpha 0.1 stable)

---

## Phase 5 — Engineering core (deterministic)

**Status:** Core calculator, unit parsing, finite numeric input validation, formula lifecycle, reference-case verification, deterministic calculation traces, hull section preview, loading stability indicators, GZ proxy, and evidence-linked reports implemented. Independent reference cases now cover every built-in deterministic formula in `nei/engineering/reference_cases.py`. Full production approval still depends on evidence-backed formula records and reviewed authoritative cases.

**Goal:** Unit-safe, reproducible engineering calculations.

### Deliverables
- `formulas` + `calculation_runs` tables (migrations 004)
- Pint-based unit framework (canonical SI)
- Formula lifecycle enforcement (only APPROVED_FOR_USE in production)
- Initial reviewed geometry + hydrostatics formula(s) with reference cases
- Calculation trace generation
- Result status assignment (VERIFIED/UNVERIFIED/INVALID)

### Acceptance criteria
- Same inputs → same result (deterministic)
- Wrong units → rejected
- Missing source or reference case → prevents VERIFIED status
- At least one reference case passes for each approved formula

### Depends on
- Phase 4 (source registry, formula registry)

---

## Phase 6 — SOLIDWORKS 2022 connector

**Status:** SOLIDWORKS 30.1.0.0082 is installed and `SldWorks.Application` COM availability is verified in `scripts/check_environment.py`. Filesystem detection, version probe, active-instance COM probe, read-only document/feature inspection, sandbox export, and disposable-part path are implemented. Connector tests pass, and the recorded runtime probe confirms document metadata and 17 features on `20261106_205156_sw_export.SLDPRT`; export-to-sandbox preserved the source checksum. Runtime verification remains limited to read-only inspection because `sw.inspect_feature`, `sw.export_copy`, and `sw.create_test_part` lack complete version-tested evidence for production dispatch.

**Goal:** Read-only inspection + one safe write operation.

### Deliverables
- SW 2022 detect + version + COM probe
- Read-only: document info, feature list, document metadata
- `sw.create_test_part` (L2, approval required, disposable document only)
- Capability report per operation (version-tested)

### Acceptance criteria
- No unsupported API assumed
- All operations version-tested and logged
- Existing user files untouched
- L2 approval enforced

### Depends on
- Phase 3 (connector framework, verification)
- Phase 5 (engineering context optional but useful)

---

## Phase 7 — Maxsurf 20 V8i connector

**Status:** Maxsurf 20.00.01.59 is installed at `C:\Program Files\Bentley\Engineering\Maxsurf 20 V8i\` with Modeler, Stability, Resistance, Motions, VPP, Structure, Link, and Fitting modules. The connector now exposes a read-only `maxsurf.get_capabilities` audit that records installed automation manuals and file formats without claiming API support. No registered COM ProgID was found for candidate classes, so automation remains file-exchange-based. Runtime probe confirms Maxsurf process availability and read-only inspection of `.msd` files in `D:\File Maxsurf` with SHA-256; sandbox import/export and generated-artifact verification remain implemented. NEI-driven input exchange remains UNKNOWN. Human declared valid SOLIDWORKS/Maxsurf licenses and permitted read-only/sandbox exchange on 2026-11-07; declaration is recorded without storing credentials or treating it as vendor proof. Maxsurf Stability output (stability report/GZ curve) is still required before production claims.

**Goal:** File-exchange or API-driven Maxsurf integration.

### Deliverables
- Maxsurf detect + version + format capability audit
- File exchange proof of concept (import/export a controlled file)
- GUI automation fallback only for gaps
- All claims backed by reproducible tests

### Acceptance criteria
- Every claimed capability has a reproducible test
- No undocumented license/protection bypass
- No production design overwritten

### Depends on
- Phase 3 (connector framework)
- Phase 5 (optional)

---

## Phase 8 — Cross-software workflow

**Status:** Sequential sandbox handoff protocol, SHA-256 provenance manifests, unit-labelled artifacts, handoff-chain metadata validation, operation allowlisting, bounding-box transfer checks, and failure-safe path validation are implemented. Approval enforcement verifies artifact bytes on disk match the SHA-256 recorded in the evidence row, closing a tamper window between evidence write and approval. Handoff metadata now fails closed for unsupported operations or incomplete software/version/path records. SOLIDWORKS COM is available locally, but document-level transfer has not been version-tested against a live SOLIDWORKS document; end-to-end CAD-to-CAD transfer remains blocked until runtime workflows are demonstrated.

**Goal:** Controlled artifact handoff between two or more software packages.

### Deliverables
- Artifact handoff protocol (unit + coordinate mapping)
- Import/export validation between software
- Provenance manifest across software, with chain metadata validation before persistence
- Human approval for design-changing steps

### Acceptance criteria
- A test artifact moves between two supported applications
- Geometry/units checked after transfer
- Failure is recoverable and visible

### Depends on
- Phase 6 AND Phase 7 (at least two connectors working)

---

## Phase 9 — Advanced engineering domains

**Status:** Deterministic preview reports, loading stability indicators, longitudinal balance preview, GZ curve proxy with UNVERIFIED classification criteria baseline (`nei/engineering/gz.py`), finite-input and angle-range validation, evidence-linked JSON artifacts, dependency-free PDF preview export (`nei/engineering/pdf_report.py`), and explicit non-approval limitations are implemented. An independent arithmetic reference case now locks proxy GZ point and trapezoidal-area behavior. Production/classification outputs remain blocked by solver validation, approved formula evidence, and authoritative independent reference cases. Human supplied Maxsurf Stability license declaration, but no stability report or GZ curve output has been produced yet.

**Goal:** Extend evidence + calculation to more naval architecture / marine engineering domains.

### Deliverables
- Additional source collections
- More approved formula/method records
- GZ curve analysis + UNVERIFIED classification criteria baseline (implemented in `nei/engineering/gz.py`; proxy only, no hydrostatic solver, no approval path)
- Advanced hydrostatics / stability / resistance / propulsion methods (only as evidence + tests mature)
- Report export (PDF with full provenance)
- Hull preview now includes GZ curve and classification baseline (implemented in `nei/engineering/hull.py`)
- Hull tasks save JSON and PDF report artifacts with SHA-256 provenance

### Acceptance criteria
- Each new method has a source, reference case, and test
- GZ proxy has independent arithmetic reference coverage; it remains UNVERIFIED and non-production
- No unreviewed formula in production

### Depends on
- Phase 5 (engineering core)
- Phase 8 (cross-software, for CFD/structures context)

---

## ANSYS

**DEFERRED.** No work in any phase until the user confirms an installed ANSYS product, version, and license. When confirmed, a new phase is proposed.
