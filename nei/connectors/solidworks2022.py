"""Read-only SOLIDWORKS 2022 installation probe.

No COM activation, process launch, document opening, or file mutation.
"""
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

from nei.connectors.base import (
    BaseConnector, DetectionResult, HealthResult, ToolResult, InspectionResult,
    Capability, CapabilityStatus,
)


class SolidWorks2022Connector(BaseConnector):
    connector_id = "solidworks2022"
    name = "SOLIDWORKS 2022"

    def __init__(self, exe_path: Optional[str] = None):
        self.exe_path = Path(exe_path) if exe_path else None

    def _candidate_paths(self) -> list[Path]:
        if self.exe_path:
            return [self.exe_path]
        candidates = []
        configured = os.environ.get("NEI_SOLIDWORKS_EXE")
        if configured:
            candidates.append(Path(configured))
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

    def com_probe(self) -> dict:
        """Attach to already-running SOLIDWORKS only; never launch an instance."""
        try:
            import win32com.client
            app = win32com.client.GetActiveObject("SldWorks.Application")
            return {
                "available": True,
                "version": str(getattr(app, "RevisionNumber", "")) or None,
                "visible": bool(getattr(app, "Visible", False)),
                "note": "Attached to existing SOLIDWORKS instance; no document opened",
            }
        except Exception as exc:
            return {
                "available": False,
                "version": None,
                "visible": None,
                "error": type(exc).__name__,
                "note": "No active SOLIDWORKS COM automation object; no instance launched",
            }

    def inspect_active_document(self, operation: str = "document_info") -> dict:
        """Inspect current active document without opening or changing it."""
        if operation not in ("document_info", "features"):
            raise ValueError(f"Unknown inspection operation: {operation}")
        try:
            import win32com.client
            app = win32com.client.GetActiveObject("SldWorks.Application")
            doc = app.ActiveDoc
            if doc is None:
                return {"available": False, "error": "NO_ACTIVE_DOCUMENT"}
            if operation == "document_info":
                return {
                    "available": True,
                    "title": str(doc.GetTitle()),
                    "path": str(doc.GetPathName()),
                    "type": int(doc.GetType()),
                    "read_only": bool(doc.IsOpenedReadOnly()),
                }
            count = int(doc.GetFeatureCount())
            return {"available": True, "feature_count": count}
        except Exception as exc:
            return {"available": False, "error": type(exc).__name__}

    def get_capabilities(self) -> list[Capability]:
        version = self.get_version()
        tested = version or None
        return [
            Capability("sw.detect", CapabilityStatus.SUPPORTED, tested, "Filesystem probe; no COM"),
            Capability("sw.get_version", CapabilityStatus.SUPPORTED, tested, "Executable version resource"),
            Capability("sw.health_check", CapabilityStatus.SUPPORTED, tested, "Filesystem availability only"),
            Capability("sw.get_document_info", CapabilityStatus.UNKNOWN, tested, "Requires live COM/document probe"),
            Capability("sw.list_features", CapabilityStatus.UNKNOWN, tested, "Requires live COM/document probe"),
            Capability("sw.create_test_part", CapabilityStatus.UNSUPPORTED, tested, "Write operation deferred"),
        ]

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
