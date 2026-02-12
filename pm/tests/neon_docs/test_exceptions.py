# pm/tests/neon_docs/test_exceptions.py
"""Tests for exception hierarchy."""

from lib.neon_docs.exceptions import (
    ChunkingError,
    ConnectionError,
    DatabaseError,
    EmbeddingError,
    NeonDocsError,
    OllamaConnectionError,
    OllamaModelError,
    QueryError,
)


class TestExceptionHierarchy:
    def test_base_exception(self) -> None:
        err = NeonDocsError("test")
        assert str(err) == "test"
        assert err.is_retryable is False

    def test_database_error_is_retryable(self) -> None:
        assert DatabaseError.is_retryable is True
        assert ConnectionError.is_retryable is True

    def test_query_error_not_retryable(self) -> None:
        assert QueryError.is_retryable is False

    def test_embedding_errors(self) -> None:
        assert EmbeddingError.is_retryable is True
        assert OllamaConnectionError.is_retryable is True
        assert OllamaModelError.is_retryable is False

    def test_inheritance_chain(self) -> None:
        err = OllamaConnectionError("timeout")
        assert isinstance(err, EmbeddingError)
        assert isinstance(err, NeonDocsError)
        assert isinstance(err, Exception)

    def test_cause_chaining(self) -> None:
        original = ValueError("bad value")
        err = DatabaseError("query failed", cause=original)
        assert err.__cause__ is original
