# NEI — Verification Specification

**Scope:** Verification engine design, postcondition checks, and the verification record schema.
**Module:** `nei/verification/`
**Phase:** 3 (minimal), extended in Phase 5+

> A task is **not** complete because a script returned exit code 0. The verification engine must inspect the **software result** and confirm all declared postconditions.

---

## Verification layers

| Layer | What it checks | Phase |
|-------|---------------|-------|
| **Script execution** | Script ran without exception, allowed APIs only, no forbidden operations | 3 |
| **Connector operation** | Connector returned a structured result (not just exit code), object IDs present | 3 |
| **Geometry** | Bounding box dimensions, object count, unit consistency | 3 |
| **Calculation** | Deterministic result matches expected within tolerance; dimensional consistency | 5 |
| **Source / evidence** | Citation is real, source status is not INVALID, page/section exists | 4 |
| **Engineering result** | Values within physical plausibility ranges; regulatory criteria (if applicable) | 5+ |

---

## Verification record schema

Every verification run produces a `VerificationRecord` stored in the task and retrievable via API.

```python
@dataclass
class VerificationCheck:
    target: str              # what was checked, e.g. "bounding_box", "object_count"
    expected: dict           # expected value or range
    actual: dict             # observed value from software result
    tolerance: float | None # acceptable deviation (None = exact match required)
    method: str              # how checked: "geometric_inspection", "value_compare", ...
    result: str              # "PASSED" | "FAILED" | "INCOMPLETE"
    evidence: str           # object ID, file path, or other proof
    timestamp: str          # ISO 8601 UTC

@dataclass
class VerificationRecord:
    task_id: str
    status: str             # "PASSED" | "FAILED" | "INCOMPLETE"
    checks: list[VerificationCheck]
    software_version: str   # version of the software where verification ran
    verified_at: str
```

**Storage:** Serialized as JSON in `tasks.verification_json` (added in Phase 3 migration). Also written to `audit_events` for the trail.

---

## Minimal postconditions (Alpha 0.1 — Rhino 6 box test)

For `rhino.create_box_test` with parameters `{length: 10.0, width: 3.0, height: 1.0}`:

| Check | Expected | Method | Tolerance |
|-------|----------|--------|-----------|
| `object_count` | 1 new object in document | `rhino.list_objects` diff before/after | exact |
| `object_type` | Brep (solid box) | `rhino.inspect_object` type field | exact |
| `bounding_box.l` | 10.0 (in document units) | `rhino.inspect_object` bbox | 0.001 |
| `bounding_box.w` | 3.0 | same | 0.001 |
| `bounding_box.h` | 1.0 | same | 0.001 |
| `document_units` | Matches requested unit | `rhino.get_document_info` units | exact |
| `artifact_saved` | `.3dm` file exists at expected path | filesystem + SHA-256 | exact |
| `original_untouched` | No file in `data/projects/<id>/artifacts/` was modified | SHA-256 compare pre/post | exact |

**All checks must PASS for the task to transition to `COMPLETED`.**
**Any check FAILED → task transitions to `NEEDS_REVIEW` with the failing check recorded.**

---

## Verification engine interface

```python
class VerificationEngine:
    def run(self, task: Task, checks: list[PostCondition]) -> VerificationRecord:
        """
        Execute all checks against the actual software state.
        Never mutates the task. Returns the record; caller applies state transition.
        """
        ...

    def verify_artifact(self, artifact_id: str) -> bool:
        """Re-read artifact from disk, compute SHA-256, compare to stored hash."""
        ...
```

**Rules:**
- Verification is read-only. It inspects software state; it does not modify documents.
- Each check is independent. One failure does not stop others — all checks run, all recorded.
- `INCOMPLETE` is returned when the software is unavailable or the check cannot be performed (e.g., Rhino closed). This is not a pass.
- Verification results are immutable once written to the record. Corrections go into a new verification run on a new task.

---

## Module location

```
nei/verification/
├── engine.py          # VerificationEngine
├── postconditions.py # PostCondition dataclasses + built-in checks
├── geometry_check.py # Bounding box, object count, unit checks
├── record.py         # VerificationRecord, VerificationCheck
└── __init__.py
```

**Dependency direction:** `verification/` depends on `connectors/` (for inspection) and `storage/` (for artifacts). It does NOT depend on `core/` or `evidence/`.
