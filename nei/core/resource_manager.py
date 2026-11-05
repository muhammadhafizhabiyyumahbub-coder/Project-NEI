"""Per-software concurrency guard.

Prevents two tasks from driving the same CAD application at the same time.
COM sessions (SOLIDWORKS) and file-based IPC (Rhino listener) are not safe
for concurrent use — one heavy app at a time is the resource policy from
ARCHITECTURE.md / environment.json.
"""
import threading
import time
from dataclasses import dataclass, field
from typing import Optional


def _now() -> float:
    return time.monotonic()


@dataclass
class _LockRecord:
    holder_task: str
    acquired_at: float = field(default_factory=_now)


class ResourceManager:
    """In-process app-lock manager. Single-writer per software ID."""

    def __init__(self):
        self._locks: dict[str, threading.Lock] = {}
        self._holders: dict[str, Optional[_LockRecord]] = {}
        self._meta = threading.Lock()

    def acquire(self, connector_id: str, task_id: str, timeout_s: float = 30.0) -> bool:
        """Acquire exclusive lock for connector_id. Returns True on success.

        Blocks up to timeout_s. If lock not released within timeout, task
        should transition to RECOVERING per ARCHITECTURE.md error table.
        """
        with self._meta:
            if connector_id not in self._locks:
                self._locks[connector_id] = threading.Lock()
                self._holders[connector_id] = None
            lock = self._locks[connector_id]
        got = lock.acquire(timeout=timeout_s)
        if got:
            with self._meta:
                self._holders[connector_id] = _LockRecord(holder_task=task_id)
        return got

    def release(self, connector_id: str, task_id: str) -> None:
        with self._meta:
            holder = self._holders.get(connector_id)
            lock = self._locks.get(connector_id)
            if lock:
                if holder is not None and holder.holder_task != task_id:
                    # Wrong task releasing — still release to avoid deadlock,
                    # log-worthy in real impl; silent for now.
                    pass
                lock.release()
                self._holders[connector_id] = None

    def holder(self, connector_id: str) -> Optional[str]:
        with self._meta:
            h = self._holders.get(connector_id)
            return h.holder_task if h else None

    def all_holders(self) -> dict[str, Optional[str]]:
        with self._meta:
            return {k: (v.holder_task if v else None) for k, v in self._holders.items()}


# Singleton for the process lifetime
_resource_manager = ResourceManager()


def get_resource_manager() -> ResourceManager:
    return _resource_manager


def acquire_app_lock(connector_id: str, task_id: str, timeout_s: float = 30.0) -> bool:
    return _resource_manager.acquire(connector_id, task_id, timeout_s)


def release_app_lock(connector_id: str, task_id: str) -> None:
    _resource_manager.release(connector_id, task_id)
