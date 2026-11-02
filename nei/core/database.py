"""Database initialization and session management."""
import aiosqlite
from pathlib import Path
from nei.core.config import settings

DB_PATH = Path("data/nei.db")


async def init_db() -> None:
    """Initialize database with schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                vessel_type TEXT,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                action TEXT NOT NULL,
                target TEXT,
                params TEXT,
                risk_level TEXT DEFAULT 'L0',
                result TEXT,
                verification_json TEXT,
                error TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                started_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
            
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );
            
            CREATE TABLE IF NOT EXISTS policies (
                id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                risk_level TEXT NOT NULL DEFAULT 'L0',
                auto_approve INTEGER DEFAULT 0,
                requires_verification INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            
            CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_artifacts_task ON artifacts(task_id);
        """)
        await db.commit()


async def get_db():
    """Get database connection."""
    return aiosqlite.connect(DB_PATH)
