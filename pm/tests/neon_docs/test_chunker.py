# pm/tests/neon_docs/test_chunker.py
"""Tests for text chunker."""

import pytest

from lib.neon_docs.chunker import chunk_text
from lib.neon_docs.config import reset_settings
from lib.neon_docs.tokenizer import count_tokens


class TestChunker:
    def setup_method(self) -> None:
        reset_settings()

    def test_short_text_single_chunk(self, sample_text: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://x@localhost/x")
        chunks = chunk_text(sample_text, max_tokens=1000)
        assert len(chunks) == 1
        assert chunks[0] == sample_text

    def test_long_text_multiple_chunks(self, long_text: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://x@localhost/x")
        chunks = chunk_text(long_text, max_tokens=100, overlap_tokens=20)
        assert len(chunks) > 1
        for chunk in chunks:
            assert count_tokens(chunk) <= 150  # allow some flex for boundary

    def test_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://x@localhost/x")
        chunks = chunk_text("", max_tokens=100)
        assert len(chunks) == 1

    def test_all_content_preserved(self, long_text: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://x@localhost/x")
        chunks = chunk_text(long_text, max_tokens=100, overlap_tokens=0)
        reconstructed = "\n\n".join(chunks)
        for para in long_text.split("\n\n"):
            assert para.strip() in reconstructed

    def test_no_empty_chunks(self, long_text: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://x@localhost/x")
        chunks = chunk_text(long_text, max_tokens=100)
        for chunk in chunks:
            assert len(chunk.strip()) > 0
