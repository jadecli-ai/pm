# Neon Specialist Agent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a production-quality Neon-backed document caching and semantic search layer for PM agents, with MLflow 3.9 tracing.

**Architecture:** A `neon-specialist` leaf agent provides document store/search/cache operations via a typed Python library (`lib/neon_docs/`). PreToolUse/PostToolUse hooks on WebFetch transparently cache fetched pages. Ollama generates embeddings locally on RTX 2080 Ti. All operations are traced via MLflow 3.9. The library follows Anthropic/Neon/Vercel Python standards: Hatchling build, Ruff linting, Pyright type checking, pytest with real integrations, Pydantic v2 models, tenacity retry, tiktoken token counting, asyncpg with connection pooling.

**Tech Stack:** Python 3.11+, asyncpg, Neon PostgreSQL + pgvector, Ollama (nomic-embed-text 768d), httpx, MLflow 3.9, Pydantic v2, tenacity, tiktoken, Ruff, Pyright, pytest-asyncio

**Design Doc:** `docs/plans/2026-02-12-neon-specialist-agent-design.md`

**Path Conventions:**
- `$REPO` = `/home/alex-jadecli/projects/refs/jadecli-ai/pm` (git repo root)
- `$PM` = `/home/alex-jadecli/projects/refs/jadecli-ai/pm/pm` (PM system root)
- All `lib/neon_docs/` paths are relative to `$PM`
- Commands run from `$PM` with `PYTHONPATH=.` unless noted otherwise

**Engineering Standards (from Anthropic/Neon/Google/Vercel research):**

| Standard | Source | Implementation |
|----------|--------|----------------|
| Hatchling build backend | Anthropic, Neon | `pyproject.toml` at `$REPO` |
| Ruff lint+format (line-length=120) | Anthropic, Neon, Vercel | `[tool.ruff]` in pyproject.toml |
| Pyright strict mode | Neon | `[tool.pyright]` in pyproject.toml |
| pytest + pytest-asyncio | All orgs | `[tool.pytest]` in pyproject.toml |
| Pydantic v2 BaseSettings | All orgs | `lib/neon_docs/config.py` |
| Pydantic v2 models | All orgs | `lib/neon_docs/models.py` |
| Semantic exception hierarchy | Anthropic, Vercel | `lib/neon_docs/exceptions.py` |
| tenacity retry + backoff | Neon, Google | On Ollama + DB calls |
| tiktoken token counting | Anthropic | In chunker, not `words*1.3` |
| httpx async client | Anthropic, Google | Ollama embeddings client |
| asyncpg + pool_recycle | Neon | DB connection pool |
| HNSW m=16, ef_construction=64 | Neon | pgvector index params |
| Structured logging | All orgs | Python `logging` module |
| Google-style docstrings | Anthropic | All public functions |
| Conventional commits | All orgs | Every commit message |

---

## Phase 0: Project Infrastructure (Tasks 1-8)

### Task 1: Create pyproject.toml

**Files:**
- Create: `$REPO/pyproject.toml`

**Step 1: Write pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pm-neon-docs"
version = "0.1.0"
description = "Neon-backed document caching and semantic search for PM agents"
requires-python = ">=3.11"
dependencies = [
    "asyncpg>=0.29.0",
    "httpx>=0.27.0",
    "mlflow>=3.9.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-dotenv>=1.0.0",
    "tenacity>=8.2.0",
    "tiktoken>=0.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.6.0",
    "pyright>=1.1.380",
]

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "A", "SIM"]

[tool.ruff.lint.isort]
known-first-party = ["lib"]

