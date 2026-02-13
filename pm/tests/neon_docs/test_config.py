# pm/tests/neon_docs/test_config.py
"""Tests for neon_docs configuration."""

import pytest
from pydantic import ValidationError

from lib.neon_docs.config import NeonDocsSettings, get_settings, reset_settings


class TestNeonDocsSettings:
    def setup_method(self) -> None:
        reset_settings()

    def test_loads_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://test:test@localhost/test")
        settings = NeonDocsSettings()  # type: ignore[call-arg]
        assert settings.database_url == "postgresql://test:test@localhost/test"

    def test_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://test:test@localhost/test")
        settings = NeonDocsSettings()  # type: ignore[call-arg]
        assert settings.db_pool_min == 1
        assert settings.db_pool_max == 5
        assert settings.ollama_host == "http://localhost:11434"
        assert settings.ollama_model == "nomic-embed-text"
        assert settings.embedding_dimensions == 768
        assert settings.chunk_max_tokens == 512
        assert settings.chunk_overlap_tokens == 64
        assert settings.search_default_limit == 5

    def test_get_settings_singleton(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://test:test@localhost/test")
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_missing_database_url_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PRJ_NEON_DATABASE_URL", raising=False)
        with pytest.raises(ValidationError):
            NeonDocsSettings(_env_file=None)  # type: ignore[call-arg]
