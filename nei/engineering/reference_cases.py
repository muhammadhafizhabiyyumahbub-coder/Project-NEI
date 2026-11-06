"""Independent reference inputs for built-in deterministic formulas."""

REFERENCE_CASES: dict[str, dict] = {
    "box_volume": {
        "inputs": {"length": 10.0, "width": 3.0, "height": 1.0},
        "expected": 30.0,
    },
    "box_surface_area": {
        "inputs": {"length": 10.0, "width": 3.0, "height": 1.0},
        "expected": 86.0,
    },
    "displacement_volume": {
        "inputs": {"loa": 10.0, "beam": 3.0, "draft": 1.0},
        "expected": 30.0,
    },
    "metacentric_height": {
        "inputs": {"km": 5.0, "kg": 3.0},
        "expected": 2.0,
    },
    "initial_stability": {
        "inputs": {"gm": 2.0},
        "expected": "STABLE",
    },
    "hydrostatic_pressure": {
        "inputs": {"density": 1025.0, "g": 9.81, "depth": 10.0},
        "expected": 100552.5,
    },
}
