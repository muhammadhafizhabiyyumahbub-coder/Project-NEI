"""Phase 8 orchestration safety tests that do not require live CAD software."""
import hashlib

import pytest

from nei.connectors.base import CapabilityStatus
from nei.connectors.rhino6.connector import Rhino6Connector
from nei.core.resource_manager import ResourceManager
from nei.engineering.handoff import (
    HandoffHop,
    save_handoff_file,
    validate_handoff_artifact,
)


def test_rhino_capability_and_parameter_validation():
    connector = Rhino6Connector(rhino_exe="missing-rhino.exe")
    capabilities = {item.name: item.status for item in connector.get_capabilities()}

    assert capabilities["rhino.create_box_test"] == CapabilityStatus.SUPPORTED
    assert connector.validate_parameters(
        "rhino.create_box_test", {"length": 10, "width": 3, "height": 1}
    ) is None
    assert connector.validate_parameters(
        "rhino.create_box_test", {"length": 0, "width": 3, "height": 1}
    ) == "length must be a positive number"


def test_handoff_rejects_hash_mismatch(tmp_path):
    hop = save_handoff_file(
        str(tmp_path), "project", b"source", "model.step", "rhino6", "6", "mm"
    )
    path = tmp_path / "project" / "artifacts" / "handoff" / "model.step"
    path.write_bytes(b"tampered")

    with pytest.raises(ValueError, match="hash mismatch"):
        validate_handoff_artifact(hop, str(tmp_path), "project")


def test_handoff_rejects_outside_sandbox(tmp_path):
    outside = tmp_path / "outside.step"
    outside.write_bytes(b"source")
    hop = HandoffHop(
        software="rhino6", software_version="6", operation="export",
        file_path=str(outside), file_sha256=hashlib.sha256(b"source").hexdigest(),
        file_format="STEP", unit="mm",
    )

    with pytest.raises(ValueError, match="outside sandbox"):
        validate_handoff_artifact(hop, str(tmp_path), "project")


def test_lock_releases_and_allows_next_task():
    manager = ResourceManager()
    assert manager.acquire("rhino6", "task-1", timeout_s=0.01)
    assert manager.holder("rhino6") == "task-1"
    manager.release("rhino6", "task-1")
    assert manager.holder("rhino6") is None
    assert manager.acquire("rhino6", "task-2", timeout_s=0.01)
    manager.release("rhino6", "task-2")
