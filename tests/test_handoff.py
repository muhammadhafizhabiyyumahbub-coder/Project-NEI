import json
from pathlib import Path
from nei.engineering.handoff import (
    HandoffHop, save_handoff_file, validate_transfer,
    write_provenance_manifest, handoff_dir, ProvenanceManifest,
    validate_handoff_chain,
)


def test_save_handoff_file_writes_and_records_sha(tmp_path):
    project_root = str(tmp_path)
    project_id = "p1"
    hop = save_handoff_file(
        project_root, project_id,
        source_bytes=b"STEP_DATA",
        filename="box_from_rhino.step",
        software="rhino6", software_version="6.18",
        unit="mm", file_format="STEP",
    )
    target = handoff_dir(project_root, project_id) / "box_from_rhino.step"
    assert target.exists()
    assert hop.file_sha256
    assert hop.software == "rhino6"


def test_validate_transfer_passes_within_tolerance():
    result = validate_transfer(
        source_bbox=(0.01, 0.003, 0.001),
        target_bbox=(0.0101, 0.0031, 0.0011),
        tolerance=0.005,
    )
    assert result["passed"] is True
    assert result["max_diff_m"] < 0.005


def test_validate_transfer_rejects_invalid_input():
    import pytest
    with pytest.raises(ValueError):
        validate_transfer((1, 2), (1, 2, 3))
    with pytest.raises(ValueError):
        validate_transfer((1, 2, 3), (1, 2, 3), tolerance=-1)


def test_validate_transfer_fails_beyond_tolerance():
    result = validate_transfer(
        source_bbox=(0.01, 0.003, 0.001),
        target_bbox=(0.05, 0.003, 0.001),
        tolerance=0.005,
    )
    assert result["passed"] is False


def test_validate_handoff_chain_requires_one_unit_and_hash():
    valid = HandoffHop("rhino6", "6.18", "export", "x.step", "abc", "STEP", "m")
    assert validate_handoff_chain([valid])["hop_count"] == 1
    import pytest
    with pytest.raises(ValueError, match="mixed units"):
        validate_handoff_chain([valid, HandoffHop("maxsurf20", "20", "import", "y.msd", "def", "MSD", "mm")])
    with pytest.raises(ValueError, match="at least one"):
        validate_handoff_chain([])
    with pytest.raises(ValueError, match="unsupported operation"):
        validate_handoff_chain([HandoffHop("rhino6", "6.18", "delete", "x.step", "abc", "STEP", "m")])


def test_write_provenance_manifest_rejects_invalid_chain(tmp_path):
    import pytest
    first = HandoffHop("rhino6", "6.18", "export", "x.step", "abc", "STEP", "m")
    second = HandoffHop("maxsurf20", "20", "import", "y.msd", "def", "MSD", "mm")
    with pytest.raises(ValueError, match="mixed units"):
        write_provenance_manifest(str(tmp_path), "p1", "task1", [first, second])


def test_write_provenance_manifest(tmp_path):
    project_root = str(tmp_path)
    project_id = "p1"
    hop = HandoffHop(
        software="rhino6", software_version="6.18", operation="export",
        file_path="x.step", file_sha256="abc", file_format="STEP", unit="mm",
    )
    manifest = write_provenance_manifest(project_root, project_id, "task1", [hop])
    out_file = handoff_dir(project_root, project_id) / "task1_provenance.json"
    assert out_file.exists()
    loaded = ProvenanceManifest.from_json(out_file.read_text())
    assert loaded.task_id == "task1"
    assert len(loaded.chain) == 1
