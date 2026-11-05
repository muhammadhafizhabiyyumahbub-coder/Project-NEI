import asyncio
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import DB_PATH, init_db


def client():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    return TestClient(app)


def test_document_info_is_unavailable_without_validated_com():
    response = client().get(
        "/api/v1/connectors/solidworks2022/inspect?operation=document_info"
    )
    assert response.status_code == 503
    assert response.json()["detail"]["code"] != ""


def test_features_is_unavailable_without_validated_com():
    response = client().get(
        "/api/v1/connectors/solidworks2022/inspect?operation=features"
    )
    assert response.status_code == 503
    assert response.json()["detail"]["operation"] == "features"


def test_unknown_inspection_operation_rejected():
    response = client().get(
        "/api/v1/connectors/solidworks2022/inspect?operation=write_part"
    )
    assert response.status_code == 400
