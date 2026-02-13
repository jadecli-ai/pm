# pm/lib/neon_docs/models.py
"""Pydantic v2 models for database entities."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


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
