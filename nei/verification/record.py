"""Verification record schema.

Stored in tasks.verification_json as JSON.
Immutable once written.
"""
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime, timezone


@dataclass
class VerificationCheck:
    """Single postcondition check result."""
    target: str
    expected: dict
    actual: dict
    tolerance: Optional[float]
    method: str
    result: str  # "PASSED" | "FAILED" | "INCOMPLETE"
    evidence: str
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VerificationRecord:
    """Full verification run result."""
    task_id: str
    status: str  # "PASSED" | "FAILED" | "INCOMPLETE"
    checks: list[VerificationCheck]
    software_version: str
    verified_at: str

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "checks": [c.to_dict() for c in self.checks],
            "software_version": self.software_version,
            "verified_at": self.verified_at,
        }

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()
