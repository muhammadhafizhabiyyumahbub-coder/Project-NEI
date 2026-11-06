"""Evidence recording for connector probe results."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from nei.core.database import get_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def record_connector_evidence(
    connector_id: str,
    capability_name: str,
    evidence_type: str,
    *,
    artifact_path: Optional[str] = None,
    artifact_sha256: Optional[str] = None,
    metadata: Optional[dict] = None,
    verified_by: str = "system",
    notes: Optional[str] = None,
) -> str:
    """Record verified probe artifact or inspection result. Returns evidence record ID."""
    import uuid

    evidence_id = str(uuid.uuid4())
    metadata_json = json.dumps(metadata) if metadata else None

    async with get_db() as db:
        existing = await db.execute_fetchall(
            """SELECT id FROM connector_evidence
               WHERE connector_id = ? AND capability_name = ? AND evidence_type = ? AND artifact_sha256 = ?""",
            (connector_id, capability_name, evidence_type, artifact_sha256),
        )
        if existing:
            return existing[0][0]
        await db.execute(
            """INSERT INTO connector_evidence
               (id, connector_id, capability_name, evidence_type, artifact_path,
                artifact_sha256, metadata_json, verified_at, verified_by, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                evidence_id,
                connector_id,
                capability_name,
                evidence_type,
                artifact_path,
                artifact_sha256,
                metadata_json,
                _now(),
                verified_by,
                notes,
            ),
        )
        await db.commit()
    return evidence_id


async def record_rhino_hull_proxy_evidence(
    artifact_path: str, artifact_sha256: str, dimensions: dict, object_type: str
) -> str:
    """Record Rhino hull proxy probe evidence."""
    return await record_connector_evidence(
        connector_id="rhino6",
        capability_name="rhino.create_hull_proxy",
        evidence_type="sandbox_artifact",
        artifact_path=artifact_path,
        artifact_sha256=artifact_sha256,
        metadata={"dimensions": dimensions, "object_type": object_type},
        notes="Rhino 6 hull proxy sandbox export verified",
    )


async def record_solidworks_inspection_evidence(
    document_info: dict, features: dict
) -> str:
    """Record SOLIDWORKS read-only inspection evidence."""
    return await record_connector_evidence(
        connector_id="solidworks2022",
        capability_name="sw.get_document_info",
        evidence_type="com_inspection",
        metadata={"document_info": document_info, "features": features},
        notes="SOLIDWORKS COM read-only inspection verified",
    )


async def record_maxsurf_probe_evidence(
    source_path: str,
    source_sha256: str,
    import_path: Optional[str] = None,
    export_path: Optional[str] = None,
) -> str:
    """Record Maxsurf file exchange probe evidence."""
    metadata = {
        "source_path": source_path,
        "source_sha256": source_sha256,
        "import_path": import_path,
        "export_path": export_path,
        "read_only": True,
    }
    if import_path and export_path:
        # Verify checksums match
        if Path(import_path).exists() and Path(export_path).exists():
            import_sha = hashlib.sha256(Path(import_path).read_bytes()).hexdigest()
            export_sha = hashlib.sha256(Path(export_path).read_bytes()).hexdigest()
            if import_sha != export_sha:
                raise ValueError("Import/export checksum mismatch")
            metadata["import_sha256"] = import_sha
            metadata["export_sha256"] = export_sha
    return await record_connector_evidence(
        connector_id="maxsurf20",
        capability_name="maxsurf.import_copy",
        evidence_type="file_exchange",
        artifact_path=import_path or source_path,
        artifact_sha256=source_sha256,
        metadata=metadata,
        notes="Maxsurf .msd file exchange sandbox verified",
    )
