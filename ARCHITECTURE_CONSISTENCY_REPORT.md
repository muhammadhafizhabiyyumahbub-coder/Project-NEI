# NEI — Architecture Consistency Report

**Date:** 2026-11-02
**Scope:** 13-item consistency audit per `NEI_ARCHITECTURE_V2_PROMPT.md` §8.

---

## 1. Module names and folder names consistent across all documents

| Check | Result |
|-------|--------|
| `nei/core/`, `nei/execution/`, `nei/connectors/`, `nei/verification/`, `nei/evidence/`, `nei/knowledge/`, `nei/engineering/`, `nei/storage/`, `nei/observability/`, `nei/reporting/` | CONSISTENT — same names in `ARCHITECTURE.md` §3, `ARCHITECTURE_DECISIONS.md` D1, `DATABASE_SCHEMA.md`, `PLAN.md`, `IMPLEMENTATION_GUIDE.md` |
| `apps/api/`, `apps/ui/` | CONSISTENT — all documents use `apps/api/` and `apps/ui/` |
| `nei/verification/` | CONSISTENT — `ARCHITECTURE.md` §3 lists it; `VERIFICATION_SPEC.md` §"Module location" confirms `nei/verification/engine.py`; `IMPLEMENTATION_GUIDE.md` Phase 3 step 1.2 references it |
| `docs/archive/` | CONSISTENT — `ARCHITECTURE_DECISIONS.md` D1 + `IMPLEMENTATION_GUIDE.md` Phase 0 |

**No conflicts found.**

---

## 2. Every module in the diagram has a location and responsibility in the repository

`ARCHITECTURE.md` §3 lists 21 modules. Cross-referenced against the repository structure in `ARCHITECTURE_DECISIONS.md` D1:

| Module | In diagram (§2) | In repo structure (D1) | Responsibility stated |
|--------|:-:|:-:|:-:|
| API routes | ✓ | ✓ `apps/api/` | ✓ |
| Orchestrator | ✓ | ✓ `nei/core/orchestrator.py` | ✓ |
| Planner | ✓ | ✓ `nei/core/planner.py` | ✓ |
| Task manager | ✓ | ✓ `nei/core/task_manager.py` | ✓ |
| State machine | ✓ | ✓ `nei/core/state_machine.py` | ✓ |
| Tool router | ✓ | ✓ `nei/core/tool_router.py` | ✓ |
| Policy gate | ✓ | ✓ `nei/execution/policy.py` | ✓ |
| Approvals | ✓ | ✓ `nei/execution/approvals.py` | ✓ |
| Resource manager | ✓ | ✓ `nei/execution/resource_manager.py` | ✓ |
| Connector base | ✓ | ✓ `nei/connectors/base.py` | ✓ |
| Connector registry | ✓ | ✓ `nei/connectors/registry.py` | ✓ |
| Rhino 6 connector | ✓ | ✓ `nei/connectors/rhino6/` | ✓ |
| SOLIDWORKS connector | ✓ | ✓ `nei/connectors/solidworks2022/` | ✓ |
| Maxsurf connector | ✓ | ✓ `nei/connectors/maxsurf/` | ✓ |
| Verification engine | ✓ | ✓ `nei/verification/engine.py` | ✓ |
| Evidence engine | ✓ | ✓ `nei/evidence/` | ✓ |
| Knowledge registries | ✓ | ✓ `nei/knowledge/` | ✓ |
| Engineering domains | ✓ | ✓ `nei/engineering/` | ✓ |
| Storage / DB | ✓ | ✓ `nei/storage/` | ✓ |
| Audit / observability | ✓ | ✓ `nei/observability/` | ✓ |
| Reporting | ✓ | ✓ `nei/reporting/` | ✓ |
| Frontend | ✓ | ✓ `apps/ui/` | ✓ |

**All 22 modules accounted for. No orphan modules.**

---

## 3. Endpoints match frontend needs

Cross-referencing `API_SPEC.md` endpoints with `FRONTEND_SPEC.md` page requirements:

