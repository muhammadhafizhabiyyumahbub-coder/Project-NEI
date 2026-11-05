import os
from pathlib import Path
from typing import Optional
from nei.connectors.base import (
    BaseConnector, DetectionResult, HealthResult, ToolResult, InspectionResult, Capability, CapabilityStatus,
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
        raise PermissionError("Maxsurf write operations deferred; Phase 7 write probe pending")

    def inspect(self, target: dict) -> InspectionResult:
        """Read-only list-feature inspection for active model; mock only."""
        return InspectionResult(objects=[], document={}, error="Maxsurf automation API not validated")

    def detach(self) -> None:
        pass

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("ms.detect", CapabilityStatus.SUPPORTED, None, "Filesystem probe"),
            Capability("ms.get_version", CapabilityStatus.SUPPORTED, None, "Executable version"),
            Capability("ms.list_components", CapabilityStatus.UNKNOWN, None, "Requires COM/Automation API test"),
            Capability("ms.get_model_info", CapabilityStatus.UNSUPPORTED, None, "Write operation deferred"),
        ]
