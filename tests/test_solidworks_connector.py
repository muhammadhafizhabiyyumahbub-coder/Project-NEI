from nei.connectors.solidworks2022 import SolidWorks2022Connector


def test_solidworks_probe_does_not_activate_com(monkeypatch):
    connector = SolidWorks2022Connector()
    monkeypatch.setattr(connector, "_candidate_paths", lambda: [])
    result = connector.detect()
    assert result.detected is False
    assert "COM" in (result.notes or "")


def test_solidworks_execute_read_action_returns_structured_result():
    """L0 inspect_feature without COM → structured error, not crash."""
    result = SolidWorks2022Connector().execute("sw.inspect_feature", {"feature_name": "Sketch1"}, timeout_s=5)
    assert result.success is False
    assert result.error  # some error string expected when no COM


def test_solidworks_health_when_missing(monkeypatch):
    connector = SolidWorks2022Connector()
    monkeypatch.setattr(connector, "_candidate_paths", lambda: [])
    health = connector.health_check()
    assert health.healthy is False
