import asyncio
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import DB_PATH, init_db, get_db


def reset_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())


def test_capability_smoke_has_no_duplicate_names():
    reset_db()
    data = TestClient(app).get('/api/v1/capabilities').json()['capabilities']
    names = [f"{item.get('connector_id')}:{item['name']}" for item in data]
    assert len(names) == len(set(names))
    maxsurf = {item['name']: item for item in data if item.get('connector_id') == 'maxsurf20'}
    assert maxsurf['maxsurf.hull_generation_manual']['status'] == 'SUPPORTED'
    assert maxsurf['maxsurf.hull_generation_from_nei']['status'] == 'UNKNOWN'


def test_global_capabilities_include_evidence_summary():
    reset_db()

    async def seed():
        async with get_db() as db:
            await db.execute("""INSERT INTO connector_evidence
                (id, connector_id, capability_name, evidence_type, verified_at)
                VALUES ('global-e1', 'maxsurf20', 'maxsurf.hull_generation_manual', 'reopen_inspection', '2026-01-01')""")
            await db.commit()

    asyncio.run(seed())
    data = TestClient(app).get('/api/v1/capabilities').json()['capabilities']
    item = next(c for c in data if c['name'] == 'maxsurf.hull_generation_manual')
    assert item['evidence'] == {'count': 1, 'last_verified_at': '2026-01-01'}
