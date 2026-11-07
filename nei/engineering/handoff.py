"""Cross-software artifact handoff protocol.

Phase 8: move a test artifact between two supported CAD applications and
verify geometry/units survive the transfer. All writes go under
data/projects/<id>/artifacts/handoff/ — original source files are never
touched.

Design constraint (from environment.json / PLAN.md Phase 0):
8GB RAM machine → handoff steps run SEQUENTIALLY, one CAD app at a time.
"""
import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from nei.core.policy import validate_sandbox_path

HANDOFF_DIR_NAME = "handoff"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class HandoffHop:
    """One step in the provenance chain: source software → file → target."""
    software: str            # e.g. "rhino6", "solidworks2022", "maxsurf20"
    software_version: str    # e.g. "30.1.0"
    operation: str          # "export" | "import" | "verify"
    file_path: str
    file_sha256: str
    file_format: str        # "STEP", "STL", "3DM", "MSD"
    unit: str               # canonical SI, e.g. "m" or "mm"
    timestamp: str = field(default_factory=_now)
    notes: Optional[str] = None


@dataclass
class ProvenanceManifest:
    task_id: str
    project_id: str
    chain: list[HandoffHop]
    created_at: str = field(default_factory=_now)
    schema_version: int = 1

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, raw: str) -> "ProvenanceManifest":
        d = json.loads(raw)
        chain = [HandoffHop(**h) for h in d.pop("chain", [])]
        return cls(chain=chain, **d)


def handoff_dir(project_root: str, project_id: str) -> Path:
    d = Path(project_root) / project_id / "artifacts" / HANDOFF_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_handoff_file(
    project_root: str,
    project_id: str,
    source_bytes: bytes,
    filename: str,
    software: str,
    software_version: str,
    unit: str,
    file_format: str = "STEP",
) -> HandoffHop:
    """Write a handoff artifact and record it as the first hop in the chain.

    Guards:
    - filename must be a simple basename (no path separators)
    - resolved target must stay inside the project sandbox
    """
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ValueError(f"Invalid handoff filename: {filename!r}")
    target = handoff_dir(project_root, project_id) / filename
    if not validate_sandbox_path(str(target), str(Path(project_root) / project_id)):
        raise ValueError(f"Handoff target outside sandbox: {target}")
    target.write_bytes(source_bytes)

    return HandoffHop(
        software=software,
        software_version=software_version,
        operation="export",
        file_path=str(target),
        file_sha256=_sha256(source_bytes),
        file_format=file_format,
        unit=unit,
        notes=f"Exported by {software} {software_version}",
    )


def validate_handoff_artifact(hop: HandoffHop, project_root: str, project_id: str) -> Path:
    """Validate recorded artifact path and content before downstream use."""
    path = Path(hop.file_path).resolve()
    sandbox = (Path(project_root) / project_id).resolve()
    if not validate_sandbox_path(str(path), str(sandbox)):
        raise ValueError(f"Handoff artifact outside sandbox: {path}")
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Handoff artifact missing or empty: {path}")
    if _sha256(path.read_bytes()) != hop.file_sha256:
        raise ValueError(f"Handoff artifact hash mismatch: {path}")
    return path


def validate_transfer(
    source_bbox: tuple[float, float, float],
    target_bbox: tuple[float, float, float],
    tolerance: float = 0.005,  # 0.5% in meters
) -> dict:
    """Check that bounding box dimensions survive a software transfer.

    Both bboxes must be in the same unit (canonical SI, meters).
    Returns a structured result; caller decides NEEDS_REVIEW vs COMPLETED.
    """
    if len(source_bbox) != 3 or len(target_bbox) != 3:
        raise ValueError("Bounding boxes must contain exactly three dimensions")
    if tolerance < 0:
        raise ValueError("Transfer tolerance must be non-negative")
    if any(value < 0 for value in (*source_bbox, *target_bbox)):
        raise ValueError("Bounding box dimensions must be non-negative")
    diffs = [abs(a - b) for a, b in zip(source_bbox, target_bbox)]
    ok = all(d <= tolerance for d in diffs)
    return {
        "passed": ok,
        "max_diff_m": max(diffs),
        "tolerance_m": tolerance,
        "deltas_m": diffs,
    }


def validate_handoff_chain(chain: list[HandoffHop]) -> dict:
    """Validate ordered handoff metadata before downstream transfer."""
    if not chain:
        raise ValueError("Handoff chain must contain at least one hop")
    units = {hop.unit for hop in chain}
    if len(units) != 1:
        raise ValueError("Handoff chain contains mixed units")
    if any(not hop.file_sha256 or not hop.file_format for hop in chain):
        raise ValueError("Every handoff hop needs file hash and format")
    allowed_operations = {"export", "import", "verify"}
    if any(hop.operation not in allowed_operations for hop in chain):
        raise ValueError("Handoff hop has unsupported operation")
    if any(not hop.software or not hop.software_version or not hop.file_path for hop in chain):
        raise ValueError("Every handoff hop needs software, version, and path")
    return {
        "valid": True,
        "hop_count": len(chain),
        "unit": chain[0].unit,
        "software": [hop.software for hop in chain],
    }


def write_provenance_manifest(
    project_root: str,
    project_id: str,
    task_id: str,
    chain: list[HandoffHop],
) -> ProvenanceManifest:
    """Persist the full handoff chain as a JSON manifest file."""
    validate_handoff_chain(chain)
    manifest = ProvenanceManifest(task_id=task_id, project_id=project_id, chain=chain)
    target = handoff_dir(project_root, project_id) / f"{task_id}_provenance.json"
    if not validate_sandbox_path(str(target), str(Path(project_root) / project_id)):
        raise ValueError(f"Manifest path outside sandbox: {target}")
    target.write_text(manifest.to_json(), encoding="utf-8")
    return manifest
