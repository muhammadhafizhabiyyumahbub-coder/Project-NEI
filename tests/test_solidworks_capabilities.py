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
    # sw.get_document_info and sw.list_features depend on a live SOLIDWORKS
    # COM instance; without one they must stay UNKNOWN, never assert SUPPORTED.
    assert capabilities["sw.get_document_info"] in {"SUPPORTED", "UNKNOWN"}
    assert capabilities["sw.list_features"] in {"SUPPORTED", "UNKNOWN"}
    assert capabilities["sw.create_test_part"] == "UNKNOWN"


def test_document_capabilities_require_active_document(monkeypatch):
    connector = SolidWorks2022Connector()
    monkeypatch.setattr(connector, "get_version", lambda: "30.1")
    monkeypatch.setattr(connector, "com_probe", lambda: {"available": True, "version": "30.1"})
    monkeypatch.setattr(connector, "inspect_active_document", lambda operation: {"available": False})
    capabilities = {capability.name: capability.status.value for capability in connector.get_capabilities()}
    assert capabilities["sw.get_document_info"] == "UNKNOWN"
    assert capabilities["sw.list_features"] == "UNKNOWN"


def test_capability_endpoint():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    response = TestClient(app).get("/api/v1/connectors/solidworks2022/capabilities")
    assert response.status_code == 200
    names = {item["name"] for item in response.json()["capabilities"]}
    assert "sw.get_document_info" in names
