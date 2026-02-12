# Neon Specialist Agent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Neon-backed document caching and semantic search layer for PM agents, with MLflow 3.9 tracing.

**Architecture:** A `neon-specialist` leaf agent provides document store/search/cache operations. PreToolUse/PostToolUse hooks on WebFetch transparently cache fetched pages. Ollama generates embeddings locally. MLflow 3.9 traces all operations.

**Tech Stack:** Python 3.11+, asyncpg, Neon PostgreSQL + pgvector, Ollama (nomic-embed-text), httpx, MLflow 3.9

**Design Doc:** `docs/plans/2026-02-12-neon-specialist-agent-design.md`

---

## Task 1: Schema Migration Script

**Files:**
- Create: `pm/scripts/neon-migrate.sql`

**Step 1: Write the migration SQL**

```sql
-- pm/scripts/neon-migrate.sql
-- Neon Document Caching Schema
-- Idempotent: safe to re-run (IF NOT EXISTS / OR REPLACE)

CREATE EXTENSION IF NOT EXISTS vector;

-- Table 1: Raw documents (source of truth)
CREATE TABLE IF NOT EXISTS crawled_documents (
    id              SERIAL PRIMARY KEY,
    url             TEXT UNIQUE,
    file_path       TEXT UNIQUE,
    title           TEXT,
    content         TEXT        NOT NULL,
    content_hash    TEXT        NOT NULL,
    content_tsv     tsvector    GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    last_fetched_at TIMESTAMPTZ DEFAULT NOW(),
    last_modified_at TIMESTAMPTZ,
    needs_processing BOOLEAN    DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT has_source CHECK (url IS NOT NULL OR file_path IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_crawled_url_hash ON crawled_documents (url, content_hash) WHERE url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_crawled_pending  ON crawled_documents (id) WHERE needs_processing = TRUE;
CREATE INDEX IF NOT EXISTS idx_crawled_tsv      ON crawled_documents USING GIN (content_tsv);

-- Table 2: Chunked + embedded content (derived)
CREATE TABLE IF NOT EXISTS document_chunks (
    id            SERIAL  PRIMARY KEY,
    document_id   INTEGER NOT NULL REFERENCES crawled_documents (id) ON DELETE CASCADE,
    chunk_index   INTEGER NOT NULL,
    content       TEXT    NOT NULL,
    embedding     vector(768),
    token_count   INTEGER,

    UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_hnsw   ON document_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
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

-- Function: Upsert document (atomic, CTE-based)
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

**Step 2: Verify the migration is idempotent**

Run: `psql "$PRJ_NEON_DATABASE_URL" -f pm/scripts/neon-migrate.sql`
Expected: All CREATE statements succeed (no errors)

Run again: `psql "$PRJ_NEON_DATABASE_URL" -f pm/scripts/neon-migrate.sql`
Expected: Same output, no errors (IF NOT EXISTS / OR REPLACE)

**Step 3: Commit**

```bash
git add pm/scripts/neon-migrate.sql
git commit -m "feat(neon): add document caching schema migration"
```

---

## Task 2: Update Dependencies

**Files:**
- Modify: `/home/alex-jadecli/projects/refs/jadecli-ai/pm/requirements.txt`

**Step 1: Add new dependencies and upgrade mlflow**

Add these lines to `requirements.txt`:

```
# Neon document caching
asyncpg>=0.29.0      # Async PostgreSQL driver for Neon
httpx>=0.27.0         # HTTP client for Ollama API

# MLflow upgrade (was >=2.10.0)
mlflow>=3.9.0         # GenAI tracing, Claude autolog, LLM judges
```

Change `mlflow>=2.10.0` to `mlflow>=3.9.0`.

**Step 2: Install to verify no conflicts**

Run: `pip install -r requirements.txt --dry-run 2>&1 | tail -5`
Expected: No version conflicts

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat(deps): add asyncpg, httpx; upgrade mlflow to 3.9"
```

---

## Task 3: Database Connection Module

**Files:**
- Create: `pm/lib/neon_docs/__init__.py`
- Create: `pm/lib/neon_docs/db.py`
- Test: manual via `python3 -c "from pm.lib.neon_docs.db import get_pool"`

**Step 1: Create the package init**

```python
# pm/lib/neon_docs/__init__.py
"""Neon document caching and semantic search."""
```

**Step 2: Write the failing test**

Run: `python3 -c "import asyncio; from pm.lib.neon_docs.db import get_pool; print(asyncio.run(get_pool()))"`
Expected: FAIL — module not found

**Step 3: Write db.py**

