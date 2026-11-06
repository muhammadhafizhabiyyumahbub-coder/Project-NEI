# NEI — Nautical Engineering Intelligence

Local-first AI engineering assistant for Naval Architecture and Marine Engineering.

## What NEI does

- Accepts engineering instructions in natural language
- Produces structured execution plans (LLM as planner, not calculator)
- Retrieves traceable technical evidence (journals, books, IMO/BKI/IACS standards)
- Runs deterministic calculations via a tested calculation engine
- Controls engineering software through capability-driven connectors (Rhino 6, SOLIDWORKS 2022, Maxsurf 20 V8i)
- Verifies results from software output (not script stdout)
- Stores artifacts, audit logs, and provenance locally
- Generates engineering reports with source citations

## What NEI does NOT do

- Not a classification authority
- Not a CAD/CAE replacement
- No autonomous regulatory certification
- No license bypass
- No unreviewed LLM arithmetic as source of truth
- ANSYS: deferred until confirmed installed

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, FastAPI, Pydantic v2, SQLite (WAL) |
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Automation | COM (SOLIDWORKS), RhinoCommon/RhinoPython (Rhino 6), file exchange (Maxsurf) |
| LLM | External OpenAI-compatible endpoint (privacy mode: template-only) |
| Tests | pytest (206 passed, 4 skipped, 1 warning) — see `PLAN.md` for implementation status |

## Documents

| File | Purpose |
|------|---------|
| `ARCHITECTURE.md` | System boundary, modules, data flow, security, decisions |
| `ARCHITECTURE_AUDIT.md` | Audit findings (Tahap 1) |
| `ARCHITECTURE_DECISIONS.md` | Decision log with rationale (Tahap 2) |
| `API_SPEC.md` | REST + SSE endpoint contracts (Phase 1–2 full, later phases listed) |
| `DATABASE_SCHEMA.md` | SQLite tables, columns, constraints, indexes |
| `STATE_MACHINE_SPEC.md` | Task state transition table, guards, side effects |
| `FRONTEND_SPEC.md` | UI components, pages, state, design tokens |
| `CONNECTOR_SPEC.md` | Connector contract + Rhino/SW/Maxsurf capability spec |
| `VERIFICATION_SPEC.md` | Verification engine: postconditions, record schema |
| `ENGINEERING_EVIDENCE_PROTOCOL.md` | Source metadata, formula lifecycle, evidence status |
| `SECURITY.md` | Local security model: binding, auth, file sandbox, LLM privacy |
| `DATA_GOVERNANCE.md` | Artifact integrity, backup, retention, document rights |
| `PLAN.md` | Roadmap phases 0–9 with dependencies and acceptance criteria |
| `IMPLEMENTATION_GUIDE.md` | Phase 0–2 build order, folder structure, test gates |

## Getting started

See `IMPLEMENTATION_GUIDE.md` for Phase 0–2.

## Status

- **Phase 0–3:** Environment probes, backend, frontend, Rhino 6 Alpha 0.1 — complete
- **Phase 4–5:** Evidence engine, engineering core, deterministic preview — complete
- **Phase 6–7:** SOLIDWORKS/Maxsurf connectors implemented; runtime verification blocked pending live document workflows
- **Phase 8:** Cross-software handoff protocol — complete
- **Phase 9:** GZ proxy, classification baseline, PDF preview, reference cases — complete; production blocked pending solver/authoritative evidence

All phases complete or blocked by genuine CAD/solver/license limits. See `PLAN.md` for details.
