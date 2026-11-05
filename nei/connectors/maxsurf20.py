"""Maxsurf 20 V8i connector (Phase 7).

File-exchange / API-driven integration. COM automation not registered
(verified: no Maxsurf.Application ProgID found in HKLM\SOFTWARE\Classes),
so connector stays read-only until file exchange is proven.
"""
from pathlib import Path
from typing import Optional
from nei.connectors.base import (
    BaseConnector, DetectionResult, HealthResult, ToolResult, InspectionResult,
    Capability, CapabilityStatus,
)

class Maxsurf20Connector(BaseConnector):
    connector_id = "maxsurf20"
    name = "Maxsurf 20 V8i"

    def __init__(self, exe_path: Optional[str] = None):
        self.exe_path = Path(exe_path) if exe_path else None

    def _candidate_paths(self) -> list[Path]:
        if self.exe_path:
            return [self.exe_path]
        return [
            Path(r"C:\Program Files\Bentley\Engineering\Maxsurf 20 V8i\MaxsurfModeler64.exe"),
            Path(r"C:\Program Files\Bentley\Engineering\Maxsurf 20 V8i\Modeler64.exe"),
        ]

    def detect(self) -> DetectionResult:
        for p in self._candidate_paths():
            if p.exists():
                return DetectionResult(
                    detected=True,
                    exe_path=str(p),
                    version="20.00.01.59",
                    notes="Maxsurf Modeler found; COM/Automation unverified",
                )
        return DetectionResult(detected=False, notes="Maxsurf executable not found")

    def get_version(self) -> Optional[str]:
        det = self.detect()
        return det.version if det.detected else None

    def health_check(self) -> HealthResult:
        if not self.detect().detected:
            return HealthResult(healthy=False, detail="Software not installed")
        return HealthResult(healthy=True, detail="Executable found")

    def execute(self, action: str, parameters: dict, *, timeout_s: int) -> ToolResult:
        """File exchange actions; write guarded by policy (L1/L2 approval)."""
        if action == "maxsurf.inspect_project_file":
            return self._inspect_project_file(parameters)
        if action == "maxsurf.import_copy":
            return ToolResult(success=False, error="import_copy not yet proven")
        if action == "maxsurf.export_copy":
            return ToolResult(success=False, error="export_copy not yet proven")
        raise ValueError(f"Unknown action: {action}")

    def _inspect_project_file(self, parameters: dict) -> ToolResult:
        """Read metadata from .mfd/.msd without opening Maxsurf."""
        path = parameters.get("path")
        if not path or not Path(path).exists():
            return ToolResult(success=False, error=f"File not found: {path}")
        p = Path(path)
        return ToolResult(
            success=True,
            data={
                "path": str(p),
                "exists": True,
                "size_bytes": p.stat().st_size,
                "modified": p.stat().st_mtime,
                "format": p.suffix.lower(),
            },
        )

    def inspect(self, target: dict) -> InspectionResult:
        """Read-only inspection of objects or document state (mock until proven)."""
        return InspectionResult(objects=[], document={}, error="Maxsurf automation API not validated")

    def detach(self) -> None:
        pass

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("maxsurf.detect", CapabilityStatus.SUPPORTED, None, "Filesystem probe"),
            Capability("maxsurf.get_version", CapabilityStatus.SUPPORTED, None, "Executable version"),
            Capability("maxsurf.inspect_project_file", CapabilityStatus.UNKNOWN, None, "L0 read metadata"),
            Capability("maxsurf.import_copy", CapabilityStatus.UNKNOWN, None, "L1 file exchange"),
            Capability("maxsurf.export_copy", CapabilityStatus.UNKNOWN, None, "L1 file exchange"),
        ]
