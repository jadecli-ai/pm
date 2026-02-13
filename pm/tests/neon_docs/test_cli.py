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