```python
# pm/lib/neon_docs/db.py
"""Async PostgreSQL connection pool for Neon."""

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the connection pool.

    Uses PRJ_NEON_DATABASE_URL env var. Strips the +asyncpg dialect
    prefix if present (SQLAlchemy-style URL).
    """
    global _pool
    if _pool is not None:
        return _pool

    dsn = os.environ["PRJ_NEON_DATABASE_URL"]
    # Strip SQLAlchemy dialect prefix: postgresql+asyncpg:// -> postgresql://
    if "+asyncpg" in dsn:
        dsn = dsn.replace("+asyncpg", "")

    _pool = await asyncpg.create_pool(
        dsn,
        min_size=1,
        max_size=5,
        command_timeout=30,
    )
    return _pool


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def connection() -> AsyncIterator[asyncpg.Connection]:
    """Get a connection from the pool."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
```

**Step 4: Verify it connects**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm && python3 -c "
import asyncio, os, sys
sys.path.insert(0, 'pm')
os.environ.setdefault('PRJ_NEON_DATABASE_URL', 'postgresql+asyncpg://neondb_owner:npg_wugMR4mSnXe9@ep-billowing-cloud-afez1v2y.c-2.us-west-2.aws.neon.tech/neondb')
from lib.neon_docs.db import get_pool, close_pool
async def test():
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchval('SELECT 1')
        print(f'Connected: {row}')
    await close_pool()
asyncio.run(test())
"`
Expected: `Connected: 1`

**Step 5: Commit**

```bash
git add pm/lib/neon_docs/__init__.py pm/lib/neon_docs/db.py
git commit -m "feat(neon): add async database connection pool"
```

---

## Task 4: Text Chunker Module

**Files:**
- Create: `pm/lib/neon_docs/chunker.py`
- Test: inline via python3 -c

**Step 1: Write the failing test**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm && python3 -c "
import sys; sys.path.insert(0, 'pm')
from lib.neon_docs.chunker import chunk_text
chunks = chunk_text('Hello world. ' * 200, max_tokens=50)
assert len(chunks) > 1, f'Expected multiple chunks, got {len(chunks)}'
assert all(len(c) > 0 for c in chunks), 'Empty chunk found'
print(f'PASS: {len(chunks)} chunks')
"`
Expected: FAIL — module not found

**Step 2: Write chunker.py**

```python
# pm/lib/neon_docs/chunker.py
"""Text chunking with token-aware splitting."""


def _approx_tokens(text: str) -> int:
    """Approximate token count (words * 1.3)."""
    return int(len(text.split()) * 1.3)


def chunk_text(
    text: str,
    max_tokens: int = 512,
    overlap_tokens: int = 64,
) -> list[str]:
    """Split text into overlapping chunks.

    Splits on paragraph boundaries first, then sentence boundaries,
    then word boundaries. Each chunk targets max_tokens with
    overlap_tokens of context from the previous chunk.

    Args:
        text: Full document text.
        max_tokens: Target max tokens per chunk.
        overlap_tokens: Overlap with previous chunk for context.

    Returns:
        List of text chunks.
    """
    if _approx_tokens(text) <= max_tokens:
        return [text]

    # Split into paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = _approx_tokens(para)

        # Single paragraph exceeds limit — split by sentences
        if para_tokens > max_tokens:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_tokens = 0

            sentences = para.replace(". ", ".\n").split("\n")
            for sent in sentences:
                sent_tokens = _approx_tokens(sent)
                if current_tokens + sent_tokens > max_tokens and current:
                    chunks.append(" ".join(current))
                    # Keep overlap
                    overlap_text = " ".join(current)
                    overlap_words = overlap_text.split()
                    keep = int(overlap_tokens / 1.3)
                    current = overlap_words[-keep:] if keep > 0 else []
                    current_tokens = _approx_tokens(" ".join(current))
                current.append(sent)
                current_tokens += sent_tokens
            continue

        if current_tokens + para_tokens > max_tokens and current:
            chunks.append("\n\n".join(current))
            # Keep overlap
            overlap_text = "\n\n".join(current)
            overlap_words = overlap_text.split()
            keep = int(overlap_tokens / 1.3)
            current = [" ".join(overlap_words[-keep:])] if keep > 0 else []
            current_tokens = _approx_tokens(" ".join(current))

        current.append(para)
        current_tokens += para_tokens

    if current:
        chunks.append("\n\n".join(current))

    return chunks
```

