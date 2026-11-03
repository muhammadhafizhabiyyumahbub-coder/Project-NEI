"""Geometry verification: bounding box, object count, unit checks.

Alpha 0.1: bounding box tolerance check only.
"""
from typing import Any
from nei.verification.record import VerificationCheck


def check_bounding_box(
    expected: dict,
    actual: dict,
    tolerance: float = 0.001,
) -> VerificationCheck:
    """Compare expected vs actual bounding box dimensions.

    expected: {"length": L, "width": W, "height": H}
    actual: {"length": L, "width": W, "height": H} from Rhino inspect_object
    tolerance: absolute difference allowed per axis (default 0.001 units)
    """
    from nei.verification.record import VerificationCheck
    from datetime import datetime, timezone

    def _within(a: float, b: float, tol: float) -> bool:
        return abs(a - b) <= tol

    dims = ["length", "width", "height"]
    results = {d: _within(expected.get(d, 0), actual.get(d, 0), tolerance) for d in dims}
    all_passed = all(results.values())

    return VerificationCheck(
        target="bounding_box",
        expected=expected,
        actual=actual,
        tolerance=tolerance,
        method="geometric_inspection",
        result="PASSED" if all_passed else "FAILED",
        evidence=f"axis_results={results}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def check_object_count(expected: int, actual: int) -> VerificationCheck:
    """Verify exact object count match."""
    from datetime import datetime, timezone

    return VerificationCheck(
        target="object_count",
        expected={"count": expected},
        actual={"count": actual},
        tolerance=None,
        method="list_objects_diff",
        result="PASSED" if expected == actual else "FAILED",
        evidence=f"expected={expected}, actual={actual}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def check_object_type(expected: str, actual: str) -> VerificationCheck:
    """Verify object type string match (case-insensitive)."""
    from datetime import datetime, timezone

    match = expected.lower() == actual.lower()
    return VerificationCheck(
        target="object_type",
        expected={"type": expected},
        actual={"type": actual},
        tolerance=None,
        method="inspect_object",
        result="PASSED" if match else "FAILED",
        evidence=f"expected={expected}, actual={actual}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def check_document_units(expected: str, actual: str) -> VerificationCheck:
    """Verify document units match (case-insensitive)."""
    from datetime import datetime, timezone

    match = expected.lower() == actual.lower()
    return VerificationCheck(
        target="document_units",
        expected={"units": expected},
        actual={"units": actual},
        tolerance=None,
        method="get_document_info",
        result="PASSED" if match else "FAILED",
        evidence=f"expected={expected}, actual={actual}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
