import asyncio
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import DB_PATH, init_db


def test_capability_mapping_includes_internal_and_hull_statuses():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    response = TestClient(app).get("/api/v1/capabilities")
    assert response.status_code == 200
    capabilities = response.json()["capabilities"]
    by_name = {item["name"]: item for item in capabilities}
    assert by_name["hull.preview_calculation"]["status"] == "SUPPORTED"
    assert by_name["maxsurf.hull_generation"]["status"] == "UNKNOWN"
    assert by_name["rhino.hull_generation"]["status"] == "UNKNOWN"
    assert by_name["solidworks.hull_generation"]["status"] == "UNSUPPORTED"
    assert by_name["maxsurf.hull_generation_manual"]["status"] == "SUPPORTED"
    assert by_name["maxsurf.hull_generation_from_nei"]["status"] == "UNKNOWN"
