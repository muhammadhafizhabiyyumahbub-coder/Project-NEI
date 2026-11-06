import asyncio
import hashlib
import json
from pathlib import Path
from nei.core.database import DB_PATH, init_db
from nei.connectors.evidence import record_connector_evidence
from nei.connectors.maxsurf20 import Maxsurf20Connector


def test_generated_hull_evidence_has_source_output_checksums(tmp_path):
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    source = tmp_path / "source.msd"
    output = tmp_path / "generated-hull.msd"
    source.write_bytes(b"source hull")
    output.write_bytes(b"generated hull")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    output_sha = hashlib.sha256(output.read_bytes()).hexdigest()

    evidence_id = asyncio.run(record_connector_evidence(
        "maxsurf20", "maxsurf.hull_generation_manual", "manual_artifact_generation",
        artifact_path=str(output), artifact_sha256=output_sha,
        metadata={"source_path": str(source), "source_sha256": source_sha,
                  "output_sha256": output_sha, "source_unchanged": True,
                  "output_differs_from_source": source_sha != output_sha,
                  "engineering_approval": "not_performed"},
    ))
    assert evidence_id
    assert source.read_bytes() == b"source hull"
    assert output_sha != source_sha


def test_verify_generated_hull_is_read_only(tmp_path):
    source = tmp_path / "source.msd"
    output = tmp_path / "generated-hull.msd"
    source.write_bytes(b"source hull")
    output.write_bytes(b"generated hull")
    before = output.read_bytes()
    result = Maxsurf20Connector().execute(
        "maxsurf.verify_generated_hull",
        {"source": str(source), "output": str(output)},
        timeout_s=5,
    )
    assert result.success
    assert result.data["output_differs_from_source"] is True
    assert result.data["read_only"] is True
    assert output.read_bytes() == before
    assert result.data["engineering_approval"] == "not_performed"
