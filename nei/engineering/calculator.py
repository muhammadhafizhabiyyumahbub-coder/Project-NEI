"""Deterministic engineering calculation engine.

- Only runs formulas with review_status = APPROVED_FOR_USE (production mode)
- Or DRAFT/earlier with research=True (sandbox mode, results labelled UNVERIFIED)
- All results carry evidence_status: VERIFIED / UNVERIFIED / INVALID
- Formula reference case verification
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Callable

from nei.core.database import get_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ── Registry of formula implementations ─────────────────────────────────────
# Maps formula name → callable(*named_args) -> value (deterministic, no I/O)
FORMULA_REGISTRY: dict[str, dict] = {}


def register_formula(name: str, fn: Callable, param_names: list[str],
                     description: str = "",
                     param_units: Optional[dict] = None,
                     domain: str = "engineering"):
    """Register a Python implementation for a formula name.

    param_names: list of input keys that map 1:1 to fn positional args, in order.
    The caller passes inputs as a dict; missing required keys → INVALID.
    param_units: optional {param_name: target_si_unit} — string quantity
    inputs (e.g. "10 mm") are parsed to canonical SI before calling fn.
    domain: evidence domain used when seeding the database.
    """
    FORMULA_REGISTRY[name] = {
        "fn": fn,
        "param_names": param_names,
        "description": description,
        "param_units": param_units or {},
        "domain": domain,
    }


def _load_standard_formulas():
    """Register built-in formulas. Called once at module import time."""
    from nei.engineering.geometry import formulas as geo
    from nei.engineering.hydrostatics import formulas as hyd

    register_formula("box_volume", geo.box_volume,
                     ["length", "width", "height"],
                     "Box volume: L*W*H (m^3)",
                     param_units={"length": "m", "width": "m", "height": "m"},
                     domain="geometry")
    register_formula("box_surface_area", geo.box_surface_area,
                     ["length", "width", "height"],
                     "Box surface area",
                     param_units={"length": "m", "width": "m", "height": "m"},
                     domain="geometry")
    register_formula("displacement_volume", geo.displacement_volume,
                     ["loa", "beam", "draft"],
                     "V_block = L*B*T",
                     param_units={"loa": "m", "beam": "m", "draft": "m"},
                     domain="geometry")
    register_formula("metacentric_height", hyd.metacentric_height,
                     ["km", "kg"],
                     "GM = KM - KG",
                     param_units={"km": "m", "kg": "m"},
                     domain="hydrostatics")
    register_formula("initial_stability", hyd.initial_stability_indicator,
                     ["gm"],
                     "GM sign → stability",
                     param_units={"gm": "m"},
                     domain="hydrostatics")
    register_formula("hydrostatic_pressure", hyd.hydrostatic_pressure,
                     ["density", "g", "depth"],
                     "P = rho*g*h",
                     param_units={"density": "kg/m^3", "depth": "m"},
                     domain="hydrostatics")


def _parse_inputs(impl: dict, raw_inputs: dict) -> dict:
    """Parse string quantity inputs to canonical SI per the formula's param_units.

    - String values: parse via unit framework, reject unknown/malformed units.
    - Numeric values: pass through unchanged (caller already in canonical SI).
    - None: pass through (missing-input check handles it downstream).
    """
    from nei.engineering.units.framework import parse_quantity
    out: dict = dict(raw_inputs)
    for param, target in impl.get("param_units", {}).items():
        v = out.get(param)
        if isinstance(v, str):
            out[param] = parse_quantity(v, target)
    return out


def _call_formula(impl: dict, inputs: dict):
    """Call a registered formula with a dict of inputs, mapped to named args."""
    parsed = _parse_inputs(impl, inputs)
    args = [parsed.get(k) for k in impl["param_names"]]
    if any(a is None for a in args):
        missing = [k for k in impl["param_names"] if parsed.get(k) is None]
        raise ValueError(f"Missing required input(s): {missing}")
    return impl["fn"](*args)



_load_standard_formulas()


# ── Core calculation ─────────────────────────────────────────────────────────

def run_formula(
    formula_id: str,
    inputs: dict,
    *,
    task_id: Optional[str] = None,
    research: bool = False,
) -> dict:
    """Run a registered formula (sync wrapper).

    - Production (research=False): only APPROVED_FOR_USE formulas allowed.
    - Sandbox (research=True): any formula allowed, but result is UNVERIFIED.
    Must be called from a non-async context. Raises RuntimeError if an event
    loop is already running in the current thread.
    """
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None:
        raise RuntimeError(
            "run_formula (sync) cannot be called inside a running event loop; "
            "use _run_formula_async directly"
        )
    return asyncio.run(_run_formula_async(formula_id, inputs, task_id, research))


async def _run_formula_async(formula_id: str, inputs: dict,
                             task_id: Optional[str], research: bool) -> dict:
    # Load formula record
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT * FROM formulas WHERE id = ?", (formula_id,))
    if not rows:
        return {"status": "INVALID", "error": f"Formula {formula_id} not found"}
    formula = rows[0]
    cols = ["id", "name", "domain", "equation_text", "implementation_ref",
            "variables_json", "canonical_units", "assumptions_json",
            "applicability_json", "source_refs_json", "source_locations_json",
            "validation_case_refs_json", "review_status", "version",
            "created_at", "reviewed_by", "change_log_json"]
    formula = dict(zip(cols, formula))
    status = formula["review_status"]

    # Check lifecycle state
    if not research and status != "APPROVED_FOR_USE":
        return {
            "status": "INVALID",
            "error": f"Formula in status {status}; only APPROVED_FOR_USE allowed in production",
            "evidence_status": "INVALID",
        }

    # Look up implementation
    impl = FORMULA_REGISTRY.get(formula["name"])
    if impl is None:
        return {
            "status": "INVALID",
            "error": f"No implementation registered for formula {formula['name']!r}",
            "evidence_status": "INVALID",
        }

    # Execute
    try:
        result = _call_formula(impl, inputs)
    except Exception as e:
        return {
            "status": "INVALID",
            "error": f"Formula execution error: {e}",
            "evidence_status": "INVALID",
        }

    # Determine evidence status
    if status == "APPROVED_FOR_USE" and not research:
        evidence_status = "VERIFIED"
    else:
        evidence_status = "UNVERIFIED"

    run_id = str(uuid.uuid4())
    record = {
        "id": run_id,
        "formula_id": formula_id,
        "formula_name": formula["name"],
        "inputs": inputs,
        "result": result,
        "evidence_status": evidence_status,
        "formula_review_status": status,
        "deterministic_hash": _sha256(json.dumps(inputs, sort_keys=True) + formula["name"]),
        "created_at": _now(),
    }

    # Persist
    async with get_db() as db:
        await db.execute(
            """INSERT INTO calculation_runs
               (id, task_id, formula_id, inputs_json, result_json, status, trace_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, task_id, formula_id,
             json.dumps(inputs, sort_keys=True),
             json.dumps(record), evidence_status,
             json.dumps({"deterministic_hash": record["deterministic_hash"]}),
             _now()),
        )
        await db.commit()

    record["run_id"] = run_id
    return record


