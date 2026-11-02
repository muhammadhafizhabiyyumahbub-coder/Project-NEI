"""Database: WAL SQLite with sequential migrations.

Schema follows DATABASE_SCHEMA.md.
Use:  async with get_db() as db: ...
"""
import aiosqlite
from pathlib import Path

DB_PATH = Path("data/nei.db")
MIGRATIONS_DIR = Path("database/migrations")


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _make_conn() -> aiosqlite.Connection:
    return aiosqlite.connect(str(DB_PATH))


def get_db():
    """Return an async context manager yielding an aiosqlite connection."""
    return _make_conn()


async def init_db() -> None:
    """Initialize DB: schema_migrations, app_state, and all migration files."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)

    db = _make_conn()
    async with db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.execute("PRAGMA synchronous=NORMAL")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        applied = {
            row[0] for row in await db.execute_fetchall(
                "SELECT version FROM schema_migrations")
        }
        for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = int(f.stem.split("_")[0])
            if version in applied:
                continue
            await db.executescript(f.read_text(encoding="utf-8"))
            await db.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (version, _now()),
            )
        await db.commit()
