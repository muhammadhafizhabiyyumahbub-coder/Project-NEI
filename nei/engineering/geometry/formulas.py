"""Geometry formulas — deterministic, unit-safe, reference-case tested."""


def box_volume(length: float, width: float, height: float) -> float:
    """Volume of a rectangular box in m^3. Inputs must be SI (meters)."""
    return length * width * height


def box_surface_area(length: float, width: float, height: float) -> float:
    """Total surface area of a rectangular box in m^2."""
    return 2 * (length * width + width * height + length * height)


def displacement_volume(loa: float, beam: float, draft: float) -> float:
    """Approximate displacement volume for a rectangular hull block (m^3).

    Formula: V_block = L * B * T
    Reference case: L=10m, B=3m, T=1m → V=30 m^3
    """
    return loa * beam * draft
