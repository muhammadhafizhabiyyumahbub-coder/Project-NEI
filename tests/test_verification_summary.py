import asyncio
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import DB_PATH, init_db


def test_verification_summary_is_conservative():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)
    project = client.post('/api/v1/projects', json={'name': 'p'}).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks", json={'user_request': 'hull'}).json()
    response = client.get(f"/api/v1/tasks/{task['id']}/verification-summary")
    assert response.status_code == 200
    data = response.json()
    assert data['overall_status'] == 'not_ready'
    assert data['hydrostatics_status'] == 'not_verified'
    assert data['engineering_approval'] == 'not_performed'


def test_summary_marks_approval_stale_when_artifact_missing():
    reset_db = lambda: (DB_PATH.unlink() if DB_PATH.exists() else None)
    reset_db()
    asyncio.run(init_db())
    client = TestClient(app)
    project = client.post('/api/v1/projects', json={'name': 'p'}).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks", json={'user_request': 'hull'}).json()
    response = client.post(f"/api/v1/tasks/{task['id']}/approval", json={'status': 'pending', 'reviewed_by': 'eng', 'reason': 'review'})
    assert response.status_code == 200

