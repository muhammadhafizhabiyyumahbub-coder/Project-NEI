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
    assert caps["ms.detect"] == "SUPPORTED"
    assert caps["ms.get_version"] == "SUPPORTED"
    assert caps["ms.list_components"] == "UNKNOWN"
    assert caps["ms.get_model_info"] == "UNSUPPORTED"
