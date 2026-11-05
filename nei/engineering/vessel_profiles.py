"""Vessel profiles with geometry ratios, speed ranges, and reference cases."""
from pydantic import BaseModel, Field
from typing import Callable


WARNING_EVALUATORS: dict[str, Callable[[float, float, float, float], bool]] = {
    "speed > 25": lambda L, B, speed, draft_ratio: speed > 25,
    "speed > 20": lambda L, B, speed, draft_ratio: speed > 20,
    "speed > 12": lambda L, B, speed, draft_ratio: speed > 12,
    "speed > 40": lambda L, B, speed, draft_ratio: speed > 40,
    "speed < 12": lambda L, B, speed, draft_ratio: speed < 12,
    "L/B < 4": lambda L, B, speed, draft_ratio: B > 0 and L / B < 4,
    "L/B < 3.5": lambda L, B, speed, draft_ratio: B > 0 and L / B < 3.5,
    "L/B < 5": lambda L, B, speed, draft_ratio: B > 0 and L / B < 5,
    "L/B > 6": lambda L, B, speed, draft_ratio: B > 0 and L / B > 6,
    "draft_ratio > 0.5": lambda L, B, speed, draft_ratio: draft_ratio > 0.5,
    "draft_ratio < 0.4": lambda L, B, speed, draft_ratio: draft_ratio < 0.4,
}


class VesselProfile(BaseModel):
    vessel_type: str
    description: str
    loa_min: float = Field(gt=0)
    loa_max: float = Field(gt=0)
    beam_min: float = Field(gt=0)
    beam_max: float = Field(gt=0)
    depth_min: float = Field(gt=0)
    depth_max: float = Field(gt=0)
    draft_ratio_min: float = Field(gt=0, le=1)
    draft_ratio_max: float = Field(gt=0, le=1)
    speed_min_kn: float = Field(ge=0)
    speed_max_kn: float = Field(ge=0)
    block_coefficient_default: float = Field(gt=0, le=1)
    hull_family: str
    applicable_formulas: list[str]
    warning_rules: list[dict]


VESSEL_PROFILES: dict[str, VesselProfile] = {
    "patrol_boat": VesselProfile(
        vessel_type="Patrol Boat",
        description="Coastal patrol vessel for security and surveillance",
        loa_min=20, loa_max=50,
        beam_min=4, beam_max=9,
        depth_min=2, depth_max=4,
        draft_ratio_min=0.35, draft_ratio_max=0.50,
        speed_min_kn=15, speed_max_kn=30,
        block_coefficient_default=0.48,
        hull_family="displacement",
        applicable_formulas=["displacement_volume", "hydrostatic_pressure"],
        warning_rules=[
            {"condition": "speed > 25", "message": "High speed patrol; confirm hull form and power"},
            {"condition": "L/B < 4", "message": "Low length-beam ratio may affect seakeeping"},
        ],
    ),
    "tugboat": VesselProfile(
        vessel_type="Tugboat",
        description="Harbor tug for docking and maneuvering assistance",
        loa_min=15, loa_max=40,
        beam_min=5, beam_max=10,
        depth_min=3, depth_max=5,
        draft_ratio_min=0.45, draft_ratio_max=0.55,
        speed_min_kn=5, speed_max_kn=13,
        block_coefficient_default=0.78,
        hull_family="barge",
        applicable_formulas=["displacement_volume", "metacentric_height"],
        warning_rules=[
            {"condition": "speed > 12", "message": "High speed tug; verify bollard pull and stability"},
            {"condition": "draft_ratio > 0.5", "message": "Deep draft; check berth depth"},
        ],
    ),
    "ferry": VesselProfile(
        vessel_type="Ferry",
        description="Passenger or vehicle ferry for short to medium routes",
        loa_min=30, loa_max=100,
        beam_min=8, beam_max=20,
        depth_min=4, depth_max=8,
        draft_ratio_min=0.40, draft_ratio_max=0.55,
        speed_min_kn=10, speed_max_kn=25,
        block_coefficient_default=0.55,
        hull_family="planing_or_displacement",
        applicable_formulas=["displacement_volume", "initial_stability", "hydrostatic_pressure"],
        warning_rules=[
            {"condition": "speed > 20", "message": "High-speed ferry; confirm planing hull form"},
            {"condition": "L/B < 3.5", "message": "Wide ferry; check roll period and stability"},
        ],
    ),
    "fishing_vessel": VesselProfile(
        vessel_type="Fishing Vessel",
        description="Working vessel for commercial fishing operations",
        loa_min=15, loa_max=60,
        beam_min=4, beam_max=12,
        depth_min=3, depth_max=6,
        draft_ratio_min=0.40, draft_ratio_max=0.55,
        speed_min_kn=5, speed_max_kn=15,
        block_coefficient_default=0.60,
        hull_family="trawler_or_longliner",
        applicable_formulas=["displacement_volume", "hydrostatic_pressure"],
        warning_rules=[
            {"condition": "L/B > 6", "message": "Long slender hull; check fishing gear interference"},
            {"condition": "draft_ratio < 0.4", "message": "Shallow draft; check stability with load"},
        ],
    ),
    "general_cargo": VesselProfile(
        vessel_type="General Cargo",
        description="Multi-purpose cargo vessel for container and bulk goods",
        loa_min=80, loa_max=150,
        beam_min=12, beam_max=24,
        depth_min=7, depth_max=12,
        draft_ratio_min=0.45, draft_ratio_max=0.60,
        speed_min_kn=12, speed_max_kn=18,
        block_coefficient_default=0.65,
        hull_family="general_cargo",
        applicable_formulas=["displacement_volume", "metacentric_height", "hydrostatic_pressure"],
        warning_rules=[
            {"condition": "speed < 12", "message": "Slow cargo; verify fuel efficiency"},
            {"condition": "L/B < 5", "message": "Short hull; check turning circle and cargo layout"},
        ],
    ),
}


