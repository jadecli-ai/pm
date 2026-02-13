# pm/lib/neon_docs/migrate.py
"""Database migration runner.

Executes numbered SQL migrations in order. Tracks applied migrations
in a _migrations table. Idempotent: re-running skips already-applied migrations.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import asyncpg

from .config import get_settings
from .log import get_logger
from .tracer import trace_operation

logger = get_logger("migrate")

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def _get_connection() -> asyncpg.Connection:
    """Get a direct connection (not pooled) for migrations."""
    settings = get_settings()
    dsn = settings.database_url
    if "+asyncpg" in dsn:
        dsn = dsn.replace("+asyncpg", "")
    return await asyncpg.connect(dsn)


async def _ensure_migrations_table(conn: asyncpg.Connection) -> None:
    """Create migrations tracking table if it doesn't exist."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            name TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)


async def _get_applied(conn: asyncpg.Connection) -> set[str]:
    """Get set of already-applied migration names."""
    rows = await conn.fetch("SELECT name FROM _migrations ORDER BY name")
    return {row["name"] for row in rows}


@trace_operation("neon.run_migrations")
async def run_migrations() -> list[str]:
    """Run all pending migrations in order.

    Returns:
        List of newly applied migration names.
    """
    conn = await _get_connection()
    try:
        await _ensure_migrations_table(conn)
        applied = await _get_applied(conn)

        migration_files = sorted(MIGRATIONS_DIR.glob("V*.sql"))
        newly_applied: list[str] = []

        for mf in migration_files:
            if mf.name in applied:
                logger.info("Skip (already applied): %s", mf.name)
                continue

            logger.info("Applying: %s", mf.name)
            sql = mf.read_text(encoding="utf-8")
            await conn.execute(sql)
            await conn.execute("INSERT INTO _migrations (name) VALUES ($1)", mf.name)
            newly_applied.append(mf.name)
            logger.info("Applied: %s", mf.name)

        return newly_applied
    finally:
        await conn.close()


def main() -> None:
    """CLI entry point for running migrations."""
    import json

    applied = asyncio.run(run_migrations())
    if applied:
        print(json.dumps({"applied": applied}))
    else:
        print(json.dumps({"applied": [], "message": "all migrations already applied"}))


if __name__ == "__main__":
    main()
