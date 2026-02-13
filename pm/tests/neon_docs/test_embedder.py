# pm/tests/neon_docs/test_embedder.py
"""Tests for Ollama embeddings client."""

import pytest

from lib.neon_docs.config import reset_settings
from lib.neon_docs.embedder import embed_single, embed_texts


class TestEmbedderUnit:
    """Unit tests (no Ollama required)."""

    def setup_method(self) -> None:
        reset_settings()


@pytest.mark.live
class TestEmbedderLive:
    """Integration tests (require Ollama running)."""

    def setup_method(self) -> None:
        reset_settings()

    async def test_embed_single(self, ollama_host: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://x@localhost/x")
        result = await embed_single("hello world")
        assert len(result) == 768
        assert all(isinstance(x, float) for x in result)

    async def test_embed_texts_batch(self, ollama_host: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://x@localhost/x")
        results = await embed_texts(["hello", "world"])
        assert len(results) == 2
        assert len(results[0]) == 768
        assert len(results[1]) == 768

    async def test_embed_different_texts_different_vectors(
        self, ollama_host: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://x@localhost/x")
        results = await embed_texts(["programming in Python", "cooking Italian food"])
        assert results[0] != results[1]
