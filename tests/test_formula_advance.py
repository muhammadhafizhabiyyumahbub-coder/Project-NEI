"""Security checks for POST /formulas/{id}/advance.

- LLM/system actor cannot advance formula lifecycle (must be human)
- Only forward transitions in lifecycle order
- Audit event written
"""
import asyncio
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import init_db, DB_PATH


def setup_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())


def make_formula(client, name="box_volume"):
    r = client.post("/api/v1/formulas", json={
        "name": name, "domain": "geometry", "equation_text": "l*w*h",
        "implementation_ref": "nei/engineering/geometry/formulas.py:box_volume",
    })
    assert r.status_code == 200, r.text
    return r.json()


def test_llm_cannot_advance_formula():
    setup_db()
    client = TestClient(app)
    f = make_formula(client)
    fid = f["id"]
    # LLM tries to advance to SOURCE_ATTACHED
    r = client.post(f"/api/v1/formulas/{fid}/advance",
                    json={"to_status": "SOURCE_ATTACHED",
                          "reviewed_by": "llm", "reason": "i found the source"})
    assert r.status_code == 400, r.text
    assert "human" in r.json()["detail"]


def test_system_cannot_advance_formula():
    setup_db()
    client = TestClient(app)
    f = make_formula(client)
    fid = f["id"]
    r = client.post(f"/api/v1/formulas/{fid}/advance",
                    json={"to_status": "SOURCE_ATTACHED",
                          "reviewed_by": "system", "reason": "auto-attach"})
    assert r.status_code == 400, r.text


def test_human_can_advance_formula():
    setup_db()
    client = TestClient(app)
    f = make_formula(client)
    fid = f["id"]
    r = client.post(f"/api/v1/formulas/{fid}/advance",
                    json={"to_status": "SOURCE_ATTACHED",
                          "reviewed_by": "muhammad", "reason": "attached source"})
    assert r.status_code == 200, r.text


def test_backward_transition_rejected():
    setup_db()
    client = TestClient(app)
    f = make_formula(client)
    fid = f["id"]
    # Cannot go from DRAFT to DRAFT (same) or backward
    r = client.post(f"/api/v1/formulas/{fid}/advance",
                    json={"to_status": "DRAFT", "reviewed_by": "muhammad", "reason": ""})
    assert r.status_code == 400, r.text
    assert "forward" in r.json()["detail"]


def test_audit_event_written():
    setup_db()
    client = TestClient(app)
    f = make_formula(client)
    fid = f["id"]
    r = client.post(f"/api/v1/formulas/{fid}/advance",
                    json={"to_status": "SOURCE_ATTACHED",
                          "reviewed_by": "muhammad", "reason": "attached source"})
    assert r.status_code == 200, r.text
    from nei.core.database import get_db
    async def _count_events():
        async with get_db() as db:
            rows = await db.execute_fetchall(
                "SELECT COUNT(*) FROM audit_events WHERE event_type = ?",
                ("FORMULA_ADVANCE",))
            return rows[0][0]
    n = asyncio.run(_count_events())
    assert n == 1, n
