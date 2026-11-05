from pathlib import Path
import hashlib

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


def test_maxsurf_import_export_preserves_checksum(tmp_path):
    source = tmp_path / "test.msd"
    source.write_bytes(b"maxsurf fixture content")
    original_sha = hashlib.sha256(source.read_bytes()).hexdigest()

    result_import = Maxsurf20Connector().execute(
        "maxsurf.import_copy",
        {"source": str(source), "project_root": str(tmp_path / "proj")},
        timeout_s=5,
    )
    assert result_import.success
    import_path = result_import.object_ids[0]

    result_export = Maxsurf20Connector().execute(
        "maxsurf.export_copy",
        {"source": import_path, "project_root": str(tmp_path / "proj")},
        timeout_s=5,
    )
    assert result_export.success
    export_sha = hashlib.sha256(Path(result_export.object_ids[0]).read_bytes()).hexdigest()
    assert original_sha == export_sha
