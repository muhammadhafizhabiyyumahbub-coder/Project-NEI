import asyncio
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import DB_PATH, init_db
from nei.connectors.solidworks2022 import SolidWorks2022Connector


def test_capability_report_has_safe_unknowns(monkeypatch):
    connector = SolidWorks2022Connector()
    monkeypatch.setattr(connector, "_candidate_paths", lambda: [])
    capabilities = {c.name: c.status.value for c in connector.get_capabilities()}
    assert capabilities["sw.detect"] == "SUPPORTED"
    assert capabilities["sw.get_document_info"] == "UNKNOWN"
    assert capabilities["sw.list_features"] == "UNKNOWN"
    assert capabilities["sw.create_test_part"] == "UNSUPPORTED"


def test_capability_endpoint():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    response = TestClient(app).get("/api/v1/connectors/solidworks2022/capabilities")
    assert response.status_code == 200
    names = {item["name"] for item in response.json()["capabilities"]}
    assert "sw.get_document_info" in names