**Step 3: Run the test**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm && python3 -c "
import sys; sys.path.insert(0, 'pm')
from lib.neon_docs.chunker import chunk_text
chunks = chunk_text('Hello world. ' * 200, max_tokens=50)
assert len(chunks) > 1, f'Expected multiple chunks, got {len(chunks)}'
assert all(len(c) > 0 for c in chunks), 'Empty chunk found'
print(f'PASS: {len(chunks)} chunks')
"`
Expected: `PASS: N chunks`

**Step 4: Commit**

```bash
git add pm/lib/neon_docs/chunker.py
git commit -m "feat(neon): add text chunker with overlap"
```

---

## Task 5: Ollama Embeddings Module

**Files:**
- Create: `pm/lib/neon_docs/embedder.py`

**Step 1: Write the failing test**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm && python3 -c "
import asyncio, sys; sys.path.insert(0, 'pm')
from lib.neon_docs.embedder import embed_texts
result = asyncio.run(embed_texts(['hello world']))
assert len(result) == 1
assert len(result[0]) == 768
print(f'PASS: embedding dim={len(result[0])}')
"`
Expected: FAIL — module not found

**Step 2: Write embedder.py**

```python
# pm/lib/neon_docs/embedder.py
"""Local embeddings via Ollama API (nomic-embed-text)."""

import os

import httpx

OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts via Ollama.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (768-dim for nomic-embed-text).
    """
    embeddings: list[list[float]] = []
    async with httpx.AsyncClient(base_url=OLLAMA_BASE, timeout=120.0) as client:
        for text in texts:
            resp = await client.post(
                "/api/embed",
                json={"model": EMBED_MODEL, "input": text},
            )
            resp.raise_for_status()
            data = resp.json()
            embeddings.append(data["embeddings"][0])
    return embeddings


async def embed_single(text: str) -> list[float]:
    """Embed a single text string."""
    results = await embed_texts([text])
    return results[0]
```

**Step 3: Pull the Ollama model (prerequisite)**

Run: `ollama pull nomic-embed-text`
Expected: Model downloaded successfully

**Step 4: Run the test**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm && python3 -c "
import asyncio, sys; sys.path.insert(0, 'pm')
from lib.neon_docs.embedder import embed_texts
result = asyncio.run(embed_texts(['hello world']))
assert len(result) == 1
assert len(result[0]) == 768
print(f'PASS: embedding dim={len(result[0])}')
"`
Expected: `PASS: embedding dim=768`

**Step 5: Commit**

```bash
git add pm/lib/neon_docs/embedder.py
git commit -m "feat(neon): add Ollama embeddings client"
```

---

## Task 6: MLflow 3.9 Tracer Module

**Files:**
- Create: `pm/lib/neon_docs/tracer.py`

**Step 1: Write tracer.py**

```python
# pm/lib/neon_docs/tracer.py
"""MLflow 3.9 tracing spans for Neon document operations."""

import functools
import time
from typing import Any, Callable

try:
    import mlflow

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


def trace_operation(name: str) -> Callable:
    """Decorator to trace a function as an MLflow span.

    Logs: function args as params, duration_ms, return value summary.
    Falls back to print logging if MLflow is unavailable.

    Usage:
        @trace_operation("neon.cache_check")
        async def check_url(url: str) -> dict:
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()

            if not MLFLOW_AVAILABLE:
                result = await func(*args, **kwargs)
                elapsed = (time.time() - start) * 1000
                print(f"[TRACE] {name}: {elapsed:.0f}ms")
                return result

            with mlflow.start_span(name=name) as span:
                # Log non-large params
                safe_kwargs = {
                    k: str(v)[:200] for k, v in kwargs.items()
                }
                span.set_inputs(safe_kwargs)

                try:
                    result = await func(*args, **kwargs)
                    elapsed = (time.time() - start) * 1000
                    span.set_attributes({"duration_ms": elapsed})

                    # Summarize output
                    if isinstance(result, dict):
                        span.set_outputs(
                            {k: str(v)[:200] for k, v in result.items()}
                        )
                    elif isinstance(result, list):
                        span.set_outputs({"count": len(result)})
                    else:
                        span.set_outputs({"result": str(result)[:200]})

                    return result

                except Exception as e:
                    span.set_status("ERROR")
                    span.set_attributes(
                        {"error": str(e), "error_type": type(e).__name__}
                    )
                    raise

        return wrapper

    return decorator


def setup_autolog() -> None:
    """Enable MLflow 3.9 Anthropic autolog if available."""
    if MLFLOW_AVAILABLE and hasattr(mlflow, "anthropic"):
        mlflow.anthropic.autolog()
```

**Step 2: Commit**

