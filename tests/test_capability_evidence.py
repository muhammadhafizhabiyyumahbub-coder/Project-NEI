import asyncio
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import DB_PATH, init_db, get_db


def test_capabilities_include_evidence_summary():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    async def seed():
        async with get_db() as db:
            await db.execute("""INSERT INTO connector_evidence
                (id, connector_id, capability_name, evidence_type, verified_at)
                VALUES ('e1', 'maxsurf20', 'maxsurf.hull_generation_manual', 'reopen_inspection', '2026-01-01')""")
            await db.commit()
    asyncio.run(seed())
    response = TestClient(app).get('/api/v1/connectors/maxsurf20/capabilities')
    assert response.status_code == 200
    item = next(c for c in response.json()['capabilities'] if c['name'] == 'maxsurf.hull_generation_manual')
    assert item['evidence']['count'] == 1
    assert item['evidence']['last_verified_at'] == '2026-01-01'
