"""Hydrostatics formulas — deterministic, SI canonical."""


def metacentric_height(km: float, kg: float) -> float:
    """GM = KM - KG (meters). Both inputs in SI (meters).

    Reference case: KM=2.5m, KG=2.0m → GM=0.5m
    """
    return km - kg


def initial_stability_indicator(gm: float) -> str:
    """Return 'STABLE' / 'NEUTRAL' / 'UNSTABLE' based on GM sign."""
    if gm > 0:
        return "STABLE"
    elif gm < 0:
        return "UNSTABLE"
    return "NEUTRAL"


def hydrostatic_pressure(density: float, g: float, depth: float) -> float:
    """P = rho * g * h (Pa). Inputs: SI kg/m^3, m/s^2, m."""
    return density * g * depth
