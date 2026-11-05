from nei.connectors.registry import registry, get_connector_class, discover_connectors


def test_registry_finds_known_connectors():
    ids = {cls.connector_id for cls in registry()}
    assert "rhino6" in ids
    assert "solidworks2022" in ids
    assert "maxsurf20" in ids


def test_get_connector_class_lookup():
    cls = get_connector_class("maxsurf20")
    assert cls is not None
    assert cls.connector_id == "maxsurf20"


def test_get_connector_class_unknown_returns_none():
    assert get_connector_class("nonexistent") is None
