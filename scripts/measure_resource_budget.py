"""Measure local resource budget without launching CAD applications."""
from __future__ import annotations
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "resource_budget.json"


def _process_memory(names: list[str]) -> list[dict[str, object]]:
    if platform.system() != "Windows":
        return []
    wanted = {name.lower().removesuffix(".exe") for name in names}
    try:
        command = (
            "Get-Process | Select-Object ProcessName,Id,WorkingSet64 | "
            "ConvertTo-Json -Compress"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True, text=True, timeout=10, check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        rows = json.loads(result.stdout)
        if isinstance(rows, dict):
            rows = [rows]
        return [
            {"process": row.get("ProcessName"), "pid": row.get("Id"),
             "working_set_bytes": row.get("WorkingSet64", 0)}
            for row in rows
            if str(row.get("ProcessName", "")).lower() in wanted
        ]
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return []


def collect() -> dict[str, object]:
    processes = _process_memory(["python", "Rhino", "SLDWORKS", "MaxsurfModeler64"])
    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "logical_cpus": os.cpu_count(),
        "software_processes": processes,
        "policy": {
            "max_concurrent_heavy_cad_apps": 1,
            "reason": "8GB RAM host; serialize Rhino, SOLIDWORKS, and Maxsurf",
        },
        "limitations": [
            "Working-set values describe processes present at collection time",
            "No CAD application was launched",
            "Browser memory is not included unless its process name is added",
        ],
    }


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(collect(), indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
