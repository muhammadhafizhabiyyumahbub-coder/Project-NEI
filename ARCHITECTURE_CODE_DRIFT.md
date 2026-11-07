# ARCHITECTURE_CODE_DRIFT

**Date:** 2026-11-03
**Scope:** Compare documentation (ARCHITECTURE.md, ARCHITECTURE_DECISIONS.md, DATABASE_SCHEMA.md, PLAN.md, IMPLEMENTATION_GUIDE.md) against the **actual code structure** and API endpoints as of commit f803135.

**Note:** This report is a *drift* check, not a consistency check. See `ARCHITECTURE_CONSISTENCY_REPORT.md` for doc↔doc alignment.

---

## 1. Code location vs. docs

| Doc claims | Actual code | Status |
|-----------|-------------|--------|
| `apps/api/` contains the FastAPI backend | Backend is at `nei/` (root); `apps/api/` does not exist | **DRIFT** |
| `nei/execution/policy.py` (path in D1) | Policy at `nei/core/policy.py` | **DRIFT** |
| `nei/execution/` directory | No `nei/execution/` dir; execution logic scattered in `nei/connectors/` and `nei/core/task_manager.py` | **DRIFT** |
| `nei/verification/engine.py` | Exists at `nei/verification/engine.py` | OK |
| `nei/evidence/engine.py` | Exists at `nei/evidence/engine.py` | OK |
| `nei/engineering/calculator.py` | Exists at `nei/engineering/calculator.py` | OK |
| `nei/knowledge/` | Does not exist (evidence engine covers sources, but formula lifecycle is in `nei/evidence/engine.py`, not a separate `knowledge/` package) | **DRIFT** |
| `nei/storage/` | No `nei/storage/`; artifacts at `nei/core/artifact_store.py` | **DRIFT** |
| `nei/observability/` | No `nei/observability/`; SSE at `nei/api/sse.py` | **DRIFT** |
| `nei/reporting/` | No `nei/reporting/` | **DRIFT** |
| `docs/archive/` | Not found in repo | **DRIFT** |
| `apps/ui/` (Vite+React+TS+Tailwind) | Exists at `apps/ui/` with `src/pages/`, `src/components/`, `src/hooks/` | OK |
| `frontend/dist` (static build path in config.py) | UI is at `apps/ui/`, build output should be `apps/ui/dist/` | **FIXED** (Butir 9) |
| `NEI_ARCHITECTURE_V2_PROMPT.md` in root | Should be in `docs/prompts/` | **DRIFT** (Butir 11) |

---

## 2. API endpoint drift vs. `API_SPEC.md`

### 2.1 Endpoints implemented (nei/api/routes.py + evidence_routes.py + engineering_routes.py)

| Endpoint | Method | Implemented |
|----------|--------|:-:|
| `/health` | GET | ✓ |
| `/projects` | GET | ✓ |
| `/projects` | POST | ✓ |
| `/projects/{id}/tasks` | POST | ✓ |
| `/projects/{id}/tasks` | GET | ✓ |
| `/tasks/{id}` | GET | ✓ |
| `/tasks/{id}/events_raw` | GET | ✓ |
| `/tasks/{id}/cancel` | POST | ✓ |
| `/tasks/{id}/execute` | POST | ✓ (Butir 2) |
| `/tasks/{id}/verify` | POST | ✓ |
| `/connectors` | GET | ✓ |
| `/evidence/sources` | POST | ✓ |
| `/evidence/sources` | GET | ✓ |
| `/evidence/sources/{id}` | GET | ✓ |
| `/evidence/sources/{id}/verify-checksum` | POST | ✓ |
| `/evidence/sources/{id}/status` | POST | ✓ |
| `/evidence/search` | POST | ✓ |
| `/formulas` | POST | ✓ |
| `/formulas` | GET | ✓ |
| `/formulas/{id}` | GET | ✓ |
| `/formulas/{id}/advance` | POST | ✓ (Butir 3) |
| `/engineering/run` | POST | ✓ |
| `/engineering/reference-case` | POST | ✓ |
| `/engineering/reference-case-advance` | POST | ✓ |

### 2.2 Endpoints in `API_SPEC.md` Phase 1–2 that are **not yet implemented**

| Endpoint | Spec location | Status |
|----------|--------------|--------|
| `/tasks/{id}/approve` (approvals) | API_SPEC Phase 2 | **MISSING** |
| `/tasks/{id}/provide-input` | API_SPEC Phase 2 | **MISSING** |
| `/tasks/{id}/retry` | API_SPEC Phase 2 | **MISSING** |
| `/tasks/{id}/events` (SSE streaming) | API_SPEC Phase 1 | Implemented as `/tasks/{id}/events_raw` (SSE endpoint at `sse.router`) — naming differs from spec |
| `/approvals/{id}` | API_SPEC Phase 2 | **MISSING** |
| `/approvals/{id}/approve` | API_SPEC Phase 2 | **MISSING** |
| `/approvals/{id}/reject` | API_SPEC Phase 2 | **MISSING** |

**Recommendation:** Implement missing Phase 2 approval and task-control endpoints as part of a separate scope. Do **not** add them to the audit-fix commit set.

---

## 3. Python version drift

| Doc / config | Claimed version |
|-------------|----------------|
| `README.md` | Python 3.13 (corrected) |

**Note:** All Python version references have been corrected to 3.13 in this commit.
| `pyproject.toml` `requires-python` | `>=3.13` |
| `ARCHITECTURE.md` §5 | Python 3.13 (corrected) |
| Actual runtime | Python 3.13.7 |

**All docs and configs must be aligned to Python 3.13.** (Butir 7)

---

## 4. Maxsurf naming drift

| Doc / code | Mention |
|-----------|---------|
| `ARCHITECTURE.md` | "Maxsurf Enterprise v8.1" |
| `IMPLEMENTATION_GUIDE.md` | "maxsurf81" path |
| Actual detection | Maxsurf 20 V8i |

**All references to "Maxsurf Enterprise v8.1" and "maxsurf81" should be updated to "Maxsurf 20 V8i".** (Butir 8)

---

## 5. Static build path drift

| Item | Current value | Correct value |
|------|--------------|---------------|
| `static_build_path` in `nei/core/config.py` | `Path("frontend/dist")` → **fixed to `Path("apps/ui/dist")`** |

(Butir 9)

---

## 6. Spike evidence and metadata

| Item | Status |
|------|--------|
| `docs/spike/` with JSON results | **FIXED** — `docs/spike/rhino_box_test.json` saved from `data/spike/rhino_box_test.json` |
| `environment.json` `generated_at` placeholder `00:00:00Z` | **FIXED** — set to `2026-11-02T22:59:12+00:00` (actual spike timestamp) |

(Butir 10)

---

## 7. Recommended actions (priority order)

1. Update all docs and `pyproject.toml` to Python 3.13 (Butir 7).
2. Update `static_build_path` to `apps/ui/dist` (Butir 9).
3. Update all Maxsurf references to "Maxsurf 20 V8i" (Butir 8).
4. Save spike JSON to `docs/spike/` (Butir 10a).
5. Move `NEI_ARCHITECTURE_V2_PROMPT.md` to `docs/prompts/` (Butir 11).
6. **Documentation-only:** update ARCHITECTURE.md §3 module table to match actual `nei/` layout; mark `apps/api/` as deprecated/renamed to `nei/`; add `docs/spike/` to docs structure.
7. **New scope (not audit-fix):** implement missing Phase 2 approval/task-control endpoints.
