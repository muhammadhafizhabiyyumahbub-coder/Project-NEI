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
    rhino_path = "data/projects/capability-probe/rhino/artifacts/20261105_173000_proxy.3dm"
    rhino_sha = "1EE8AC7FDF3DFECF76E60C41B7968C5035192645F239DFC543BC2B5431BD4C9C"
    if not Path(rhino_path).exists():
        raise FileNotFoundError(f"Missing sandbox artifact: {rhino_path}")
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
    msd_sha = "c3cb80611d51e9f22c8391164f676182cf7229d6e2b883c7c273c8692e2eb266"
    if not Path(msd_path).exists():
        raise FileNotFoundError(f"Missing sandbox artifact: {msd_path}")
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
