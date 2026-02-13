# pm/tests/neon_docs/test_repository.py
"""Tests for document repository (requires live Neon DB)."""

import pytest

from lib.neon_docs.db import close_pool
from lib.neon_docs.repository import (
    check_url,
    get_status,
    upsert_document,
)


@pytest.mark.live
class TestRepository:
    async def test_upsert_insert(self, neon_url: str) -> None:
        result = await upsert_document(
            url="https://test.example.com/repo-test-insert",
            title="Test Insert",
            content="Test content for repository test",
        )
        assert result.action == "inserted"
        assert result.doc_id > 0
        await close_pool()

    async def test_upsert_unchanged(self, neon_url: str) -> None:
        url = "https://test.example.com/repo-test-unchanged"
        content = "Unchanged content for repo test"
        await upsert_document(url=url, title="Test", content=content)
        result = await upsert_document(url=url, title="Test", content=content)
        assert result.action == "unchanged"
        await close_pool()

    async def test_upsert_updated(self, neon_url: str) -> None:
        url = "https://test.example.com/repo-test-updated"
        await upsert_document(url=url, title="Test", content="version 1")
        result = await upsert_document(url=url, title="Test", content="version 2")
        assert result.action == "updated"
        await close_pool()

    async def test_check_url_hit(self, neon_url: str) -> None:
        url = "https://test.example.com/repo-test-check-hit"
        await upsert_document(url=url, title="Test", content="cached content")
        result = await check_url(url)
        assert result.hit is True
        assert result.content == "cached content"
        await close_pool()

    async def test_check_url_miss(self, neon_url: str) -> None:
        result = await check_url("https://test.example.com/nonexistent-url-12345")
        assert result.hit is False
        await close_pool()

    async def test_get_status(self, neon_url: str) -> None:
        status = await get_status()
        assert status.documents >= 0
        assert status.chunks >= 0
        await close_pool()
