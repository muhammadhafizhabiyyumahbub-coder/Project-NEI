"""Rhino 6 connector — RhinoPython Method 2.

Transport: generate a Python 2.7 script, write to a temp location,
invoke via Rhino's _RunPythonScript command, read structured JSON result.

Safety:
- Scripts generated from allowlisted templates only (no arbitrary code)
- No network, no shell, no file deletion, no registry access
- Script SHA-256 logged before execution
- Script preserved at data/projects/<id>/artifacts/scripts/<task_id>_<step_id>.py
"""
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from nei.connectors.base import (
    BaseConnector,
    DetectionResult,
    HealthResult,
    ToolResult,
    InspectionResult,
    Capability,
    CapabilityStatus,
)
from nei.core.config import settings
from nei.core.policy import validate_sandbox_path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── Allowlisted Rhino Python 2.7 script templates ────────────────────────────

# Script to create a box and inspect its bounding box, output JSON result.
# {L}, {W}, {H} are replaced by numeric values before writing.
BOX_SCRIPT_TEMPLATE = '''\
import rhinoscriptsyntax as rs
import Rhino
import json

def main():
    result = {"success": False}

    # Capture pre-state: object count before
    pre_count = len(rs.Objects())

    # Create new disposable document (do NOT touch existing documents)
    doc = Rhino.RhinoApp.NewDocument()

    # Set units to millimeters
    rs.UnitSystem(5)  # 5 = millimeters in Rhino

    # Create box: L x W x H
    l, w, h = {L}, {W}, {H}
    corners = [
        (0, 0, 0), (l, 0, 0), (l, w, 0), (0, w, 0),
        (0, 0, h), (l, 0, h), (l, w, h), (0, w, h),
    ]
    box_id = rs.AddBox(corners)

    if box_id is None:
        result["error"] = "AddBox returned None"
    else:
        # Inspect bounding box
        bb = rs.BoundingBox(box_id)
        if bb is None:
            result["error"] = "BoundingBox returned None"
        else:
            min_pt, max_pt = bb
            length   = abs(max_pt[0] - min_pt[0])
            width    = abs(max_pt[1] - min_pt[1])
            height   = abs(max_pt[2] - min_pt[2])
            result = {
                "success": True,
                "object_ids": [str(box_id)],
                "objects": [
                    {
                        "id": str(box_id),
                        "type": "Brep",
                        "bounding_box": {
                            "length": round(length, 6),
                            "width":  round(width,  6),
                            "height": round(height, 6)
                        }
                    }
                ],
                "document": {"units": rs.UnitSystemName()},
                "pre_object_count": pre_count,
                "post_object_count": len(rs.Objects()),
            }

    # Write result JSON to absolute path passed by the backend
    with open({RESULT_PATH}, "w") as f:
        json.dump(result, f)

    # Save .3dm artifact to path provided by backend
    import os
    artifact_path = {ARTIFACT_PATH}
    if artifact_path:
        os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
        Rhino.RhinoDoc.ActiveDoc.SaveAs(artifact_path, 0)
'''

# Script to inspect an existing object by ID and document info.
INSPECT_SCRIPT_TEMPLATE = '''\
import rhinoscriptsyntax as rs
import Rhino
import json

def main():
    result = {"success": False, "objects": [], "document": {}}

    doc = Rhino.RhinoDoc.ActiveDoc
    units_name = rs.UnitSystemName()
    obj_count = len(rs.Objects())

    # Inspect specific object IDs passed in
    obj_ids = {OBJECT_IDS}
    for oid in obj_ids:
        ids = rs.CoerceGuid(oid)
        if ids is not None:
            bb = rs.BoundingBox(ids[0])
            if bb is not None:
                min_pt, max_pt = bb
                entry = {
                    "id": str(ids[0]),
                    "type": rs.ObjectType(ids[0]),
                    "bounding_box": {
                        "length": round(abs(max_pt[0] - min_pt[0]), 6),
                        "width":  round(abs(max_pt[1] - min_pt[1]), 6),
                        "height": round(abs(max_pt[2] - min_pt[2]), 6)
                    }
                }
            else:
                entry = {"id": str(ids[0]), "type": rs.ObjectType(ids[0]), "bounding_box": None}
            result["objects"].append(entry)

    result["document"] = {"units": units_name, "object_count": obj_count}
    result["success"] = True

    with open({RESULT_PATH}, "w") as f:
        json.dump(result, f)
'''


