"""CLI for Meta Ads → Google Sheets sync.

depends_on:
  - lib/get_env.py
  - lib/meta_client.py
  - lib/sheets_client.py
  - lib/orchestrator.py
depended_by: []
semver: minor

Usage:
    # Default: last 7 days
    python -m lib.cli --campaign 123456789 --sheet 1abc123xyz

    # Custom date range
    python -m lib.cli --campaign 123456789 --sheet 1abc123xyz \\
        --start 2025-01-01 --end 2025-01-31

    # Dry run
    python -m lib.cli --campaign 123456789 --sheet 1abc123xyz --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date, timedelta

from lib.get_env import env
from lib.meta_client import get_meta_client
from lib.orchestrator import MetaSheetsOrchestrator
from lib.sheets_client import get_sheets_client


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Sync Meta Ads campaign spend to Google Sheets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--campaign",
        required=True,
        help="Meta campaign ID to sync",
    )
    parser.add_argument(
        "--sheet",
        required=True,
        help="Google Sheet ID to write to",
    )
    parser.add_argument(
        "--start",
        type=date.fromisoformat,
        default=None,
        help="Start date (YYYY-MM-DD). Default: 7 days ago",
    )
    parser.add_argument(
        "--end",
        type=date.fromisoformat,
        default=None,
        help="End date (YYYY-MM-DD). Default: yesterday",
    )
    parser.add_argument(
        "--sheet-name",
        default="Daily Spend",
        help="Tab name in the sheet (default: 'Daily Spend')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch data but don't write to sheet",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock clients (for testing)",
    )

    return parser.parse_args(args)


async def main(args: argparse.Namespace) -> int:
    """Run the sync operation."""
    # Default date range: last 7 days (excluding today)
    today = date.today()
    end_date = args.end or (today - timedelta(days=1))
    start_date = args.start or (end_date - timedelta(days=6))

    print(f"Meta Ads → Google Sheets Sync")
    print(f"  Campaign: {args.campaign}")
    print(f"  Sheet: {args.sheet}")
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Dry run: {args.dry_run}")
    print()

    # Create clients
    meta = get_meta_client(use_mock=args.mock)
    sheets = get_sheets_client(use_mock=args.mock)

    # Run sync
    orchestrator = MetaSheetsOrchestrator(meta=meta, sheets=sheets)

    result = await orchestrator.sync_campaign_spend(
        campaign_id=args.campaign,
        start_date=start_date,
        end_date=end_date,
        sheet_id=args.sheet,
        sheet_name=args.sheet_name,
        dry_run=args.dry_run,
    )

    # Print result
    if result.success:
        print(f"SUCCESS: {result.message}")
        print(f"  Rows written: {result.rows_written}")
        return 0
    else:
        print(f"FAILED: {result.message}")
        return 1


def cli() -> None:
    """CLI entry point."""
    args = parse_args()
    exit_code = asyncio.run(main(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    cli()
