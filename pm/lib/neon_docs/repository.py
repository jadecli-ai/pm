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
    """Upsert a document via the upsert_document() SQL function."""
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
    """Check if a URL is cached."""
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
    """Hybrid search across cached documents."""
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
    """Pick the next pending queue job (atomic)."""
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
    """Get document content and title by ID."""
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
    """Insert chunks with embeddings for a document."""
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
