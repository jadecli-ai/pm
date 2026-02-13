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
