import asyncio
import hashlib
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import init_db, DB_PATH, get_db
from nei.connectors.evidence import (
    record_rhino_hull_proxy_evidence,
    record_solidworks_inspection_evidence,
    record_maxsurf_probe_evidence,
    record_connector_evidence,
)

def setup_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    return TestClient(app)

def test_unknown_connector_evidence_returns_404():
    client = setup_db()
    response = client.get("/api/v1/connectors/not-registered/evidence")
    assert response.status_code == 404


def test_record_connector_evidence_rejects_unknown_connector():
    import pytest
    with pytest.raises(ValueError, match="Unknown connector"):
        asyncio.run(record_connector_evidence(
            "unknown-connector", "some.capability", "probe",
            artifact_sha256="abc"
        ))


def test_connector_probe_writes_probe_history():
    client = setup_db()
    r = client.post("/api/v1/connectors/rhino6/probe")
    assert r.status_code == 200

    rows = asyncio.run(_fetch_probe_rows("rhino6"))
    assert len(rows) >= 1
    probe_type, result_json, timestamp = rows[-1]
    assert probe_type == "detect"
    assert timestamp
    result = json.loads(result_json)
    assert "detected" in result
    assert "status" in result


async def _fetch_probe_rows(connector_id: str):
    async with get_db() as db:
        return await db.execute_fetchall(
            "SELECT probe_type, result_json, timestamp FROM connector_probes "
            "WHERE connector_id = ? ORDER BY timestamp ASC",
            (connector_id,),
        )


def test_connector_evidence_recording():
    client = setup_db()
    
    # 1. Rhino evidence
    rhino_id = asyncio.run(record_rhino_hull_proxy_evidence(
        artifact_path="data/projects/test/rhino_proxy.3dm",
        artifact_sha256="abc123rhino",
        dimensions={"length": 10.0, "beam": 2.0},
        object_type="Brep"
    ))
    assert rhino_id

    # 2. SW evidence
    sw_id = asyncio.run(record_solidworks_inspection_evidence(
        document_info={"name": "test.SLDPRT", "path": "C:\\test.SLDPRT"},
        features={"count": 5}
    ))
    assert sw_id

    # 3. Maxsurf evidence (mock file paths for test)
    tmp_file = Path("data/projects/test/maxsurf_tmp.msd")
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file.write_bytes(b"maxsurf test")
    sha = hashlib.sha256(tmp_file.read_bytes()).hexdigest()
    
    mx_id = asyncio.run(record_maxsurf_probe_evidence(
        source_path=str(tmp_file),
        source_sha256=sha,
        import_path=str(tmp_file),
        export_path=str(tmp_file)
    ))
    assert mx_id

    # 4. Verify via API
    r = client.get("/api/v1/connectors/rhino6/evidence")
    assert r.status_code == 200
    data = r.json()
    assert len(data["evidence"]) >= 1
    assert data["evidence"][0]["capability_name"] == "rhino.create_hull_proxy"
    assert data["evidence"][0]["artifact_sha256"] == "abc123rhino"

    r = client.get("/api/v1/connectors/solidworks2022/evidence")
    assert r.status_code == 200
    data = r.json()
    assert data["evidence"][0]["metadata"]["features"]["count"] == 5

    r = client.get("/api/v1/connectors/maxsurf20/evidence")
    assert r.status_code == 200
    data = r.json()
    assert data["evidence"][0]["metadata"]["source_sha256"] == sha

    # Clean up tmp file
    if tmp_file.exists():
        tmp_file.unlink()