| Frontend page | Endpoints needed | Present in API_SPEC? |
|---------------|-----------------|:--:|
| Dashboard | `GET /health`, `GET /projects/{id}/tasks` (active), `GET /connectors` | ✓ |
| Project list | `GET /projects`, `POST /projects` | ✓ |
| Project detail | `GET /projects/{id}`, `GET /projects/{id}/tasks`, `GET /projects/{id}/tasks/{id}` | ✓ |
| Task detail | `GET /tasks/{id}`, `POST /cancel`, `POST /provide-input`, `POST /retry`, `POST /approvals` | ✓ |
| Task detail — verification | `GET /projects/{id}/tasks/{id}/verification` (Phase 3) | ✓ |
| Connector health | `GET /connectors`, `GET /connectors/{id}`, `POST /connectors/{id}/probe` | ✓ |
| Settings (read-only) | No write endpoint in Phase 2 — read-only display only | ✓ (intentionally limited) |
| SSE live update | `GET /events` | ✓ |

**No frontend page requires an endpoint that is missing from `API_SPEC.md`.**

---

## 4. Request/response schemas match planned Pydantic models

| Pydantic model (planned) | Used in API spec | Consistent? |
|--------------------------|-----------------|:--:|
| `Task` | `POST /tasks` response, `GET /tasks/{id}` response | ✓ — fields match `tasks` DB table |
| `Plan` / `PlanStep` | `plan_json` in task response | ✓ |
| `Approval` | `POST /approvals` request/response | ✓ |
| `Artifact` | `GET /artifacts` (Phase 3), manifest | ✓ |
| `DetectionResult` | `POST /connectors/{id}/probe` response | ✓ |
| `ToolResult` | Connector `execute()` return | ✓ |
| `VerificationRecord` | `GET /verification` response | ✓ — fields match `VERIFICATION_SPEC.md` |
| `TaskState` enum | `task.state`, `task_events.from_state/to_state` | ✓ — 13 states match `STATE_MACHINE_SPEC.md` |

**One gap:** `API_SPEC.md` `POST /projects/{id}/tasks` request does not include `risk_level` — it is derived by the planner, not supplied by the user. This is consistent: the planner assigns `risk_level` from the task type and tool actions. No conflict, but worth noting for implementation.

---

## 5. State machine matches task API

| State machine event | API endpoint that triggers it | Consistent? |
|-------------------|-------------------------------|:--:|
| `created` → PENDING | `POST /tasks` | ✓ |
| `planning_start` → PLANNING | Internal (auto after PENDING) | ✓ |
| `input_provided` → PLANNING | `POST /tasks/{id}/provide-input` | ✓ |
| `validation_passed` → WAITING_APPROVAL/QUEUED | Internal (auto) | ✓ |
| `approved` → QUEUED | `POST /tasks/{id}/approvals` (action=approve) | ✓ |
| `rejected` → CANCELLED | `POST /tasks/{id}/approvals` (action=reject) | ✓ |
| `user_cancelled` → CANCELLED | `POST /tasks/{id}/cancel` | ✓ |
| `user_retry` → new task | `POST /tasks/{id}/retry` | ✓ |
| `lock_acquired` → RUNNING | Internal (resource manager) | ✓ |
| `all_steps_done` → VERIFYING | Internal (tool router) | ✓ |
| `all_postconditions_passed` → COMPLETED | Internal (verification engine) | ✓ |
| `postcondition_failed` → NEEDS_REVIEW | Internal (verification engine) | ✓ |
| `timeout` → RECOVERING | Internal (connector timeout) | ✓ |
| `software_back` → QUEUED | Internal (user confirms in UI) | ⚠ see conflict C1 |
| `emergency_timeout` → FAILED | Internal (timer) | ✓ |

**Conflict C1 (MEDIUM):** `STATE_MACHINE_SPEC.md` says `RECOVERING → QUEUED` is triggered by `software_back` event with guard "user confirms software is responsive". `API_SPEC.md` has no endpoint for this confirmation. The frontend has no UI element for it in Phase 2. **Resolution:** Add `POST /api/v1/projects/{project_id}/tasks/{task_id}/confirm-recovery` in a Phase 3 API addition, or treat `software_back` as an automatic internal event triggered by the connector's `health_check` returning OK. **Recommendation:** automatic — connector polls health; if healthy, `software_back` fires without user action. Document this in `STATE_MACHINE_SPEC.md` as a clarification.

---

## 6. Database supports task, audit, and verification

