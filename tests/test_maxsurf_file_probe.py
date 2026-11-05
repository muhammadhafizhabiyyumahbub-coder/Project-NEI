from pathlib import Path

from nei.connectors.maxsurf20 import Maxsurf20Connector


def test_maxsurf_project_probe_is_read_only(tmp_path):
    source = tmp_path / "test.msd"
    source.write_bytes(b"maxsurf fixture")
    before = source.read_bytes()

    result = Maxsurf20Connector().execute(
        "maxsurf.inspect_project_file", {"path": str(source)}, timeout_s=5
    )

    assert result.success
    assert result.data["read_only"] is True
    assert result.data["sha256"]
    assert source.read_bytes() == before
