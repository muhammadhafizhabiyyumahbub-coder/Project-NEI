"""Postcondition definitions for Alpha 0.1.

Each PostCondition declares what must be true after connector execution.
VerificationEngine runs these checks against the actual software result.
"""
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class PostCondition:
    """Base postcondition check."""
    target: str
    expected: dict
    tolerance: Optional[float] = None
    method: str = "unspecified"


@dataclass
class BoundingBoxCheck(PostCondition):
    """Check bounding box dimensions of a created object."""
    def __init__(self, length: float, width: float, height: float, tolerance: float = 0.001):
        super().__init__(
            target="bounding_box",
            expected={"length": length, "width": width, "height": height},
            tolerance=tolerance,
            method="geometric_inspection",
        )


@dataclass
class ObjectCountCheck(PostCondition):
    """Check that exactly N new objects were created."""
    def __init__(self, count: int):
        super().__init__(
            target="object_count",
            expected={"count": count},
            tolerance=None,
            method="list_objects_diff",
        )


@dataclass
class ObjectTypeCheck(PostCondition):
    """Check object type (e.g., Brep, Curve, Surface)."""
    def __init__(self, object_type: str):
        super().__init__(
            target="object_type",
            expected={"type": object_type},
            tolerance=None,
            method="inspect_object",
        )


@dataclass
class DocumentUnitsCheck(PostCondition):
    """Check document units match requested."""
    def __init__(self, units: str):
        super().__init__(
            target="document_units",
            expected={"units": units},
            tolerance=None,
            method="get_document_info",
        )


@dataclass
class ArtifactSavedCheck(PostCondition):
    """Check artifact file exists at expected path with valid SHA-256."""
    def __init__(self, filename: str, expected_sha256: Optional[str] = None):
        super().__init__(
            target="artifact_saved",
            expected={"filename": filename, "sha256": expected_sha256},
            tolerance=None,
            method="filesystem_sha256",
        )


def rhino_box_postconditions(length: float, width: float, height: float) -> list[PostCondition]:
    """Standard checks for Rhino create_box_test."""
    return [
        ObjectCountCheck(count=1),
        ObjectTypeCheck(object_type="Brep"),
        BoundingBoxCheck(length=length, width=width, height=height, tolerance=0.001),
        DocumentUnitsCheck(units="Millimeters"),
    ]


def rhino_export_copy_postconditions(filename: str, expected_sha256: Optional[str] = None) -> list[PostCondition]:
    """Postconditions for Rhino export_copy: artifact exists with optional known SHA-256."""
    return [
        ArtifactSavedCheck(filename=filename, expected_sha256=expected_sha256),
    ]
