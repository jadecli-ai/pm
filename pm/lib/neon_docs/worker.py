# pm/lib/neon_docs/worker.py
"""Queue processing worker: chunk + embed pipeline."""

from __future__ import annotations

from .chunker import chunk_text
from .embedder import embed_texts
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
from .tracer import trace_operation

logger = get_logger("worker")


@trace_operation("neon.process_one_job")
async def process_one_job(job: QueueJob) -> bool:
    """Process a single queue job."""
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


@trace_operation("neon.drain_queue")
async def drain_queue() -> dict[str, int]:
    """Process all pending queue jobs."""
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
