# Neon Specialist Agent + Document Caching Pipeline

> Design document for adding a Neon-backed document caching and semantic search layer to the PM agent system.

**Date**: 2026-02-12
**Status**: Approved
**Author**: Claude Opus 4.6 + Alex

---

## Problem

The PM agent team needs access to large reference documentation (~500-700K tokens across 10 crawler-improvement files). Today, every agent that needs these docs re-reads them from disk, burning tokens and adding latency. There is no caching layer, no deduplication, and no semantic search.

## Solution

Build a **Neon Specialist Agent** with a transparent document caching layer:

1. **Neon PostgreSQL + pgvector** stores documents and embeddings
2. **Ollama** (nomic-embed-text on RTX 2080 Ti) generates embeddings locally
3. **PreToolUse/PostToolUse hooks** on WebFetch transparently cache fetched pages
4. **Task(neon-specialist)** lets PM agents explicitly query the knowledge base
5. **MLflow 3.9 GenAI Tracing** measures token savings, latency, and search quality

---

## Section 1: Database Schema

### Entity Relationship Overview

```
+----------------------+
|  crawled_documents   |
|  ==================  |
|  id (PK)             |
|  url (UNIQUE)        |--------+
|  file_path (UNIQUE)  |        |
|  content             |        | 1
|  content_hash        |        |
|  content_tsv (GIN)   |        |
|  needs_processing    |        |
|  last_fetched_at     |        |
+----------+-----------+        |
           |                    |
           | 1:N                | 1:N
           |                    |
           v                    v
+----------------------+  +----------------------+
|  document_chunks     |  |  processing_queue    |
|  ==================  |  |  ==================  |
|  id (PK)             |  |  id (PK)             |
|  document_id (FK)    |  |  document_id (FK)    |
|  chunk_index         |  |  operation           |
|  content             |  |  status              |
|  embedding (HNSW)    |  |  priority            |
|  token_count         |  |  attempts            |
+----------------------+  |  error_message       |
                          +----------------------+
```

### Data Flow

```
Document arrives (URL or file)
        |
        v
+-------------------+   content_hash
| upsert_document() |------------------+
+-------+-----------+                  |
        |                              v
        |                   +-----------------------+
        |  INSERT/UPDATE    | crawled_documents     |
        |------------------>|  (raw content)        |
        |                   +-----------------------+
        |
        |  enqueue job
        |-----------------> processing_queue
        |                         |
        |                         | worker picks up
        |                         v
        |                   +-----------------------+
        |                   | Ollama embed          |
        |                   | nomic-embed-text      |
        |                   +-----------+-----------+
        |                               |
        |                               v
        |                   +-----------------------+
        |                   | document_chunks       |
        |                   |  (embeddings)         |
        |                   +-----------------------+
        |
        v
Search query arrives
        |
        v
+-----------------------+
| search_documents()    |
|                       |
|  ranked_chunks (CTE)  |---> document_chunks (vector <=>)
|       |               |
|       v               |
|  keyword_filter (CTE) |---> crawled_documents (tsvector @@)
|       |               |
|       v               |
|  JOIN + ORDER + LIMIT |
+-----------------------+
```

### crawled_documents -- Source of Truth

```
+----------------------------------------------+
|               crawled_documents              |
|                                              |
|  Primary store for raw document content.     |
|  No joins -- standalone table.               |
|  Change detection via content_hash (SHA256). |
|  Full-text search via generated tsvector.    |
|                                              |
|  Access patterns:                            |
|    READ  -> cache-check by url + hash        |
|    WRITE -> upsert (insert or update)        |
|    SCAN  -> pending processing queue pickup  |
+----------------------------------------------+
```

