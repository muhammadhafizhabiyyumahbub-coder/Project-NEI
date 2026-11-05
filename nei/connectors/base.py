"""Base connector interface (shared by all CAD connectors)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class CapabilityStatus(str, Enum):
    SUPPORTED   = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN     = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class DetectionResult:
    detected: bool
    exe_path: Optional[str] = None
    version: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class HealthResult:
    healthy: bool
    detail: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ToolResult:
    success: bool
    object_ids: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class InspectionResult:
    objects: list[dict] = field(default_factory=list)
    document: dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class Capability:
    name: str
    status: CapabilityStatus
    version_tested: Optional[str] = None
    notes: Optional[str] = None


class BaseConnector(ABC):
    connector_id: str
    name: str

    @abstractmethod
    def detect(self) -> DetectionResult:
        """Check if software is installed. Filesystem + registry only, no COM."""
        ...

    @abstractmethod
    def get_version(self) -> Optional[str]:
        """Return exact version string, or None if undetectable."""
        ...

    @abstractmethod
    def health_check(self) -> HealthResult:
        """Is process running and responsive?"""
        ...

    def get_capabilities(self) -> list[Capability]:
        """Return advertised action capabilities."""
        return []

    def validate_parameters(self, action: str, parameters: dict) -> Optional[str]:
        """Return validation error before execution, or None when valid."""
        return None

    @abstractmethod
    def execute(self, action: str, parameters: dict, *, timeout_s: int) -> ToolResult:
        """Execute an allowlisted action. Idempotent-safe where possible."""
        ...

    @abstractmethod
    def inspect(self, target: dict) -> InspectionResult:
        """Read-only inspection of objects or document state."""
        ...

    @abstractmethod
    def detach(self) -> None:
        """Release COM/session handle. Do NOT close the software."""
        ...