```bash
git add pm/lib/neon_docs/tracer.py
git commit -m "feat(neon): add MLflow 3.9 tracing decorator"
```

---

## Task 7: Main CLI Module (neon_docs.py)

**Files:**
- Create: `pm/lib/neon_docs/cli.py` (CLI entry point)
- Modify: `pm/lib/neon_docs/__init__.py` (expose public API)

**Step 1: Write the failing test**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm && python3 -m pm.lib.neon_docs.cli status`
Expected: FAIL — module not found

**Step 2: Write cli.py**

```python
#!/usr/bin/env python3
# pm/lib/neon_docs/cli.py
"""CLI for Neon document caching operations.

Usage:
    python3 -m pm.lib.neon_docs.cli store --url <url>
    python3 -m pm.lib.neon_docs.cli store --file <path>
    python3 -m pm.lib.neon_docs.cli check-url <url>
    python3 -m pm.lib.neon_docs.cli search "<query>" [--limit N] [--threshold F]
    python3 -m pm.lib.neon_docs.cli process-queue
    python3 -m pm.lib.neon_docs.cli bulk-index <directory>
    python3 -m pm.lib.neon_docs.cli status
"""

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path

from .db import close_pool, connection
from .chunker import chunk_text
from .embedder import embed_single, embed_texts
from .tracer import trace_operation


@trace_operation("neon.check_url")
async def check_url(url: str) -> dict:
    """Check if URL is cached. Returns content or CACHE_MISS."""
    async with connection() as conn:
        row = await conn.fetchrow(
            "SELECT id, content, content_hash FROM crawled_documents WHERE url = $1",
            url,
        )
        if row:
            return {"hit": True, "content": row["content"], "doc_id": row["id"]}
        return {"hit": False}


@trace_operation("neon.store")
async def store_document(
    url: str | None = None,
    file_path: str | None = None,
    title: str | None = None,
    content: str | None = None,
) -> dict:
    """Store a document via upsert_document function."""
    if file_path and content is None:
        content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        if title is None:
            title = Path(file_path).name

    if content is None:
        raise ValueError("Either --file or content must be provided")

    async with connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM upsert_document($1, $2, $3, $4)",
            url,
            file_path,
            title,
            content,
        )
        return {"action": row["action"], "doc_id": row["doc_id"]}


