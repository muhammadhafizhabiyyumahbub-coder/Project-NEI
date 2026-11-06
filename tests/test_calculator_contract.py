import asyncio

from nei.core.database import DB_PATH, init_db
from nei.evidence import register_formula
from nei.engineering.calculator import run_formula


def setup_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())


def test_formula_requires_approved_status_and_parses_units():
    setup_db()
    formula = asyncio.run(register_formula(
        "box_volume", "geometry", "V = L * W * H",
        source_refs=["source-reference"],
    ))
    blocked = run_formula(formula["id"], {"length": "1 m", "width": "2 m", "height": "3 m"})
    assert blocked["status"] == "INVALID"
    sandbox = run_formula(formula["id"], {"length": "1 m", "width": "2 m", "height": "3 m"}, research=True)
    assert sandbox["result"] == 6.0
    assert sandbox["evidence_status"] == "UNVERIFIED"
