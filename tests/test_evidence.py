"""Phase 4 evidence engine tests: ingest, checksum, search, formula lifecycle."""
import asyncio
import json
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from nei.main import app
from nei.core.database import init_db, DB_PATH

# Use a temp docs root so we don't touch real data/documents
DOCUMENTS_DIR = Path("data/documents")


def setup(tmp_test_file=None):
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    client = TestClient(app)
    return client


def test_ingest_and_list_source(tmp_path):
    # Create a sample text source
    src_file = tmp_path / "buoyancy.txt"
    src_file.write_text(
        "# Archimedes Principle\n"
        "The buoyant force equals the weight of displaced fluid.\n"
        "Fb = rho * g * V\n"
        "Where rho is fluid density, g is gravity, V is displaced volume.\n",
        encoding="utf-8",
    )
    client = setup()

    r = client.post("/api/v1/evidence/sources", json={
        "title": "Buoyancy Fundamentals",
        "source_type": "textbook",
        "authority_level": "academic",
        "local_file_path": str(src_file),
        "author": "Test Author",
        "year": 2020,
    })
    assert r.status_code == 200, r.text
    src = r.json()
    assert src["verification_status"] == "unverified"
    assert src["chunk_count"] >= 1

    # List
    r = client.get("/api/v1/evidence/sources")
    assert r.status_code == 200
    items = r.json()
    assert any(s["id"] == src["id"] for s in items)

    # Get by ID
    r = client.get(f"/api/v1/evidence/sources/{src['id']}")
    assert r.status_code == 200
    assert r.json()["title"] == "Buoyancy Fundamentals"


def test_source_checksum(tmp_path):
    src_file = tmp_path / "check.txt"
    src_file.write_text("hello world", encoding="utf-8")
    client = setup()

    r = client.post("/api/v1/evidence/sources", json={
        "title": "Check Test",
        "source_type": "other",
        "authority_level": "other",
        "local_file_path": str(src_file),
    })
    src = r.json()

    r = client.post(f"/api/v1/evidence/sources/{src['id']}/checksum")
    assert r.status_code == 200
    assert r.json()["intact"] is True


def test_source_status(tmp_path):
    src_file = tmp_path / "status.txt"
    src_file.write_text("test", encoding="utf-8")
    client = setup()

    r = client.post("/api/v1/evidence/sources", json={
        "title": "Status Test",
        "source_type": "other",
        "authority_level": "other",
        "local_file_path": str(src_file),
    })
    src = r.json()

    r = client.post(f"/api/v1/evidence/sources/{src['id']}/status",
                    json={"status": "verified", "reason": "identity confirmed"})
    assert r.status_code == 200
    assert r.json()["verification_status"] == "verified"

    # invalid status
    r = client.post(f"/api/v1/evidence/sources/{src['id']}/status",
                    json={"status": "bogus"})
    assert r.status_code == 400


def test_search(tmp_path):
    src_file = tmp_path / "search.txt"
    src_file.write_text(
        "# Hydrostatics\n"
        "Metacentric height GM determines initial stability.\n"
        "GM = KM - KG. Positive GM means stable.\n"
        "Displacement delta = rho * L * B * T.\n",
        encoding="utf-8",
    )
    client = setup()

    r = client.post("/api/v1/evidence/sources", json={
        "title": "Stability Textbook",
        "source_type": "textbook",
        "authority_level": "academic",
        "local_file_path": str(src_file),
    })
    src = r.json()

    r = client.post("/api/v1/evidence/search", json={"query": "metacentric", "limit": 10})
    assert r.status_code == 200
    results = r.json()
    assert any("Metacentric" in res["text"] for res in results), results


def test_formula_lifecycle(tmp_path):
    # First register a source to reference
    src_file = tmp_path / "ref.txt"
    src_file.write_text("reference text", encoding="utf-8")
    client = setup()

    r = client.post("/api/v1/evidence/sources", json={
        "title": "Ref",
        "source_type": "textbook",
        "authority_level": "academic",
        "local_file_path": str(src_file),
    })
    src = r.json()

    # Register formula with source ref -> SOURCE_ATTACHED
    r = client.post("/api/v1/formulas", json={
        "name": "Displacement Volume",
        "domain": "hydrostatics",
        "equation_text": "V = L * B * T",
        "source_refs": [src["id"]],
    })
    assert r.status_code == 200, r.text
    formula = r.json()
    assert formula["review_status"] == "SOURCE_ATTACHED"
    fid = formula["id"]

    # Advance forward
    for next_status in ["IMPLEMENTED", "UNIT_TESTED", "REFERENCE_CASE_TESTED",
                        "TECHNICAL_REVIEW", "APPROVED_FOR_USE"]:
        r = client.post(f"/api/v1/formulas/{fid}/advance",
                        json={"to_status": next_status, "reason": "test"})
        assert r.status_code == 200, r.text
        assert r.json()["review_status"] == next_status

    # Cannot transition backward
    r = client.post(f"/api/v1/formulas/{fid}/advance", json={"to_status": "DRAFT"})
    assert r.status_code == 400

    # Unknown status
    r = client.post(f"/api/v1/formulas/{fid}/advance", json={"to_status": "BOGUS"})
    assert r.status_code == 400


def test_formula_draft_no_refs():
    client = setup()
    r = client.post("/api/v1/formulas", json={
        "name": "No Ref Formula",
        "domain": "geometry",
        "equation_text": "A = w * h",
    })
    assert r.status_code == 200
    assert r.json()["review_status"] == "DRAFT"


def test_list_formulas():
    client = setup()
    client.post("/api/v1/formulas", json={
        "name": "F1", "domain": "geometry", "equation_text": "A=1",
    })
    client.post("/api/v1/formulas", json={
        "name": "F2", "domain": "stability", "equation_text": "GM=1",
    })
    r = client.get("/api/v1/formulas?domain=geometry")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["name"] == "F1"
