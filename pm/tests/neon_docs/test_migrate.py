# pm/tests/neon_docs/test_migrate.py
"""Tests for migration runner."""

import pytest

from lib.neon_docs.migrate import run_migrations


@pytest.mark.live
class TestMigrations:
    async def test_run_migrations_applies_v001(self, neon_url: str) -> None:
        applied = await run_migrations()
        assert "V001_initial_schema.sql" in applied or len(applied) == 0

    async def test_run_migrations_idempotent(self, neon_url: str) -> None:
        _first = await run_migrations()
        second = await run_migrations()
        assert len(second) == 0, "Second run should apply nothing"
