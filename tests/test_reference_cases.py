import asyncio

from nei.core.database import DB_PATH, init_db
from nei.engineering.reference_cases import REFERENCE_CASES
from nei.engineering.seed import ensure_built_in_formulas
from nei.engineering.calculator import verify_reference_case
from nei.evidence import list_formulas


def test_all_builtin_formulas_have_passing_reference_cases():
    if DB_PATH.exists():
        DB_PATH.unlink()
    asyncio.run(init_db())
    asyncio.run(ensure_built_in_formulas())
    formulas = asyncio.run(list_formulas())
    by_name = {formula["name"]: formula["id"] for formula in formulas}
    assert set(REFERENCE_CASES) <= set(by_name)
    for name, case in REFERENCE_CASES.items():
        result = asyncio.run(verify_reference_case(
            by_name[name], case["inputs"], case["expected"], tolerance=1e-9
        ))
        assert result["passed"], result