| Requirement | Table(s) | Present? |
|-------------|----------|:--:|
| Task lifecycle | `tasks`, `task_events` | ✓ |
| Audit trail | `audit_events`, `task_events` | ✓ |
| Verification record | `tasks` (JSON column needed) or separate table | ⚠ see conflict C2 |
| Approval record | `approvals` | ✓ |
| Artifact integrity | `artifacts` (SHA-256) | ✓ |
| Model usage / cost | `model_usage` | ✓ |
| App state (session token) | `app_state` | ✓ |

**Conflict C2 (MEDIUM):** `VERIFICATION_SPEC.md` says the verification record is stored as JSON in `tasks.verification_json` (added in Phase 3 migration). `DATABASE_SCHEMA.md` `tasks` table has no `verification_json` column in Phase 1–2 spec. This is a **Phase 3 migration gap** — `verification_json` must be added to the `tasks` table in migration 002 or a new `verification_records` table created in Phase 3. `DATABASE_SCHEMA.md` currently lists `connectors` and `connector_probes` as Phase 1 tables (migration 002), but the Phase 4+ deferred list also includes `connectors` and `connector_probes`. **Resolution:** Move `connectors` and `connector_probes` to Phase 3 (when Rhino connector is implemented), not Phase 1. Add `verification_json` to `tasks` in Phase 3 migration. Update `DATABASE_SCHEMA.md` accordingly.

---

## 7. Approval policy consistent with risk levels L0–L3

| Risk level | Policy (from `ARCHITECTURE.md` §12.1 in old doc, confirmed in `ARCHITECTURE_DECISIONS.md`) | `STATE_MACHINE_SPEC.md` | `API_SPEC.md` | Consistent? |
|-----------|------|------------------------|---------------|:--:|
| L0 | Auto-run, no approval | `VALIDATING → QUEUED` (L0) | No approval endpoint needed | ✓ |
| L1 | Auto-run after preflight | `VALIDATING → QUEUED` (L1) | No approval endpoint needed | ✓ |
| L2 | Explicit user approval | `VALIDATING → WAITING_APPROVAL` | `POST /approvals` | ✓ |
| L3 | Approval immediately before; prefer disallow | `VALIDATING → WAITING_APPROVAL` (stricter) | `POST /approvals` with `APPROVAL_PAYLOAD_MISMATCH` check | ✓ |

**One clarification needed:** `STATE_MACHINE_SPEC.md` does not distinguish L2 from L3 in the transition table — both go to `WAITING_APPROVAL`. The guard difference (L3 requires approval "immediately before action") is not encoded. **Recommendation:** Add a note to `STATE_MACHINE_SPEC.md`: "For L3 actions, the `WAITING_APPROVAL` state has a shorter TTL (e.g., 5 minutes); if not approved within TTL, task auto-transitions to `FAILED`." Or: L3 is disallowed in MVP (per old doc §12.1 "prefer disallow in MVP"). **Decision:** L3 is not implemented in Alpha 0.1. Document this as a limitation.

---

## 8. Capability connector matches tool router

| Connector capability | Tool router dispatch | Consistent? |
|---------------------|--------------------|:--:|
| `rhino.detect` (L0) | `MockToolRouter` in Phase 1 → real `Rhino6Connector.detect()` in Phase 3 | ✓ |
| `rhino.create_box_test` (L1) | `MockToolRouter` → real connector | ✓ |
| `rhino.export_copy` (L1) | `MockToolRouter` → real connector | ✓ |
| `sw.create_test_part` (L2) | Not in Phase 1 mock (SW not in scope until Phase 6) | ✓ — correctly deferred |
| Capability status `UNKNOWN` (default) | Tool router should refuse to dispatch if capability is `UNKNOWN` and no probe has been run | ⚠ see conflict C3 |

**Conflict C3 (MEDIUM):** `CONNECTOR_SPEC.md` says default capability status is `UNKNOWN`. `API_SPEC.md` `GET /connectors` returns capabilities with status. But `ARCHITECTURE.md` §4 data flow shows the tool router dispatching steps to connectors without checking capability status. **Resolution:** Tool router must check capability status before dispatching. If status is `UNKNOWN`, the task transitions to `NEEDS_INPUT` with reason "connector capability not yet probed; run probe first" rather than attempting execution. Add this guard to `IMPLEMENTATION_GUIDE.md` Phase 1 tool router spec.

---

## 9. Verification engine matches task lifecycle

