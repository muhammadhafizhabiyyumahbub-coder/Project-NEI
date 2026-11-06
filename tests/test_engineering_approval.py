import asyncio
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import DB_PATH, init_db


def test_engineering_approval_is_explicit_and_task_scoped():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)
    project = client.post('/api/v1/projects', json={'name': 'p'}).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks", json={'user_request': 'hull'}).json()
    response = client.post(f"/api/v1/tasks/{task['id']}/approval", json={
        'status': 'pending', 'reviewed_by': 'engineer', 'reason': 'Awaiting hydrostatic review',
        'artifact_sha256': 'abc',
    })
    assert response.status_code == 200
    assert response.json()['status'] == 'pending'
    listed = client.get(f"/api/v1/tasks/{task['id']}/approval")
    assert listed.status_code == 200
    assert listed.json()[0]['reason'] == 'Awaiting hydrostatic review'


def test_final_approval_requires_reviewer_reason_and_checksum():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)
    project = client.post('/api/v1/projects', json={'name': 'p'}).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks", json={'user_request': 'hull'}).json()
    base = f"/api/v1/tasks/{task['id']}/approval"
    for body in ({'status': 'approved'}, {'status': 'approved', 'reviewed_by': 'eng'}, {'status': 'approved', 'reason': 'ok'}):
        assert client.post(base, json=body).status_code == 400
