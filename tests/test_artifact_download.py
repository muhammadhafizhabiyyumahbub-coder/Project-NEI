import asyncio
import os
from pathlib import Path
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import DB_PATH, init_db
from nei.core.artifact_store import save_artifact

def test_safe_artifact_download():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)
    
    # 1. Setup project & task
    project = client.post('/api/v1/projects', json={'name': 'p'}).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks", json={'user_request': 'hull'}).json()
    task_id = task['id']
    
    # 2. Save an artifact directly
    content = b"test content"
    filename = "test.txt"
    asyncio.run(save_artifact(task_id, filename, content))
    
    # 3. Test successful download
    response = client.get(f"/api/v1/tasks/{task_id}/artifacts/{filename}")
    assert response.status_code == 200
    assert response.content == content
    
    # Test path traversal rejection (query or path)
    r1 = client.get(f"/api/v1/tasks/{task_id}/artifacts/..%2Fconfig.py")
    r2 = client.get(f"/api/v1/tasks/{task_id}/artifacts/%2E%2E%2Fsecret.txt")
    assert r1.status_code in (400, 404)
    
    # Direct invalid filename check
    r3 = client.get(f"/api/v1/tasks/{task_id}/artifacts/invalid..name")
    assert r3.status_code == 400
        
    # 5. Test missing file
    response = client.get(f"/api/v1/tasks/{task_id}/artifacts/nonexistent.txt")
    assert response.status_code == 404
