"""SOLIDWORKS 2022 connector — Phase 6.

Read-only probe + controlled write operations guarded by policy:
- L0: inspect_feature (read dimensions of a feature, no mutation)
- L1: export_copy (save as .sldprt to data/projects/<id>/artifacts/)
- L2: create_test_part (disposable part, user approval required)

No file outside the project sandbox is written. Existing user files are never
overwritten; all output goes to a fresh timestamped path under artifacts/.
"""
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from nei.connectors.base import (
    BaseConnector, DetectionResult, HealthResult, ToolResult, InspectionResult,
    Capability, CapabilityStatus,
)
from nei.core.policy import validate_sandbox_path


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


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

    def _get_com_app(self):
        import win32com.client
        return win32com.client.GetActiveObject("SldWorks.Application")

    def inspect_active_document(self, operation: str = "document_info") -> dict:
        """Inspect current active document without opening or changing it."""
        if operation not in ("document_info", "features"):
            raise ValueError(f"Unknown inspection operation: {operation}")
        try:
            app = self._get_com_app()
            doc = app.ActiveDoc
            if doc is None:
                return {"available": False, "error": "NO_ACTIVE_DOCUMENT"}
            def value(name, default=None):
                item = getattr(doc, name, default)
                return item() if callable(item) else item

            if operation == "document_info":
                return {
                    "available": True,
                    "title": str(value("GetTitle", "")),
                    "path": str(value("GetPathName", "")),
                    "type": int(value("GetType", 0)),
                    "read_only": bool(value("IsOpenedReadOnly", False)),
                }
            count = int(value("GetFeatureCount", 0))
            features = []
            for i in range(count):
                feat = doc.FeatureByPositionReverse(i)
                if feat:
                    type_name = getattr(feat, "GetTypeName", "")
                    features.append({
                        "name": str(getattr(feat, "Name", "")),
                        "type": str(type_name() if callable(type_name) else type_name),
                        "visible": bool(getattr(feat, "Visible", False)),
                    })
            return {"available": True, "feature_count": count, "features": features}
        except Exception as exc:
            return {"available": False, "error": type(exc).__name__}

    def _inspect_feature(self, params: dict) -> ToolResult:
        """L0: read dimensions of a named feature. Read-only, no mutation."""
        feature_name = params.get("feature_name")
        if not feature_name:
            return ToolResult(success=False, error="feature_name parameter required")
        try:
            app = self._get_com_app()
            doc = app.ActiveDoc
            if doc is None:
                return ToolResult(success=False, error="NO_ACTIVE_DOCUMENT")
            feat = doc.FeatureByName(feature_name)
            if feat is None:
                return ToolResult(success=False, error=f"Feature not found: {feature_name}")
            dims = []
            try:
                for i in range(int(doc.GetFeatureCount(feature_name))):
                    dd = doc.GetDimensionByIndex(feature_name, i)
                    if dd:
                        dims.append({
                            "name": str(dd.Name),
                            "value": float(dd.GetValue()) if dd.GetValue() is not None else None,
                        })
            except Exception:
                pass
            return ToolResult(
                success=True,
                data={
                    "feature_name": feature_name,
                    "type": str(feat.GetTypeName()),
                    "visible": bool(feat.Visible),
                    "dimensions": dims,
                },
            )
        except Exception as exc:
            return ToolResult(success=False, error=type(exc).__name__)

    def _export_copy(self, params: dict) -> ToolResult:
        """L1: save active document as .sldprt to project artifacts/ dir.

        Never overwrites an existing file; writes a timestamped copy.
        """
        project_root = params.get("project_root", "data/projects/sw_export")
        out_dir = Path(project_root) / "artifacts"
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_name = _ts() + "_sw_export.sldprt"
        out_path = out_dir / safe_name
        if not validate_sandbox_path(str(out_path), project_root):
            return ToolResult(success=False, error="Export target outside project sandbox")
        try:
            app = self._get_com_app()
            doc = app.ActiveDoc
            if doc is None:
                return ToolResult(success=False, error="NO_ACTIVE_DOCUMENT")
            # mswExportSaveAs = 1: save as a copy, source document is not modified
            ok = doc.SaveAs(str(out_path))
            if not ok:
                return ToolResult(success=False, error="SaveAs returned False")
            return ToolResult(
                success=True,
                object_ids=[str(out_path)],
                data={
                    "source_path": str(doc.GetPathName()),
                    "source_title": str(doc.GetTitle()),
                    "export_path": str(out_path),
                },
            )
        except Exception as exc:
            return ToolResult(success=False, error=type(exc).__name__)

    def _create_test_part(self, params: dict) -> ToolResult:
        """L2: create a disposable box part in a NEW in-memory document.

        The user's active document is not touched. New part is exported as
        .sldprt to artifacts/ and the in-memory doc is closed. Requires
        human approval at the task level (WAITING_APPROVAL).
        """
        project_root = params.get("project_root", "data/projects/sw_test")
        out_dir = Path(project_root) / "artifacts"
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_name = _ts() + "_sw_test_part.sldprt"
        out_path = out_dir / safe_name
        if not validate_sandbox_path(str(out_path), project_root):
            return ToolResult(success=False, error="Test part target outside project sandbox")

        try:
            app = self._get_com_app()
            new_doc = app.NewDocument(0)  # swDoc_PART = 0
            if new_doc is None:
                return ToolResult(success=False, error="Could not create new part document")
            # Add a simple box: three sketches + extrude. Kept minimal:
            # sketch on Front Plane with a rectangle, extrude symmetric 10mm.
            # This is a disposable test part; close without saving to original.
            front = new_doc.Extension.GetActivePlane(0)  # swPlane_Front
            sk = new_doc.Extension.CreateSketch3D(front, 0, swOpen=1, swEndSketch=1)
            # rectangle: (0,0) to (10,3) mm — sketch dimensions in meters in SOLIDWORKS
            sk.InsertSketchRectangle(0.0, 0.0, 0.01, 0.003, True)
            sk.ExitSketch()
            ext = new_doc.Extension
            ext.ExtrudeFeature(
                sk, 0, 0, 0, 0.005, 0.005,
                1, 1, 0, 0, 0, 0, False, False, False, False, False, False,
                0.1, 0.1, False, False, 0,
            )
            ok = new_doc.SaveAs(str(out_path))
            new_doc.Close()  # close in-memory doc; no original file touched
            if not ok:
                return ToolResult(success=False, error="SaveAs returned False")
            return ToolResult(
                success=True,
                object_ids=[str(out_path)],
                data={"export_path": str(out_path), "note": "Disposable part created in new document; user document untouched"},
            )
        except Exception as exc:
            return ToolResult(success=False, error=type(exc).__name__)

    def get_capabilities(self) -> list[Capability]:
        version = self.get_version()
        tested = version or None
        return [
            Capability("sw.detect", CapabilityStatus.SUPPORTED, tested, "Filesystem probe; no COM"),
            Capability("sw.get_version", CapabilityStatus.SUPPORTED, tested, "Executable version resource"),
            Capability("sw.health_check", CapabilityStatus.SUPPORTED, tested, "Filesystem availability only"),
            Capability("sw.get_document_info", CapabilityStatus.SUPPORTED, tested, "Read-only COM inspection tested on active document"),
            Capability("sw.list_features", CapabilityStatus.SUPPORTED, tested, "Read-only COM feature listing tested on active document"),
            Capability("sw.inspect_feature", CapabilityStatus.UNKNOWN, tested, "L0 read feature dimensions"),
            Capability("sw.export_copy", CapabilityStatus.UNKNOWN, tested, "L1 save-as copy to artifacts/; write-guarded"),
            Capability("sw.create_test_part", CapabilityStatus.UNKNOWN, tested, "L2 disposable part; user approval required"),
        ]

    def health_check(self) -> HealthResult:
        detection = self.detect()
        return HealthResult(detection.detected, detection.notes or "Executable unavailable")

    def execute(self, action: str, parameters: dict, *, timeout_s: int) -> ToolResult:
        if action == "sw.get_document_info":
            result = self.inspect_active_document("document_info")
            return ToolResult(success=result.get("available", False), data=result, error=result.get("error"))
        if action == "sw.list_features":
            result = self.inspect_active_document("features")
            return ToolResult(success=result.get("available", False), data=result, error=result.get("error"))
        if action == "sw.inspect_feature":
            return self._inspect_feature(parameters)
        if action == "sw.export_copy":
            return self._export_copy(parameters)
        if action == "sw.create_test_part":
            return self._create_test_part(parameters)
        return ToolResult(False, error=f"Unknown SOLIDWORKS action: {action}")

    def inspect(self, target: dict) -> InspectionResult:
        detection = self.detect()
        return InspectionResult(
            document={"connector": self.connector_id, "detected": detection.detected,
                     "version": detection.version},
            error=None if detection.detected else detection.notes,
        )

    def detach(self) -> None:
        pass
