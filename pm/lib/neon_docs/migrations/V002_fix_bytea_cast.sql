-- V002_fix_bytea_cast.sql
-- Fix: use convert_to() instead of ::bytea cast
-- The ::bytea cast fails on content containing backslash-x sequences
-- because PostgreSQL interprets them as bytea escape sequences.
-- convert_to() properly encodes UTF-8 text to bytes.

CREATE OR REPLACE FUNCTION upsert_document(
    p_url       TEXT,
    p_file_path TEXT,
    p_title     TEXT,
    p_content   TEXT
) RETURNS TABLE(action TEXT, doc_id INTEGER) AS $$
DECLARE
    v_hash TEXT := encode(sha256(convert_to(p_content, 'UTF8')), 'hex');
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