@trace_operation("neon.search")
async def search(
    query: str,
    limit: int = 5,
    threshold: float = 0.3,
    keyword: str | None = None,
) -> list[dict]:
    """Semantic search across cached documents."""
    query_embedding = await embed_single(query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    async with connection() as conn:
        rows = await conn.fetch(
            "SELECT * FROM search_documents($1::vector, $2, $3, $4)",
            embedding_str,
            keyword,
            limit,
            threshold,
        )
        return [
            {
                "doc_id": r["doc_id"],
                "title": r["title"],
                "chunk_text": r["chunk_text"][:500],
                "similarity": round(r["similarity"], 4),
                "url": r["url"],
                "file_path": r["file_path"],
            }
            for r in rows
        ]


@trace_operation("neon.process_queue")
async def process_queue() -> dict:
    """Process pending chunk+embed jobs."""
    processed = 0
    failed = 0

    async with connection() as conn:
        while True:
            # Pick next job
            job = await conn.fetchrow(
                """UPDATE processing_queue
                   SET status = 'processing', started_at = NOW(), attempts = attempts + 1
                   WHERE id = (
                       SELECT id FROM processing_queue
                       WHERE status = 'pending'
                       ORDER BY priority DESC, id ASC
                       LIMIT 1
                       FOR UPDATE SKIP LOCKED
                   )
                   RETURNING id, document_id""",
            )

            if job is None:
                break

            try:
                # Get document content
                doc = await conn.fetchrow(
                    "SELECT content, title FROM crawled_documents WHERE id = $1",
                    job["document_id"],
                )

                # Chunk
                chunks = chunk_text(doc["content"])

                # Embed all chunks
                embeddings = await embed_texts(chunks)

                # Delete old chunks
                await conn.execute(
                    "DELETE FROM document_chunks WHERE document_id = $1",
                    job["document_id"],
                )

                # Insert new chunks
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
                    token_count = int(len(chunk.split()) * 1.3)
                    await conn.execute(
                        """INSERT INTO document_chunks
                           (document_id, chunk_index, content, embedding, token_count)
                           VALUES ($1, $2, $3, $4::vector, $5)""",
                        job["document_id"],
                        i,
                        chunk,
                        embedding_str,
                        token_count,
                    )

                # Mark done
                await conn.execute(
                    "UPDATE processing_queue SET status = 'done', completed_at = NOW() WHERE id = $1",
                    job["id"],
                )
                await conn.execute(
                    "UPDATE crawled_documents SET needs_processing = FALSE WHERE id = $1",
                    job["document_id"],
                )
                processed += 1

            except Exception as e:
                await conn.execute(
                    "UPDATE processing_queue SET status = 'failed', error_message = $1 WHERE id = $2",
                    str(e)[:500],
                    job["id"],
                )
                failed += 1

    return {"processed": processed, "failed": failed}


@trace_operation("neon.bulk_index")
async def bulk_index(directory: str) -> dict:
    """Index all files in a directory."""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    results = {"inserted": 0, "updated": 0, "unchanged": 0, "errors": 0}

    for file_path in sorted(dir_path.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix not in (".md", ".json", ".txt"):
            continue

        try:
            result = await store_document(
                file_path=str(file_path),
                title=file_path.name,
            )
            action = result["action"]
            if action in results:
                results[action] += 1
        except Exception as e:
            print(f"ERROR: {file_path}: {e}", file=sys.stderr)
            results["errors"] += 1

    return results


async def get_status() -> dict:
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
        return {
            "documents": doc_count,
            "chunks": chunk_count,
            "queue_pending": pending,
            "queue_failed": failed,
        }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Neon document cache CLI")
    sub = parser.add_subparsers(dest="command")

    # store
    p_store = sub.add_parser("store")
    p_store.add_argument("--url", type=str)
    p_store.add_argument("--file", type=str)
    p_store.add_argument("--title", type=str)

    # check-url
    p_check = sub.add_parser("check-url")
    p_check.add_argument("url", type=str)

    # search
    p_search = sub.add_parser("search")
    p_search.add_argument("query", type=str)
    p_search.add_argument("--limit", type=int, default=5)
    p_search.add_argument("--threshold", type=float, default=0.3)
    p_search.add_argument("--keyword", type=str)

    # process-queue
    sub.add_parser("process-queue")

    # bulk-index
    p_bulk = sub.add_parser("bulk-index")
    p_bulk.add_argument("directory", type=str)

    # status
    sub.add_parser("status")

    args = parser.parse_args()

    try:
        if args.command == "store":
            result = await store_document(url=args.url, file_path=args.file, title=args.title)
        elif args.command == "check-url":
            result = await check_url(url=args.url)
            if result["hit"]:
                print(result["content"])
                return
            else:
                print("CACHE_MISS")
                return
        elif args.command == "search":
            result = await search(args.query, args.limit, args.threshold, args.keyword)
        elif args.command == "process-queue":
            result = await process_queue()
        elif args.command == "bulk-index":
            result = await bulk_index(args.directory)
        elif args.command == "status":
            result = await get_status()
        else:
            parser.print_help()
            return

        print(json.dumps(result, indent=2, default=str))
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 3: Update __init__.py**

```python
# pm/lib/neon_docs/__init__.py
"""Neon document caching and semantic search."""

from .cli import check_url, store_document, search, process_queue, bulk_index, get_status

__all__ = ["check_url", "store_document", "search", "process_queue", "bulk_index", "get_status"]
```

**Step 4: Test status command**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm && PYTHONPATH=pm python3 -m lib.neon_docs.cli status`
Expected: `{"documents": 0, "chunks": 0, "queue_pending": 0, "queue_failed": 0}`

**Step 5: Commit**

```bash
git add pm/lib/neon_docs/cli.py pm/lib/neon_docs/__init__.py
git commit -m "feat(neon): add document cache CLI with all operations"
```

---

## Task 8: Hook Scripts

**Files:**
- Create: `pm/scripts/neon-cache-check.sh`
- Create: `pm/scripts/neon-cache-store.sh`

**Step 1: Write neon-cache-check.sh**

```bash
#!/usr/bin/env bash
# pm/scripts/neon-cache-check.sh
# PreToolUse hook for WebFetch — checks Neon cache before fetching
# Reads the tool input JSON from stdin, extracts the URL

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(dirname "$SCRIPT_DIR")"

# Extract URL from hook input (passed as JSON on stdin)
URL=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('url',''))" 2>/dev/null || echo "")

if [ -z "$URL" ]; then
    exit 0  # No URL, let WebFetch proceed
fi

# Check cache
RESULT=$(cd "$PM_DIR" && PYTHONPATH="$PM_DIR" python3 -m lib.neon_docs.cli check-url "$URL" 2>/dev/null || echo "CACHE_MISS")

if [ "$RESULT" != "CACHE_MISS" ]; then
    echo "[neon-cache] HIT: $URL"
else
    echo "[neon-cache] MISS: $URL"
fi

exit 0
```

**Step 2: Write neon-cache-store.sh**

```bash
#!/usr/bin/env bash
# pm/scripts/neon-cache-store.sh
# PostToolUse hook for WebFetch — stores fetched content in Neon cache

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(dirname "$SCRIPT_DIR")"

# Extract URL from hook input
URL=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('url',''))" 2>/dev/null || echo "")

