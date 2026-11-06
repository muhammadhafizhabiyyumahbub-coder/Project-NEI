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
    free_surface_moment: Optional[float] = Field(default=None, ge=0)
    fluid_density: float = Field(default=1025.0, gt=0)

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
        weight_groups = condition.get("weight_groups", [])
        if weight_groups:
            if any(float(w.get("mass_kg", 0)) <= 0 or float(w.get("kg_m", 0)) < 0 for w in weight_groups):
                raise ValueError("Weight groups require positive mass_kg and non-negative kg_m")
            total_weight = sum(float(w["mass_kg"]) for w in weight_groups)
            condition_kg = sum(float(w["mass_kg"]) * float(w["kg_m"]) for w in weight_groups) / total_weight
        condition_km = condition.get("km", request.km)
        condition_fsm = condition.get("free_surface_moment", request.free_surface_moment or 0.0)
        condition_density = condition.get("fluid_density", request.fluid_density)
        displacement_mass = volume * condition_density
        total_weight = sum(float(w.get("mass_kg", 0)) for w in weight_groups)
        mass_status = "failed" if total_weight > displacement_mass else "passed" if weight_groups else "not_verified"
        condition_gm = condition_km - condition_kg - condition_fsm / displacement_mass if condition_kg is not None and condition_km is not None else None
        loading_results.append({
            "id": condition_id,
            "gm_m": round(condition_gm, 6) if condition_gm is not None else None,
            "free_surface_moment": condition_fsm,
            "fluid_density": condition_density,
            "displacement_mass_kg": round(displacement_mass, 6),
            "weight_groups": weight_groups,
            "total_weight_kg": round(total_weight, 6),
            "mass_status": mass_status,
            "status": "failed" if mass_status == "failed" else "not_verified" if condition_gm is None else "stable" if condition_gm > 0 else "unstable" if condition_gm < 0 else "neutral",
        })
    froude = (request.speed * 0.514444) / math.sqrt(9.80665 * request.loa) if request.speed else 0.0
    
    from nei.engineering.geometry.hull_sections import generate_sections, section_manifest, section_volume
    sections = generate_sections(request.loa, request.beam, request.draft)
    geometry_volume = section_volume(sections, request.draft)
    volume_delta = geometry_volume - volume
    volume_delta_ratio = abs(volume_delta) / volume if volume else 0.0
    volume_consistency = "passed" if volume_delta_ratio <= 0.05 else "failed"
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
            "section_geometry_volume_m3": round(geometry_volume, 6),
            "section_volume_delta_m3": round(volume_delta, 6),
            "section_volume_delta_ratio": round(volume_delta_ratio, 6),
            "volume_consistency": volume_consistency,
            "waterplane_area_m2": round(waterplane_area, 6),
            "center_of_buoyancy_z_m": round(kb, 6),
            "metacentric_height_m": round(gm, 6) if gm is not None else None,
            "stability_status": stability_status,
            "loading_conditions": loading_results,
            "froude_number": round(froude, 6),
        },
        "sections": section_manifest(sections),
        "warnings": list(set(warnings)),
        "assumptions": ["Section geometry is deterministic preview only", f"Block coefficient Cb={request.block_coefficient}"],
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
