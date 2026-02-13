# pm/lib/neon_docs/db.py
"""Async PostgreSQL connection pool for Neon."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg

from .config import get_settings
from .exceptions import DbConnectionError
from .log import get_logger

logger = get_logger("db")

_pool: asyncpg.Pool | None = None  # type: ignore[type-arg]


def _clean_dsn(dsn: str) -> str:
    """Strip SQLAlchemy dialect prefix if present."""
    if "+asyncpg" in dsn:
        dsn = dsn.replace("+asyncpg", "")
    return dsn


async def get_pool() -> asyncpg.Pool:  # type: ignore[type-arg]
    """Get or create the connection pool."""
    global _pool
    if _pool is not None:
        return _pool

    settings = get_settings()
    dsn = _clean_dsn(settings.database_url)

    try:
        _pool = await asyncpg.create_pool(
            dsn,
            min_size=settings.db_pool_min,
            max_size=settings.db_pool_max,
            command_timeout=settings.db_command_timeout,
        )
        logger.info("Connection pool created (min=%d, max=%d)", settings.db_pool_min, settings.db_pool_max)
        return _pool
    except Exception as e:
        raise DbConnectionError(f"Failed to create pool: {e}", cause=e) from e


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Connection pool closed")


@asynccontextmanager
async def connection() -> AsyncIterator[asyncpg.Connection]:  # type: ignore[type-arg]
    """Get a connection from the pool."""
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            yield conn
    except asyncpg.PostgresError as e:
        raise DbConnectionError(f"Connection error: {e}", cause=e) from e


async def health_check() -> bool:
    """Check if database is reachable."""
    try:
        async with connection() as conn:
            result = await conn.fetchval("SELECT 1")
            return result == 1
    except Exception:
        return False
