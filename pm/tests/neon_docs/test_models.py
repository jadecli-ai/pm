# pm/tests/neon_docs/test_models.py
"""Tests for Pydantic models."""

from lib.neon_docs.models import (
    CacheCheckResult,
    CacheStatus,
    CrawledDocument,
    QueueStatus,
    SearchResult,
    UpsertAction,
    UpsertResult,
)


class TestModels:
    def test_crawled_document(self) -> None:
        doc = CrawledDocument(id=1, content="hello", content_hash="abc123")
        assert doc.url is None
        assert doc.needs_processing is True

    def test_upsert_result(self) -> None:
        r = UpsertResult(action=UpsertAction.INSERTED, doc_id=1)
        assert r.action == "inserted"

    def test_search_result(self) -> None:
        r = SearchResult(doc_id=1, chunk_text="hello", similarity=0.95)
        assert r.similarity == 0.95
        assert r.title is None

    def test_queue_status_enum(self) -> None:
        assert QueueStatus.PENDING == "pending"
        assert QueueStatus.DONE == "done"

    def test_cache_check_hit(self) -> None:
        r = CacheCheckResult(hit=True, content="cached", doc_id=1)
        assert r.hit is True

    def test_cache_check_miss(self) -> None:
        r = CacheCheckResult(hit=False)
        assert r.content is None

    def test_cache_status(self) -> None:
        s = CacheStatus(documents=10, chunks=100, queue_pending=0, queue_failed=0)
        assert s.documents == 10