```yaml
cubes:
  - name: crawled_documents
    description: "Raw documents ingested from URLs or local files. Change-tracked via content hash."
    sql_table: crawled_documents

    dimensions:
      - name: id
        type: number
        primary_key: true
      - name: url
        type: string
        description: "Source URL (NULL for local files)"
      - name: file_path
        type: string
        description: "Local file path (NULL for URLs)"
      - name: title
        type: string
      - name: content_hash
        type: string
        description: "SHA256 of content -- change detection key"
      - name: needs_processing
        type: boolean
        description: "TRUE when content changed and chunks need regeneration"
      - name: created_at
        type: time
      - name: updated_at
        type: time

    measures:
      - name: count
        type: count
      - name: pending_count
        type: count
        filters:
          - sql: "{CUBE}.needs_processing = TRUE"
      - name: avg_content_size
        type: avg
        sql: "length({CUBE}.content)"

    segments:
      - name: from_urls
        sql: "{CUBE}.url IS NOT NULL"
      - name: from_files
        sql: "{CUBE}.file_path IS NOT NULL"
      - name: pending_processing
        sql: "{CUBE}.needs_processing = TRUE"
```

```sql
CREATE TABLE crawled_documents (
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

CREATE INDEX idx_crawled_url_hash    ON crawled_documents (url, content_hash) WHERE url IS NOT NULL;
CREATE INDEX idx_crawled_pending     ON crawled_documents (id)                WHERE needs_processing = TRUE;
CREATE INDEX idx_crawled_tsv         ON crawled_documents USING GIN (content_tsv);
```

### document_chunks -- Derived Embeddings

```
+------------------------------------------------------+
|                  document_chunks                     |
|                                                      |
|  Derived from crawled_documents.                     |
|  JOIN: document_chunks.document_id ->                |
|        crawled_documents.id (many-to-one)            |
|                                                      |
|  +------------------+     +----------------------+   |
|  | document_chunks  | N:1 | crawled_documents    |   |
|  | .document_id     |---->| .id                  |   |
|  +------------------+     +----------------------+   |
|                                                      |
|  Access patterns:                                    |
|    READ  -> HNSW vector search (cosine similarity)   |
|    WRITE -> bulk insert after Ollama embedding        |
|    DELETE -> cascade when parent doc changes          |
+------------------------------------------------------+
```

```yaml
cubes:
  - name: document_chunks
    description: "Chunked and embedded content. Regenerated when parent document changes."
    sql_table: document_chunks

    joins:
      - name: crawled_documents
        relationship: many_to_one
        sql: "{CUBE}.document_id = {crawled_documents}.id"

    dimensions:
      - name: id
        type: number
        primary_key: true
      - name: document_id
        type: number
      - name: chunk_index
        type: number
        description: "0-based position within parent document"
      - name: content
        type: string
      - name: token_count
        type: number

    measures:
      - name: count
        type: count
      - name: total_tokens
        type: sum
        sql: "{CUBE}.token_count"
      - name: avg_chunk_tokens
        type: avg
        sql: "{CUBE}.token_count"
```

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    id            SERIAL  PRIMARY KEY,
    document_id   INTEGER NOT NULL REFERENCES crawled_documents (id) ON DELETE CASCADE,
    chunk_index   INTEGER NOT NULL,
    content       TEXT    NOT NULL,
    embedding     vector(768),
    token_count   INTEGER,

    UNIQUE (document_id, chunk_index)
);

