"""Connector registry: discover and register available connectors.

Instead of hard-coding the CONNECTORS list in api.py, this module scans
`nei/connectors/` for modules that define a `BaseConnector` subclass and
exposes a stable list + lookup helpers. Adding a new connector file is
enough; no API-layer changes required.
"""
import importlib
import inspect
from pathlib import Path
from typing import Optional

from nei.connectors.base import BaseConnector


def discover_connectors() -> list[type[BaseConnector]]:
    """Find all concrete BaseConnector subclasses in the connectors package.

    Scans both top-level `.py` files and sub-package modules (e.g. `rhino6/connector.py`),
    skipping `__init__.py` (to avoid re-importing package inits recursively).
    """
    found: list[type[BaseConnector]] = []
    package_dir = Path(__file__).parent
    for py_file in sorted(package_dir.rglob("*.py")):
        if py_file.name == "__init__.py" or py_file.name.startswith("_"):
            continue
        # nei/connectors/rhino6/connector.py → nei.connectors.rhino6.connector
        # relative_to(nei/) → connectors/rhino6/connector → replace / with .
        relative = py_file.relative_to(package_dir.parent)
        module_name = f"nei.{relative.with_suffix('').as_posix().replace('/', '.')}"
        try:
            module = importlib.import_module(module_name)
        except (ImportError, AttributeError, ModuleNotFoundError):
            continue
        for name, obj in vars(module).items():
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseConnector)
                and obj is not BaseConnector
                and not inspect.isabstract(obj)
                and getattr(obj, "connector_id", None)
            ):
                found.append(obj)
    return found


_REGISTRY_CACHE: Optional[list[type[BaseConnector]]] = None


def registry() -> list[type[BaseConnector]]:
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is None:
        _REGISTRY_CACHE = discover_connectors()
    return _REGISTRY_CACHE


def get_connector_class(connector_id: str) -> Optional[type[BaseConnector]]:
    for cls in registry():
        if cls.connector_id == connector_id:
            return cls
    return None
