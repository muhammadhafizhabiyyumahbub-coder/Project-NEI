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
    assert caps["maxsurf.hull_generation"] == "UNKNOWN"
    assert caps["maxsurf.hull_generation_manual"] == "SUPPORTED"
    assert caps["maxsurf.hull_generation_from_nei"] == "UNKNOWN"


def test_get_capabilities_is_conservative():
    result = Maxsurf20Connector().execute("maxsurf.get_capabilities", {}, timeout_s=5)
    assert result.success is True
    assert result.data["automation_api"] == "UNVERIFIED"
    assert result.data["com_registered"] is False
    assert result.data["documentation_present"]["modeler_automation_doc"] is True


def test_inspect_project_file():
    connector = Maxsurf20Connector()
    result = connector.execute("maxsurf.inspect_project_file", {"path": r"C:\Program Files\Bentley\Engineering\Maxsurf 20 V8i\MaxsurfModeler64.exe"}, timeout_s=5)
    assert result.success is True
    assert result.data["exists"] is True