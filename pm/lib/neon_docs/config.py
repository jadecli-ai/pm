# pm/lib/neon_docs/config.py
"""Configuration via Pydantic BaseSettings.

Loads from environment variables with PRJ_ prefix for project-specific settings.
Falls back to .env file at repo root.
"""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # pm/ repo root


class NeonDocsSettings(BaseSettings):
    """Settings for neon_docs library.

    All settings can be overridden via environment variables.
    """

    # Database
    database_url: str = Field(
        alias="PRJ_NEON_DATABASE_URL",
        description="Neon PostgreSQL connection string",
    )
    db_pool_min: int = Field(default=1, alias="DB_POOL_MIN")
    db_pool_max: int = Field(default=5, alias="DB_POOL_MAX")
    db_command_timeout: int = Field(default=30, alias="DB_COMMAND_TIMEOUT")

    # Ollama
    ollama_host: str = Field(default="http://localhost:11434", alias="OLLAMA_HOST")
    ollama_model: str = Field(default="nomic-embed-text", alias="OLLAMA_EMBED_MODEL")
    embedding_dimensions: int = Field(default=768, alias="EMBEDDING_DIMENSIONS")

    # Chunking
    chunk_max_tokens: int = Field(default=512, alias="CHUNK_MAX_TOKENS")
    chunk_overlap_tokens: int = Field(default=64, alias="CHUNK_OVERLAP_TOKENS")

    # Search
    search_default_limit: int = Field(default=5, alias="SEARCH_DEFAULT_LIMIT")
    search_default_threshold: float = Field(default=0.3, alias="SEARCH_DEFAULT_THRESHOLD")

    # MLflow
    mlflow_enabled: bool = Field(default=True, alias="MLFLOW_ENABLED")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = {
        "env_file": str(_REPO_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


_settings: NeonDocsSettings | None = None


def get_settings() -> NeonDocsSettings:
    """Get cached settings singleton."""
    global _settings
    if _settings is None:
        _settings = NeonDocsSettings()  # type: ignore[call-arg]
    return _settings


def reset_settings() -> None:
    """Reset settings (for testing)."""
    global _settings
    _settings = None
