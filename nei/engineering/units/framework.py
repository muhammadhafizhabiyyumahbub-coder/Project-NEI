"""Unit framework using Pint.

All engineering calculations use canonical SI internally.
Unit mismatches are rejected at input, not silently converted.
"""
import re
from typing import Optional

# Unit registry — single source of truth for canonical SI base units.
# Using a minimal built-in set to avoid a Pint dependency unless already installed.

try:
    import pint
    UNIT_REGISTRY = pint.UnitRegistry()
    HAS_PINT = True
except ImportError:
    UNIT_REGISTRY = None
    HAS_PINT = False


# ── Built-in unit handling (no external dependency) ─────────────────────────

# Canonical units for common engineering quantities
CANONICAL_UNITS = {
    "length": "m",
    "area": "m^2",
    "volume": "m^3",
    "mass": "kg",
    "force": "N",
    "pressure": "Pa",
    "density": "kg/m^3",
}

# Numeric regex for parsing "value unit" pairs
_UNIT_RE = re.compile(r"^(\d+\.?\d*)\s*(\S+)$")

# Common unit multipliers to SI
UNIT_TO_M = {
    "mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0,
    "in": 0.0254, "ft": 0.3048,
}
UNIT_TO_KG = {"kg": 1.0, "ton": 1000.0, "tonne": 1000.0}
UNIT_TO_M3 = {"m^3": 1.0, "mm^3": 1e-9, "cm^3": 1e-6}
UNIT_TO_PA = {"Pa": 1.0, "kPa": 1e3, "MPa": 1e6, "bar": 1e5}
UNIT_TO_KGM3 = {"kg/m^3": 1.0, "kg/m²^3": 1.0, "kg/m^2^3": 1.0, "kg/m³": 1.0}
UNIT_TO_MS2 = {"m/s^2": 1.0, "m/s²": 1.0}


def parse_quantity(value: str, target_unit: str = "m") -> float:
    """Parse '10 mm' → 0.010 m (SI).

    Raises ValueError on unknown unit or malformed input.
    """
    m = _UNIT_RE.match(value.strip())
    if not m:
        raise ValueError(f"Cannot parse quantity: {value!r}")
    num = float(m.group(1))
    unit = m.group(2)

    if target_unit == "m":
        if unit not in UNIT_TO_M:
            raise ValueError(f"Unknown length unit: {unit!r}")
        return num * UNIT_TO_M[unit]

    if target_unit == "m^3":
        if unit not in UNIT_TO_M3:
            raise ValueError(f"Unknown volume unit: {unit!r}")
        return num * UNIT_TO_M3[unit]

    if target_unit == "Pa":
        if unit not in UNIT_TO_PA:
            raise ValueError(f"Unknown pressure unit: {unit!r}")
        return num * UNIT_TO_PA[unit]

    if target_unit in {"kg/m^3", "kg/m³"}:
        if unit not in UNIT_TO_KGM3:
            raise ValueError(f"Unknown density unit: {unit!r}")
        return num * UNIT_TO_KGM3[unit]

    if target_unit in {"m/s^2", "m/s²"}:
        if unit not in UNIT_TO_MS2:
            raise ValueError(f"Unknown acceleration unit: {unit!r}")
        return num * UNIT_TO_MS2[unit]

    raise ValueError(f"Unsupported target unit: {target_unit}")


def is_valid_unit(value: str, target_unit: str = "m") -> bool:
    """Check if a quantity string is parseable for the target unit."""
    try:
        parse_quantity(value, target_unit)
        return True
    except ValueError:
        return False


def canonical_unit_for(quantity: str) -> str:
    """Return the canonical SI unit string for a quantity name."""
    return CANONICAL_UNITS.get(quantity, quantity)
