import asyncio
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import DB_PATH, init_db


def test_capability_smoke_has_no_duplicate_names():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    data = TestClient(app).get('/api/v1/capabilities').json()['capabilities']
    names = [item['name'] for item in data]
    assert len(names) == len(set(names))
    maxsurf = {item['name']: item for item in data if item.get('connector_id') == 'maxsurf20'}
    assert maxsurf['maxsurf.hull_generation_manual']['status'] == 'SUPPORTED'
    assert maxsurf['maxsurf.hull_generation_from_nei']['status'] == 'UNKNOWN'