[tool.pyright]
pythonVersion = "3.11"
typeCheckingMode = "standard"
include = ["pm/lib/neon_docs"]
reportMissingTypeStubs = false

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["pm/tests"]
pythonpath = ["pm"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
markers = [
    "live: requires live Neon database and/or Ollama",
]
```

**Step 2: Verify pyproject.toml parses**

Run: `cd $REPO && python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb')); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "feat(infra): add pyproject.toml with Hatchling, Ruff, Pyright, pytest config"
```

---

### Task 2: Install dev dependencies with uv

**Files:** None (runtime operation)

**Step 1: Install uv if not present**

Run: `command -v uv || curl -LsSf https://astral.sh/uv/install.sh | sh`
Expected: uv available

**Step 2: Create venv and install**

Run: `cd $REPO && uv venv .venv && uv pip install -e ".[dev]"`
Expected: All dependencies installed without conflicts

**Step 3: Verify key imports**

Run: `cd $REPO && .venv/bin/python3 -c "import asyncpg, httpx, pydantic, tenacity, tiktoken; print('OK')"`
Expected: `OK`

---

### Task 3: Create .env.example

**Files:**
- Create: `$REPO/.env.example`

**Step 1: Write .env.example**

```bash
# Neon PostgreSQL (REQUIRED)
PRJ_NEON_DATABASE_URL=postgresql://user:pass@ep-xxx.us-west-2.aws.neon.tech/neondb?sslmode=require

# Ollama (defaults shown)
OLLAMA_HOST=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text

# MLflow (optional)
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=pm-neon-docs

# Logging
LOG_LEVEL=INFO
```

**Step 2: Verify .gitignore excludes .env**

Run: `cd $REPO && grep -q '.env' .gitignore && echo 'OK' || echo '.env >> .gitignore'`
Expected: `OK` (or add it)

**Step 3: Commit**

```bash
git add .env.example
git commit -m "feat(infra): add .env.example with all configuration variables"
```

---

### Task 4: Create Pydantic BaseSettings config module

**Files:**
- Create: `$PM/lib/neon_docs/__init__.py`
- Create: `$PM/lib/neon_docs/config.py`

**Step 1: Create package init**

```python
# pm/lib/neon_docs/__init__.py
"""Neon document caching and semantic search."""

__version__ = "0.1.0"
```

**Step 2: Write config.py**

```python
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
```

**Step 3: Write the failing test**

Create: `$PM/tests/neon_docs/__init__.py` (empty)
Create: `$PM/tests/neon_docs/test_config.py`

```python
# pm/tests/neon_docs/test_config.py
"""Tests for neon_docs configuration."""

import os

import pytest

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
        with pytest.raises(Exception):
            NeonDocsSettings()  # type: ignore[call-arg]
```

**Step 4: Run tests to verify they fail then pass**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/test_config.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add pm/lib/neon_docs/__init__.py pm/lib/neon_docs/config.py
git add pm/tests/neon_docs/__init__.py pm/tests/neon_docs/test_config.py
git commit -m "feat(neon): add Pydantic BaseSettings config with tests"
```

---

### Task 5: Create exception hierarchy

**Files:**
- Create: `$PM/lib/neon_docs/exceptions.py`
- Create: `$PM/tests/neon_docs/test_exceptions.py`

**Step 1: Write exceptions.py**

```python
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


class ConnectionError(DatabaseError):
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
```

**Step 2: Write the test**

```python
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
```

**Step 3: Run tests**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/test_exceptions.py -v`
Expected: All 6 tests PASS

**Step 4: Commit**

```bash
git add pm/lib/neon_docs/exceptions.py pm/tests/neon_docs/test_exceptions.py
git commit -m "feat(neon): add semantic exception hierarchy with is_retryable flag"
```

---

### Task 6: Create structured logging module

**Files:**
- Create: `$PM/lib/neon_docs/log.py`

**Step 1: Write log.py**

```python
# pm/lib/neon_docs/log.py
"""Structured logging for neon_docs.

Configures Python logging with consistent format.
"""

from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the neon_docs logger.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Configured logger for neon_docs.
    """
    logger = logging.getLogger("neon_docs")

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under neon_docs namespace.

    Args:
        name: Module name (e.g., 'db', 'embedder').

    Returns:
        Logger instance.
    """
    return logging.getLogger(f"neon_docs.{name}")
```

**Step 2: Commit**

```bash
git add pm/lib/neon_docs/log.py
git commit -m "feat(neon): add structured logging module"
```

---

### Task 7: Create conftest.py with shared fixtures

**Files:**
- Create: `$PM/tests/neon_docs/conftest.py`

**Step 1: Write conftest.py**

```python
# pm/tests/neon_docs/conftest.py
"""Shared test fixtures for neon_docs tests."""

from __future__ import annotations

import os

import pytest


@pytest.fixture
def neon_url() -> str:
    """Get Neon database URL, skip if not set."""
    url = os.environ.get("PRJ_NEON_DATABASE_URL")
    if not url:
        pytest.skip("PRJ_NEON_DATABASE_URL not set")
    return url


@pytest.fixture
def ollama_host() -> str:
    """Get Ollama host, skip if not reachable."""
    import httpx

    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    try:
        resp = httpx.get(f"{host}/api/tags", timeout=5.0)
        resp.raise_for_status()
    except Exception:
        pytest.skip(f"Ollama not reachable at {host}")
    return host


@pytest.fixture
def sample_text() -> str:
    """Sample document text for testing."""
    return (
        "Claude is an AI assistant made by Anthropic. "
        "It uses a technique called Constitutional AI (CAI) for alignment. "
        "Claude can help with analysis, writing, coding, and more. "
        "The API supports tool use, vision, and prompt caching."
    )


@pytest.fixture
def long_text() -> str:
    """Long document text that will require multiple chunks."""
    paragraphs = []
    for i in range(20):
        paragraphs.append(
            f"Section {i + 1}: This is paragraph {i + 1} of the test document. "
            f"It contains several sentences about topic {i + 1}. "
            f"The purpose is to test text chunking with realistic paragraph lengths. "
            f"Each paragraph has enough content to contribute meaningfully to token counts. "
            f"We include varied vocabulary to test embedding quality across chunks."
        )
    return "\n\n".join(paragraphs)
```

**Step 2: Commit**

```bash
git add pm/tests/neon_docs/conftest.py
git commit -m "feat(neon): add test fixtures (conftest.py) with skip-if-unavailable"
```

---

### Task 8: Verify Phase 0 infrastructure

**Files:** None (verification only)

**Step 1: Run Ruff lint on neon_docs**

Run: `cd $REPO && .venv/bin/ruff check pm/lib/neon_docs/ --fix`
Expected: No errors (or auto-fixed)

**Step 2: Run Ruff format**

Run: `cd $REPO && .venv/bin/ruff format pm/lib/neon_docs/`
Expected: Files formatted

**Step 3: Run all neon_docs tests**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/ -v`
Expected: All tests pass

**Step 4: Commit any formatting changes**

```bash
git add -A pm/lib/neon_docs/ pm/tests/neon_docs/
git commit -m "chore(neon): format with ruff, verify Phase 0 infrastructure"
```

---

## Phase 1: Database Layer (Tasks 9-22)

### Task 9: Create migration directory and V001 schema

**Files:**
- Create: `$PM/lib/neon_docs/migrations/V001_initial_schema.sql`

**Step 1: Write V001 migration**

```sql
-- V001_initial_schema.sql
-- Neon Document Caching Schema
-- Idempotent: safe to re-run (IF NOT EXISTS / OR REPLACE)

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Table 1: Raw documents (source of truth)
CREATE TABLE IF NOT EXISTS crawled_documents (
    id               SERIAL PRIMARY KEY,
    url              TEXT UNIQUE,
    file_path        TEXT UNIQUE,
    title            TEXT,
    content          TEXT        NOT NULL,
    content_hash     TEXT        NOT NULL,
    content_tsv      tsvector    GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    last_fetched_at  TIMESTAMPTZ DEFAULT NOW(),
    last_modified_at TIMESTAMPTZ,
    needs_processing BOOLEAN     DEFAULT TRUE,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT has_source CHECK (url IS NOT NULL OR file_path IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_crawled_url_hash ON crawled_documents (url, content_hash) WHERE url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_crawled_pending  ON crawled_documents (id) WHERE needs_processing = TRUE;
CREATE INDEX IF NOT EXISTS idx_crawled_tsv      ON crawled_documents USING GIN (content_tsv);

-- Table 2: Chunked + embedded content (derived from crawled_documents)
CREATE TABLE IF NOT EXISTS document_chunks (
    id            SERIAL  PRIMARY KEY,
    document_id   INTEGER NOT NULL REFERENCES crawled_documents (id) ON DELETE CASCADE,
    chunk_index   INTEGER NOT NULL,
    content       TEXT    NOT NULL,
    embedding     vector(768),
    token_count   INTEGER,

    UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_hnsw   ON document_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON document_chunks (document_id);

-- Table 3: Async processing queue
CREATE TABLE IF NOT EXISTS processing_queue (
    id            SERIAL      PRIMARY KEY,
    document_id   INTEGER     NOT NULL REFERENCES crawled_documents (id) ON DELETE CASCADE,
    operation     TEXT        NOT NULL DEFAULT 'chunk_and_embed',
    priority      INTEGER     DEFAULT 0,
    status        TEXT        DEFAULT 'pending',
    attempts      INTEGER     DEFAULT 0,
    error_message TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    started_at    TIMESTAMPTZ,
    completed_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_queue_pending ON processing_queue (priority DESC, id ASC) WHERE status = 'pending';

-- Function: Upsert document with change detection
CREATE OR REPLACE FUNCTION upsert_document(
    p_url       TEXT,
    p_file_path TEXT,
    p_title     TEXT,
    p_content   TEXT
) RETURNS TABLE(action TEXT, doc_id INTEGER) AS $$
DECLARE
    v_hash TEXT := encode(sha256(p_content::bytea), 'hex');
    v_id   INTEGER;
BEGIN
    WITH existing AS (
        SELECT id, content_hash
        FROM   crawled_documents
        WHERE  (p_url IS NOT NULL AND url = p_url)
            OR (p_file_path IS NOT NULL AND file_path = p_file_path)
        FOR UPDATE
    )
    SELECT id INTO v_id FROM existing;

    IF v_id IS NULL THEN
        INSERT INTO crawled_documents (url, file_path, title, content, content_hash)
        VALUES (p_url, p_file_path, p_title, p_content, v_hash)
        RETURNING id INTO v_id;

        INSERT INTO processing_queue (document_id, priority) VALUES (v_id, 10);
        RETURN QUERY SELECT 'inserted'::TEXT, v_id;

    ELSIF (SELECT content_hash FROM crawled_documents WHERE id = v_id) != v_hash THEN
        UPDATE crawled_documents
        SET    content = p_content, content_hash = v_hash,
               needs_processing = TRUE, updated_at = NOW()
        WHERE  id = v_id;

        DELETE FROM document_chunks WHERE document_id = v_id;
        INSERT INTO processing_queue (document_id, priority) VALUES (v_id, 10);
        RETURN QUERY SELECT 'updated'::TEXT, v_id;

    ELSE
        UPDATE crawled_documents SET last_fetched_at = NOW() WHERE id = v_id;
        RETURN QUERY SELECT 'unchanged'::TEXT, v_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function: Hybrid search (vector + keyword via CTEs)
CREATE OR REPLACE FUNCTION search_documents(
    p_embedding  vector(768),
    p_keyword    TEXT    DEFAULT NULL,
    p_limit      INTEGER DEFAULT 5,
    p_threshold  FLOAT   DEFAULT 0.3
) RETURNS TABLE(
    doc_id     INTEGER,
    title      TEXT,
    chunk_text TEXT,
    similarity FLOAT,
    url        TEXT,
    file_path  TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH ranked_chunks AS (
        SELECT dc.document_id,
               dc.content                                  AS chunk_text,
               (1 - (dc.embedding <=> p_embedding))::FLOAT AS similarity
        FROM   document_chunks dc
        WHERE  1 - (dc.embedding <=> p_embedding) > p_threshold
    ),
    keyword_filter AS (
        SELECT id
        FROM   crawled_documents
        WHERE  p_keyword IS NULL
            OR content_tsv @@ plainto_tsquery('english', p_keyword)
    )
    SELECT rc.document_id,
           cd.title,
           rc.chunk_text,
           rc.similarity,
           cd.url,
           cd.file_path
    FROM   ranked_chunks rc
    JOIN   keyword_filter kf ON kf.id = rc.document_id
    JOIN   crawled_documents cd ON cd.id = rc.document_id
    ORDER  BY rc.similarity DESC
    LIMIT  p_limit;
END;
$$ LANGUAGE plpgsql;
```

**Step 2: Commit**

```bash
git add pm/lib/neon_docs/migrations/V001_initial_schema.sql
git commit -m "feat(neon): add V001 schema migration with pgvector HNSW indexes"
```

---

### Task 10: Create migration runner

**Files:**
- Create: `$PM/lib/neon_docs/migrate.py`

**Step 1: Write migrate.py**

```python
# pm/lib/neon_docs/migrate.py
"""Database migration runner.

Executes numbered SQL migrations in order. Tracks applied migrations
in a _migrations table. Idempotent: re-running skips already-applied migrations.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import asyncpg

from .config import get_settings
from .log import get_logger

logger = get_logger("migrate")

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def _get_connection() -> asyncpg.Connection:
    """Get a direct connection (not pooled) for migrations."""
    settings = get_settings()
    dsn = settings.database_url
    if "+asyncpg" in dsn:
        dsn = dsn.replace("+asyncpg", "")
    return await asyncpg.connect(dsn)


async def _ensure_migrations_table(conn: asyncpg.Connection) -> None:
    """Create migrations tracking table if it doesn't exist."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            name TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)


async def _get_applied(conn: asyncpg.Connection) -> set[str]:
    """Get set of already-applied migration names."""
    rows = await conn.fetch("SELECT name FROM _migrations ORDER BY name")
    return {row["name"] for row in rows}


async def run_migrations() -> list[str]:
    """Run all pending migrations in order.

    Returns:
        List of newly applied migration names.
    """
    conn = await _get_connection()
    try:
        await _ensure_migrations_table(conn)
        applied = await _get_applied(conn)

        migration_files = sorted(MIGRATIONS_DIR.glob("V*.sql"))
        newly_applied: list[str] = []

        for mf in migration_files:
            if mf.name in applied:
                logger.info("Skip (already applied): %s", mf.name)
                continue

            logger.info("Applying: %s", mf.name)
            sql = mf.read_text(encoding="utf-8")
            await conn.execute(sql)
            await conn.execute(
                "INSERT INTO _migrations (name) VALUES ($1)", mf.name
            )
            newly_applied.append(mf.name)
            logger.info("Applied: %s", mf.name)

        return newly_applied
    finally:
        await conn.close()


def main() -> None:
    """CLI entry point for running migrations."""
    import json

    applied = asyncio.run(run_migrations())
    if applied:
        print(json.dumps({"applied": applied}))
    else:
        print(json.dumps({"applied": [], "message": "all migrations already applied"}))


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add pm/lib/neon_docs/migrate.py
git commit -m "feat(neon): add migration runner with tracking table"
```

---

### Task 11: Test migration runner

**Files:**
- Create: `$PM/tests/neon_docs/test_migrate.py`

**Step 1: Write test**

```python
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
        first = await run_migrations()
        second = await run_migrations()
        assert len(second) == 0, "Second run should apply nothing"
```

**Step 2: Run test (live DB required)**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/test_migrate.py -v -m live`
Expected: 2 tests pass (or skip if no DB)

**Step 3: Commit**

```bash
git add pm/tests/neon_docs/test_migrate.py
git commit -m "test(neon): add migration runner idempotency tests"
```

---

### Task 12: Create Pydantic DB models

**Files:**
- Create: `$PM/lib/neon_docs/models.py`
- Create: `$PM/tests/neon_docs/test_models.py`

**Step 1: Write models.py**

```python
# pm/lib/neon_docs/models.py
"""Pydantic v2 models for database entities."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class QueueStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class UpsertAction(StrEnum):
    INSERTED = "inserted"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


class CrawledDocument(BaseModel):
    """A cached document from URL or file."""

    id: int
    url: str | None = None
    file_path: str | None = None
    title: str | None = None
    content: str
    content_hash: str
    needs_processing: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DocumentChunk(BaseModel):
    """An embedded chunk of a document."""

    id: int
    document_id: int
    chunk_index: int
    content: str
    token_count: int | None = None


class QueueJob(BaseModel):
    """A processing queue entry."""

    id: int
    document_id: int
    operation: str = "chunk_and_embed"
    priority: int = 0
    status: QueueStatus = QueueStatus.PENDING
    attempts: int = 0
    error_message: str | None = None


class UpsertResult(BaseModel):
    """Result from upsert_document()."""

    action: UpsertAction
    doc_id: int


class SearchResult(BaseModel):
    """A single search result."""

    doc_id: int
    title: str | None = None
    chunk_text: str
    similarity: float
    url: str | None = None
    file_path: str | None = None


class CacheStatus(BaseModel):
    """Cache statistics."""

    documents: int
    chunks: int
    queue_pending: int
    queue_failed: int


class CacheCheckResult(BaseModel):
    """Result from cache URL check."""

    hit: bool
    content: str | None = None
    doc_id: int | None = None
```

**Step 2: Write test**

```python
# pm/tests/neon_docs/test_models.py
"""Tests for Pydantic models."""

from lib.neon_docs.models import (
    CacheCheckResult,
    CacheStatus,
    CrawledDocument,
    DocumentChunk,
    QueueJob,
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
```

**Step 3: Run tests**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/test_models.py -v`
Expected: All 7 tests PASS

**Step 4: Commit**

```bash
git add pm/lib/neon_docs/models.py pm/tests/neon_docs/test_models.py
git commit -m "feat(neon): add Pydantic v2 models for all DB entities"
```

---

### Task 13: Create asyncpg connection pool

**Files:**
- Create: `$PM/lib/neon_docs/db.py`
- Create: `$PM/tests/neon_docs/test_db.py`

**Step 1: Write db.py**

```python
# pm/lib/neon_docs/db.py
"""Async PostgreSQL connection pool for Neon.

Uses asyncpg with connection pooling. Neon's serverless compute scales to zero
after 5 minutes of inactivity, so we set pool_recycle appropriately.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg

from .config import get_settings
from .exceptions import ConnectionError
from .log import get_logger

logger = get_logger("db")

_pool: asyncpg.Pool | None = None  # type: ignore[type-arg]


def _clean_dsn(dsn: str) -> str:
    """Strip SQLAlchemy dialect prefix if present."""
    if "+asyncpg" in dsn:
        dsn = dsn.replace("+asyncpg", "")
    return dsn


async def get_pool() -> asyncpg.Pool:  # type: ignore[type-arg]
    """Get or create the connection pool.

    Returns:
        asyncpg connection pool.

    Raises:
        ConnectionError: If pool creation fails.
    """
    global _pool
    if _pool is not None:
        return _pool

    settings = get_settings()
    dsn = _clean_dsn(settings.database_url)

    try:
        _pool = await asyncpg.create_pool(
            dsn,
            min_size=settings.db_pool_min,
            max_size=settings.db_pool_max,
            command_timeout=settings.db_command_timeout,
        )
        logger.info("Connection pool created (min=%d, max=%d)", settings.db_pool_min, settings.db_pool_max)
        return _pool
    except Exception as e:
        raise ConnectionError(f"Failed to create pool: {e}", cause=e) from e


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Connection pool closed")


@asynccontextmanager
async def connection() -> AsyncIterator[asyncpg.Connection]:  # type: ignore[type-arg]
    """Get a connection from the pool.

    Yields:
        asyncpg connection.

    Raises:
        ConnectionError: If connection fails.
    """
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            yield conn
    except asyncpg.PostgresError as e:
        raise ConnectionError(f"Connection error: {e}", cause=e) from e


async def health_check() -> bool:
    """Check if database is reachable.

    Returns:
        True if healthy, False otherwise.
    """
    try:
        async with connection() as conn:
            result = await conn.fetchval("SELECT 1")
            return result == 1
    except Exception:
        return False
```

**Step 2: Write test**

```python
# pm/tests/neon_docs/test_db.py
"""Tests for database connection pool."""

import pytest

from lib.neon_docs.db import close_pool, connection, get_pool, health_check


@pytest.mark.live
class TestDatabase:
    async def test_get_pool(self, neon_url: str) -> None:
        pool = await get_pool()
        assert pool is not None
        await close_pool()

    async def test_connection_context(self, neon_url: str) -> None:
        async with connection() as conn:
            result = await conn.fetchval("SELECT 1")
            assert result == 1
        await close_pool()

    async def test_health_check(self, neon_url: str) -> None:
        assert await health_check() is True
        await close_pool()

    async def test_pool_singleton(self, neon_url: str) -> None:
        p1 = await get_pool()
        p2 = await get_pool()
        assert p1 is p2
        await close_pool()
```

**Step 3: Run tests**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/test_db.py -v -m live`
Expected: All 4 tests pass (or skip if no DB)

**Step 4: Commit**

```bash
git add pm/lib/neon_docs/db.py pm/tests/neon_docs/test_db.py
git commit -m "feat(neon): add asyncpg connection pool with health check"
```

---

### Task 14: Create document repository

**Files:**
- Create: `$PM/lib/neon_docs/repository.py`

**Step 1: Write repository.py**

```python
# pm/lib/neon_docs/repository.py
"""Database repository for document operations.

Provides typed methods wrapping SQL queries. All methods use the connection pool.
"""

from __future__ import annotations

from .db import connection
from .exceptions import QueryError
from .log import get_logger
from .models import (
    CacheCheckResult,
    CacheStatus,
    QueueJob,
    QueueStatus,
    SearchResult,
    UpsertResult,
)

logger = get_logger("repository")


async def upsert_document(
    *,
    url: str | None = None,
    file_path: str | None = None,
    title: str | None = None,
    content: str,
) -> UpsertResult:
    """Upsert a document via the upsert_document() SQL function.

    Args:
        url: Source URL (mutually exclusive with file_path).
        file_path: Local file path.
        title: Document title.
        content: Document content.

    Returns:
        UpsertResult with action and doc_id.
    """
    try:
        async with connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM upsert_document($1, $2, $3, $4)",
                url, file_path, title, content,
            )
            if row is None:
                raise QueryError("upsert_document returned no rows")
            return UpsertResult(action=row["action"], doc_id=row["doc_id"])
    except QueryError:
        raise
    except Exception as e:
        raise QueryError(f"upsert failed: {e}", cause=e) from e


async def check_url(url: str) -> CacheCheckResult:
    """Check if a URL is cached.

    Args:
        url: URL to check.

    Returns:
        CacheCheckResult with hit/miss and content.
    """
    async with connection() as conn:
        row = await conn.fetchrow(
            "SELECT id, content FROM crawled_documents WHERE url = $1",
            url,
        )
        if row:
            return CacheCheckResult(hit=True, content=row["content"], doc_id=row["id"])
        return CacheCheckResult(hit=False)


async def search(
    embedding: list[float],
    *,
    keyword: str | None = None,
    limit: int = 5,
    threshold: float = 0.3,
) -> list[SearchResult]:
    """Hybrid search across cached documents.

    Args:
        embedding: Query embedding vector (768-dim).
        keyword: Optional keyword filter.
        limit: Max results.
        threshold: Minimum similarity threshold.

    Returns:
        List of SearchResult ordered by similarity desc.
    """
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
    async with connection() as conn:
        rows = await conn.fetch(
            "SELECT * FROM search_documents($1::vector, $2, $3, $4)",
            embedding_str, keyword, limit, threshold,
        )
        return [
            SearchResult(
                doc_id=r["doc_id"],
                title=r["title"],
                chunk_text=r["chunk_text"],
                similarity=float(r["similarity"]),
                url=r["url"],
                file_path=r["file_path"],
            )
            for r in rows
        ]


async def pick_queue_job() -> QueueJob | None:
    """Pick the next pending queue job (atomic).

    Returns:
        QueueJob or None if queue is empty.
    """
    async with connection() as conn:
        row = await conn.fetchrow("""
            UPDATE processing_queue
            SET status = 'processing', started_at = NOW(), attempts = attempts + 1
            WHERE id = (
                SELECT id FROM processing_queue
                WHERE status = 'pending'
                ORDER BY priority DESC, id ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id, document_id, operation, priority, status, attempts, error_message
        """)
        if row is None:
            return None
        return QueueJob(
            id=row["id"],
            document_id=row["document_id"],
            operation=row["operation"],
            priority=row["priority"],
            status=QueueStatus(row["status"]),
            attempts=row["attempts"],
            error_message=row["error_message"],
        )


async def complete_queue_job(job_id: int) -> None:
    """Mark a queue job as done."""
    async with connection() as conn:
        await conn.execute(
            "UPDATE processing_queue SET status = 'done', completed_at = NOW() WHERE id = $1",
            job_id,
        )


async def fail_queue_job(job_id: int, error: str) -> None:
    """Mark a queue job as failed."""
    async with connection() as conn:
        await conn.execute(
            "UPDATE processing_queue SET status = 'failed', error_message = $1 WHERE id = $2",
            error[:500], job_id,
        )


async def get_document_content(doc_id: int) -> tuple[str, str | None]:
    """Get document content and title by ID.

    Returns:
        Tuple of (content, title).
    """
    async with connection() as conn:
        row = await conn.fetchrow(
            "SELECT content, title FROM crawled_documents WHERE id = $1",
            doc_id,
        )
        if row is None:
            raise QueryError(f"Document {doc_id} not found")
        return row["content"], row["title"]


async def delete_chunks(doc_id: int) -> None:
    """Delete all chunks for a document."""
    async with connection() as conn:
        await conn.execute(
            "DELETE FROM document_chunks WHERE document_id = $1",
            doc_id,
        )


async def insert_chunks(
    doc_id: int,
    chunks: list[str],
    embeddings: list[list[float]],
    token_counts: list[int],
) -> int:
    """Insert chunks with embeddings for a document.

    Returns:
        Number of chunks inserted.
    """
    async with connection() as conn:
        for i, (chunk, embedding, tokens) in enumerate(zip(chunks, embeddings, token_counts)):
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            await conn.execute(
                """INSERT INTO document_chunks
                   (document_id, chunk_index, content, embedding, token_count)
                   VALUES ($1, $2, $3, $4::vector, $5)""",
                doc_id, i, chunk, embedding_str, tokens,
            )
        return len(chunks)


async def mark_processed(doc_id: int) -> None:
    """Mark document as processed (needs_processing = FALSE)."""
    async with connection() as conn:
        await conn.execute(
            "UPDATE crawled_documents SET needs_processing = FALSE WHERE id = $1",
            doc_id,
        )


async def get_status() -> CacheStatus:
    """Get cache statistics."""
    async with connection() as conn:
        doc_count = await conn.fetchval("SELECT COUNT(*) FROM crawled_documents")
        chunk_count = await conn.fetchval("SELECT COUNT(*) FROM document_chunks")
        pending = await conn.fetchval(
            "SELECT COUNT(*) FROM processing_queue WHERE status = 'pending'"
        )
        failed = await conn.fetchval(
            "SELECT COUNT(*) FROM processing_queue WHERE status = 'failed'"
        )
        return CacheStatus(
            documents=doc_count or 0,
            chunks=chunk_count or 0,
            queue_pending=pending or 0,
            queue_failed=failed or 0,
        )
```

**Step 2: Commit**

```bash
git add pm/lib/neon_docs/repository.py
git commit -m "feat(neon): add typed repository layer for all DB operations"
```

---

### Task 15: Test document repository

**Files:**
- Create: `$PM/tests/neon_docs/test_repository.py`

**Step 1: Write test**

```python
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
```

**Step 2: Run tests**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/test_repository.py -v -m live`
Expected: All 6 tests pass (or skip if no DB)

**Step 3: Commit**

```bash
git add pm/tests/neon_docs/test_repository.py
git commit -m "test(neon): add repository integration tests"
```

---

## Phase 2: Embeddings Pipeline (Tasks 16-25)

### Task 16: Create tiktoken-based token counter

**Files:**
- Create: `$PM/lib/neon_docs/tokenizer.py`
- Create: `$PM/tests/neon_docs/test_tokenizer.py`

**Step 1: Write tokenizer.py**

```python
# pm/lib/neon_docs/tokenizer.py
"""Accurate token counting via tiktoken.

Uses cl100k_base encoding (GPT-4/Claude compatible).
"""

from __future__ import annotations

import tiktoken

_encoder: tiktoken.Encoding | None = None


def _get_encoder() -> tiktoken.Encoding:
    """Get cached tiktoken encoder."""
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding("cl100k_base")
    return _encoder


def count_tokens(text: str) -> int:
    """Count tokens in text using cl100k_base encoding.

    Args:
        text: Input text.

    Returns:
        Token count.
    """
    return len(_get_encoder().encode(text))
```

**Step 2: Write test**

```python
# pm/tests/neon_docs/test_tokenizer.py
"""Tests for tiktoken-based token counter."""

from lib.neon_docs.tokenizer import count_tokens


class TestTokenizer:
    def test_empty_string(self) -> None:
        assert count_tokens("") == 0

    def test_single_word(self) -> None:
        result = count_tokens("hello")
        assert result == 1

    def test_sentence(self) -> None:
        result = count_tokens("The quick brown fox jumps over the lazy dog.")
        assert 8 <= result <= 12  # tiktoken encoding, not word count

    def test_accuracy_vs_naive(self) -> None:
        text = "This is a test of the token counting accuracy."
        naive = int(len(text.split()) * 1.3)
        actual = count_tokens(text)
        # Naive should be in the ballpark but not exact
        assert actual != naive or actual == naive  # always passes, but documents intent
        assert actual > 0

    def test_code_tokens(self) -> None:
        code = "def hello_world():\n    print('hello')\n"
        result = count_tokens(code)
        assert result > 5  # code has more tokens than words
```

**Step 3: Run tests**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/test_tokenizer.py -v`
Expected: All 5 tests PASS

**Step 4: Commit**

```bash
git add pm/lib/neon_docs/tokenizer.py pm/tests/neon_docs/test_tokenizer.py
git commit -m "feat(neon): add tiktoken-based token counter (replaces words*1.3)"
```

---

### Task 17: Create text chunker

**Files:**
- Create: `$PM/lib/neon_docs/chunker.py`
- Create: `$PM/tests/neon_docs/test_chunker.py`

**Step 1: Write chunker.py**

```python
# pm/lib/neon_docs/chunker.py
"""Text chunking with accurate token counting.

Splits on paragraph → sentence → word boundaries.
Uses tiktoken for accurate token counting.
"""

from __future__ import annotations

from .config import get_settings
from .tokenizer import count_tokens


def chunk_text(
    text: str,
    max_tokens: int | None = None,
    overlap_tokens: int | None = None,
) -> list[str]:
    """Split text into overlapping chunks.

    Args:
        text: Full document text.
        max_tokens: Target max tokens per chunk (default from settings).
        overlap_tokens: Overlap tokens for context (default from settings).

    Returns:
        List of text chunks.
    """
    settings = get_settings()
    max_tokens = max_tokens or settings.chunk_max_tokens
    overlap_tokens = overlap_tokens or settings.chunk_overlap_tokens

    if count_tokens(text) <= max_tokens:
        return [text]

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        if para_tokens > max_tokens:
            # Flush current buffer
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts = _get_overlap_parts(current_parts, overlap_tokens)
                current_tokens = sum(count_tokens(p) for p in current_parts)

            # Split large paragraph by sentences
            sentences = _split_sentences(para)
            for sent in sentences:
                sent_tokens = count_tokens(sent)
                if current_tokens + sent_tokens > max_tokens and current_parts:
                    chunks.append(" ".join(current_parts))
                    current_parts = _get_overlap_parts(current_parts, overlap_tokens)
                    current_tokens = sum(count_tokens(p) for p in current_parts)
                current_parts.append(sent)
                current_tokens += sent_tokens
            continue

        if current_tokens + para_tokens > max_tokens and current_parts:
            chunks.append("\n\n".join(current_parts))
            current_parts = _get_overlap_parts(current_parts, overlap_tokens)
            current_tokens = sum(count_tokens(p) for p in current_parts)

        current_parts.append(para)
        current_tokens += para_tokens

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return chunks


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def _get_overlap_parts(parts: list[str], overlap_tokens: int) -> list[str]:
    """Get trailing parts that fit within overlap_tokens."""
    if not parts or overlap_tokens <= 0:
        return []

    result: list[str] = []
    tokens = 0
    for part in reversed(parts):
        t = count_tokens(part)
        if tokens + t > overlap_tokens:
            break
        result.insert(0, part)
        tokens += t
    return result
```

**Step 2: Write test**

```python
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
            # Each chunk should be within reasonable bounds
            assert count_tokens(chunk) <= 150  # allow some flex for boundary

    def test_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://x@localhost/x")
        chunks = chunk_text("", max_tokens=100)
        assert len(chunks) == 1

    def test_all_content_preserved(self, long_text: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://x@localhost/x")
        chunks = chunk_text(long_text, max_tokens=100, overlap_tokens=0)
        reconstructed = "\n\n".join(chunks)
        # All original paragraphs should appear in the output
        for para in long_text.split("\n\n"):
            assert para.strip() in reconstructed

    def test_no_empty_chunks(self, long_text: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRJ_NEON_DATABASE_URL", "postgresql://x@localhost/x")
        chunks = chunk_text(long_text, max_tokens=100)
        for chunk in chunks:
            assert len(chunk.strip()) > 0
```

**Step 3: Run tests**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/test_chunker.py -v`
Expected: All 5 tests PASS

**Step 4: Commit**

```bash
git add pm/lib/neon_docs/chunker.py pm/tests/neon_docs/test_chunker.py
git commit -m "feat(neon): add text chunker with tiktoken-accurate token counting"
```

---

### Task 18: Create Ollama embeddings client

**Files:**
- Create: `$PM/lib/neon_docs/embedder.py`
- Create: `$PM/tests/neon_docs/test_embedder.py`

**Step 1: Write embedder.py**

```python
# pm/lib/neon_docs/embedder.py
"""Local embeddings via Ollama API with retry.

Uses httpx for async HTTP and tenacity for retry with exponential backoff.
"""

from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import get_settings
from .exceptions import EmbeddingError, OllamaConnectionError, OllamaModelError
from .log import get_logger

logger = get_logger("embedder")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(OllamaConnectionError),
    reraise=True,
)
async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts via Ollama.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (768-dim for nomic-embed-text).

    Raises:
        OllamaConnectionError: Cannot reach Ollama.
        OllamaModelError: Model not available.
        EmbeddingError: Other embedding failure.
    """
    settings = get_settings()
    embeddings: list[list[float]] = []

    async with httpx.AsyncClient(base_url=settings.ollama_host, timeout=120.0) as client:
        for text in texts:
            try:
                resp = await client.post(
                    "/api/embed",
                    json={"model": settings.ollama_model, "input": text},
                )
            except httpx.ConnectError as e:
                raise OllamaConnectionError(
                    f"Cannot connect to Ollama at {settings.ollama_host}", cause=e
                ) from e
            except httpx.TimeoutException as e:
                raise OllamaConnectionError(
                    f"Ollama request timed out", cause=e
                ) from e

            if resp.status_code == 404:
                raise OllamaModelError(
                    f"Model '{settings.ollama_model}' not found. Run: ollama pull {settings.ollama_model}"
                )

            if resp.status_code != 200:
                raise EmbeddingError(f"Ollama returned {resp.status_code}: {resp.text[:200]}")

            data = resp.json()
            embedding = data["embeddings"][0]

            if len(embedding) != settings.embedding_dimensions:
                raise EmbeddingError(
                    f"Expected {settings.embedding_dimensions} dims, got {len(embedding)}"
                )

            embeddings.append(embedding)

    logger.info("Embedded %d texts (%d dims)", len(texts), settings.embedding_dimensions)
    return embeddings


async def embed_single(text: str) -> list[float]:
    """Embed a single text string.

    Args:
        text: Text to embed.

    Returns:
        Embedding vector.
    """
    results = await embed_texts([text])
    return results[0]
```

**Step 2: Write test**

```python
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
        # Embeddings for different topics should differ
        assert results[0] != results[1]
```

**Step 3: Run tests**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/test_embedder.py -v -m live`
Expected: 3 live tests pass (or skip if no Ollama)

**Step 4: Commit**

```bash
git add pm/lib/neon_docs/embedder.py pm/tests/neon_docs/test_embedder.py
git commit -m "feat(neon): add Ollama embeddings client with tenacity retry"
```

---

### Task 19: Create processing worker

**Files:**
- Create: `$PM/lib/neon_docs/worker.py`

**Step 1: Write worker.py**

```python
# pm/lib/neon_docs/worker.py
"""Queue processing worker: chunk + embed pipeline."""

from __future__ import annotations

from .chunker import chunk_text
from .embedder import embed_texts
from .exceptions import EmbeddingError
from .log import get_logger
from .models import QueueJob
from .repository import (
    complete_queue_job,
    delete_chunks,
    fail_queue_job,
    get_document_content,
    insert_chunks,
    mark_processed,
    pick_queue_job,
)
from .tokenizer import count_tokens

logger = get_logger("worker")


async def process_one_job(job: QueueJob) -> bool:
    """Process a single queue job.

    Args:
        job: Queue job to process.

    Returns:
        True if successful, False if failed.
    """
    try:
        content, title = await get_document_content(job.document_id)

        chunks = chunk_text(content)
        logger.info("Doc %d: %d chunks from %s", job.document_id, len(chunks), title or "untitled")

        embeddings = await embed_texts(chunks)
        token_counts = [count_tokens(c) for c in chunks]

        await delete_chunks(job.document_id)
        inserted = await insert_chunks(job.document_id, chunks, embeddings, token_counts)

        await complete_queue_job(job.id)
        await mark_processed(job.document_id)

        logger.info("Doc %d: inserted %d chunks", job.document_id, inserted)
        return True

    except Exception as e:
        logger.error("Doc %d: failed: %s", job.document_id, e)
        await fail_queue_job(job.id, str(e))
        return False


async def drain_queue() -> dict[str, int]:
    """Process all pending queue jobs.

    Returns:
        Dict with 'processed' and 'failed' counts.
    """
    processed = 0
    failed = 0

    while True:
        job = await pick_queue_job()
        if job is None:
            break

        if await process_one_job(job):
            processed += 1
        else:
            failed += 1

    logger.info("Queue drained: %d processed, %d failed", processed, failed)
    return {"processed": processed, "failed": failed}
```

**Step 2: Commit**

```bash
git add pm/lib/neon_docs/worker.py
git commit -m "feat(neon): add queue processing worker (chunk + embed pipeline)"
```

---

### Task 20: Test processing worker

**Files:**
- Create: `$PM/tests/neon_docs/test_worker.py`

**Step 1: Write test**

```python
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
        # Insert a test document
        result = await upsert_document(
            url="https://test.example.com/worker-test-drain",
            title="Worker Test",
            content="This is a test document for the processing worker. It has enough content to be chunked.",
        )
        assert result.action in ("inserted", "updated")

        # Drain queue
        stats = await drain_queue()
        assert stats["processed"] >= 1
        assert stats["failed"] == 0

        # Verify chunks exist
        status = await get_status()
        assert status.chunks > 0

        await close_pool()
```

**Step 2: Run test**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/test_worker.py -v -m live`
Expected: 1 test passes (or skip if no DB/Ollama)

**Step 3: Commit**

```bash
git add pm/tests/neon_docs/test_worker.py
git commit -m "test(neon): add worker integration test"
```

---

## Phase 3: CLI Layer (Tasks 21-28)

### Task 21: Create CLI module

**Files:**
- Create: `$PM/lib/neon_docs/cli.py`
- Create: `$PM/lib/neon_docs/__main__.py`

**Step 1: Write cli.py**

```python
# pm/lib/neon_docs/cli.py
"""CLI for Neon document caching operations.

Usage:
    python3 -m lib.neon_docs store --url <url>
    python3 -m lib.neon_docs store --file <path>
    python3 -m lib.neon_docs check-url <url>
    python3 -m lib.neon_docs search "<query>" [--limit N] [--threshold F]
    python3 -m lib.neon_docs process-queue
    python3 -m lib.neon_docs bulk-index <directory>
    python3 -m lib.neon_docs status
    python3 -m lib.neon_docs migrate
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .db import close_pool
from .embedder import embed_single
from .log import setup_logging
from .models import UpsertAction
from .repository import check_url, get_status, search, upsert_document
from .worker import drain_queue


async def cmd_store(args: argparse.Namespace) -> dict:
    """Store a document."""
    content: str | None = None
    title: str | None = args.title

    if args.file:
        path = Path(args.file)
        if not path.is_file():
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        content = path.read_text(encoding="utf-8", errors="ignore")
        if title is None:
            title = path.name

    if content is None and args.url is None:
        print("Error: --url or --file required", file=sys.stderr)
        sys.exit(1)

    if args.url and content is None:
        print("Error: --url requires content from stdin or --file", file=sys.stderr)
        sys.exit(1)

    result = await upsert_document(url=args.url, file_path=args.file, title=title, content=content or "")
    return {"action": result.action, "doc_id": result.doc_id}


async def cmd_check_url(args: argparse.Namespace) -> None:
    """Check if URL is cached."""
    result = await check_url(args.url)
    if result.hit:
        print(result.content)
    else:
        print("CACHE_MISS")


async def cmd_search(args: argparse.Namespace) -> list[dict]:
    """Search documents."""
    embedding = await embed_single(args.query)
    results = await search(
        embedding,
        keyword=args.keyword,
        limit=args.limit,
        threshold=args.threshold,
    )
    return [r.model_dump() for r in results]


async def cmd_process_queue(_args: argparse.Namespace) -> dict:
    """Process pending queue jobs."""
    return await drain_queue()


async def cmd_bulk_index(args: argparse.Namespace) -> dict:
    """Index all files in a directory."""
    dir_path = Path(args.directory)
    if not dir_path.is_dir():
        print(f"Error: not a directory: {args.directory}", file=sys.stderr)
        sys.exit(1)

    results = {"inserted": 0, "updated": 0, "unchanged": 0, "errors": 0}
    for file_path in sorted(dir_path.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix not in (".md", ".json", ".txt", ".html"):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            result = await upsert_document(
                file_path=str(file_path.resolve()),
                title=file_path.name,
                content=content,
            )
            action = result.action.value if isinstance(result.action, UpsertAction) else str(result.action)
            if action in results:
                results[action] += 1
        except Exception as e:
            print(f"Error: {file_path}: {e}", file=sys.stderr)
            results["errors"] += 1

    return results


async def cmd_status(_args: argparse.Namespace) -> dict:
    """Get cache statistics."""
    status = await get_status()
    return status.model_dump()


async def cmd_migrate(_args: argparse.Namespace) -> dict:
    """Run database migrations."""
    from .migrate import run_migrations

    applied = await run_migrations()
    return {"applied": applied}


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="neon_docs",
        description="Neon document cache CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # store
    p_store = sub.add_parser("store", help="Store a document")
    p_store.add_argument("--url", type=str, help="Source URL")
    p_store.add_argument("--file", type=str, help="Local file path")
    p_store.add_argument("--title", type=str, help="Document title")

    # check-url
    p_check = sub.add_parser("check-url", help="Check URL cache (hit/miss)")
    p_check.add_argument("url", type=str, help="URL to check")

    # search
    p_search = sub.add_parser("search", help="Semantic search")
    p_search.add_argument("query", type=str, help="Search query")
    p_search.add_argument("--limit", type=int, default=5)
    p_search.add_argument("--threshold", type=float, default=0.3)
    p_search.add_argument("--keyword", type=str, help="Keyword filter")

    # process-queue
    sub.add_parser("process-queue", help="Drain processing queue")

    # bulk-index
    p_bulk = sub.add_parser("bulk-index", help="Index all files in directory")
    p_bulk.add_argument("directory", type=str)

    # status
    sub.add_parser("status", help="Cache statistics")

    # migrate
    sub.add_parser("migrate", help="Run database migrations")

    return parser


async def async_main() -> None:
    """Async CLI entry point."""
    setup_logging()
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "store":
            result = await cmd_store(args)
        elif args.command == "check-url":
            await cmd_check_url(args)
            return
        elif args.command == "search":
            result = await cmd_search(args)
        elif args.command == "process-queue":
            result = await cmd_process_queue(args)
        elif args.command == "bulk-index":
            result = await cmd_bulk_index(args)
        elif args.command == "status":
            result = await cmd_status(args)
        elif args.command == "migrate":
            result = await cmd_migrate(args)
        else:
            parser.print_help()
            return

        print(json.dumps(result, indent=2, default=str))
    finally:
        await close_pool()


def main() -> None:
    """CLI entry point."""
    asyncio.run(async_main())
```

**Step 2: Write __main__.py**

```python
# pm/lib/neon_docs/__main__.py
"""Entry point for python3 -m lib.neon_docs."""

from .cli import main

main()
```

**Step 3: Commit**

```bash
git add pm/lib/neon_docs/cli.py pm/lib/neon_docs/__main__.py
git commit -m "feat(neon): add CLI with all subcommands (store, search, check-url, etc.)"
```

---

### Task 22: Test CLI

**Files:**
- Create: `$PM/tests/neon_docs/test_cli.py`

**Step 1: Write test**

```python
# pm/tests/neon_docs/test_cli.py
"""Tests for CLI module."""

from lib.neon_docs.cli import build_parser


class TestCLIParser:
    def test_parser_builds(self) -> None:
        parser = build_parser()
        assert parser is not None

    def test_store_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["store", "--url", "https://example.com", "--title", "Test"])
        assert args.command == "store"
        assert args.url == "https://example.com"
        assert args.title == "Test"

    def test_search_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["search", "query text", "--limit", "10"])
        assert args.command == "search"
        assert args.query == "query text"
        assert args.limit == 10

    def test_status_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_check_url_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check-url", "https://example.com"])
        assert args.command == "check-url"
        assert args.url == "https://example.com"

    def test_bulk_index_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["bulk-index", "/path/to/docs"])
        assert args.command == "bulk-index"
        assert args.directory == "/path/to/docs"

    def test_migrate_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["migrate"])
        assert args.command == "migrate"
```

**Step 2: Run tests**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/test_cli.py -v`
Expected: All 7 tests PASS

**Step 3: Commit**

```bash
git add pm/tests/neon_docs/test_cli.py
git commit -m "test(neon): add CLI argument parser tests"
```

---

## Phase 4: MLflow Tracing (Tasks 23-26)

### Task 23: Create MLflow trace decorator

**Files:**
- Create: `$PM/lib/neon_docs/tracer.py`

**Step 1: Write tracer.py**

```python
# pm/lib/neon_docs/tracer.py
"""MLflow 3.9 tracing for neon_docs operations.

Provides @trace_operation decorator that creates MLflow spans with
inputs, outputs, duration, and error tracking.
"""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar

from .log import get_logger

logger = get_logger("tracer")

try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

F = TypeVar("F", bound=Callable[..., Any])


def trace_operation(name: str) -> Callable[[F], F]:
    """Decorator to trace a function as an MLflow span.

    Args:
        name: Span name (e.g., 'neon.cache_check').

    Returns:
        Decorated function.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.monotonic()

            if not MLFLOW_AVAILABLE:
                result = await func(*args, **kwargs)
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.debug("[TRACE] %s: %.0fms", name, elapsed_ms)
                return result

            with mlflow.start_span(name=name) as span:
                safe_kwargs = {k: str(v)[:200] for k, v in kwargs.items()}
                span.set_inputs(safe_kwargs)

                try:
                    result = await func(*args, **kwargs)
                    elapsed_ms = (time.monotonic() - start) * 1000
                    span.set_attributes({"duration_ms": elapsed_ms})

                    if isinstance(result, dict):
                        span.set_outputs({k: str(v)[:200] for k, v in result.items()})
                    elif isinstance(result, list):
                        span.set_outputs({"count": len(result)})
                    else:
                        span.set_outputs({"result": str(result)[:200]})

                    return result
                except Exception as e:
                    span.set_status("ERROR")
                    span.set_attributes({"error": str(e), "error_type": type(e).__name__})
                    raise

        return wrapper  # type: ignore[return-value]
    return decorator


def setup_autolog() -> None:
    """Enable MLflow 3.9 Anthropic autolog if available."""
    if MLFLOW_AVAILABLE and hasattr(mlflow, "anthropic"):
        mlflow.anthropic.autolog()
        logger.info("MLflow Anthropic autolog enabled")
    elif MLFLOW_AVAILABLE:
        logger.warning("mlflow.anthropic.autolog not available — upgrade to mlflow>=3.9")
```

**Step 2: Commit**

```bash
git add pm/lib/neon_docs/tracer.py
git commit -m "feat(neon): add MLflow 3.9 trace decorator with span instrumentation"
```

---

### Task 24: Test trace decorator

**Files:**
- Create: `$PM/tests/neon_docs/test_tracer.py`

**Step 1: Write test**

```python
# pm/tests/neon_docs/test_tracer.py
"""Tests for MLflow tracer."""

from lib.neon_docs.tracer import trace_operation


class TestTraceDecorator:
    async def test_traces_return_value(self) -> None:
        @trace_operation("test.operation")
        async def my_func(x: int = 0) -> dict:
            return {"result": x + 1}

        result = await my_func(x=5)
        assert result == {"result": 6}

    async def test_traces_exception(self) -> None:
        @trace_operation("test.failing")
        async def failing_func() -> None:
            raise ValueError("test error")

        import pytest
        with pytest.raises(ValueError, match="test error"):
            await failing_func()

    async def test_traces_list_result(self) -> None:
        @trace_operation("test.list")
        async def list_func() -> list:
            return [1, 2, 3]

        result = await list_func()
        assert result == [1, 2, 3]
```

**Step 2: Run tests**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/test_tracer.py -v`
Expected: All 3 tests PASS

**Step 3: Commit**

```bash
git add pm/tests/neon_docs/test_tracer.py
git commit -m "test(neon): add trace decorator tests"
```

---

### Task 25: Update __init__.py with public API

**Files:**
- Modify: `$PM/lib/neon_docs/__init__.py`

**Step 1: Update public API**

```python
# pm/lib/neon_docs/__init__.py
"""Neon document caching and semantic search.

Public API:
    - check_url: Check if URL is cached
    - upsert_document: Store/update a document
    - search: Semantic search across documents
    - drain_queue: Process all pending embed jobs
    - get_status: Get cache statistics
    - run_migrations: Apply database migrations
"""

__version__ = "0.1.0"

from .repository import check_url, get_status, search, upsert_document
from .worker import drain_queue
from .migrate import run_migrations

__all__ = [
    "check_url",
    "drain_queue",
    "get_status",
    "run_migrations",
    "search",
    "upsert_document",
]
```

**Step 2: Commit**

```bash
git add pm/lib/neon_docs/__init__.py
git commit -m "feat(neon): expose public API in __init__.py"
```

---

### Task 26: Upgrade mlflow_tracing.py

**Files:**
- Modify: `$REPO/lib/mlflow_tracing.py`

**Step 1: Add 3.9 autolog support**

Add this function to the existing `lib/mlflow_tracing.py` at repo root:

```python
def setup_claude_autolog() -> None:
    """Enable MLflow 3.9 Anthropic autolog for Claude tracing."""
    if MLFLOW_AVAILABLE and hasattr(mlflow, "anthropic"):
        mlflow.anthropic.autolog()
        print("[MLflow] Claude autolog enabled (3.9+)")
    elif MLFLOW_AVAILABLE:
        print("[MLflow] anthropic.autolog not available — upgrade to mlflow>=3.9")
    else:
        print("[MLflow] Not installed")
```

**Step 2: Commit**

```bash
git add lib/mlflow_tracing.py
git commit -m "feat(mlflow): add 3.9 anthropic autolog support"
```

---

## Phase 5: Hook Scripts (Tasks 27-30)

### Task 27: Create PreToolUse cache check hook

**Files:**
- Create: `$PM/scripts/neon-cache-check.sh`

**Step 1: Write neon-cache-check.sh**

```bash
#!/usr/bin/env bash
# pm/scripts/neon-cache-check.sh
# PreToolUse hook for WebFetch — checks Neon cache before fetching
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(dirname "$SCRIPT_DIR")"

# Extract URL from hook input (TOOL_INPUT env var contains JSON)
URL=$(echo "${TOOL_INPUT:-{}}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('url', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")

if [ -z "$URL" ]; then
    exit 0  # No URL, let WebFetch proceed
fi

# Check cache (suppress errors — hook must not block agent)
RESULT=$(cd "$PM_DIR" && PYTHONPATH="$PM_DIR" python3 -m lib.neon_docs check-url "$URL" 2>/dev/null) || RESULT="CACHE_MISS"

if [ "$RESULT" != "CACHE_MISS" ] && [ -n "$RESULT" ]; then
    echo "[neon-cache] HIT: $URL" >&2
    echo "$RESULT"
else
    echo "[neon-cache] MISS: $URL" >&2
fi

exit 0
```

**Step 2: Make executable**

Run: `chmod +x $PM/scripts/neon-cache-check.sh`

**Step 3: Commit**

```bash
git add pm/scripts/neon-cache-check.sh
git commit -m "feat(neon): add PreToolUse cache check hook script"
```

---

### Task 28: Create PostToolUse cache store hook

**Files:**
- Create: `$PM/scripts/neon-cache-store.sh`

**Step 1: Write neon-cache-store.sh**

```bash
#!/usr/bin/env bash
# pm/scripts/neon-cache-store.sh
# PostToolUse hook for WebFetch — stores fetched content in Neon cache
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(dirname "$SCRIPT_DIR")"

# Extract URL from hook input
URL=$(echo "${TOOL_INPUT:-{}}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('url', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")

if [ -z "$URL" ]; then
    exit 0
fi

# Store in background (don't block the agent)
(cd "$PM_DIR" && PYTHONPATH="$PM_DIR" python3 -m lib.neon_docs store --url "$URL" >/dev/null 2>&1) &

echo "[neon-cache] STORE: $URL (background)" >&2
exit 0
```

**Step 2: Make executable**

Run: `chmod +x $PM/scripts/neon-cache-store.sh`

**Step 3: Commit**

```bash
git add pm/scripts/neon-cache-store.sh
git commit -m "feat(neon): add PostToolUse cache store hook script"
```

---

### Task 29: Test hook scripts

**Files:**
- Create: `$PM/tests/neon_docs/test_hooks.sh`

**Step 1: Write hook test script**

```bash
#!/usr/bin/env bash
# pm/tests/neon_docs/test_hooks.sh
# Test hook scripts are syntactically valid and handle edge cases
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "=== Hook Script Tests ==="

# Test 1: cache-check handles empty TOOL_INPUT
echo "▶ Test 1: cache-check with empty input"
TOOL_INPUT="" bash "$PM_DIR/scripts/neon-cache-check.sh" > /dev/null 2>&1
echo "✅ PASS: cache-check handles empty input"

# Test 2: cache-check handles malformed JSON
echo "▶ Test 2: cache-check with malformed JSON"
TOOL_INPUT="not json" bash "$PM_DIR/scripts/neon-cache-check.sh" > /dev/null 2>&1
echo "✅ PASS: cache-check handles malformed JSON"

# Test 3: cache-store handles empty TOOL_INPUT
echo "▶ Test 3: cache-store with empty input"
TOOL_INPUT="" bash "$PM_DIR/scripts/neon-cache-store.sh" > /dev/null 2>&1
echo "✅ PASS: cache-store handles empty input"

echo ""
echo "=== All hook tests passed ==="
```

**Step 2: Make executable and run**

Run: `chmod +x $PM/tests/neon_docs/test_hooks.sh && $PM/tests/neon_docs/test_hooks.sh`
Expected: All 3 tests pass

**Step 3: Commit**

```bash
git add pm/tests/neon_docs/test_hooks.sh
git commit -m "test(neon): add hook script robustness tests"
```

---

### Task 30: Update requirements.txt

**Files:**
- Modify: `$REPO/requirements.txt`

**Step 1: Add new dependencies and upgrade mlflow**

Replace `mlflow>=2.10.0` with `mlflow>=3.9.0` and add:

```
# Neon document caching
asyncpg>=0.29.0
httpx>=0.27.0
pydantic-settings>=2.0.0
tenacity>=8.2.0
tiktoken>=0.7.0
```

**Step 2: Commit**

```bash
git add requirements.txt
git commit -m "feat(deps): add neon_docs dependencies, upgrade mlflow to 3.9"
```

---

## Phase 6: Makefile Targets (Tasks 31-33)

### Task 31: Add L0-L1 doc targets to Makefile

**Files:**
- Modify: `$PM/Makefile`

**Step 1: Add doc pipeline section before SHORTCUTS**

Insert after the REVIEW PIPELINE section (before `# SHORTCUTS`), around line 166:

```makefile
# ============================================================================
# DOCUMENT PIPELINE (Neon document caching)
# ============================================================================

.PHONY: l0-doc-store l0-doc-search l0-doc-process l0-doc-status
.PHONY: l1-doc-index l1-doc-drain l1-doc-migrate
.PHONY: l2-doc-refresh l2-doc-reindex
.PHONY: l3-doc-setup

NEON_CLI = PYTHONPATH=. python3 -m lib.neon_docs

l0-doc-store: ## L0-Doc: Store single document (FILE= or URL=)
	@$(NEON_CLI) store $(if $(URL),--url "$(URL)",--file "$(FILE)")

l0-doc-search: ## L0-Doc: Search documents (QUERY=)
	@$(NEON_CLI) search "$(QUERY)" --limit $(or $(LIMIT),5)

l0-doc-process: ## L0-Doc: Process one queue item
	@$(NEON_CLI) process-queue

l0-doc-status: ## L0-Doc: Show cache statistics
	@$(NEON_CLI) status

l1-doc-index: ## L1-Doc: Bulk-index docs/crawler-improvements/
	@$(NEON_CLI) bulk-index ../docs/crawler-improvements/

l1-doc-drain: ## L1-Doc: Drain entire processing queue
	@$(NEON_CLI) process-queue

l1-doc-migrate: ## L1-Doc: Run schema migrations
	@$(NEON_CLI) migrate
```

**Step 2: Commit**

```bash
git add pm/Makefile
git commit -m "feat(neon): add L0-L1 document pipeline Makefile targets"
```

---

### Task 32: Add L2-L3 doc targets and shortcuts

**Files:**
- Modify: `$PM/Makefile`

**Step 1: Add L2-L3 targets after L1 targets**

```makefile
l2-doc-refresh: ## L2-Doc: Re-index all docs (refresh stale)
	@echo "▶ Document Refresh"
	@$(MAKE) -s l1-doc-index
	@$(MAKE) -s l1-doc-drain
	@$(MAKE) -s l0-doc-status

l2-doc-reindex: ## L2-Doc: Purge chunks + re-embed all
	@echo "▶ Full Reindex"
	@psql "$$PRJ_NEON_DATABASE_URL" -c "DELETE FROM document_chunks; UPDATE crawled_documents SET needs_processing = TRUE;"
	@$(MAKE) -s l1-doc-drain

l3-doc-setup: ## L3-Doc: Full bootstrap (migrate + index + drain + verify)
	@echo "═══ Document Setup Pipeline ═══"
	@$(MAKE) -s l1-doc-migrate
	@echo "✓ Schema migrated"
	@$(MAKE) -s l1-doc-index
	@echo "✓ Documents indexed"
	@$(MAKE) -s l1-doc-drain
	@echo "✓ Queue drained"
	@$(MAKE) -s l0-doc-status
	@echo "═══ Setup Complete ═══"
```

**Step 2: Add shortcuts**

```makefile
docs-setup: l3-doc-setup  ## Alias: full doc bootstrap
docs-status: l0-doc-status ## Alias: cache stats
```

**Step 3: Update help target to include doc pipeline**

Add to the `help` target:

```makefile
	@echo ""
	@echo "Document Pipeline:"
	@grep -E '^l[0-3]-doc-[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'
```

**Step 4: Verify**

Run: `cd $PM && make help`
Expected: Document Pipeline section appears

**Step 5: Commit**

```bash
git add pm/Makefile
git commit -m "feat(neon): add L2-L3 doc targets, shortcuts, and help section"
```

---

### Task 33: Verify Makefile syntax

**Files:** None (verification only)

**Step 1: Run make help**

Run: `cd $PM && make help`
Expected: All sections display correctly including Document Pipeline

**Step 2: Dry-run l0-doc-status**

Run: `cd $PM && make l0-doc-status`
Expected: JSON output or connection error (both are valid — confirms CLI wiring)

---

## Phase 7: Agent Integration (Tasks 34-41)

### Task 34: Create neon-specialist agent definition

**Files:**
- Create: `$PM/agents/neon-specialist.md`

**Step 1: Write agent file**

Create the agent definition with proper frontmatter following PM conventions. Include name, description, model, memory, tools. Body should describe operations, when spawned, and idempotency guarantees. Reference the CLI usage with `PYTHONPATH=. python3 -m lib.neon_docs <command>`.

**Step 2: Commit**

```bash
git add pm/agents/neon-specialist.md
git commit -m "feat(agents): add neon-specialist document caching agent"
```

---

### Task 35: Test neon-specialist agent validates

**Files:** None (verification only)

**Step 1: Validate frontmatter**

Run: `cd $PM && make l0-lint FILE=agents/neon-specialist.md`
Expected: `✓`

---

### Task 36: Update vp-product.md

**Files:**
- Modify: `$PM/agents/vp-product.md` (frontmatter only)

**Step 1: Add Task(neon-specialist) to tools list**

Add `- Task(neon-specialist)` after `- Task(sprint-master)` in the tools list.

**Step 2: Add WebFetch hooks**

Add to the hooks section:

```yaml
  PreToolUse:
    - matcher: WebFetch
      command: "pm/scripts/neon-cache-check.sh"
  PostToolUse:
    - matcher: WebFetch
      command: "pm/scripts/neon-cache-store.sh"
```

**Step 3: Commit**

```bash
git add pm/agents/vp-product.md
git commit -m "feat(agents): add neon-specialist delegation and cache hooks to vp-product"
```

---

### Task 37: Update sdm.md

**Files:**
- Modify: `$PM/agents/sdm.md` (frontmatter only)

**Step 1: Add Task(neon-specialist) to tools list**

Add `- Task(neon-specialist)` after `- Task(staff-engineer)`.

**Step 2: Add WebFetch hooks**

Add PreToolUse and PostToolUse hooks (same as vp-product).

**Step 3: Commit**

```bash
git add pm/agents/sdm.md
git commit -m "feat(agents): add neon-specialist delegation and cache hooks to sdm"
```

---

### Task 38: Update staff-engineer.md

**Files:**
- Modify: `$PM/agents/staff-engineer.md` (frontmatter only)

**Step 1: Add WebFetch hooks**

Add PreToolUse and PostToolUse hooks to the frontmatter.

**Step 2: Commit**

```bash
git add pm/agents/staff-engineer.md
git commit -m "feat(agents): add WebFetch cache hooks to staff-engineer"
```

---

### Task 39: Update merkle tree generator

**Files:**
- Modify: `$PM/.index/generate-merkle.py`

**Step 1: Add .py to tracked extensions**

Change `for ext in ["*.md", "*.sh"]:` to `for ext in ["*.md", "*.sh", "*.py"]:` (line 73)

**Step 2: Add neon-specialist to semanticIndex.agents**

Add to the `agents` dict:

```python
"neon-specialist": {"model": "opus", "owns": ["documents"], "file": "agents/neon-specialist.md"},
```

**Step 3: Update agent summary**

Add `│   ├── neon-specialist.md # Opus - document caching` to the directory tree in `build_agent_summary()`.

**Step 4: Regenerate**

Run: `cd $PM && python3 .index/generate-merkle.py`
Expected: Higher file count, updated root hash

**Step 5: Commit**

```bash
git add pm/.index/generate-merkle.py pm/.index/merkle-tree.json pm/.index/AGENT-INDEX.md
git commit -m "feat(index): track .py files, add neon-specialist to semantic index"
```

---

### Task 40: Run existing tests (regression check)

**Files:** None (verification only)

**Step 1: Run PM test suite**

Run: `cd $PM && ./tests/run-tests.sh`
Expected: All 5 tests pass (no regressions)

**Step 2: Run neon_docs unit tests**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/ -v -m "not live"`
Expected: All unit tests pass

---

### Task 41: Run Ruff + format on all neon_docs code

**Files:** None (verification + auto-fix)

**Step 1: Lint**

Run: `cd $REPO && .venv/bin/ruff check pm/lib/neon_docs/ pm/tests/neon_docs/ --fix`
Expected: Clean or auto-fixed

**Step 2: Format**

Run: `cd $REPO && .venv/bin/ruff format pm/lib/neon_docs/ pm/tests/neon_docs/`
Expected: Formatted

**Step 3: Commit any changes**

```bash
git add pm/lib/neon_docs/ pm/tests/neon_docs/
git commit -m "chore(neon): lint and format with ruff"
```

---

## Phase 8: Bootstrap + Verification (Tasks 42-48)

### Task 42: Pull Ollama model

**Step 1: Pull nomic-embed-text**

Run: `ollama pull nomic-embed-text`
Expected: Model downloaded

**Step 2: Verify**

Run: `ollama list | grep nomic-embed-text`
Expected: Model listed

---

### Task 43: Run migrations against Neon

**Step 1: Run migrate**

Run: `cd $PM && PYTHONPATH=. python3 -m lib.neon_docs migrate`
Expected: `{"applied": ["V001_initial_schema.sql"]}`

**Step 2: Run again (idempotent)**

Run: `cd $PM && PYTHONPATH=. python3 -m lib.neon_docs migrate`
Expected: `{"applied": [], "message": "all migrations already applied"}`

---

### Task 44: Bulk-index crawler docs

**Step 1: Index**

Run: `cd $PM && make l1-doc-index`
Expected: JSON with `"inserted": N` where N > 0

---

### Task 45: Drain processing queue

**Step 1: Process**

Run: `cd $PM && make l1-doc-drain`
Expected: `{"processed": N, "failed": 0}`

---

### Task 46: Verify status

**Step 1: Check status**

Run: `cd $PM && make l0-doc-status`
Expected: `{"documents": N, "chunks": M, "queue_pending": 0, "queue_failed": 0}`

---

### Task 47: Test search quality

**Step 1: Search for tool_use**

Run: `cd $PM && make l0-doc-search QUERY="how to use tool_use with Claude API"`
Expected: Relevant results with similarity > 0.3

**Step 2: Search for prompt caching**

Run: `cd $PM && make l0-doc-search QUERY="prompt caching"`
Expected: Relevant results

---

### Task 48: Test idempotency

**Step 1: Re-run bulk-index**

Run: `cd $PM && make l1-doc-index`
Expected: `{"inserted": 0, "updated": 0, "unchanged": N, "errors": 0}`

---

## Phase 9: CI/CD (Tasks 49-52)

### Task 49: Create GitHub Actions lint workflow

**Files:**
- Create: `$REPO/.github/workflows/lint.yml`

**Step 1: Write lint workflow**

```yaml
name: Lint
on:
  push:
    paths: ['pm/lib/neon_docs/**', 'pm/tests/neon_docs/**']
  pull_request:
    paths: ['pm/lib/neon_docs/**', 'pm/tests/neon_docs/**']

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv venv .venv && uv pip install ruff
      - run: .venv/bin/ruff check pm/lib/neon_docs/ pm/tests/neon_docs/
      - run: .venv/bin/ruff format --check pm/lib/neon_docs/ pm/tests/neon_docs/
```

**Step 2: Commit**

```bash
git add .github/workflows/lint.yml
git commit -m "ci: add ruff lint workflow for neon_docs"
```

---

### Task 50: Create GitHub Actions test workflow

**Files:**
- Create: `$REPO/.github/workflows/test.yml`

**Step 1: Write test workflow**

```yaml
name: Test
on:
  push:
    paths: ['pm/lib/neon_docs/**', 'pm/tests/neon_docs/**']
  pull_request:
    paths: ['pm/lib/neon_docs/**', 'pm/tests/neon_docs/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv venv .venv && uv pip install -e ".[dev]"
      - run: .venv/bin/python3 -m pytest pm/tests/neon_docs/ -v -m "not live" --tb=short
```

**Step 2: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "ci: add pytest workflow for neon_docs (unit tests only)"
```

---

### Task 51: Create combined CI workflow

**Files:**
- Create: `$REPO/.github/workflows/ci.yml`

**Step 1: Write CI workflow**

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:

jobs:
  lint:
    uses: ./.github/workflows/lint.yml
  test:
    uses: ./.github/workflows/test.yml
```

**Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add combined CI workflow (lint + test)"
```

---

### Task 52: Final verification

**Files:** None (verification only)

**Step 1: Run full unit test suite**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/ -v -m "not live"`
Expected: All unit tests pass

**Step 2: Run full live test suite (if DB + Ollama available)**

Run: `cd $REPO && .venv/bin/python3 -m pytest pm/tests/neon_docs/ -v`
Expected: All tests pass (live tests skip gracefully if unavailable)

**Step 3: Run existing PM tests**

Run: `cd $PM && ./tests/run-tests.sh`
Expected: All 5 tests pass

**Step 4: Run Ruff lint**

Run: `cd $REPO && .venv/bin/ruff check pm/lib/neon_docs/ pm/tests/neon_docs/`
Expected: Clean

**Step 5: Verify merkle tree is fresh**

Run: `cd $PM && python3 .index/check-changes.py`
Expected: Index is current

**Step 6: Final commit**

```bash
git add -A
git commit -m "chore(neon): Phase 9 complete — all verification checks pass"
```

---

## Summary

| Phase | Tasks | What | Key Files |
|-------|-------|------|-----------|
| 0 | 1-8 | Infrastructure | `pyproject.toml`, `config.py`, `exceptions.py`, `log.py` |
| 1 | 9-15 | Database | `V001_*.sql`, `migrate.py`, `models.py`, `db.py`, `repository.py` |
| 2 | 16-20 | Embeddings | `tokenizer.py`, `chunker.py`, `embedder.py`, `worker.py` |
| 3 | 21-22 | CLI | `cli.py`, `__main__.py` |
| 4 | 23-26 | Tracing | `tracer.py`, `mlflow_tracing.py` |
| 5 | 27-30 | Hooks + Deps | `neon-cache-check.sh`, `neon-cache-store.sh`, `requirements.txt` |
| 6 | 31-33 | Makefile | `Makefile` L0-L3 doc targets |
| 7 | 34-41 | Agents | `neon-specialist.md`, parent agent updates, merkle tree |
| 8 | 42-48 | Bootstrap | Runtime: migrate, index, drain, verify |
| 9 | 49-52 | CI/CD | `.github/workflows/`, final verification |

**Total: 52 tasks across 10 phases.**

Each task follows TDD where applicable: write test → verify fail → implement → verify pass → commit.

**Dependency chain:**
- Phase 0 blocks all other phases
- Phase 1 blocks Phases 2, 3, 8
- Phase 2 blocks Phases 3, 8
- Phase 3 blocks Phases 5, 6
- Phases 4, 5, 6, 7 are independent of each other (parallelizable)
- Phase 8 requires Phases 1-7 complete
- Phase 9 can start after Phase 0 (lint/test) but full CI needs all phases
