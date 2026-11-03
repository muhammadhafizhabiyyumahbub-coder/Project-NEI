"""Engineering core API routes (Phase 5)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from nei.evidence import get_formula
from nei.engineering.calculator import (
    run_formula,
    verify_reference_case,
    get_calc_run,
)
from nei.core.database import get_db

router = APIRouter()


class CalcRunRequest(BaseModel):
    formula_id: str
    inputs: dict
    task_id: Optional[str] = None
    research: bool = False  # sandbox mode allows non-APPROVED formulas


class CalcVerifyRequest(BaseModel):
    formula_id: str
    reference_inputs: dict
    expected_result: float | str
    tolerance: float = 1e-9


class CalcReferenceCaseRequest(BaseModel):
    """Register a reference case outcome on a formula + advance lifecycle."""
    formula_id: str
    to_status: str = "REFERENCE_CASE_TESTED"
    reference_inputs: dict
    expected_result: float | str
    tolerance: float = 1e-9
    reviewed_by: str = "user"


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/calculations")
async def calc_run_endpoint(body: CalcRunRequest):
    # Production guard: verify formula exists
    f = await get_formula(body.formula_id)
    if not f:
        raise HTTPException(status_code=404, detail="Formula not found")

    # run_formula is sync-wrapped; call async version directly
    from nei.engineering.calculator import _run_formula_async
    import asyncio
    result = await _run_formula_async(body.formula_id, body.inputs,
                                       body.task_id, body.research)
    if result.get("status") == "INVALID":
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/calculations/verify")
async def calc_verify_endpoint(body: CalcVerifyRequest):
    result = await verify_reference_case(
        body.formula_id, body.reference_inputs, body.expected_result,
        body.tolerance,
    )
    if not result.get("passed"):
        return {"ok": False, "result": result}
    return {"ok": True, "result": result}


@router.post("/calculations/reference-case")
async def calc_reference_case_endpoint(body: CalcReferenceCaseRequest):
    """Run reference case + advance formula to REFERENCE_CASE_TESTED.

    The formula must be at least SOURCE_ATTACHED to be advanced by a reference
    case test — running a reference case on a bare DRAFT (no source attached)
    is rejected.
    """
    from nei.evidence.engine import advance_formula
    vr = await verify_reference_case(
        body.formula_id, body.reference_inputs, body.expected_result,
        body.tolerance,
    )
    if not vr.get("passed"):
        raise HTTPException(
            status_code=400,
            detail=f"Reference case failed: expected={vr.get('expected')}, actual={vr.get('actual')}",
        )
    try:
        formula = await advance_formula(
            body.formula_id, body.to_status,
            reviewed_by=body.reviewed_by,
            reason=f"reference case passed: {body.reference_inputs} → {body.expected_result}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "reference_case": vr, "formula": formula}


@router.get("/calculations/{run_id}")
async def calc_run_id_endpoint(run_id: str):
    rec = await get_calc_run(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Calculation run not found")
    return rec
