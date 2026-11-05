import asyncio
import pytest
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import init_db, DB_PATH
from nei.connectors.evidence import (
    record_rhino_hull_proxy_evidence,
    record_solidworks_inspection_evidence,
    record_maxsurf_probe_evidence,
)

def setup_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    return TestClient(app)

def test_connector_evidence_recording():
    client = setup_db()
    
    # 1. Rhino evidence
    rhino_id = record_rhino_hull_proxy_evidence(
        artifact_path="data/projects/test/rhino_proxy.3dm",
        artifact_sha256="abc123rhino",
        dimensions={"length": 10.0, "beam": 2.0},
        object_type="Brep"
    )
    assert rhino_id

    # 2. SW evidence
    sw_id = record_solidworks_inspection_evidence(
        document_info={"name": "test.SLDPRT", "path": "C:\\test.SLDPRT"},
        features={"count": 5}
    )
    assert sw_id

    # 3. Maxsurf evidence (mock file paths for test)
    import hashlib
    from pathlib import Path
    
    tmp_file = Path("data/projects/test/maxsurf_tmp.msd")
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file.write_bytes(b"maxsurf test")
    sha = hashlib.sha256(tmp_file.read_bytes()).hexdigest()
    
    mx_id = record_maxsurf_probe_evidence(
        source_path=str(tmp_file),
        source_sha256=sha,
        import_path=str(tmp_file),
        export_path=str(tmp_file)
    )
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
