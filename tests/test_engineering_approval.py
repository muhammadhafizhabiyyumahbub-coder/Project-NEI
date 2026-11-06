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


def test_approval_accepts_matching_evidence_checksum():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)
    project = client.post('/api/v1/projects', json={'name': 'p'}).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks", json={'user_request': 'hull'}).json()
    async def seed():
        from nei.core.database import get_db
        async with get_db() as db:
            await db.execute("""INSERT INTO connector_evidence
                (id, connector_id, capability_name, evidence_type, artifact_sha256, metadata_json, verified_at)
                VALUES ('ev', 'rhino6', 'rhino.export_copy', 'artifact_exchange', 'abc', ?, '2026-01-01')""", ('{"task_id": "' + task['id'] + '"}',))
            await db.commit()
    asyncio.run(seed())
    response = client.post(f"/api/v1/tasks/{task['id']}/approval", json={'status': 'approved', 'reviewed_by': 'eng', 'reason': 'reviewed', 'artifact_sha256': 'abc'})
    assert response.status_code == 200


def test_final_approval_requires_reviewer_reason_and_checksum():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)
    project = client.post('/api/v1/projects', json={'name': 'p'}).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks", json={'user_request': 'hull'}).json()
    base = f"/api/v1/tasks/{task['id']}/approval"
    for body in ({'status': 'approved'}, {'status': 'approved', 'reviewed_by': 'eng'}, {'status': 'approved', 'reason': 'ok'}, {'status': 'approved', 'reviewed_by': 'eng', 'reason': 'ok', 'artifact_sha256': 'missing'}):
        assert client.post(base, json=body).status_code == 400


def test_approval_rejects_tampered_artifact_bytes():
    """An approval whose SHA matches the DB record but whose file on disk was
    modified after the evidence row was written must be rejected (409)."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)
    project = client.post('/api/v1/projects', json={'name': 'p'}).json()
    task = client.post(f"/api/v1/projects/{project['id']}/tasks", json={'user_request': 'hull'}).json()

    import hashlib
    import json as _json
    artifact_sha = hashlib.sha256(b"original").hexdigest()

    async def seed():
        from nei.core.database import get_db
        from nei.core import artifact_store
        await artifact_store.save_artifact(task['id'], "art.bin", b"original")
        async with get_db() as db:
            await db.execute("""INSERT INTO connector_evidence
                (id, connector_id, capability_name, evidence_type,
                 artifact_path, artifact_sha256, metadata_json, verified_at)
                VALUES ('ev', 'rhino6', 'rhino.export_copy', 'artifact_exchange',
                        ?, ?, ?, '2026-01-01')""",
                (f"data/artifacts/{task['id']}/art.bin", artifact_sha,
                 _json.dumps({"task_id": task['id']})))
            await db.commit()

    asyncio.run(seed())

    # Approval passes when the artifact on disk still matches
    ok = client.post(f"/api/v1/tasks/{task['id']}/approval",
                     json={'status': 'approved', 'reviewed_by': 'eng',
                           'reason': 'ok', 'artifact_sha256': artifact_sha})
    assert ok.status_code == 200

    # Tamper with the file after the evidence row exists
    from pathlib import Path
    Path(f"data/artifacts/{task['id']}/art.bin").write_bytes(b"tampered")

    rejected = client.post(f"/api/v1/tasks/{task['id']}/approval",
                           json={'status': 'approved', 'reviewed_by': 'eng',
                                 'reason': 'ok', 'artifact_sha256': artifact_sha})
    assert rejected.status_code == 409
    assert 'artifact_bytes_mismatch' in rejected.json()['detail']

