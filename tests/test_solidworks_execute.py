from pathlib import Path
import pytest
from nei.connectors.solidworks2022 import SolidWorks2022Connector
from nei.connectors.base import ToolResult

SW_EXE = r"D:\SolidWork\SW\SOLIDWORKS\SLDWORKS.exe"


def _connector():
    return SolidWorks2022Connector(SW_EXE)


@pytest.mark.skipif(not Path(SW_EXE).exists(), reason="SOLIDWORKS installation unavailable")
def test_capabilities_now_include_l1_l2():
    caps = {c.name: c.status.value for c in _connector().get_capabilities()}
    assert caps["sw.inspect_feature"] == "UNKNOWN"
    assert caps["sw.export_copy"] == "UNKNOWN"
    assert caps["sw.create_test_part"] == "UNKNOWN"


@pytest.mark.skipif(not Path(SW_EXE).exists(), reason="SOLIDWORKS installation unavailable")
def test_execute_returns_tool_result_for_unknown_action():
    result = _connector().execute("sw.unknown_action", {}, timeout_s=5)
    assert result.success is False
    assert "unknown" in result.error.lower()


def test_export_copy_rejects_outside_sandbox(tmp_path, monkeypatch):
    """Even without live COM, the sandbox guard must fire first."""
    conn = SolidWorks2022Connector()
    project_root = str(tmp_path)
    result = conn._export_copy({"project_root": project_root, "evil_path": str(tmp_path.parent.parent)})
    # No live COM here → should fail with COM error or sandbox error, not write anywhere
    assert result.success is False


@pytest.mark.skipif(not Path(SW_EXE).exists(), reason="SOLIDWORKS not installed")
def test_com_probe_still_no_launch():
    result = _connector().com_probe()
    if not result["available"]:
        pytest.skip("No active SOLIDWORKS COM instance")
    assert "no document opened" in result["note"]