# ── Reference case verification ──────────────────────────────────────────────

async def verify_reference_case(
    formula_id: str,
    reference_inputs: dict,
    expected_result,
    tolerance: float = 1e-9,
) -> dict:
    """Run formula with reference inputs and compare to expected within tolerance."""
    impl = None
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT name FROM formulas WHERE id = ?", (formula_id,))
    if not rows:
        return {"passed": False, "error": "Formula not found"}
    formula_name = rows[0][0]
    impl = FORMULA_REGISTRY.get(formula_name)
    if impl is None:
        return {"passed": False, "error": "No implementation"}

    actual = _call_formula(impl, reference_inputs)
    if isinstance(expected_result, (int, float)) and isinstance(actual, (int, float)):
        passed = abs(actual - expected_result) <= tolerance
    elif isinstance(expected_result, str) and isinstance(actual, str):
        passed = actual == expected_result
    else:
        passed = actual == expected_result

    return {
        "formula_id": formula_id,
        "formula_name": formula_name,
        "reference_inputs": reference_inputs,
        "expected": expected_result,
        "actual": actual,
        "tolerance": tolerance,
        "passed": passed,
    }


# ── Get run record ───────────────────────────────────────────────────────────

async def get_calc_run(run_id: str) -> Optional[dict]:
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT * FROM calculation_runs WHERE id = ?", (run_id,))
    if not rows:
        return None
    r = rows[0]
    cols = ["id", "task_id", "formula_id", "inputs_json", "result_json",
            "status", "trace_json", "created_at"]
    rec = dict(zip(cols, r))
    rec["inputs"] = json.loads(rec.pop("inputs_json") or "{}")
    rec["result"] = json.loads(rec.pop("result_json") or "{}")
    rec["trace"] = json.loads(rec.pop("trace_json") or "{}")
    return rec
