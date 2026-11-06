"""Connector API routes.

Phase 2: mock connectors report detected/unknown. Phase 3+ replace `mock_probe`
with real Rhino/SW/Maxsurf probes (kept as `connectors/{id}/probe` endpoint so
frontend is stable across phases).
"""
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException
from nei.core.database import get_db
from nei.connectors.registry import get_connector_class

router = APIRouter()


def _connector_meta(connector_id: str) -> dict:
    cls = get_connector_class(connector_id)
    if cls is None:
        return {"id": connector_id, "name": connector_id, "transport": "unknown"}
    return {"id": connector_id, "name": cls.name, "transport": getattr(cls, "transport", "unknown")}


def _registered_connectors() -> list[dict]:
    from nei.connectors.registry import registry
    out = []
    for cls in registry():
        out.append({"id": cls.connector_id, "name": cls.name, "transport": getattr(cls, "transport", "unknown")})
    return out


def _capability_dict(capability):
    return {
        "name": capability.name,
        "status": capability.status.value,
        "version_tested": capability.version_tested,
        "notes": capability.notes,
    }


CONNECTORS = _registered_connectors()


@router.get("/capabilities")
async def list_capabilities():
    """Return capability status, including internal deterministic actions."""
    capabilities = [{
        "name": "hull.preview_calculation",
        "status": "SUPPORTED",
        "version_tested": "NEI deterministic engine",
        "notes": "Unit-safe preview only; no CAD artifact generated.",
    }]
    for connector in CONNECTORS:
        cls = get_connector_class(connector["id"])
        if cls is None:
            continue
        from nei.core.config import settings
        kwargs = {}
        if connector["id"] == "solidworks2022":
            kwargs["exe_path"] = settings.solidworks_exe_path
        elif connector["id"] == "rhino6":
            kwargs["rhino_exe"] = settings.rhino_exe_path
        elif connector["id"] == "maxsurf20":
            kwargs["exe_path"] = settings.maxsurf_exe_path
        for item in cls(**kwargs).get_capabilities():
            capabilities.append({"connector_id": connector["id"], **_capability_dict(item)})
    capabilities.extend([
        {"connector_id": "rhino6", "name": "rhino.hull_generation", "status": "UNKNOWN", "version_tested": None, "notes": "No validated hull-generation artifact test."},
        {"connector_id": "solidworks2022", "name": "solidworks.hull_generation", "status": "UNSUPPORTED", "version_tested": None, "notes": "Connector supports inspection/safe operations only."},
    ])
    return {"capabilities": capabilities}


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


@router.get("/connectors/{connector_id}/capabilities")
async def connector_capabilities(connector_id: str):
    """Return version-tested capability status without activating CAD software."""
    from nei.core.config import settings

    cls = get_connector_class(connector_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="Capability report unavailable")

    kwargs = {}
    if connector_id == "solidworks2022":
        kwargs["exe_path"] = settings.solidworks_exe_path
    elif connector_id == "rhino6":
        kwargs["rhino_exe"] = settings.rhino_exe_path
    elif connector_id == "maxsurf20":
        kwargs["exe_path"] = settings.maxsurf_exe_path
    conn = cls(**kwargs)
    capabilities = [_capability_dict(c) for c in conn.get_capabilities()]
    async with get_db() as db:
        rows = await db.execute_fetchall(
            """SELECT capability_name, COUNT(*), MAX(verified_at)
               FROM connector_evidence WHERE connector_id = ?
               GROUP BY capability_name""", (connector_id,))
    evidence = {r[0]: {"count": r[1], "last_verified_at": r[2]} for r in rows}
    for item in capabilities:
        item["evidence"] = evidence.get(item["name"], {"count": 0, "last_verified_at": None})
    return {"connector_id": connector_id, "capabilities": capabilities}


