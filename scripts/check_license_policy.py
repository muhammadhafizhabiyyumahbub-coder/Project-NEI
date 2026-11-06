"""Record CAD license/automation policy without reading license credentials.

NEI does not inspect, store, or bypass vendor license keys. This probe only
records installed software, observed automation registration, and the fact
that vendor license terms still require human/vendor confirmation.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENT = ROOT / "data" / "environment.json"
OUTPUT = ROOT / "data" / "license_policy.json"


def collect() -> dict:
    environment = json.loads(ENVIRONMENT.read_text(encoding="utf-8"))
    software = environment.get("software", {})
    probes = environment.get("probes", {})
    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "policy": "UNVERIFIED",
        "credentials_accessed": False,
        "automation_license_claimed": False,
        "software": {
            name: {
                "detected": record.get("detected", False),
                "version": record.get("version", "UNVERIFIED"),
                "license_status": record.get("license_status", "UNVERIFIED"),
            }
            for name, record in software.items()
            if isinstance(record, dict)
        },
        "observations": {
            "solidworks_com": probes.get("solidworks_com", "UNVERIFIED"),
            "maxsurf_com": probes.get("maxsurf_com", "UNVERIFIED"),
            "rhino_transport": probes.get("rhino_transport", "UNVERIFIED"),
        },
        "required_human_confirmation": [
            "Confirm SOLIDWORKS license edition and automation permission with vendor terms",
            "Confirm Rhino 6 license edition and RhinoPython automation permission",
            "Confirm Maxsurf license permits file exchange and manual sandbox workflows",
        ],
        "safety": [
            "No license key or credential was read or stored",
            "No license bypass was attempted",
            "UNVERIFIED is not an automation permission grant",
        ],
    }


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(collect(), indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
