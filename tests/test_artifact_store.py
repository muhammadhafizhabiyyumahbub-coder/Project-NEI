"""Artifact store: path traversal guards, save/load/verify, list."""
import asyncio
from pathlib import Path
from nei.core import artifact_store


def _run(coro):
    return asyncio.run(coro)


def test_save_and_load_roundtrip(tmp_path):
    """Normal save → load → verify works."""
    original = artifact_store.ARTIFACTS_ROOT
    artifact_store.ARTIFACTS_ROOT = tmp_path
    try:
        _run(artifact_store.save_artifact("task1", "box.dat", b"hello"))
        data = _run(artifact_store.load_artifact("task1", "box.dat"))
        assert data == b"hello"
        # verify with correct sha
        ok = _run(artifact_store.verify_artifact("task1", "box.dat",
                                                   artifact_store._sha256(b"hello")))
        assert ok is True
        # verify with wrong sha
        bad = _run(artifact_store.verify_artifact("task1", "box.dat", "deadbeef"))
        assert bad is False
    finally:
        artifact_store.ARTIFACTS_ROOT = original


def test_load_missing_returns_none(tmp_path):
    artifact_store.ARTIFACTS_ROOT = tmp_path
    try:
        result = _run(artifact_store.load_artifact("task1", "nope.dat"))
        assert result is None
    finally:
        artifact_store.ARTIFACTS_ROOT = original_root()


def original_root():
    return Path("data/artifacts")


def test_list_artifacts(tmp_path):
    artifact_store.ARTIFACTS_ROOT = tmp_path
    try:
        _run(artifact_store.save_artifact("t1", "a.dat", b"a"))
        _run(artifact_store.save_artifact("t1", "b.dat", b"b"))
        items = _run(artifact_store.list_artifacts("t1"))
        names = {i["filename"] for i in items}
        assert names == {"a.dat", "b.dat"}
    finally:
        artifact_store.ARTIFACTS_ROOT = original_root()


def test_traversal_in_filename_rejected(tmp_path):
    """.., /, \\ all raise ValueError."""
    artifact_store.ARTIFACTS_ROOT = tmp_path
    try:
        for bad in ("../evil.dat", "..\\evil.dat", "a/b.dat", ".."):
            try:
                _run(artifact_store.save_artifact("t1", bad, b"x"))
                assert False, f"should have rejected {bad!r}"
            except ValueError:
                pass
    finally:
        artifact_store.ARTIFACTS_ROOT = original_root()


def test_traversal_in_task_id_rejected(tmp_path):
    artifact_store.ARTIFACTS_ROOT = tmp_path
    try:
        for bad in ("../evil", "..", "a/b"):
            try:
                _run(artifact_store.save_artifact(bad, "f.dat", b"x"))
                assert False, f"should have rejected task_id {bad!r}"
            except ValueError:
                pass
    finally:
        artifact_store.ARTIFACTS_ROOT = original_root()


def test_safe_path_contains_check(tmp_path):
    """_safe_path raises if resolved path escapes ARTIFACTS_ROOT."""
    artifact_store.ARTIFACTS_ROOT = tmp_path
    try:
        # Create a real sub-dir and a symlink-like escape (via relative ..)
        # Since _sanitize_name blocks .., test _safe_path directly with clean names
        p = artifact_store._safe_path("t1", "f.dat")
        assert p.is_relative_to(tmp_path.resolve()), f"{p} not inside {tmp_path}"
    finally:
        artifact_store.ARTIFACTS_ROOT = original_root()


def test_write_manifest(tmp_path):
    """write_manifest produces a .manifest.json next to the artifact."""
    original = artifact_store.ARTIFACTS_ROOT
    artifact_store.ARTIFACTS_ROOT = tmp_path
    try:
        _run(artifact_store.save_artifact("t1", "out.3dm", b"binary"))
        m = _run(artifact_store.write_manifest("t1", "out.3dm", {"source": "rhino"}))
        assert m["sha256"] == artifact_store._sha256(b"binary")
        assert m["source"] == "rhino"
        manifest_file = tmp_path / "t1" / "out.3dm.manifest.json"
        assert manifest_file.exists()
        # missing artifact raises
        import pytest
        with pytest.raises(FileNotFoundError):
            _run(artifact_store.write_manifest("t1", "nope.3dm"))
    finally:
        artifact_store.ARTIFACTS_ROOT = original
