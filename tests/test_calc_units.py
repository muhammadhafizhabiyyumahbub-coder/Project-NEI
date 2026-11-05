"""Unit-safe calculation endpoint tests (Phase 5 wire-up)."""
import asyncio
import pathlib

from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import init_db, DB_PATH


def setup():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    return TestClient(app)


def _approved_box_volume(client):
    p = pathlib.Path(__file__).parent / "ref_source.txt"
    if not p.exists():
        p.write_text("reference source for tests\n", encoding="utf-8")
    r = client.post("/api/v1/evidence/sources", json={
        "title": "Ref", "source_type": "textbook",
        "authority_level": "academic", "local_file_path": str(p),
    })
    assert r.status_code == 200, r.text
    sid = r.json()["id"]
    r = client.post("/api/v1/formulas", json={
        "name": "box_volume", "domain": "geometry",
        "equation_text": "V=L*W*H", "source_refs": [sid],
    })
    assert r.status_code == 200, r.text
    fid = r.json()["id"]
    for s in ["IMPLEMENTED", "UNIT_TESTED", "REFERENCE_CASE_TESTED",
              "TECHNICAL_REVIEW", "APPROVED_FOR_USE"]:
        r = client.post(f"/api/v1/formulas/{fid}/advance", json={"to_status": s})
        assert r.status_code == 200, r.text
    return fid


def test_unit_string_inputs_parsed_to_si():
    client = setup()
    fid = _approved_box_volume(client)
    # 1000mm x 3000mm x 1000mm = 1m * 3m * 1m = 3 m^3
    r = client.post("/api/v1/calculations", json={
        "formula_id": fid,
        "inputs": {"length": "1000 mm", "width": "3000 mm", "height": "1000 mm"},
        "research": False,
    })
    assert r.status_code == 200, r.text
    assert abs(r.json()["result"] - 3.0) < 1e-9
    assert r.json()["evidence_status"] == "VERIFIED"


def test_mixed_numeric_and_unit_string_inputs():
    client = setup()
    fid = _approved_box_volume(client)
    # 2.0 m (raw number) x 500 cm (5 m) x 1000 mm (1 m) = 10
    r = client.post("/api/v1/calculations", json={
        "formula_id": fid,
        "inputs": {"length": 2.0, "width": "500 cm", "height": "1000 mm"},
        "research": False,
    })
    assert r.status_code == 200, r.text
    assert abs(r.json()["result"] - 10.0) < 1e-9


def test_unknown_unit_rejected():
    client = setup()
    fid = _approved_box_volume(client)
    r = client.post("/api/v1/calculations", json={
        "formula_id": fid,
        "inputs": {"length": "10 lightyears", "width": 3, "height": 1},
        "research": False,
    })
    assert r.status_code == 400
    assert "lightyears" in r.text.lower() or "unknown" in r.text.lower()
