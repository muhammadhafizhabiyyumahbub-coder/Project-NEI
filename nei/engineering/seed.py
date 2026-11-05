"""Seed built-in formulas into the evidence store at startup.

The built-in registry is vetted source code, so rows are seeded directly as
APPROVED_FOR_USE rather than flowing through the human review pipeline.
Idempotent: existing formula names are left untouched.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from nei.core.database import get_db
from nei.evidence import list_formulas


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def seed_builtin_formulas() -> list[dict]:
    from nei.engineering.calculator import FORMULA_REGISTRY

    existing = {f["name"] for f in await list_formulas()}
    now = _now()
    out = []
    async with get_db() as db:
        for name, impl in FORMULA_REGISTRY.items():
            if name in existing:
                continue
            fid = uuid.uuid4().hex
            domain = impl["domain"]
            await db.execute(
                """INSERT INTO formulas
                   (id, name, domain, equation_text, implementation_ref, variables_json,
                    canonical_units, assumptions_json, applicability_json,
                    source_refs_json, source_locations_json, review_status, version,
                    created_at, change_log_json)
                VALUES (?, ?, ?, ?, ?, ?, 'SI', ?, ?, ?, ?, ?, 1, ?, ?)""",
                (fid, name, domain, impl["description"], f"builtin:{name}",
                 json.dumps([]), json.dumps([]), json.dumps([]), json.dumps([]),
                 json.dumps([]), "APPROVED_FOR_USE", now,
                 json.dumps([{"ts": now, "event": "seeded built-in formula"}])),
            )
            out.append({"id": fid, "name": name, "domain": domain})
        await db.commit()
    return out


async def ensure_built_in_formulas() -> None:
    """Seed built-in formulas; no-op if anything is already present."""
    if await list_formulas():
        return
    await seed_builtin_formulas()