if [ -z "$URL" ]; then
    exit 0
fi

# Store in background (don't block the agent)
cd "$PM_DIR" && PYTHONPATH="$PM_DIR" python3 -m lib.neon_docs.cli store --url "$URL" >/dev/null 2>&1 &

exit 0
```

**Step 3: Make executable**

Run: `chmod +x pm/scripts/neon-cache-check.sh pm/scripts/neon-cache-store.sh`

**Step 4: Commit**

```bash
git add pm/scripts/neon-cache-check.sh pm/scripts/neon-cache-store.sh
git commit -m "feat(neon): add WebFetch cache hook scripts"
```

---

## Task 9: Makefile Targets

**Files:**
- Modify: `pm/Makefile` (at `/home/alex-jadecli/projects/refs/jadecli-ai/pm/pm/Makefile`)

**Step 1: Add doc pipeline targets**

Append before the `# SHORTCUTS` section (after the REVIEW PIPELINE section, around line 165):

```makefile
# ============================================================================
# DOCUMENT PIPELINE (Neon document caching)
# ============================================================================

.PHONY: l0-doc-store l0-doc-search l0-doc-process l0-doc-status
.PHONY: l1-doc-index l1-doc-drain l1-doc-migrate
.PHONY: l2-doc-refresh l2-doc-reindex
.PHONY: l3-doc-setup

NEON_CLI = PYTHONPATH=. python3 -m lib.neon_docs.cli

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

l1-doc-migrate: ## L1-Doc: Run schema migration
	@psql "$$PRJ_NEON_DATABASE_URL" -f scripts/neon-migrate.sql

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

**Step 2: Update help target to include doc pipeline**

Add after the Review Pipeline grep in the `help` target:

```makefile
	@echo ""
	@echo "Document Pipeline:"
	@grep -E '^l[0-3]-doc-[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'
```

**Step 3: Update shortcuts**

Add after the existing shortcuts:

```makefile
docs-setup: l3-doc-setup  ## Alias: full doc bootstrap
docs-status: l0-doc-status ## Alias: cache stats
```

**Step 4: Verify Makefile syntax**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm/pm && make help`
Expected: Shows all targets including Document Pipeline section

**Step 5: Commit**

```bash
git add pm/Makefile
git commit -m "feat(neon): add L0-L3 document pipeline Makefile targets"
```

---

## Task 10: Neon Specialist Agent Definition

**Files:**
- Create: `pm/agents/neon-specialist.md`

**Step 1: Write the agent**

```markdown
---
name: neon-specialist
description: Stores, indexes, and searches documents in Neon pgvector. Transparent cache for WebFetch.
model: claude-opus-4-6
memory: project
tools:
  - Read
  - Bash
  - Glob
  - Grep
---

# Neon Specialist Agent

> **Quick Start**: Read `.index/AGENT-INDEX.md` for pre-computed system overview.

You are a document caching specialist. You store, index, and search documents in Neon PostgreSQL with pgvector. You operate as a leaf node — no sub-agents.

## Operations

All operations use the CLI at `pm/lib/neon_docs/cli.py`:

| Command | What | Example |
|---------|------|---------|
| `store --url <url>` | Cache a URL's content | `PYTHONPATH=. python3 -m lib.neon_docs.cli store --url "https://docs.anthropic.com/api"` |
| `store --file <path>` | Index a local file | `PYTHONPATH=. python3 -m lib.neon_docs.cli store --file "../docs/crawler-improvements/FULL-CRAWLER-INPUTS-1-ALL-API-DOCS.json"` |
| `search "<query>"` | Semantic search | `PYTHONPATH=. python3 -m lib.neon_docs.cli search "how to use tool_use" --limit 5` |
| `check-url <url>` | Cache check (hit/miss) | `PYTHONPATH=. python3 -m lib.neon_docs.cli check-url "https://docs.anthropic.com/api"` |
| `process-queue` | Run pending embed jobs | `PYTHONPATH=. python3 -m lib.neon_docs.cli process-queue` |
| `bulk-index <dir>` | Index all files in dir | `PYTHONPATH=. python3 -m lib.neon_docs.cli bulk-index "../docs/crawler-improvements/"` |
| `status` | Cache statistics | `PYTHONPATH=. python3 -m lib.neon_docs.cli status` |

## When Spawned

You receive one of:
1. **"Store this URL"** — run `store --url`
2. **"Search for X"** — run `search`
3. **"Index these docs"** — run `bulk-index`
4. **"Process queue"** — run `process-queue`
5. **"Check status"** — run `status`

Always report the result JSON back to your parent agent.

## Idempotency

All operations are idempotent. Re-storing the same content is a no-op (content hash match). Re-indexing skips unchanged files. Safe to re-run.
```

