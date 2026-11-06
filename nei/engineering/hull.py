"""Validated, deterministic hull input calculations. No CAD generation."""
from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime, timezone
import json
import math


from nei.engineering.vessel_profiles import get_default_block_coefficient, validate_hull_against_profile
from nei.core.database import get_db

class HullDesignRequest(BaseModel):
    vessel_type: str = Field(min_length=1)
    loa: float = Field(gt=0)
    beam: float = Field(gt=0)
    depth: float = Field(gt=0)
    draft: float = Field(gt=0)
    speed: float = Field(ge=0)
    block_coefficient: Optional[float] = Field(default=None, gt=0, le=1)
    kg: Optional[float] = Field(default=None, ge=0)
    km: Optional[float] = Field(default=None, ge=0)
    loading_conditions: list[dict] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_geometry(self):
        if self.draft >= self.depth:
            raise ValueError("Draft must be less than depth")
        if self.draft >= self.beam:
            raise ValueError("Draft must be less than beam")
        if self.block_coefficient is None:
            # Use lowercase for registry lookup
            key = self.vessel_type.lower().replace(" ", "_")
            self.block_coefficient = get_default_block_coefficient(key)
        return self


def hull_preview(request: HullDesignRequest) -> dict:
    volume = request.block_coefficient * request.loa * request.beam * request.draft
    waterplane_area = request.loa * request.beam
    kb = request.draft / 2.0
    gm = request.km - request.kg if request.km is not None and request.kg is not None else None
    stability_status = "not_verified" if gm is None else ("stable" if gm > 0 else "unstable" if gm < 0 else "neutral")
    loading_results = []
    for condition in request.loading_conditions:
        condition_id = condition.get("id", f"condition_{len(loading_results) + 1}")
        condition_kg = condition.get("kg")
        condition_km = condition.get("km", request.km)
        condition_gm = condition_km - condition_kg if condition_kg is not None and condition_km is not None else None
        loading_results.append({
            "id": condition_id,
            "gm_m": round(condition_gm, 6) if condition_gm is not None else None,
            "status": "not_verified" if condition_gm is None else "stable" if condition_gm > 0 else "unstable" if condition_gm < 0 else "neutral",
        })
    froude = (request.speed * 0.514444) / math.sqrt(9.80665 * request.loa) if request.speed else 0.0
    
    key = request.vessel_type.lower().replace(" ", "_")
    profile_warnings = validate_hull_against_profile(request.model_dump(), key)
    
    warnings = profile_warnings
    if request.speed > 40:
        warnings.append("Speed is unusually high; confirm vessel type and units.")
    return {
        "status": "PREVIEW_ONLY",
        "inputs": request.model_dump(),
        "calculations": {
            "displacement_volume_m3": round(volume, 6),
            "waterplane_area_m2": round(waterplane_area, 6),
            "center_of_buoyancy_z_m": round(kb, 6),
            "metacentric_height_m": round(gm, 6) if gm is not None else None,
            "stability_status": stability_status,
            "loading_conditions": loading_results,
            "froude_number": round(froude, 6),
        },
        "warnings": list(set(warnings)),
        "assumptions": [f"Block coefficient Cb={request.block_coefficient}"],
        "connector_status": "NOT_GENERATED",
    }


async def record_hull_run(task_id: str, request: HullDesignRequest, result: dict) -> str:
    """Record hull preview as a calculation run in the evidence engine."""
    import uuid

    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    result_json = json.dumps(result)
    inputs_json = json.dumps(request.model_dump(), sort_keys=True)

    async with get_db() as db:
        await db.execute(
            """INSERT INTO calculation_runs
               (id, task_id, formula_id, inputs_json, result_json, status, trace_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, task_id, "hull_preview", inputs_json, result_json, "UNVERIFIED",
             json.dumps({"preview": True}), now),
        )
        await db.commit()

    return run_id
