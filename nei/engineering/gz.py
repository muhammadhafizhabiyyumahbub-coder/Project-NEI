"""Phase 9 — GZ curve analysis and classification criteria baseline.

GZ curve generation and stability evaluation for the deterministic hull
preview. No CAD input; no solver. All outputs are UNVERIFIED preview data
unless a classification body reference case is attached and reviewed.

Safety:
- GZ curve points are computed from the metacentric height and beam only.
- No hydrostatic integration over the actual hull surface is performed.
- Trim, MCT, and full hydrostatic curves are out of scope.
"""
import math
from typing import Optional


class GZResult:
    def __init__(
        self,
        points: list[dict],
        gm_at_0_m: Optional[float],
        area_m0rad: Optional[float],
        min_angle_m: Optional[float],
        max_angle_m: Optional[float],
        status: str,
        limitations: list[str],
    ) -> None:
        self.points = points
        self.gm_at_0_m = gm_at_0_m
        self.area_m0rad = area_m0rad
        self.min_angle_m = min_angle_m
        self.max_angle_m = max_angle_m
        self.status = status
        self.limitations = limitations

    def to_dict(self) -> dict:
        return {
            "points": self.points,
            "gm_at_0_m": self.gm_at_0_m,
            "area_m0rad": self.area_m0rad,
            "min_angle_m": self.min_angle_m,
            "max_angle_m": self.max_angle_m,
            "status": self.status,
            "limitations": self.limitations,
            "not_for_approval": True,
        }


def _gm(angle_rad: float, gm_0: float, beam: float, draft: float) -> float:
    """Approximate GZ(theta) = gm_0 * sin(theta) + draft/2 * (1 - cos(theta)).

    This is a deterministic proxy, not a hydrostatic GZ curve. It captures
    the restoring-trend shape without integrating hull sections.
    """
    sin_t = math.sin(angle_rad)
    cos_t = math.cos(angle_rad)
    return gm_0 * sin_t + (draft / 2.0) * (1.0 - cos_t)


def generate_gz_curve(
    gm_0_m: float,
    beam_m: float,
    draft_m: float,
    *,
    min_angle_deg: float = 0.0,
    max_angle_deg: float = 90.0,
    step_deg: float = 1.0,
) -> GZResult:
    """Generate a proxy GZ curve and classify stability indicators.

    Returns UNVERIFIED by design; no approval path exists without a
    classification reference case attached to the formula record.
    """
    if gm_0_m is None:
        raise ValueError("gm_0_m required")
    if beam_m <= 0 or draft_m <= 0:
        raise ValueError("beam_m and draft_m must be positive")
    if min_angle_deg < 0 or max_angle_deg <= min_angle_deg:
        raise ValueError("invalid angle range")
    if step_deg <= 0:
        raise ValueError("step_deg must be positive")

    points = []
    area_m0rad = 0.0
    prev_t = None
    prev_gz = 0.0

    angle = min_angle_deg
    while angle <= max_angle_deg + 1e-9:
        t_rad = math.radians(angle)
        gz = _gm(t_rad, gm_0_m, beam_m, draft_m)
        if prev_t is not None:
            trapezoid_m0rad = 0.5 * (prev_gz + gz) * (t_rad - prev_t)
            area_m0rad += trapezoid_m0rad
        points.append({"angle_deg": round(angle, 6), "angle_rad": round(t_rad, 9), "gz_m": round(gz, 9)})
        prev_t = t_rad
        prev_gz = gz
        angle += step_deg

    # Stability indicators (proxy, UNVERIFIED)
    min_angle_m = min(p["angle_deg"] for p in points)
    max_angle_m = max(p["angle_deg"] for p in points)

    # Minimum GZ (can be negative if GM at 0 is negative and draft term not enough)
    gz_min_val = min(p["gz_m"] for p in points)
    status = "not_verified"
    if gz_min_val < 0:
        status = "unstable"
    elif gm_0_m > 0 and area_m0rad > 0:
        status = "stable"
    else:
        status = "neutral"

    limitations = [
        "GZ curve is a deterministic proxy; no hydrostatic integration performed",
        "No classification criteria evaluation; UNVERIFIED",
        "Trim, MCT, and full hydrostatic curves out of scope",
    ]

    return GZResult(
        points=points,
        gm_at_0_m=gm_0_m,
        area_m0rad=round(area_m0rad, 9),
        min_angle_m=round(min_angle_m, 6),
        max_angle_m=round(max_angle_m, 6),
        status=status,
        limitations=limitations,
    )


# ── Classification criteria baseline (UNVERIFIED, placeholder values) ──────

class ClassificationBaseline:
    """Baseline stability criteria for naval classification.

    All thresholds are UNVERIFIED placeholders; no class-approval value
    is asserted. Use as reference for comparison only.
    """
    MIN_GM_M: float = 0.0            # threshold GM in meters
    MIN_AREAS_M0RAD: list[float] = [0.05, 0.055, 0.09]  # approximate IMO Intact Stability thresholds
    MAX_KEEL_TO_KG_RATIO: float = 1.0 # KG must not exceed 1.0 * draft in most classes

    @classmethod
    def evaluate(cls, gm_m: Optional[float], area_m0rad: Optional[float],
                 keel_ratio: Optional[float]) -> dict:
        """Return a UNVERIFIED classification comparison report.

        Never claims compliance. Each criterion is shown with pass/fail
        against the placeholder threshold, and the overall status is
        UNVERIFIED.
        """
        results = {}
        results["gm_m"] = {
            "value": gm_m,
            "threshold": cls.MIN_GM_M,
            "pass": gm_m is not None and gm_m > cls.MIN_GM_M,
            "verified": False,
            "note": "Placeholder threshold; UNVERIFIED",
        }
        results["area_m0rad"] = {
            "value": area_m0rad,
            "thresholds": cls.MIN_AREAS_M0RAD,
            "pass": all(area_m0rad is not None and area_m0rad > t for t in cls.MIN_AREAS_M0RAD),
            "verified": False,
            "note": "Placeholder thresholds; UNVERIFIED",
        }
        results["keel_ratio"] = {
            "value": keel_ratio,
            "threshold": cls.MAX_KEEL_TO_KG_RATIO,
            "pass": keel_ratio is not None and keel_ratio <= cls.MAX_KEEL_TO_KG_RATIO,
            "verified": False,
            "note": "Placeholder threshold; UNVERIFIED",
        }
        return {
            "criteria": results,
            "status": "UNVERIFIED",
            "compliance_claimed": False,
            "limitations": [
                "All thresholds are UNVERIFIED placeholders",
                "No classification body approval is claimed",
                "This report is not a substitute for a classification society review",
            ],
        }
