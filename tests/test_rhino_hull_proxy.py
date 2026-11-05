from pathlib import Path
from nei.connectors.rhino6.connector import Rhino6Connector
from nei.core.config import settings


def test_hull_proxy_sandbox_artifact():
    artifact = Path("data/projects/capability-probe/artifacts/rhino_hull_proxy.3dm").resolve()
    result = Rhino6Connector(settings.rhino_exe_path).execute(
        "rhino.create_hull_proxy",
        {"loa": 30, "beam": 8, "depth": 5, "artifact_path": str(artifact)},
        timeout_s=60,
    )
    assert result.success, result.error
    assert result.data["objects"][0]["type"] == "Brep"
    saved_artifact = Path(result.data["artifact_path"])
    assert result.data["artifact_saved"]
    assert saved_artifact.exists()
    assert saved_artifact.stat().st_size > 0
