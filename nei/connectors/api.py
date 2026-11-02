"""Connector API routes.

Phase 2: mock connectors report detected/unknown. Phase 3+ replace `mock_probe`
with real Rhino/SW/Maxsurf probes (kept as `connectors/{id}/probe` endpoint so
frontend is stable across phases).
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from nei.core.database import get_db

router = APIRouter()

CONNECTORS = [
    {"id": "rhino6", "name": "Rhino 6", "transport": "RhinoPython Method 2"},
    {"id": "solidworks2022", "name": "SOLIDWORKS 2022", "transport": "COM"},
    {"id": "maxsurf_v8i", "name": "Maxsurf 20 V8i", "transport": "file exchange"},
]


@router.get("/connectors")
async def list_connectors():
    """Static connector registry. Detect/probe fields filled by probe call."""
    return CONNECTORS


@router.get("/connectors/{connector_id}")
async def get_connector(connector_id: str):
    for c in CONNECTORS:
        if c["id"] == connector_id:
            return c
    raise HTTPException(status_code=404, detail="Connector not found")


@router.post("/connectors/{connector_id}/probe")
async def probe_connector(connector_id: str):
    """Phase 2 mock probe: returns UNKNOWN status + version=None.

    Phase 3+ replaces this body with the real detect/version/COM/file-format
    probe. Endpoint path stays stable so the connector-health UI works from
    Phase 2 forward.
    """
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT id FROM connectors WHERE id = ?", (connector_id,))
        if not rows:
            await db.execute(
                "INSERT INTO connectors (id, name, status, last_probe_ts) VALUES (?, ?, 'UNKNOWN', ?)",
                (connector_id, connector_id, datetime.now(timezone.utc).isoformat()),
            )
        else:
            await db.execute(
                "UPDATE connectors SET last_probe_ts = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), connector_id),
            )
        await db.commit()
    return {
        "connector_id": connector_id,
        "detected": None,  # UNKNOWN until real probe in Phase 3+
        "version": None,
        "bitness": None,
        "probe_ts": datetime.now(timezone.utc).isoformat(),
        "note": "Mock probe (Phase 2). Real probe lands in Phase 3+.",
    }
