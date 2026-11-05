import asyncio
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import DB_PATH, init_db, get_db


def test_task_evidence_endpoint_returns_only_linked_records():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)
    project = client.post('/api/v1/projects', json={'name': 'p'}).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks", json={'user_request': 'x'}).json()

    async def insert():
        async with get_db() as db:
            await db.execute("""INSERT INTO connector_evidence
                (id, connector_id, capability_name, evidence_type, artifact_path,
                 artifact_sha256, metadata_json, verified_at, verified_by, notes)
                VALUES ('linked', 'rhino6', 'rhino.export_copy', 'artifact_exchange',
                        'box.3dm', 'abc', ?, '2026-01-01', 'system', 'linked')""",
                ('{"task_id": "' + task['id'] + '"}',))
            await db.execute("""INSERT INTO connector_evidence
                (id, connector_id, capability_name, evidence_type, verified_at)
                VALUES ('other', 'rhino6', 'rhino.export_copy', 'artifact_exchange', '2026-01-01')""")
            await db.commit()
    asyncio.run(insert())

    response = client.get(f"/api/v1/tasks/{task['id']}/evidence")
    assert response.status_code == 200
    assert [item['id'] for item in response.json()] == ['linked']