**Step 2: Commit**

```bash
git add pm/agents/neon-specialist.md
git commit -m "feat(agents): add neon-specialist document caching agent"
```

---

## Task 11: Update Parent Agent Definitions

**Files:**
- Modify: `pm/agents/vp-product.md:1-20` (frontmatter)
- Modify: `pm/agents/sdm.md:1-21` (frontmatter)
- Modify: `pm/agents/staff-engineer.md:1-15` (frontmatter)

**Step 1: Add Task(neon-specialist) to vp-product.md tools and add WebFetch hooks**

In `pm/agents/vp-product.md`, update the frontmatter `tools:` list to include `Task(neon-specialist)`, and add `PreToolUse`/`PostToolUse` hooks:

```yaml
---
name: vp-product
description: VP of Product Management - orchestrates roadmap, prioritization, and team coordination
model: claude-opus-4-6
memory: project
tools:
  - Task(sdm)
  - Task(sprint-master)
  - Task(neon-specialist)
  - Read
  - Write
  - Glob
  - Grep
  - WebSearch
  - WebFetch
  - mcp__memory__*
  - mcp__git__*
hooks:
  TaskCompleted:
    - command: "echo '[vp-product] SDM/Sprint task completed — reviewing iteration progress'"
  PreToolUse:
    - matcher: WebFetch
      command: "pm/scripts/neon-cache-check.sh"
  PostToolUse:
    - matcher: WebFetch
      command: "pm/scripts/neon-cache-store.sh"
---
```

**Step 2: Add Task(neon-specialist) to sdm.md tools and add WebFetch hooks**

In `pm/agents/sdm.md`, update frontmatter:

```yaml
---
name: sdm
description: Software Development Manager - manages a domain team of Staff Engineers
model: claude-opus-4-6
memory: project
tools:
  - Task(staff-engineer)
  - Task(neon-specialist)
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - mcp__memory__*
  - mcp__git__*
hooks:
  TeammateIdle:
    - command: "echo '[sdm] Staff engineer idle — checking for unassigned tasks'"
  TaskCompleted:
    - command: "echo '[sdm] Staff engineer task completed — queuing review'"
  PreToolUse:
    - matcher: WebFetch
      command: "pm/scripts/neon-cache-check.sh"
  PostToolUse:
    - matcher: WebFetch
      command: "pm/scripts/neon-cache-store.sh"
---
```

**Step 3: Add WebFetch hooks to staff-engineer.md**

In `pm/agents/staff-engineer.md`, update frontmatter:

```yaml
---
name: staff-engineer
description: Staff Engineer - executes implementation tasks with high quality
model: claude-opus-4-6
memory: project
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - WebSearch
  - WebFetch
hooks:
  PreToolUse:
    - matcher: WebFetch
      command: "pm/scripts/neon-cache-check.sh"
  PostToolUse:
    - matcher: WebFetch
      command: "pm/scripts/neon-cache-store.sh"
---
```

**Step 4: Commit**

```bash
git add pm/agents/vp-product.md pm/agents/sdm.md pm/agents/staff-engineer.md
git commit -m "feat(agents): add neon-specialist delegation and WebFetch cache hooks"
```

---

## Task 12: Update Merkle Tree Generator

**Files:**
- Modify: `pm/.index/generate-merkle.py` (at `/home/alex-jadecli/projects/refs/jadecli-ai/pm/pm/.index/generate-merkle.py`)

**Step 1: Add .py to tracked extensions**

In `build_index()`, change line 73:
```python
# Before
for ext in ["*.md", "*.sh"]:

# After
for ext in ["*.md", "*.sh", "*.py"]:
```

**Step 2: Add neon-specialist to semanticIndex.agents**

In `build_index()`, add to the `agents` dict (around line 148):

```python
"neon-specialist": {"model": "opus", "owns": ["documents"], "file": "agents/neon-specialist.md"},
```

