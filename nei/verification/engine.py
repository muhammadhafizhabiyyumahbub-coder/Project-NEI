"""Verification engine orchestrator.

Runs postcondition checks against connector results.
"""
from typing import Any
from nei.verification.record import VerificationRecord, VerificationCheck
from nei.verification.postconditions import PostCondition
from nei.verification import geometry_check


class VerificationEngine:
    """Run postcondition checks and produce VerificationRecord."""

    def __init__(self, connector_inspect_fn: Any = None):
        """connector_inspect_fn: async fn(object_id) -> dict from connector."""
        self.inspect_fn = connector_inspect_fn

    async def run(
        self,
        task_id: str,
        postconditions: list[PostCondition],
        connector_result: dict,
        software_version: str,
    ) -> VerificationRecord:
        """Run all postconditions against connector_result.

        connector_result shape:
          {
            "status": "ok",
            "object_ids": ["abc123"],
            "objects": [{"id": "abc123", "type": "Brep", "bounding_box": {...}}],
            "document": {"units": "Millimeters"},
          }
        """
        checks: list[VerificationCheck] = []

        for pc in postconditions:
            check = await self._run_one(pc, connector_result)
            checks.append(check)

        # Determine overall status
        all_passed = all(c.result == "PASSED" for c in checks)
        any_incomplete = any(c.result == "INCOMPLETE" for c in checks)

        if any_incomplete:
            status = "INCOMPLETE"
        elif all_passed:
            status = "PASSED"
        else:
            status = "FAILED"

        return VerificationRecord(
            task_id=task_id,
            status=status,
            checks=checks,
            software_version=software_version,
            verified_at=VerificationRecord.now(),
        )

    async def _run_one(self, pc: PostCondition, result: dict) -> VerificationCheck:
        """Dispatch to appropriate checker based on pc.target."""
        if pc.target == "bounding_box":
            # Extract first object's bounding box from result
            objects = result.get("objects", [])
            if not objects:
                return self._incomplete(pc, "no objects in connector result")
            bbox = objects[0].get("bounding_box", {})
            return geometry_check.check_bounding_box(
                pc.expected, bbox, pc.tolerance or 0.001
            )

        elif pc.target == "object_count":
            actual = len(result.get("object_ids", []))
            expected = pc.expected.get("count", 0)
            return geometry_check.check_object_count(expected, actual)

        elif pc.target == "object_type":
            objects = result.get("objects", [])
            if not objects:
                return self._incomplete(pc, "no objects in connector result")
            actual_type = objects[0].get("type", "unknown")
            expected_type = pc.expected.get("type", "")
            return geometry_check.check_object_type(expected_type, actual_type)

        elif pc.target == "document_units":
            actual = result.get("document", {}).get("units", "unknown")
            expected = pc.expected.get("units", "")
            return geometry_check.check_document_units(expected, actual)

        elif pc.target == "artifact_saved":
            # Filesystem check — not connector result
            return self._incomplete(pc, "artifact_saved not implemented in Alpha 0.1")

        else:
            return self._incomplete(pc, f"unknown target: {pc.target}")

    def _incomplete(self, pc: PostCondition, reason: str) -> VerificationCheck:
        """Return INCOMPLETE check with reason."""
        from datetime import datetime, timezone

        return VerificationCheck(
            target=pc.target,
            expected=pc.expected,
            actual={},
            tolerance=pc.tolerance,
            method=pc.method,
            result="INCOMPLETE",
            evidence=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
