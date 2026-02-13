# pm/lib/neon_docs/exceptions.py
"""Semantic exception hierarchy for neon_docs.

Follows Anthropic/Vercel pattern: typed exceptions with is_retryable flag.
"""

from __future__ import annotations


class NeonDocsError(Exception):
    """Base exception for all neon_docs errors."""

    is_retryable: bool = False

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.__cause__ = cause


class DatabaseError(NeonDocsError):
    """Database operation failed."""

    is_retryable = True


class DbConnectionError(DatabaseError):
    """Could not connect to database."""

    is_retryable = True


class QueryError(DatabaseError):
    """SQL query failed."""

    is_retryable = False


class EmbeddingError(NeonDocsError):
    """Embedding generation failed."""

    is_retryable = True


class OllamaConnectionError(EmbeddingError):
    """Could not connect to Ollama."""

    is_retryable = True


class OllamaModelError(EmbeddingError):
    """Ollama model not available."""

    is_retryable = False


class ChunkingError(NeonDocsError):
    """Text chunking failed."""

    is_retryable = False


class ConfigError(NeonDocsError):
    """Configuration error."""

    is_retryable = False
