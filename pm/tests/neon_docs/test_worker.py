# pm/tests/neon_docs/test_worker.py
"""Tests for processing worker (requires live Neon + Ollama)."""

import pytest

from lib.neon_docs.db import close_pool
from lib.neon_docs.repository import get_status, upsert_document
from lib.neon_docs.worker import drain_queue


@pytest.mark.live
class TestWorker:
    async def test_drain_queue_processes_job(
        self, neon_url: str, ollama_host: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = await upsert_document(
            url="https://test.example.com/worker-test-drain",
            title="Worker Test",
            content="This is a test document for the processing worker. It has enough content to be chunked.",
        )
        assert result.action in ("inserted", "updated")
        stats = await drain_queue()
        assert stats["processed"] >= 1
        assert stats["failed"] == 0
        status = await get_status()
        assert status.chunks > 0
        await close_pool()
