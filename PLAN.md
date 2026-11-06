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

**Status:** Source ingestion with sandbox validation, SHA-256 provenance, PDF/text extraction, page-aware chunks, SQLite FTS5 search, formula lifecycle enforcement, citations, and UNVERIFIED status handling are implemented and covered by tests. Production evidence remains dependent on permitted authoritative source documents.

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

**Status:** Core calculator, unit parsing, formula lifecycle, reference-case verification, deterministic calculation traces, hull section preview, loading stability indicators, GZ proxy, and evidence-linked reports implemented. Independent reference cases now cover every built-in deterministic formula in `nei/engineering/reference_cases.py`. Full production approval still depends on evidence-backed formula records and reviewed authoritative cases.

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

**Status:** SOLIDWORKS 30.1.0.0082 is installed and `SldWorks.Application` COM availability is verified in `scripts/check_environment.py`. Filesystem detection, version probe, active-instance COM probe, read-only document/feature inspection, sandbox export, and disposable-part path are implemented. Capability reporting now requires a live active document before marking read-only document/feature inspection SUPPORTED; runtime verification remains UNKNOWN when no document is open.

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

**Status:** Maxsurf 20.00.01.59 is installed at `C:\Program Files\Bentley\Engineering\Maxsurf 20 V8i\` with Modeler, Stability, Resistance, Motions, VPP, Structure, Link, and Fitting modules. No registered COM ProgID was found for those candidate classes, so automation remains file-exchange-based and unverified. Detect/version, read-only `.msd` inspection, sandbox import/export, and generated-artifact verification are implemented with reproducible tests. Operator evidence in `docs/maxsurf_engineering_verification_report.md` confirms sandbox generation and manual reopen; NEI-driven input exchange remains UNKNOWN.

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

**Status:** Sequential sandbox handoff protocol, SHA-256 provenance manifests, unit-labelled artifacts, handoff-chain metadata validation, bounding-box transfer checks, and failure-safe path validation are implemented. SOLIDWORKS COM is available locally, but document-level inspection has not been version-tested against a live SOLIDWORKS document, so end-to-end CAD-to-CAD transfer remains blocked until runtime workflows are demonstrated.

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

**Status:** Deterministic preview reports, loading stability indicators, longitudinal balance preview, GZ curve proxy with UNVERIFIED classification criteria baseline (`nei/engineering/gz.py`), evidence-linked JSON artifacts, dependency-free PDF preview export (`nei/engineering/pdf_report.py`), and explicit non-approval limitations are implemented. An independent arithmetic reference case now locks proxy GZ point and trapezoidal-area behavior. Production/classification outputs remain blocked by solver validation, approved formula evidence, and authoritative independent reference cases.

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