**Step 3: Update build_agent_summary() to include neon-specialist**

In the directory tree string, add:
```
│   ├── neon-specialist.md # Opus - document caching
```

**Step 4: Regenerate merkle tree**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm/pm && python3 .index/generate-merkle.py`
Expected: Output showing new file count (higher than before due to .py tracking)

**Step 5: Commit**

```bash
git add pm/.index/generate-merkle.py pm/.index/merkle-tree.json pm/.index/AGENT-INDEX.md
git commit -m "feat(index): track .py files, add neon-specialist to semantic index"
```

---

## Task 13: Bootstrap — Run l3-doc-setup

**Files:** None created (runtime operation)

**Step 1: Run schema migration**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm/pm && make l1-doc-migrate`
Expected: All CREATE/INDEX statements succeed

**Step 2: Bulk-index crawler docs**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm/pm && make l1-doc-index`
Expected: JSON output showing documents indexed (e.g., `{"inserted": 10, "updated": 0, "unchanged": 0, "errors": 0}`)

**Step 3: Drain processing queue (chunk + embed)**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm/pm && make l1-doc-drain`
Expected: `{"processed": N, "failed": 0}` where N matches inserted count

**Step 4: Verify status**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm/pm && make l0-doc-status`
Expected: `{"documents": 10, "chunks": N, "queue_pending": 0, "queue_failed": 0}`

**Step 5: Test search quality**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm/pm && make l0-doc-search QUERY="how to use tool_use with Claude API"`
Expected: Relevant chunks returned with similarity > 0.3

**Step 6: Test idempotency**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm/pm && make l1-doc-index`
Expected: `{"inserted": 0, "updated": 0, "unchanged": 10, "errors": 0}`

---

## Task 14: Run Existing Tests

**Files:** None modified

**Step 1: Run PM test suite**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm/pm && ./tests/run-tests.sh`
Expected: All existing tests pass (no regressions from hook/agent changes)

**Step 2: Verify merkle tree is fresh**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm/pm && python3 .index/check-changes.py`
Expected: Index is current (no stale files)

---

## Task 15: MLflow 3.9 Tracing Verification

**Files:**
- Modify: `/home/alex-jadecli/projects/refs/jadecli-ai/pm/lib/mlflow_tracing.py`

**Step 1: Update mlflow_tracing.py for 3.9 autolog**

Add to the module:

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

**Step 2: Verify tracing works**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm && python3 -c "
from lib.mlflow_tracing import setup_claude_autolog
setup_claude_autolog()
"`
Expected: `[MLflow] Claude autolog enabled (3.9+)` (after pip install mlflow>=3.9)

**Step 3: Run a traced search**

Run: `cd /home/alex-jadecli/projects/refs/jadecli-ai/pm/pm && PYTHONPATH=. python3 -m lib.neon_docs.cli search "prompt caching" --limit 3`
Expected: Results returned, plus MLflow trace spans logged (check `mlflow ui` at localhost:5000)

**Step 4: Commit**

```bash
git add lib/mlflow_tracing.py
git commit -m "feat(mlflow): add 3.9 anthropic autolog setup"
```

---

## Summary

| Task | What | Files | Phase |
|------|------|-------|-------|
| 1 | Schema migration | `pm/scripts/neon-migrate.sql` | 1 |
| 2 | Dependencies | `requirements.txt` | 1 |
| 3 | DB connection | `pm/lib/neon_docs/db.py` | 1 |
| 4 | Text chunker | `pm/lib/neon_docs/chunker.py` | 1 |
| 5 | Ollama embedder | `pm/lib/neon_docs/embedder.py` | 1 |
| 6 | MLflow tracer | `pm/lib/neon_docs/tracer.py` | 1 |
| 7 | CLI module | `pm/lib/neon_docs/cli.py` | 1 |
| 8 | Hook scripts | `pm/scripts/neon-cache-*.sh` | 1 |
| 9 | Makefile targets | `pm/Makefile` | 1 |
| 10 | Neon specialist agent | `pm/agents/neon-specialist.md` | 3 |
| 11 | Update parent agents | `pm/agents/{vp-product,sdm,staff-engineer}.md` | 3 |
| 12 | Update merkle tree | `pm/.index/generate-merkle.py` | 3 |
| 13 | Bootstrap data | Runtime: `make l3-doc-setup` | 2 |
| 14 | Run existing tests | Runtime: `./tests/run-tests.sh` | 3 |
| 15 | MLflow 3.9 tracing | `lib/mlflow_tracing.py` | 4 |