CREATE INDEX idx_chunks_hnsw   ON document_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_chunks_doc_id ON document_chunks (document_id);
```

### processing_queue -- Async Job Queue

```
+------------------------------------------------------+
|                  processing_queue                    |
|                                                      |
|  Async jobs triggered by upsert_document().          |
|  JOIN: processing_queue.document_id ->               |
|        crawled_documents.id (many-to-one)            |
|                                                      |
|  +------------------+     +----------------------+   |
|  | processing_queue | N:1 | crawled_documents    |   |
|  | .document_id     |---->| .id                  |   |
|  +------------------+     +----------------------+   |
|                                                      |
|  Lifecycle:                                          |
|    pending -> processing -> done | failed            |
|                                                      |
|  Access patterns:                                    |
|    READ  -> pick next job (priority DESC, id ASC)    |
|    WRITE -> enqueue on document upsert               |
|    UPDATE -> status transitions by worker            |
+------------------------------------------------------+
```

```yaml
cubes:
  - name: processing_queue
    description: "Async jobs for chunking and embedding documents. Triggered by upserts."
    sql_table: processing_queue

    joins:
      - name: crawled_documents
        relationship: many_to_one
        sql: "{CUBE}.document_id = {crawled_documents}.id"

    dimensions:
      - name: id
        type: number
        primary_key: true
      - name: operation
        type: string
        description: "Job type: chunk_and_embed"
      - name: status
        type: string
        description: "pending | processing | done | failed"
      - name: priority
        type: number

    measures:
      - name: count
        type: count
      - name: pending_jobs
        type: count
        filters:
          - sql: "{CUBE}.status = 'pending'"
      - name: failed_jobs
        type: count
        filters:
          - sql: "{CUBE}.status = 'failed'"
      - name: avg_processing_seconds
        type: avg
        sql: "EXTRACT(EPOCH FROM ({CUBE}.completed_at - {CUBE}.started_at))"
