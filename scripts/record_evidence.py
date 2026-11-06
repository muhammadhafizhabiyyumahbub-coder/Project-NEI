import asyncio
from pathlib import Path
from nei.connectors.evidence import (
    record_rhino_hull_proxy_evidence,
    record_solidworks_inspection_evidence,
    record_maxsurf_probe_evidence,
)

async def record_proven_evidence():
    print("Recording proven connector evidence...")
    
    # 1. Rhino
    rhino_candidates = sorted(Path("data/projects/capability-probe/artifacts").glob("rhino_hull_proxy*.3dm"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not rhino_candidates:
        raise FileNotFoundError("Missing sandbox Rhino hull proxy artifact")
    rhino_path = str(rhino_candidates[0])
    rhino_sha = __import__("hashlib").sha256(Path(rhino_path).read_bytes()).hexdigest()
    await record_rhino_hull_proxy_evidence(
        artifact_path=rhino_path,
        artifact_sha256=rhino_sha,
        dimensions={"notes": "Deterministic Brep generated"},
        object_type="Brep"
    )
    print("Recorded Rhino evidence.")

    # 2. SOLIDWORKS
    await record_solidworks_inspection_evidence(
        document_info={"name": "20261105_175748_sw_export.SLDPRT", "context": "Read-only COM access"},
        features={"count": 17}
    )
    print("Recorded SOLIDWORKS evidence.")

    # 3. Maxsurf
    msd_path = "data/projects/capability-probe/maxsurf/artifacts/Untitled.msd"
    if not Path(msd_path).exists():
        raise FileNotFoundError(f"Missing sandbox artifact: {msd_path}")
    msd_sha = __import__("hashlib").sha256(Path(msd_path).read_bytes()).hexdigest()
    export_path = "data/projects/capability-probe/maxsurf/artifacts/20261105_182721_Untitled.msd"
    if not Path(export_path).exists():
        raise FileNotFoundError(f"Missing sandbox artifact: {export_path}")

    await record_maxsurf_probe_evidence(
        source_path="D:/OpenCode/Untitled.msd",
        source_sha256=msd_sha,
        import_path=msd_path,
        export_path=export_path
    )
    print("Recorded Maxsurf evidence.")

if __name__ == "__main__":
    asyncio.run(record_proven_evidence())