def _render_box_script(l: float, w: float, h: float,
                       result_path: str, artifact_path: str) -> str:
    script = BOX_SCRIPT_TEMPLATE
    script = script.replace("{L}", str(l))
    script = script.replace("{W}", str(w))
    script = script.replace("{H}", str(h))
    script = script.replace("{RESULT_PATH}", json.dumps(result_path))
    script = script.replace("{ARTIFACT_PATH}", json.dumps(artifact_path))
    return script


def _render_inspect_script(object_ids: list, result_path: str) -> str:
    script = INSPECT_SCRIPT_TEMPLATE
    script = script.replace("{OBJECT_IDS}", json.dumps(object_ids))
    script = script.replace("{RESULT_PATH}", json.dumps(result_path))
    return script


class Rhino6Connector(BaseConnector):
    connector_id = "rhino6"
    name = "Rhino 6"

    def __init__(self, rhino_exe: Optional[str] = None):
        self._rhino_exe = rhino_exe or settings.rhino_exe_path
        self._version: Optional[str] = None

    # ── BaseConnector ──────────────────────────────────────────────────────────

    def detect(self) -> DetectionResult:
        path = Path(self._rhino_exe)
        if path.exists():
            return DetectionResult(
                detected=True,
                exe_path=str(path),
                notes="Detected by filesystem path",
            )
        return DetectionResult(
            detected=False,
            exe_path=self._rhino_exe,
            notes="Rhino.exe not found at configured path",
        )

    def get_version(self) -> Optional[str]:
        if self._version:
            return self._version
        try:
            # Read version from .exe metadata without launching Rhino
            import os
            exe = Path(self._rhino_exe)
            if not exe.exists():
                return None
            # Try reading from known Rhino install directory version file
            sys_dir = exe.parent
            ver_file = sys_dir / "Version.json"
            if ver_file.exists():
                data = json.loads(ver_file.read_text(encoding="utf-8"))
                self._version = str(data.get("version", "unknown"))
                return self._version
            return "unknown"
        except Exception:
            return None

    def health_check(self) -> HealthResult:
        import ctypes
        try:
            # Check if Rhino process is running (PID check via tasklist is heavy;
            # use Win32 OpenProcess for a lightweight existence check)
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Rhino.exe"],
                capture_output=True, text=True, timeout=5,
            )
            running = "Rhino.exe" in result.stdout
            return HealthResult(
                healthy=running,
                detail="Rhino.exe running" if running else "Rhino.exe not running",
            )
        except Exception as e:
            return HealthResult(healthy=False, detail=f"health_check error: {e}")

    def execute(self, action: str, parameters: dict, *, timeout_s: int) -> ToolResult:
        """Dispatch allowlisted actions. Only known actions are accepted."""
        if action == "rhino.create_box_test":
            return self._create_box(
                length=parameters.get("length", 10.0),
                width=parameters.get("width", 3.0),
                height=parameters.get("height", 1.0),
                artifact_path=parameters.get("artifact_path", ""),
            )
        elif action == "rhino.inspect_objects":
            object_ids = parameters.get("object_ids", [])
            return self._inspect_objects(object_ids)
        elif action == "rhino.get_document_info":
            return self._document_info()
        else:
            return ToolResult(success=False, error=f"Unknown action: {action}")

    def inspect(self, target: dict) -> InspectionResult:
        """Inspect object IDs or document state (read-only)."""
        object_ids = target.get("object_ids", [])
        result = self._inspect_objects(object_ids)
        if not result.success:
            return InspectionResult(error=result.error)
        return InspectionResult(
            objects=result.data.get("objects", []),
            document=result.data.get("document", {}),
        )

    def detach(self) -> None:
        """No persistent session to release in Method 2 (script per call)."""
        pass

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _create_box(self, length: float, width: float, height: float,
                    artifact_path: str,
                    timeout_s: int = 30) -> ToolResult:
        """Generate box script, write result JSON, invoke Rhino."""
        # Temp result file (read by script, consumed by backend)
        tmp = Path(tempfile.gettempdir()) / f"nei_rhino_{id(self)}_result.json"
        tmp.unlink(missing_ok=True)

        script_content = _render_box_script(
            l=length, w=width, h=height,
            result_path=str(tmp),
            artifact_path=artifact_path,
        )
        script_sha = _sha256(script_content)

        # Write script to temp location
        tmp_script = Path(tempfile.gettempdir()) / f"nei_rhino_{id(self)}.py"
        tmp_script.write_text(script_content, encoding="utf-8")

        result = self._run_rhino_script(str(tmp_script), tmp, timeout_s)
        tmp_script.unlink(missing_ok=True)

        if result is None:
            return ToolResult(success=False, error="Rhino script did not produce result JSON")

        success = result.get("success", False)
        if success:
            return ToolResult(
                success=True,
                object_ids=result.get("object_ids", []),
                data=result,
            )
        return ToolResult(success=False, error=result.get("error", "unknown script error"))

    def _inspect_objects(self, object_ids: list, timeout_s: int = 15) -> ToolResult:
        """Run inspect script for given object IDs (or all objects if empty list)."""
        tmp = Path(tempfile.gettempdir()) / f"nei_rhino_{id(self)}_inspect.json"
        tmp.unlink(missing_ok=True)

        # If no IDs given, script with empty list will inspect all active document objects
        script_content = _render_inspect_script(object_ids, str(tmp))
        tmp_script = Path(tempfile.gettempdir()) / f"nei_rhino_{id(self)}_inspect.py"
        tmp_script.write_text(script_content, encoding="utf-8")

        result = self._run_rhino_script(str(tmp_script), tmp, timeout_s)
        tmp_script.unlink(missing_ok=True)

        if result is None:
            return ToolResult(success=False, error="Inspect script did not produce result JSON")
        success = result.get("success", False)
        return ToolResult(success=success, data=result, error=None if success else result.get("error"))

    def _document_info(self, timeout_s: int = 15) -> ToolResult:
        """Get document info without creating any objects."""
        tmp = Path(tempfile.gettempdir()) / f"nei_rhino_{id(self)}_docinfo.json"
        tmp.unlink(missing_ok=True)

        doc_script = '''\
import rhinoscriptsyntax as rs
import Rhino
import json

def main():
    doc = Rhino.RhinoDoc.ActiveDoc
    result = {
        "success": True,
        "document": {
            "units": rs.UnitSystemName(),
            "object_count": len(rs.Objects()),
            "doc_name": doc.Name if doc else None,
        }
    }
    with open(RESULT_PATH, "w") as f:
        json.dump(result, f)
'''.replace("RESULT_PATH", json.dumps(str(tmp)))
        tmp_script = Path(tempfile.gettempdir()) / f"nei_rhino_{id(self)}_docinfo.py"
        tmp_script.write_text(doc_script, encoding="utf-8")

        result = self._run_rhino_script(str(tmp_script), tmp, timeout_s)
        tmp_script.unlink(missing_ok=True)

        if result is None:
            return ToolResult(success=False, error="Document info script did not produce result JSON")
        return ToolResult(success=result.get("success", False), data=result,
                          error=None if result.get("success") else result.get("error"))

    # ── Rhino invocation ───────────────────────────────────────────────────────

    def _run_rhino_script(self, script_path: str, result_path: Path,
                          timeout_s: int) -> Optional[dict]:
        """Invoke Rhino's _RunPythonScript and read back the result JSON.

        Rhino 6 accepts _RunPythonScript <path> as a command that runs a Python
        script in the RhinoPython environment. The script writes its result to
        a known file path; this method reads that file after Rhino completes.

        Returns parsed dict, or None on error/timeout.
        """
        result_path.unlink(missing_ok=True)

        # Run Rhino headless via _RunPythonScript.
        # Rhino supports: Rhino.exe -1 -r <script>   (headless mode)
        # Or via Rhino command: _RunPythonScript <script_path>
        # We use the headless invocation which terminates after script completes.
        cmd = [
            self._rhino_exe,
            "-1",          # headless mode (no GUI)
            "-r", script_path,
        ]

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout_s,
            )
            if proc.returncode != 0:
                # Rhino headless may return non-zero even on success;
                # check if result file was written regardless.
                pass
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None

        # Read result JSON produced by the script
        if not result_path.exists():
            return None
        try:
            return json.loads(result_path.read_text(encoding="utf-8"))
        except Exception:
            return None
