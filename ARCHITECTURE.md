# NEI — Architecture

**Status:** Living document. After Phase 1, Pydantic schemas and DB migrations in code are the source of truth for types and schema. This document records decisions and rationale.

**Source of truth map:**
| Fact | Source document |
|------|---------------|
| Module names, folder structure, dependency direction | This file (`ARCHITECTURE.md`) |
| Task state machine transitions, guards | `STATE_MACHINE_SPEC.md` |
| API endpoints, schemas, error codes | `API_SPEC.md` |
| Database tables, columns, indexes | `DATABASE_SCHEMA.md` |
| Connector capability status per software | `CONNECTOR_SPEC.md` |
| Verification postconditions and record schema | `VERIFICATION_SPEC.md` |
| Source metadata, formula lifecycle, evidence status | `ENGINEERING_EVIDENCE_PROTOCOL.md` |
| Security controls: binding, auth, file sandbox | `SECURITY.md` |
| Artifact integrity, backup, retention | `DATA_GOVERNANCE.md` |
| UI pages, components, design tokens, state | `FRONTEND_SPEC.md` |
| Phase deliverables and acceptance criteria | `PLAN.md` |

---

## 1. Mission

NEI is a local-first engineering assistant for naval architecture and marine engineering. It is not an autonomous authority. A qualified human remains responsible for design approval, regulatory interpretation, and release of deliverables.

**Core principles (non-negotiable):**
1. Evidence before assertion — claims tied to identifiable sources
2. Deterministic calculation — tested code, not LLM arithmetic
3. LLM as planner, not calculator
4. Local-first — all data on workstation by default
5. Explicit provenance — every input, equation, source, and output traceable
6. Fail closed — uncertain → UNVERIFIED, not invented
7. Human approval for consequential actions
8. No license circumvention
9. Reproducibility
10. ANSYS deferred until confirmed

---

## 2. System boundary

```
┌──────────────────────────────────────────────────────────────────┐
│  NEI Backend (Python 3.13, FastAPI, single process)             │
│                                                                │
│  API layer ── Orchestrator ── Execution Policy ── Connector Reg│
│  (routes)    (Planner +     (policy gate,  (capability-driven)│
│               Tool Router)   approvals +                                  │
│                               resource mgr)                              │
│                                                                │
│  Storage ── Evidence Engine ── Verification Engine            │
│  (SQLite     (Phase 4+)      (postcondition                        │
│  WAL +                                   checks)                                    │
│  artifacts)                                                     │
└──────────────────────────────────────────────────────────────────┘
       │                     │                     │
       ▼                     ▼                     ▼
  Rhino 6 (COM/IPC)  SOLIDWORKS 2022 (COM)  Maxsurf 20 V8i (file)
  [Phase 3]          [Phase 6]             [Phase 7]
```

**Outside the boundary:**
- ANSYS — deferred, no code
- Cloud / multi-machine orchestration
- Automated regulatory certification

---

## 3. Module responsibilities

| Module | Location | Responsibility | Phase |
|--------|----------|--------------|-------|
| API routes | `apps/api/` | HTTP interface, validation, auth check | 1 |
| Orchestrator | `nei/core/orchestrator.py` | Interpret request, build plan, dispatch | 1 |
| Planner | `nei/core/planner.py` | Structured plan generation (template + LLM) | 1 |
| Task manager | `nei/core/task_manager.py` | Task lifecycle, state transitions | 1 |
| State machine | `nei/core/state_machine.py` | Transition table, guards, audit | 1 |
| Tool router | `nei/core/tool_router.py` | Route steps to registered tools | 1 |
| Policy gate | `nei/execution/policy.py` | Risk level check, path validation | 1 |
| Approvals | `nei/execution/approvals.py` | Human approval workflow | 1 |
| Resource manager | `nei/execution/resource_manager.py` | Per-app locks, concurrent limit | 1 |
| Connector base | `nei/connectors/base.py` | Abstract connector interface | 1 |
| Connector registry | `nei/connectors/registry.py` | Discover + register available connectors | 1 |
| Rhino 6 connector | `nei/connectors/rhino6/` | Rhino 6 automation | 3 |
| SOLIDWORKS connector | `nei/connectors/solidworks2022/` | SW 2022 COM automation | 6 |
| Maxsurf connector | `nei/connectors/maxsurf_v8i/` | Maxsurf file exchange | 7 |
| Verification engine | `nei/verification/engine.py` | Postcondition checks, verification records | 3 |
| Evidence engine | `nei/evidence/` | Ingestion, retrieval, citation | 4 |
| Knowledge registries | `nei/knowledge/` | Source, formula, method, unit registries | 4–5 |
| Engineering domains | `nei/engineering/` | Unit-safe calculations by domain | 5 |
| Storage / DB | `nei/storage/` | SQLite, repositories, migrations, artifacts | 1 |
| Audit / observability | `nei/observability/` | Audit events, metrics, event bus | 1 |
| Reporting | `nei/reporting/` | Engineering report generation | 5 |
| Frontend | `apps/ui/` | React dashboard + workspace | 2 |

