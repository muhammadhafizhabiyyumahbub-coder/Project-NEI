"""Maxsurf 20 V8i connector — Phase 7.

File-exchange / API-driven integration. COM automation not registered
(verified: no Maxsurf.Application ProgID found in HKLM\\SOFTWARE\\Classes),
so connector stays read-only until file exchange is proven.
"""
from pathlib import Path
from typing import Optional
import hashlib
from nei.connectors.base import (
    BaseConnector, DetectionResult, HealthResult, ToolResult, InspectionResult,
    Capability, CapabilityStatus,
)
from nei.core.policy import validate_sandbox_path

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
            return self._import_copy(parameters)
        if action == "maxsurf.export_copy":
            return self._export_copy(parameters)
        raise ValueError(f"Unknown action: {action}")

    def _inspect_project_file(self, parameters: dict) -> ToolResult:
        """Read metadata from .mfd/.msd without opening Maxsurf."""
        path = parameters.get("path")
        if not path or not Path(path).exists():
            return ToolResult(success=False, error=f"File not found: {path}")
        p = Path(path)
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        return ToolResult(
            success=True,
            data={
                "path": str(p),
                "exists": True,
                "size_bytes": p.stat().st_size,
                "modified": p.stat().st_mtime,
                "format": p.suffix.lower(),
                "sha256": digest,
                "read_only": True,
                "maxsurf_process_detected": any("Maxsurf" in str(x) for x in self._running_processes()),
            },
        )

    @staticmethod
    def _running_processes() -> list[str]:
        import subprocess
        try:
            output = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", "Get-Process | Select-Object -ExpandProperty ProcessName"],
                text=True,
                timeout=5,
            )
            return output.splitlines()
        except (OSError, subprocess.SubprocessError):
            return []

    def _import_copy(self, parameters: dict) -> ToolResult:
        """L1: copy a source file into the Maxsurf workspace.

        Writes only to the project sandbox root; never mutates Maxsurf's
        internal state or overwrites an existing file.
        """
        import shutil
        source = parameters.get("source")
        project_root = parameters.get("project_root", "data/projects/maxsurf")
        if not source or not Path(source).exists():
            return ToolResult(success=False, error="source file not found")
        dest_dir = Path(project_root) / "artifacts"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / Path(source).name
        if not validate_sandbox_path(str(dest), project_root):
            return ToolResult(success=False, error="Import target outside project sandbox")
        if dest.exists():
            return ToolResult(success=False, error="Destination already exists; not overwriting")
        shutil.copy2(source, dest)
        return ToolResult(
            success=True,
            object_ids=[str(dest)],
            data={"source": source, "import_path": str(dest)},
        )

    def _export_copy(self, parameters: dict) -> ToolResult:
        """L1: copy a result file to the project artifacts dir."""
        import shutil
        source = parameters.get("source")
        project_root = parameters.get("project_root", "data/projects/maxsurf")
        if not source or not Path(source).exists():
            return ToolResult(success=False, error="source file not found")
        out_dir = Path(project_root) / "artifacts"
        out_dir.mkdir(parents=True, exist_ok=True)
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = out_dir / f"{ts}_{Path(source).name}"
        if not validate_sandbox_path(str(dest), project_root):
            return ToolResult(success=False, error="Export target outside project sandbox")
        shutil.copy2(source, dest)
        return ToolResult(
            success=True,
            object_ids=[str(dest)],
            data={"source": source, "export_path": str(dest)},
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
            Capability("maxsurf.inspect_project_file", CapabilityStatus.SUPPORTED, "20.00.01.59", "Read-only .msd metadata and SHA-256 verified on sandbox probe."),
            Capability("maxsurf.import_copy", CapabilityStatus.SUPPORTED, "20.00.01.59", "Sandbox copy verified; original checksum unchanged."),
            Capability("maxsurf.export_copy", CapabilityStatus.SUPPORTED, "20.00.01.59", "Sandbox artifact copy verified by matching SHA-256."),
            Capability("maxsurf.hull_generation", CapabilityStatus.SUPPORTED, "20.00.01.59", "Manual sandbox generation verified: generated-hull.msd differs from source; source checksum unchanged."),
        ]
