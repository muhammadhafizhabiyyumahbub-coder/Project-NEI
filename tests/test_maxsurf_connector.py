from pathlib import Path
import pytest
from nei.connectors.maxsurf20 import Maxsurf20Connector


@pytest.mark.skipif(
    not Path(r"C:\Program Files\Bentley\Engineering\Maxsurf 20 V8i\MaxsurfModeler64.exe").exists(),
    reason="Maxsurf installation unavailable",
)
def test_detect():
    connector = Maxsurf20Connector()
    result = connector.detect()
    assert result.detected is True
    assert result.version == "20.00.01.59"


def test_get_capabilities():
    caps = {c.name: c.status.value for c in Maxsurf20Connector().get_capabilities()}
    assert caps["maxsurf.detect"] == "SUPPORTED"
    assert caps["maxsurf.get_version"] == "SUPPORTED"
    assert caps["maxsurf.inspect_project_file"] == "SUPPORTED"
    assert caps["maxsurf.import_copy"] == "SUPPORTED"
    assert caps["maxsurf.export_copy"] == "SUPPORTED"
    assert caps["maxsurf.hull_generation"] == "SUPPORTED"


def test_inspect_project_file():
    connector = Maxsurf20Connector()
    result = connector.execute("maxsurf.inspect_project_file", {"path": r"C:\Program Files\Bentley\Engineering\Maxsurf 20 V8i\MaxsurfModeler64.exe"}, timeout_s=5)
    assert result.success is True
    assert result.data["exists"] is True