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
    rows = {}
    async with get_db() as db:
        for r in await db.execute_fetchall("SELECT id, status FROM connectors"):
            rows[r[0]] = r[1]
    out = []
    for c in CONNECTORS:
        c = {**c}
        c["status"] = rows.get(c["id"])
        out.append(c)
    return out


@router.get("/connectors/{connector_id}")
async def get_connector(connector_id: str):
    for c in CONNECTORS:
        if c["id"] == connector_id:
            return c
    raise HTTPException(status_code=404, detail="Connector not found")


@router.post("/connectors/{connector_id}/probe")
async def probe_connector(connector_id: str):
    """Probe a connector: real detect/version for rhino6, mock for others."""
    from nei.connectors.rhino6 import Rhino6Connector
    from nei.core.config import settings

    if connector_id == "solidworks2022":
        from nei.connectors.solidworks2022 import SolidWorks2022Connector
        conn = SolidWorks2022Connector()
        det = conn.detect()
        ts = datetime.now(timezone.utc).isoformat()
        status = "DETECTED" if det.detected else "NOT_FOUND"
        async with get_db() as db:
            await db.execute(
                "INSERT OR REPLACE INTO connectors (id, name, status, last_probe_ts, version, exe_path) VALUES (?, ?, ?, ?, ?, ?)",
                (connector_id, conn.name, status, ts, det.version, det.exe_path),
            )
            await db.commit()
        return {
            "connector_id": connector_id, "detected": det.detected,
            "version": det.version, "exe_path": det.exe_path,
            "probe_ts": ts, "note": det.notes,
        }

    if connector_id != "rhino6":
        return await _mock_probe(connector_id)

    conn = Rhino6Connector(rhino_exe=settings.rhino_exe_path)
    det = conn.detect()
    version = conn.get_version()
    ts = datetime.now(timezone.utc).isoformat()

    status = "DETECTED" if det.detected else "NOT_FOUND"
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT id FROM connectors WHERE id = ?", (connector_id,))
        if not rows:
            await db.execute(
                "INSERT INTO connectors (id, name, status, last_probe_ts, version, exe_path) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (connector_id, "Rhino 6", status, ts, version,
                 det.exe_path if det.detected else None),
            )
        else:
            await db.execute(
                "UPDATE connectors SET status = ?, last_probe_ts = ?, version = ?, exe_path = ? WHERE id = ?",
                (status, ts, version,
                 det.exe_path if det.detected else None, connector_id),
            )
        await db.commit()
    return {
        "connector_id": connector_id,
        "detected": det.detected,
        "version": version,
        "exe_path": det.exe_path if det.detected else None,
        "probe_ts": ts,
        "note": "Rhino 6 probe (RhinoPython Method 2)." if det.detected else "Rhino 6 not found at configured path.",
    }


async def _mock_probe(connector_id: str) -> dict:
    """Fallback mock probe for connectors without a real implementation yet."""
    ts = datetime.now(timezone.utc).isoformat()
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT id FROM connectors WHERE id = ?", (connector_id,))
        if not rows:
            await db.execute(
                "INSERT INTO connectors (id, name, status, last_probe_ts) VALUES (?, ?, 'UNKNOWN', ?)",
                (connector_id, connector_id, ts),
            )
        else:
            await db.execute(
                "UPDATE connectors SET last_probe_ts = ? WHERE id = ?",
                (ts, connector_id),
            )
        await db.commit()
    return {
        "connector_id": connector_id,
        "detected": None,
        "version": None,
        "probe_ts": ts,
        "note": "Mock probe (Phase 2). Real probe lands in Phase 3+.",
    }