@router.get("/connectors/{connector_id}/inspect")
async def inspect_connector(connector_id: str, operation: str = "document_info"):
    """Read-only inspection endpoint; never opens or mutates a document.

    SOLIDWORKS document inspection remains unavailable until a live COM probe
    is validated on a licensed installation.
    """
    if connector_id != "solidworks2022":
        raise HTTPException(status_code=404, detail="Inspection unavailable")
    if operation not in ("document_info", "features"):
        raise HTTPException(status_code=400, detail="Unknown inspection operation")
    from nei.connectors.solidworks2022 import SolidWorks2022Connector
    from nei.core.config import settings
    result = SolidWorks2022Connector(settings.solidworks_exe_path).inspect_active_document(operation)
    if not result.get("available"):
        raise HTTPException(
            status_code=503,
            detail={"code": result.get("error", "SOLIDWORKS_COM_UNAVAILABLE"),
                    "operation": operation, **result},
        )
    return {"connector_id": connector_id, "operation": operation, "data": result}


@router.post("/connectors/{connector_id}/probe")
async def probe_connector(connector_id: str):
    """Probe a registered connector: detect/version/capabilities.

    Per-connector instantiation logic lives in each connector class; the
    generic path here works for any connector that implements BaseConnector.
    SOLIDWORKS additionally reports its COM attach status.
    """
    from nei.core.config import settings

    cls = get_connector_class(connector_id)
    if cls is None:
        return await _mock_probe(connector_id)

    # Resolve the connector instance (SOLIDWORKS/Maxsurf take an optional exe path).
    kwargs = {}
    if connector_id == "solidworks2022":
        kwargs["exe_path"] = settings.solidworks_exe_path
    elif connector_id == "rhino6":
        kwargs["rhino_exe"] = settings.rhino_exe_path
    elif connector_id == "maxsurf20":
        kwargs["exe_path"] = settings.maxsurf_exe_path
    conn = cls(**kwargs)

    det = conn.detect()
    version = conn.get_version()
    ts = datetime.now(timezone.utc).isoformat()
    status = "DETECTED" if det.detected else "NOT_FOUND"
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO connectors (id, name, status, last_probe_ts, version, exe_path) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (connector_id, conn.name, status, ts, version,
             det.exe_path if det.detected else None),
        )
        await db.commit()

    response = {
        "connector_id": connector_id,
        "detected": det.detected,
        "version": version,
        "exe_path": det.exe_path if det.detected else None,
        "probe_ts": ts,
        "note": det.notes,
        "capabilities": [_capability_dict(c) for c in conn.get_capabilities()],
    }

    # SOLIDWORKS reports COM attach status alongside the filesystem probe.
    if connector_id == "solidworks2022" and hasattr(conn, "com_probe"):
        response["com"] = conn.com_probe()

    return response


@router.get("/connectors/{connector_id}/evidence")
async def list_connector_evidence(connector_id: str, capability: str = None):
    """Return evidence records for a connector, optionally filtered by capability."""
    async with get_db() as db:
        if capability:
            rows = await db.execute_fetchall(
                """SELECT id, connector_id, capability_name, evidence_type, artifact_path,
                          artifact_sha256, metadata_json, verified_at, verified_by, notes
                   FROM connector_evidence
                   WHERE connector_id = ? AND capability_name = ?
                   ORDER BY verified_at DESC""",
                (connector_id, capability),
            )
        else:
            rows = await db.execute_fetchall(
                """SELECT id, connector_id, capability_name, evidence_type, artifact_path,
                          artifact_sha256, metadata_json, verified_at, verified_by, notes
                   FROM connector_evidence
                   WHERE connector_id = ?
                   ORDER BY verified_at DESC""",
                (connector_id,),
            )
    return {
        "connector_id": connector_id,
        "evidence": [
            {
                "id": r[0],
                "capability_name": r[2],
                "evidence_type": r[3],
                "artifact_path": r[4],
                "artifact_sha256": r[5],
                "metadata": __import__("json").loads(r[6]) if r[6] else None,
                "verified_at": r[7],
                "verified_by": r[8],
                "notes": r[9],
            }
            for r in rows
        ],
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
