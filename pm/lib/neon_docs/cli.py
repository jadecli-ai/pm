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
