"""Neon-backed document caching and semantic search for PM agents.

Public API (available after all phases complete):
    - check_url: Check if URL is cached
    - upsert_document: Store/update a document
    - search: Semantic search across documents
    - drain_queue: Process all pending embed jobs
    - get_status: Get cache statistics
    - run_migrations: Apply database migrations
"""

__version__ = "0.1.0"