| Check | Consistent? |
|-------|:--:|
| Verification runs after `VERIFYING` state entry | ✓ — `STATE_MACHINE_SPEC.md` |
| All postconditions must PASS for `COMPLETED` | ✓ — `STATE_MACHINE_SPEC.md` rule 1, `VERIFICATION_SPEC.md` |
| Any postcondition FAILED → `NEEDS_REVIEW` | ✓ — `STATE_MACHINE_SPEC.md` |
| `NEEDS_REVIEW` is terminal (retry creates new task) | ✓ — `STATE_MACHINE_SPEC.md` rule 4, `API_SPEC.md` retry endpoint |
| Verification record stored with task | ⚠ Conflict C2 (DB schema gap) |
| Verification is read-only (does not modify software) | ✓ — `VERIFICATION_SPEC.md` rules |
| `INCOMPLETE` status (software unavailable) is not a pass | ✓ — `VERIFICATION_SPEC.md` |

**Consistent, subject to C2 resolution.**

---

## 10. Roadmap consistent with dependencies and Alpha 0.1

| Phase | Depends on | Listed in PLAN.md | Correct? |
|-------|-----------|-------------------|:--:|
| 0 | — | ✓ | ✓ |
| 1 | 0 | ✓ | ✓ |
| 2 | 1 | ✓ | ✓ |
| 3 (Alpha 0.1) | 0, 1, 2 | ✓ | ✓ |
| 4 | 3 | ✓ | ✓ |
| 5 | 4 | ✓ | ✓ |
| 6 | 3, 5 | ✓ | ✓ |
| 7 | 3, 5 | ✓ | ✓ |
| 8 | 6, 7 | ✓ | ✓ |
| 9 | 5, 8 | ✓ | ✓ |

**Alpha 0.1 definition in `PLAN.md` Phase 3:**
- Matches `NEI_ARCHITECTURE_V2_PROMPT.md` §7 definition exactly ✓
- Does not require evidence engine ✓
- Does not require engineering core ✓
- Rhino box test from Rhino result (not stdout) ✓
- Artifact + manifest saved ✓
- No original file overwritten ✓

**No dependency conflicts found.**

---

## 11. ANSYS remains DEFERRED

| Document | ANSYS status | Consistent? |
|----------|-------------|:--:|
| `ARCHITECTURE.md` §8 | `DEFERRED — no code` | ✓ |
| `ARCHITECTURE_DECISIONS.md` D10 | `DEFERRED` | ✓ |
| `PLAN.md` | `DEFERRED. No work in any phase` | ✓ |
| `CONNECTOR_SPEC.md` | `No code, no probe, no placeholder` | ✓ |
| `IMPLEMENTATION_GUIDE.md` | No ANSYS in any phase | ✓ |
| `DATABASE_SCHEMA.md` | No `ansys` table | ✓ |
| `API_SPEC.md` | No ANSYS endpoint | ✓ |

**CONSISTENT across all documents.**

---

## 12. No unproven API or library version claims

| Claim | Status |
|-------|--------|
| FastAPI `>=0.100` in `pyproject.toml` | UNVERIFIED — version not checked against PyPI. Acceptable: `>=` constraint allows any compatible version. |
| Pydantic v2 in `pyproject.toml` | UNVERIFIED — not checked against registry. |
| Pint `>=0.20` | UNVERIFIED. |
| NumPy `>=1.24`, SciPy `>=1.10` | UNVERIFIED. |
| shadcn/ui + Tailwind versions in `FRONTEND_SPEC.md` | Not specified (intentionally — to be resolved in Phase 2 scaffold). |
| `openapi-typescript` tool | Not versioned. |
| Rhino 6 API capability | UNVERIFIED — correctly marked in `CONNECTOR_SPEC.md`. |
| SOLIDWORKS COM availability | UNVERIFIED — correctly marked. |
| Maxsurf automation | UNVERIFIED — correctly marked. |

**No document claims a specific library version as verified. All are either UNVERIFIED or intentionally left unspecified. CONSISTENT with the "don't claim unverified" rule.**

---

## 13. No fact defined in more than one source document

