import json
from unittest.mock import patch

from scripts.check_license_policy import collect, main


def test_license_policy_never_claims_automation_permission(tmp_path, monkeypatch):
    environment = tmp_path / "environment.json"
    output = tmp_path / "license_policy.json"
    environment.write_text(json.dumps({
        "software": {"solidworks2022": {"detected": True, "version": "30.1"}},
        "probes": {"solidworks_com": "AVAILABLE"},
    }))
    import scripts.check_license_policy as module
    monkeypatch.setattr(module, "ENVIRONMENT", environment)
    monkeypatch.setattr(module, "OUTPUT", output)
    result = collect()
    assert result["policy"] == "UNVERIFIED"
    assert result["automation_license_claimed"] is False
    assert result["credentials_accessed"] is False
    assert result["software"]["solidworks2022"]["license_status"] == "UNVERIFIED"


def test_license_policy_writes_json(tmp_path, monkeypatch):
    environment = tmp_path / "environment.json"
    output = tmp_path / "license_policy.json"
    environment.write_text(json.dumps({"software": {}, "probes": {}}))
    import scripts.check_license_policy as module
    monkeypatch.setattr(module, "ENVIRONMENT", environment)
    monkeypatch.setattr(module, "OUTPUT", output)
    assert main() == 0
    assert json.loads(output.read_text())["policy"] == "UNVERIFIED"
