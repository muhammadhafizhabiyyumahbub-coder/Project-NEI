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
        DocumentUnitsCheck(units="millimeter"),
    ]


def hull_preview_postconditions(vessel_type: str, loa: float, beam: float,
                                 depth: float, draft: float, speed: float,
                                 block_coefficient: float) -> list[PostCondition]:
    """Postconditions for hull preview: deterministic calculation checks.

    These verify the recorded calculation, not a CAD model.
    """
    return [
        BoundingBoxCheck(length=loa, width=beam, height=depth, tolerance=0.001),
        BoundingBoxCheck(length=draft, width=beam, height=depth, tolerance=0.001),
    ]



def rhino_export_copy_postconditions(filename: str, expected_sha256: Optional[str] = None) -> list[PostCondition]:
    """Postconditions for Rhino export_copy: artifact exists with optional known SHA-256."""
    return [
        ArtifactSavedCheck(filename=filename, expected_sha256=expected_sha256),
    ]


@dataclass
class DimensionsCheck(PostCondition):
    """Check hull dimensions (length, beam, depth, draft) match expected."""
    def __init__(self, loa: float, beam: float, depth: float, draft: float):
        super().__init__(
            target="dimensions",
            expected={"loa": loa, "beam": beam, "depth": depth, "draft": draft},
            tolerance=0.001,
            method="hull_spec_validation",
        )


@dataclass
class VolumeCheck(PostCondition):
    """Check displacement/volume estimate matches expected."""
    def __init__(self, expected_volume: float):
        super().__init__(
            target="volume",
            expected={"volume": expected_volume},
            tolerance=0.01,
            method="displacement_estimate",
        )


@dataclass
class StabilityCheck(PostCondition):
    """Check basic stability criteria: beam > draft, positive moment arm."""
    def __init__(self, beam: float, draft: float):
        super().__init__(
            target="stability",
            expected={"beam": beam, "draft": draft},
            tolerance=0.001,
            method="min_beam_over_draft",
        )


@dataclass
class WatertightCheck(PostCondition):
    """Check artifact file type/format validity for watertightness requirement."""
    def __init__(self, ext: str):
        super().__init__(
            target="watertight",
            expected={"ext": ext},
            tolerance=None,
            method="file_extension_validity",
        )
