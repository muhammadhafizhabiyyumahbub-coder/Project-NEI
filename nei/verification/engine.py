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
            check = await self._run_one(task_id, pc, connector_result)
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

    async def _run_one(self, task_id: str, pc: PostCondition, result: dict) -> VerificationCheck:
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

        elif pc.target == "dimensions":
            return await self._check_dimensions(pc, result)

        elif pc.target == "volume":
            return await self._check_volume(pc, result)

        elif pc.target == "stability":
            return await self._check_stability(pc, result)

        elif pc.target == "watertight":
            return await self._check_watertight(pc, result)

        elif pc.target == "artifact_saved":
            # Real filesystem check via artifact_store (needs task_id from outer scope)
            from nei.core import artifact_store
            filename = pc.expected.get("filename", "")
            expected_sha = pc.expected.get("sha256")
            if not filename:
                return self._incomplete(pc, "artifact filename missing in expected")
            # load_artifact returns None if file does not exist
            content = await artifact_store.load_artifact(task_id, filename)
            if content is None:
                return VerificationCheck(
                    target=pc.target, expected=pc.expected, actual={"exists": False},
                    tolerance=pc.tolerance, method=pc.method,
                    result="FAILED", evidence=f"artifact not found: {filename}",
                    timestamp=VerificationRecord.now(),
                )
            if expected_sha:
                ok = await artifact_store.verify_artifact(task_id, filename, expected_sha)
                return VerificationCheck(
                    target=pc.target,
                    expected=pc.expected,
                    actual={"exists": True, "sha_ok": ok},
                    tolerance=pc.tolerance, method=pc.method,
                    result="PASSED" if ok else "FAILED",
                    evidence=f"sha256 match={ok}",
                    timestamp=VerificationRecord.now(),
                )
            return VerificationCheck(
                target=pc.target, expected=pc.expected,
                actual={"exists": True},
                tolerance=pc.tolerance, method=pc.method,
                result="PASSED",
                evidence=f"artifact exists: {filename}",
                timestamp=VerificationRecord.now(),
            )

        else:
            return self._incomplete(pc, f"unknown target: {pc.target}")

    async def _check_dimensions(self, pc, result: dict) -> VerificationCheck:
        inputs = result.get("inputs", {})
        actual = {k: inputs.get(k) for k in pc.expected}
        ok = all(actual.get(k) is not None and abs(actual[k] - pc.expected[k]) <= (pc.tolerance or 0.001) for k in pc.expected)
        return VerificationCheck(
            target=pc.target, expected=pc.expected, actual=actual,
            tolerance=pc.tolerance, method=pc.method,
            result="PASSED" if ok else "FAILED",
            evidence=f"deterministic dimensions match={ok}",
            timestamp=VerificationRecord.now(),
        )

    async def _check_volume(self, pc, result: dict) -> VerificationCheck:
        calc = result.get("calculations", {})
        actual = calc.get("displacement_volume_m3")
        ok = actual is not None and abs(actual - pc.expected["volume"]) <= (pc.tolerance or 0.01)
        return VerificationCheck(
            target=pc.target, expected=pc.expected, actual={"volume": actual},
            tolerance=pc.tolerance, method=pc.method,
            result="PASSED" if ok else "FAILED",
            evidence=f"deterministic volume match={ok}",
            timestamp=VerificationRecord.now(),
        )

    async def _check_stability(self, pc, result: dict) -> VerificationCheck:
        inputs = result.get("inputs", {})
        beam = inputs.get("beam"); draft = inputs.get("draft")
        ok = beam is not None and draft is not None and beam > draft
        return VerificationCheck(
            target=pc.target, expected=pc.expected, actual={"beam": beam, "draft": draft},
            tolerance=pc.tolerance, method=pc.method,
            result="PASSED" if ok else "FAILED",
            evidence=f"deterministic beam_over_draft={ok}",
            timestamp=VerificationRecord.now(),
        )

    async def _check_watertight(self, pc, result: dict) -> VerificationCheck:
        # Only valid if artifact exists; preview geometry is not a hull.
        artifact_saved = result.get("artifact_saved") is True
        ok = artifact_saved and result.get("watertight") is True
        return VerificationCheck(
            target=pc.target, expected=pc.expected, actual={"artifact_saved": artifact_saved, "watertight": result.get("watertight")},
            tolerance=pc.tolerance, method=pc.method,
            result="PASSED" if ok else "INCOMPLETE",
            evidence=f"watertight requires CAD inspection; artifact_saved={artifact_saved}",
            timestamp=VerificationRecord.now(),
        )

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
