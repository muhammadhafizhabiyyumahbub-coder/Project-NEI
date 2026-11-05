"""Read-only SOLIDWORKS 2022 installation probe.

No COM activation, process launch, document opening, or file mutation.
"""
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

from nei.connectors.base import BaseConnector, DetectionResult, HealthResult, ToolResult, InspectionResult


class SolidWorks2022Connector(BaseConnector):
    connector_id = "solidworks2022"
    name = "SOLIDWORKS 2022"

    def _candidate_paths(self) -> list[Path]:
        candidates = []
        for env in ("PROGRAMFILES", "PROGRAMW6432"):
            root = os.environ.get(env)
            if root:
                candidates.append(Path(root) / "SOLIDWORKS Corp" / "SOLIDWORKS" / "SLDWORKS.exe")
        return candidates

    def detect(self) -> DetectionResult:
        for path in self._candidate_paths():
            if path.is_file():
                return DetectionResult(True, str(path), self._exe_version(path), "Executable found; COM not activated")
        return DetectionResult(False, notes="SOLIDWORKS 2022 executable not found; COM not activated")

    @staticmethod
    def _exe_version(path: Path) -> Optional[str]:
        if platform.system() != "Windows":
            return None
        try:
            command = f"(Get-Item -LiteralPath '{path}').VersionInfo.ProductVersion"
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True, text=True, timeout=15, check=False,
            )
            return result.stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            return None

    def get_version(self) -> Optional[str]:
        return self.detect().version

    def health_check(self) -> HealthResult:
        detection = self.detect()
        return HealthResult(detection.detected, detection.notes or "Executable unavailable")

    def execute(self, action: str, parameters: dict, *, timeout_s: int) -> ToolResult:
        return ToolResult(False, error="SOLIDWORKS connector is read-only in Phase 6")

    def inspect(self, target: dict) -> InspectionResult:
        detection = self.detect()
        return InspectionResult(
            document={"connector": self.connector_id, "detected": detection.detected,
                     "version": detection.version},
            error=None if detection.detected else detection.notes,
        )

    def detach(self) -> None:
        pass
