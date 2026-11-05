from nei.connectors.solidworks2022 import SolidWorks2022Connector


def test_solidworks_probe_does_not_activate_com(monkeypatch):
    connector = SolidWorks2022Connector()
    monkeypatch.setattr(connector, "_candidate_paths", lambda: [])
    result = connector.detect()
    assert result.detected is False
    assert "COM" in (result.notes or "")


def test_solidworks_execute_is_read_only():
    result = SolidWorks2022Connector().execute("sw.create_test_part", {}, timeout_s=1)
    assert result.success is False
    assert "read-only" in (result.error or "")


def test_solidworks_health_when_missing(monkeypatch):
    connector = SolidWorks2022Connector()
    monkeypatch.setattr(connector, "_candidate_paths", lambda: [])
    health = connector.health_check()
    assert health.healthy is False
