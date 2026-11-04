"""Live Rhino CLI integration test.

Only runs when NEI_LIVE_RHINO=1. Skipped by default (no Rhino in CI).
Tests the candidate C1 form:
    Rhino.exe /nosplash /notemplate /runscript=_-RunPythonScript <path> _-Exit
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

from nei.connectors.rhino6 import Rhino6Connector

LIVE = os.environ.get("NEI_LIVE_RHINO") == "1"


@pytest.mark.skipif(not LIVE, reason="NEI_LIVE_RHINO not set — skipping live test")
def test_live_cli_box_test():
    """Run create_box_test against real Rhino and verify result JSON on disk."""
    from nei.core.config import settings
    conn = Rhino6Connector(rhino_exe=settings.rhino_exe_path)
    det = conn.detect()
    if not det.detected:
        pytest.skip(f"Rhino not found at {det.exe_path}")

    with tempfile.TemporaryDirectory(prefix="nei_rhino_live_") as tmpdir:
        result_path = Path(tmpdir) / "result.json"
        script_path = Path(tmpdir) / "box.py"
        script_path.write_text(
            BOX_TEST_PY2, encoding="utf-8"
        ).replace(BOX_TEST_PY2, BOX_TEST_PY2.replace("RESULT_PATH", repr(str(result_path))))

        result = conn.execute(
            "rhino.create_box_test",
            {"length": 10.0, "width": 3.0, "height": 1.0},
            timeout_s=60,
        )
        assert result.success is True, f"live box test failed: {result.error}"
        bb = result.data["objects"][0]["bounding_box"]
        assert abs(bb["length"] - 10.0) < 1e-6
        assert abs(bb["width"] - 3.0) < 1e-6
        assert abs(bb["height"] - 1.0) < 1e-6
        assert result.data["document"]["units"]


# Python 2.7-compatible box script (matches BOX_SCRIPT_TEMPLATE).
# {RESULT_PATH} is substituted at test-run time.
BOX_TEST_PY2 = '''\
import rhinoscriptsyntax as rs
import Rhino
import Rhino.Geometry as rg
import json
import os

def main():
    result = {"success": False}
    doc = Rhino.RhinoDoc.ActiveDoc
    if doc is None:
        result["error"] = "No active document"
    else:
        l, w, h = 10.0, 3.0, 1.0
        corners = [
            rg.Point3d(0,0,0), rg.Point3d(l,0,0),
            rg.Point3d(l,w,0), rg.Point3d(0,w,0),
            rg.Point3d(0,0,h), rg.Point3d(l,0,h),
            rg.Point3d(l,w,h), rg.Point3d(0,w,h),
        ]
        box_id = rs.AddBox(corners)
        if box_id is None:
            result["error"] = "AddBox returned None"
        else:
            pts = rs.BoundingBox(box_id)
            xs = [p.X for p in pts]
            ys = [p.Y for p in pts]
            zs = [p.Z for p in pts]
            result = {
                "success": True,
                "object_ids": [str(box_id)],
                "objects": [{
                    "id": str(box_id),
                    "type": "Brep",
                    "bounding_box": {
                        "length": round(max(xs)-min(xs), 6),
                        "width":  round(max(ys)-min(ys), 6),
                        "height": round(max(zs)-min(zs), 6),
                    },
                }],
                "document": {"units": rs.UnitSystemName(), "object_count": len(rs.Objects())},
            }
    with open(RESULT_PATH, "w") as f:
        json.dump(result, f)

main()
'''