def get_vessel_profile(vessel_type: str) -> VesselProfile | None:
    """Return vessel profile or None if not found."""
    return VESSEL_PROFILES.get(vessel_type)


def validate_hull_against_profile(hull_data: dict, vessel_type: str) -> list[str]:
    """Validate hull dimensions against vessel profile. Return list of warnings/errors."""
    profile = get_vessel_profile(vessel_type)
    if not profile:
        return [f"Unknown vessel type: {vessel_type}"]

    warnings = []
    loa = hull_data.get("loa", 0)
    beam = hull_data.get("beam", 0)
    depth = hull_data.get("depth", 0)
    draft = hull_data.get("draft", 0)
    speed = hull_data.get("speed", 0)

    if not (profile.loa_min <= loa <= profile.loa_max):
        warnings.append(f"LOA {loa}m outside range [{profile.loa_min}, {profile.loa_max}]")
    if not (profile.beam_min <= beam <= profile.beam_max):
        warnings.append(f"Beam {beam}m outside range [{profile.beam_min}, {profile.beam_max}]")
    if not (profile.depth_min <= depth <= profile.depth_max):
        warnings.append(f"Depth {depth}m outside range [{profile.depth_min}, {profile.depth_max}]")

    draft_ratio = draft / depth if depth > 0 else 0
    if not (profile.draft_ratio_min <= draft_ratio <= profile.draft_ratio_max):
        warnings.append(f"Draft ratio {draft_ratio:.2f} outside range [{profile.draft_ratio_min}, {profile.draft_ratio_max}]")

    if not (profile.speed_min_kn <= speed <= profile.speed_max_kn):
        warnings.append(f"Speed {speed}kn outside range [{profile.speed_min_kn}, {profile.speed_max_kn}]")

    for rule in profile.warning_rules:
        evaluator = WARNING_EVALUATORS.get(rule["condition"])
        if evaluator and evaluator(loa, beam, speed, draft_ratio):
            warnings.append(rule["message"])

    return warnings


def get_default_block_coefficient(vessel_type: str) -> float:
    """Return default block coefficient for vessel type."""
    profile = get_vessel_profile(vessel_type)
    return profile.block_coefficient_default if profile else 0.65


def get_applicable_formulas(vessel_type: str) -> list[str]:
    """Return list of formula names applicable to vessel type."""
    profile = get_vessel_profile(vessel_type)
    return profile.applicable_formulas if profile else []
