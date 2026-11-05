import asyncio
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import DB_PATH, init_db
from nei.core import artifact_store


def test_task_artifacts_endpoint_returns_sha256(tmp_path, monkeypatch):
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    monkeypatch.setattr(artifact_store, "ARTIFACTS_ROOT", tmp_path)
    client = TestClient(app)
    project = client.post('/api/v1/projects', json={'name': 'p'}).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks", json={'user_request': 'x'}).json()
    asyncio.run(artifact_store.save_artifact(task['id'], 'hull.3dm', b'hull'))

    response = client.get(f"/api/v1/tasks/{task['id']}/artifacts")
    assert response.status_code == 200
    assert response.json()[0]["filename"] == "hull.3dm"
    assert response.json()[0]["sha256"]