```

```sql
CREATE TABLE processing_queue (
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

CREATE INDEX idx_queue_pending ON processing_queue (priority DESC, id ASC) WHERE status = 'pending';
```

### SQL Functions (CTE-based)

```sql
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

---

## Section 2: Agent, Hooks, Library, and MLflow Tracing

### 2A: Neon Specialist Agent

```
PM Agent Hierarchy (updated)

VP Product --- Task(sdm), Task(sprint-master),
|              Task(neon-specialist)  <-- NEW
+-- SDM --- Task(staff-engineer),
|           Task(neon-specialist)     <-- NEW
|   +-- Staff Engineer (leaf)
+-- Sprint Master (leaf -- read-only)

Team Lead --- Task(implementer), Task(tester),
|             Task(reviewer),
|             Task(neon-specialist)   <-- NEW
+-- Implementer (leaf)
+-- Tester (leaf)
+-- Reviewer (leaf -- read-only)

Neon Specialist (leaf -- DB operations only)  <-- NEW
```

**Agent file:** `pm/agents/neon-specialist.md`

```yaml
---
name: neon-specialist
description: "Stores, indexes, and searches documents in Neon pgvector. Transparent cache for WebFetch."
model: claude-opus-4-6
memory: project
tools:
  - Read
  - Bash
  - Glob
  - Grep
---
```

Operations:
1. **Store**: `python3 pm/lib/neon_docs.py store --url <url>` or `--file <path>`
2. **Search**: `python3 pm/lib/neon_docs.py search "<query>" --limit 5`
3. **Process**: `python3 pm/lib/neon_docs.py process-queue`
4. **Status**: `python3 pm/lib/neon_docs.py status`

### 2B: PreToolUse / PostToolUse Hooks

```
PM Agent calls WebFetch("https://docs.anthropic.com/tool-use")
     |
     v
+------------------------------------------+
| PreToolUse hook (matcher: WebFetch)      |
|                                          |
| pm/scripts/neon-cache-check.sh <url>     |
|   -> python3 pm/lib/neon_docs.py         |
|         check-url <url>                  |
|                                          |
|   HIT:  stdout -> cached content         |
|         exit 0 (hook passes)             |
|                                          |
|   MISS: stdout -> "CACHE_MISS"           |
|         exit 0 (proceed to WebFetch)     |
+------------------------------------------+
     | (on MISS, WebFetch runs normally)
     v
+------------------------------------------+
| PostToolUse hook (matcher: WebFetch)     |
|                                          |
| pm/scripts/neon-cache-store.sh           |
|   -> python3 pm/lib/neon_docs.py         |
|         store-page <url> <content>       |
|                                          |
|   Upserts into crawled_documents         |
|   Enqueues processing job                |
|   exit 0                                 |
+------------------------------------------+
```

Hook config added to VP Product, SDM, Team Lead, Staff Engineer, Implementer:

```yaml
hooks:
  PreToolUse:
    - matcher: WebFetch
      command: "pm/scripts/neon-cache-check.sh"
  PostToolUse:
    - matcher: WebFetch
      command: "pm/scripts/neon-cache-store.sh"
```

### 2C: lib/neon_docs.py -- CLI Interface

```
pm/lib/neon_docs.py

  CLI commands:
    store    --url <url> | --file <path>
    search   "<query>" --limit N --threshold 0.3
    check-url <url>
    process-queue
    bulk-index <directory>
    status

  Internal modules:
    db.py         -> asyncpg connection pool
    chunker.py    -> text splitting (512 token chunks with 64 token overlap)
    embedder.py   -> Ollama API (nomic-embed-text)
    tracer.py     -> MLflow 3.9 span instrumentation

  Dependencies:
    asyncpg       -> Neon connection (pooler endpoint)
    httpx         -> Ollama HTTP API calls
    mlflow>=3.9   -> tracing spans
```

Connection strategy: Neon `-pooler` endpoint, asyncpg with prepared statements, `PRJ_NEON_DATABASE_URL` env var.

### 2D: Makefile Targets

| Level | Target | Description |
|-------|--------|-------------|
| L0 | `l0-doc-store` | Store single document |
| L0 | `l0-doc-search` | Search single query |
| L0 | `l0-doc-process` | Process one queue item |
| L0 | `l0-doc-status` | Show queue/cache stats |
| L1 | `l1-doc-index` | Bulk-index docs/crawler-improvements/ |
| L1 | `l1-doc-drain` | Drain entire processing queue |
| L1 | `l1-doc-migrate` | Run schema migrations |
| L2 | `l2-doc-refresh` | Re-fetch all URLs, update stale |
| L2 | `l2-doc-reindex` | Purge chunks + re-embed all |
| L3 | `l3-doc-setup` | Migrate + bulk-index + drain + verify |

### 2E: MLflow 3.9 GenAI Tracing

```
Tracing Architecture

mlflow.anthropic.autolog()  <-- enabled in agent entry
         |
         v
+---------------------+
| Claude CLI Traces    | -- tool calls, prompts,
| (automatic)          |    responses, timing
+---------------------+

@mlflow.trace  <-- custom spans in lib/neon_docs.py
         |
         v
+---------------------+  +-------------------------+
| neon.cache_check    |  | neon.store              |
|  - url              |  |  - url/path             |
|  - hit/miss         |  |  - action (insert/      |
|  - latency_ms       |  |    update/unchanged)    |
+---------------------+  +-------------------------+

+---------------------+  +-------------------------+
| neon.search         |  | ollama.embed            |
|  - query            |  |  - model                |
|  - results_count    |  |  - chunk_count          |
|  - top_similarity   |  |  - latency_ms           |
|  - latency_ms       |  |  - tokens_processed     |
+---------------------+  +-------------------------+
```

Upgrade: `mlflow>=2.10.0` -> `mlflow>=3.9.0`

### 2F: File Inventory

| File | Action | Purpose |
|------|--------|---------|
| `pm/agents/neon-specialist.md` | CREATE | New agent definition |
| `pm/lib/neon_docs.py` | CREATE | CLI + core library |
| `pm/lib/neon_docs/db.py` | CREATE | asyncpg connection pool |
| `pm/lib/neon_docs/chunker.py` | CREATE | Text splitting |
| `pm/lib/neon_docs/embedder.py` | CREATE | Ollama API client |
| `pm/lib/neon_docs/tracer.py` | CREATE | MLflow span wrappers |
| `pm/scripts/neon-cache-check.sh` | CREATE | PreToolUse hook script |
| `pm/scripts/neon-cache-store.sh` | CREATE | PostToolUse hook script |
| `pm/scripts/neon-migrate.sql` | CREATE | Schema DDL |
| `pm/Makefile` | MODIFY | Add l0-l3 doc targets |
| `pm/requirements.txt` | MODIFY | Add asyncpg, httpx; upgrade mlflow |
| `pm/agents/vp-product.md` | MODIFY | Add hooks + Task(neon-specialist) |
| `pm/agents/sdm.md` | MODIFY | Add hooks + Task(neon-specialist) |
| `pm/agents/staff-engineer.md` | MODIFY | Add hooks |
| `pm/.index/generate-merkle.py` | MODIFY | Track .py files, add neon-specialist |
| `pm/lib/mlflow_tracing.py` | MODIFY | Upgrade to MLflow 3.9 autolog API |

---

## Section 3: Deterministic Workflow Integration

### Document Pipeline (L0-L3)

```
L0 (atomic)
+---------+  +---------+  +----------+  +---------+
|l0-store |  |l0-search|  |l0-process|  |l0-status|
| (1 doc) |  |(1 query)|  | (1 job)  |  | (stats) |
+----+----+  +---------+  +----+-----+  +---------+
     |                         |
L1 (composed)                  |
+----+----------------+  +----+------------+
| l1-bulk-index       |  | l1-drain-queue  |
| (all crawler docs)  |  | (all pending)   |
+----+----------------+  +----+------------+
     |                        |
L2 (workflow)                 |
+----+------------------------+--+
| l2-doc-refresh                 |
| (re-fetch stale + reindex)     |
+----+---------------------------+
     |
L3 (pipeline)
+----+---------------------------+
| l3-doc-setup                   |
| (migrate + index + drain +     |
|  verify + trace report)        |
+--------------------------------+
```

### Idempotency Guarantees

| Operation | Idempotent? | Mechanism |
|-----------|-------------|-----------|
| `l0-store` (same content) | Yes | content_hash match -> NO-OP |
| `l0-store` (new content) | Yes | content_hash mismatch -> UPDATE + re-queue |
| `l0-process` | Yes | queue status prevents double-process |
| `l1-bulk-index` | Yes | each file checked by hash before storing |
| `l2-doc-refresh` | Yes | re-fetch all URLs, only update if hash differs |
| `l3-doc-setup` | Yes | migration is idempotent (IF NOT EXISTS) |

### MLflow 3.9 Measurement Plan

| Metric | Target | Source |
|--------|--------|--------|
| Cache hit rate (after warm-up) | > 60% | MLflow trace dashboard |
| Cache check latency p95 | < 100ms | @mlflow.trace on check-url |
| Search latency p95 | < 200ms | @mlflow.trace on search |
| Tokens saved per cache hit | > 500 avg | WebFetch vs cache response size |
| All crawler docs indexed | 10/10 | l0-status output |
| Queue drain complete | 0 pending | Queue status check |
| Idempotent re-runs | No duplicates | Run l1-bulk-index twice |
| MLflow traces visible | All ops | Manual dashboard check |
| Existing tests pass | Green | pm/tests/run-tests.sh |

### Rollout Phases

**Phase 1: Infrastructure (no agent changes)**
- Schema migration (neon-migrate.sql)
- lib/neon_docs.py + sub-modules
- Ollama model pull (nomic-embed-text)
- Makefile targets
- MLflow 3.9 upgrade

**Phase 2: Bootstrap data**
- l3-doc-setup (one-time)
- Index all 10 crawler-improvement docs
- Verify search quality

**Phase 3: Agent integration**
- Create neon-specialist.md
- Add hooks to PM agents
- Update parent agent tool lists
- Regenerate merkle tree
- Run tests

**Phase 4: Measurement**
- Run agents with tracing enabled
- Collect baseline metrics
- Compare token usage before/after
- Tune search threshold and chunk size
