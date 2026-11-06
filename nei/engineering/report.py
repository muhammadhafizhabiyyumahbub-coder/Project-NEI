"""Deterministic engineering report generation."""
import hashlib
import json
from datetime import datetime, timezone


def build_hull_report(*, task_id: str, hull: dict, preview: dict,
                      verification: dict | None = None,
                      gz_analysis: dict | None = None,
                      classification_baseline: dict | None = None) -> dict:
    """Build auditable JSON report; preview remains explicitly non-approval."""
    report = {
        "report_type": "hull_engineering_preview",
        "report_version": "1.1",
        "task_id": task_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": hull,
        "calculations": preview.get("calculations", {}),
        "loading_conditions": preview.get("calculations", {}).get("loading_conditions", []),
        "verification": verification or {},
        "gz_curve": gz_analysis or {},
        "classification_baseline": classification_baseline or {},
        "status": "NOT_FOR_APPROVAL",
        "limitations": [
            "Deterministic preview, not CAD-derived geometry",
            "No hydrostatic solver, trim-angle, MCT, or classification stability analysis",
            "No classification compliance determination",
        ],
    }
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"))
    report["report_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return report
