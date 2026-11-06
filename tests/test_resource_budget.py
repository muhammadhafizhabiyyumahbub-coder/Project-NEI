import json
from pathlib import Path
from unittest.mock import patch

from scripts.measure_resource_budget import collect


def test_resource_budget_declares_serial_cad_policy():
    with patch("scripts.measure_resource_budget._process_memory", return_value=[]):
        result = collect()
    assert result["policy"]["max_concurrent_heavy_cad_apps"] == 1
    assert result["software_processes"] == []
    assert "8GB" in result["policy"]["reason"]


def test_resource_budget_output_is_json(tmp_path, monkeypatch):
    import scripts.measure_resource_budget as module
    output = tmp_path / "budget.json"
    monkeypatch.setattr(module, "OUTPUT", output)
    with patch.object(module, "_process_memory", return_value=[]):
        assert module.main() == 0
    loaded = json.loads(output.read_text())
    assert loaded["policy"]["max_concurrent_heavy_cad_apps"] == 1
