"""Artifact store safety edge cases."""
import pytest
from nei.core.artifact_store import _sanitize_name, _safe_path
from pathlib import Path


def test_sanitize_name_rejects_traversal_sequences():
    with pytest.raises(ValueError, match="Invalid"):
        _sanitize_name("..", "test")
    with pytest.raises(ValueError, match="Invalid"):
        _sanitize_name("../evil", "test")
    with pytest.raises(ValueError, match="Invalid"):
        _sanitize_name("a/../b", "test")
    with pytest.raises(ValueError, match="Invalid"):
        _sanitize_name("a\\..\\b", "test")
    with pytest.raises(ValueError, match="Invalid"):
        _sanitize_name(".", "test")


def test_sanitize_name_rejects_separators():
    with pytest.raises(ValueError, match="Invalid"):
        _sanitize_name("a/b", "test")
    with pytest.raises(ValueError, match="Invalid"):
        _sanitize_name("a\\b", "test")


def test_safe_path_resolves_within_root(tmp_path, monkeypatch):
    from nei.core import artifact_store
    root = tmp_path / "artifacts"
    root.mkdir()
    monkeypatch.setattr(artifact_store, "ARTIFACTS_ROOT", root)
    path = _safe_path("task1", "file.txt")
    assert str(root) in str(path.resolve())


async def test_save_and_verify_artifact(tmp_path, monkeypatch):
    from nei.core import artifact_store
    root = tmp_path / "artifacts"
    root.mkdir()
    monkeypatch.setattr(artifact_store, "ARTIFACTS_ROOT", root)
    sha = await artifact_store.save_artifact("task1", "test.bin", b"hello")
    assert sha
    verified = await artifact_store.verify_artifact("task1", "test.bin", sha)
    assert verified is True
    wrong = await artifact_store.verify_artifact("task1", "test.bin", "wronghash")
    assert wrong is False


async def test_load_artifact_returns_bytes(tmp_path, monkeypatch):
    from nei.core import artifact_store
    root = tmp_path / "artifacts"
    root.mkdir()
    monkeypatch.setattr(artifact_store, "ARTIFACTS_ROOT", root)
    await artifact_store.save_artifact("task2", "data.bin", b"test data")
    loaded = await artifact_store.load_artifact("task2", "data.bin")
    assert loaded == b"test data"
    missing = await artifact_store.load_artifact("task2", "missing.bin")
    assert missing is None