---

## 4. Data flow (one task, end to end)

```
User request (natural language)
  → API POST /tasks
  → Task created: state=PENDING
  → Planner: LLM + template → Plan JSON (steps, tools, risk levels)
  → state=PLANNING → VALIDATING
  → Policy gate: check paths, risk level, approval requirement
  → state=WAITING_APPROVAL (if L2+) or QUEUED (if L0/L1)
  → Approval recorded (L2+) or auto-pass (L0/L1)
  → state=QUEUED → RUNNING (acquire app lock)
  → Tool router dispatches steps to connector
  → Connector executes in software (Rhino/SW/Maxsurf)
  → Connector returns structured result + object IDs
  → state=VERIFYING
  → Verification engine: check postconditions against software result
  → All pass → state=COMPLETED
  → Any fail → state=NEEDS_REVIEW or FAILED
  → Artifact saved (SHA-256 manifest)
  → Audit event written
  → SSE event broadcast to UI
  → Report generated on request
```

---

## 5. Error handling and recovery

| Scenario | Behaviour |
|----------|-----------|
| LLM call fails / timeout | Task → NEEDS_INPUT with reason; user can retry or provide inputs manually |
| Connector unavailable | Task → FAILED with `CONNECTOR_UNAVAILABLE`; no retry unless user re-requests |
| Software hangs (timeout) | Task → RECOVERING; graceful detach; if not back within emergency timeout → FAILED |
| Verification postcondition fails | Task → NEEDS_REVIEW; report shows which check failed |
| Path outside allowed root | Request rejected before execution; `PATH_FORBIDDEN` |
| Approval payload changed after approval | Approval invalidated; task → WAITING_APPROVAL |
| Script exit 0 but postconditions fail | Task → NEEDS_REVIEW (not COMPLETED) |

**Recovery states:**
- `RECOVERING` → `QUEUED` (software back, user confirms) or `FAILED` (user cancels / emergency timeout)
- `NEEDS_REVIEW` is terminal for that task; a new task can be created linked via `parent_task_id`

---

## 6. Security summary

Full detail in `SECURITY.md`.

- Bind `127.0.0.1` only
- Session token (random UUID, httpOnly, SameSite=Strict)
- CORS: `http://localhost:5173` + `http://127.0.0.1:8000` only
- File sandbox: all paths canonicalised, checked against `data/` root
- LLM privacy mode: `NEI_LLM_PRIVACY=on` → no external calls, template-only planner
- No secrets in logs or responses

---

## 7. Deployment (local-first)

Single machine, single user.

```
dev_start.ps1
  → python apps/api/main.py  (uvicorn --host 127.0.0.1 --port 8000 --workers 1)
  → (dev only) cd apps/ui && npm run dev  (vite port 5173)
```

Production (same machine):
- `apps/ui` built → static files served by FastAPI at `/`
- Single process, single port (8000)
- No Docker, no service, no multi-process

---

## 8. Technology decisions (with status)

| Area | Decision | Status |
|------|----------|--------|
| Backend runtime | Python 3.13 | FAKTA |
| Web framework | FastAPI + Uvicorn | FAKTA |
| Schemas | Pydantic v2 | FAKTA |
| Database | SQLite WAL, single writer | FAKTA |
| Unit system | Pint, canonical SI | FAKTA |
| Numerical | NumPy, SciPy | FAKTA |
| Frontend | React + TypeScript + Vite | FAKTA |
| UI components | Tailwind CSS + shadcn/ui + Lucide | FAKTA |
| Data fetching | TanStack Query | FAKTA |
| Charts | Recharts (only when needed) | FAKTA |
| LLM | External OpenAI-compatible endpoint | KEPUTUSAN |
| Privacy mode | Template-only planner, no LLM | KEPUTUSAN |
| Vector search | SQLite FTS5 first; Qdrant only if justified | KEPUTUSAN |
| State management | Explicit state machine (no LangGraph unless measured need) | KEPUTUSAN |
| ANSYS | DEFERRED — no code | KEPUTUSAN |
| Library versions | `UNVERIFIED` until checked against registry | ASUMSI |

---

## 9. Deferred features

| Feature | Deferred to | Reason |
|---------|-------------|-------|
| ANSYS connector | After user confirms installation | Not confirmed; no version known |
| Vector DB (Qdrant) | Phase 4+ | SQLite FTS5 sufficient for initial retrieval |
| GUI automation (pywinauto) | Phase 7 | Maxsurf fallback only; fragile; last resort |
| Multi-user / auth passwords | Never (local-first single user) | Scope |
| Distributed microservices | Never for MVP | No measured need |
| Regulatory certification output | Phase 9+ | Requires full evidence + applicability engine |

