"""Pytest bootstrap for NEI.

Ensures the shared SQLite database is initialized before tests that
unlink it, so that migrations are applied before first use.
"""
import asyncio
from pathlib import Path

import pytest

from nei.core.database import DB_PATH, init_db


@pytest.fixture(autouse=True)
def _ensure_db_initialized():
    """Initialize the database if it does not already exist.

    Many test modules call a local ``_reset`` helper that unlinks
    ``data/nei.db`` and then calls ``init_db`` to recreate it. This
    fixture guarantees that a fresh database is created before any
    such reset happens in the current test module, and that the
    migrations directory exists.
    """
    if not DB_PATH.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        from nei.core.database import MIGRATIONS_DIR
        MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
        asyncio.run(init_db())
    yield
