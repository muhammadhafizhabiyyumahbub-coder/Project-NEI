from pathlib import Path
import pytest
from nei.connectors.solidworks2022 import SolidWorks2022Connector


@pytest.mark.skipif(
    not Path(r"D:\SolidWork\SW\SOLIDWORKS\SLDWORKS.exe").exists(),
    reason="SOLIDWORKS installation unavailable",
)
def test_com_probe_attaches_without_launching():
    connector = SolidWorks2022Connector(r"D:\SolidWork\SW\SOLIDWORKS\SLDWORKS.exe")
    result = connector.com_probe()
    if not result["available"]:
        pytest.skip(result["note"])
    assert result["visible"] is True
    assert "no document opened" in result["note"]