| Fact | Primary source | Duplicated elsewhere? |
|------|---------------|----------------------|
| Module names + locations | `ARCHITECTURE.md` §3 | Referenced in `ARCHITECTURE_DECISIONS.md` D1 (copy) — **acceptable**: D1 is the decision record; ARCHITECTURE.md is the living doc. Both should stay in sync; the source of truth is ARCHITECTURE.md. |
| State transitions | `STATE_MACHINE_SPEC.md` | Referenced in `ARCHITECTURE.md` §5 (summary only, no transition table) — **OK** |
| API endpoints | `API_SPEC.md` | Referenced in `FRONTEND_SPEC.md` (page-to-endpoint mapping) — **OK** (mapping, not redefinition) |
| DB tables | `DATABASE_SCHEMA.md` | Referenced in `PLAN.md` (table names only, no column specs) — **OK** |
| Connector capabilities | `CONNECTOR_SPEC.md` | Referenced in `API_SPEC.md` `GET /connectors` response example — **OK** (example, not redefinition) |
| Verification postconditions | `VERIFICATION_SPEC.md` | Referenced in `API_SPEC.md` (response example) — **OK** |
| Formula lifecycle | `ENGINEERING_EVIDENCE_PROTOCOL.md` | Referenced in `PLAN.md` Phase 5 (name only) — **OK** |
| Alpha 0.1 definition | `PLAN.md` Phase 3 | Referenced in `NEI_ARCHITECTURE_V2_PROMPT.md` §7 (original) and `ARCHITECTURE_DECISIONS.md` D7 (copy) — **drift risk**: if Alpha 0.1 definition changes, it must be updated in PLAN.md (primary) and both secondary copies. |

**No fact is defined as primary source in more than one document. Two secondary copies exist (Alpha 0.1 in 3 places; module structure in 2 places). These are acceptable as long as the primary source is always updated first.**

---

## Summary of conflicts and gaps

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| **C1** | MEDIUM | `RECOVERING → QUEUED` (`software_back`) has no API endpoint in `API_SPEC.md` and no UI element in `FRONTEND_SPEC.md` | Add auto-trigger: connector `health_check` OK → `software_back` fires internally. No new endpoint needed. Clarify in `STATE_MACHINE_SPEC.md`. |
| **C2** | MEDIUM | `tasks.verification_json` column missing from `DATABASE_SCHEMA.md` Phase 1–2 spec; `connectors`/`connector_probes` listed as Phase 1 but should be Phase 3 | Add `verification_json TEXT` to `tasks` in Phase 3 migration. Move `connectors` + `connector_probes` to Phase 3 in `DATABASE_SCHEMA.md`. |
| **C3** | MEDIUM | Tool router does not check capability status before dispatching (would dispatch to `UNKNOWN` capability) | Add guard to `IMPLEMENTATION_GUIDE.md` Phase 1: "Tool router refuses to dispatch if connector capability status is `UNKNOWN` and no probe has been recorded." |
| **C4** | LOW | L3 risk level: `STATE_MACHINE_SPEC.md` does not encode the "immediately before action" stricter policy for L3 | L3 is out of scope for Alpha 0.1. Document as limitation in `PLAN.md` Phase 3 "Not included". |
| **C5** | LOW | `POST /tasks` request does not include `risk_level` — it is derived by planner. This is correct but not documented in `API_SPEC.md` | Add note to `API_SPEC.md` `POST /tasks`: "risk_level is derived by the planner from task_type and tool actions; not supplied by the user." |

---

## Items not in conflict

- ANSYS consistently deferred ✓
- No unverified library version claims ✓
- No fact defined as primary source in 2+ documents ✓
- All 22 modules have locations ✓
- All frontend pages map to existing API endpoints ✓
- Roadmap dependencies are acyclic and consistent ✓
- State machine terminal states are correct ✓

---

## Recommended actions before Phase 1 coding

1. **C2 (do first):** Update `DATABASE_SCHEMA.md` — add `verification_json TEXT` to `tasks` table (Phase 3 migration). Move `connectors` + `connector_probes` from Phase 1 deferred list to Phase 3.
2. **C1:** Add clarification note to `STATE_MACHINE_SPEC.md`: "The `software_back` event is triggered automatically by the connector's `health_check` returning OK. No user action or API call is required."
3. **C3:** Add capability guard to `IMPLEMENTATION_GUIDE.md` Phase 1, tool router section.
4. **C4, C5:** Add notes to `PLAN.md` and `API_SPEC.md` respectively.
