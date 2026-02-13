# pm/tests/neon_docs/test_db.py
"""Tests for database connection pool."""

import pytest

from lib.neon_docs.db import close_pool, connection, get_pool, health_check


@pytest.mark.live
class TestDatabase:
    async def test_get_pool(self, neon_url: str) -> None:
        pool = await get_pool()
        assert pool is not None
        await close_pool()

    async def test_connection_context(self, neon_url: str) -> None:
        async with connection() as conn:
            result = await conn.fetchval("SELECT 1")
            assert result == 1
        await close_pool()

    async def test_health_check(self, neon_url: str) -> None:
        assert await health_check() is True
        await close_pool()

    async def test_pool_singleton(self, neon_url: str) -> None:
        p1 = await get_pool()
        p2 = await get_pool()
        assert p1 is p2
        await close_pool()
