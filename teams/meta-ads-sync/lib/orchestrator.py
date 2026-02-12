"""Data pipeline orchestrator: Meta Ads → Google Sheets.

depends_on:
  - lib/meta_client.py
  - lib/sheets_client.py
depended_by:
  - lib/cli.py
  - tests/test_orchestrator.py
semver: minor
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from lib.meta_client import DailySpend, MetaAdsClient
from lib.sheets_client import SheetRange, SheetsClient


@dataclass(frozen=True)
class SyncResult:
    """Result of a sync operation."""

    success: bool
    rows_written: int
    start_date: date
    end_date: date
    campaign_id: str
    sheet_id: str
    message: str


class MetaSheetsOrchestrator:
    """Orchestrates the Meta Ads → Google Sheets data pipeline."""

    HEADERS = ["Date", "Campaign ID", "Campaign Name", "Spend (USD)", "Impressions", "Clicks"]

    def __init__(
        self,
        meta: MetaAdsClient,
        sheets: SheetsClient,
    ) -> None:
        self._meta = meta
        self._sheets = sheets

    async def sync_campaign_spend(
        self,
        campaign_id: str,
        start_date: date,
        end_date: date,
        sheet_id: str,
        sheet_name: str = "Daily Spend",
        *,
        dry_run: bool = False,
    ) -> SyncResult:
        """Sync campaign spend data to Google Sheets.

        1. Fetch from Meta Ads API
        2. Transform to spreadsheet rows
        3. Clear existing data + write new

        Args:
            campaign_id: Meta campaign ID to fetch
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            sheet_id: Google Sheet ID
            sheet_name: Tab name in the sheet
            dry_run: If True, fetch but don't write
        """
        # Validate date range
        if end_date < start_date:
            return SyncResult(
                success=False,
                rows_written=0,
                start_date=start_date,
                end_date=end_date,
                campaign_id=campaign_id,
                sheet_id=sheet_id,
                message=f"Invalid date range: {end_date} is before {start_date}",
            )

        # Fetch from Meta
        try:
            spend_data = await self._meta.get_daily_spend(
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as e:
            return SyncResult(
                success=False,
                rows_written=0,
                start_date=start_date,
                end_date=end_date,
                campaign_id=campaign_id,
                sheet_id=sheet_id,
                message=f"Failed to fetch from Meta Ads: {e}",
            )

        if not spend_data:
            return SyncResult(
                success=True,
                rows_written=0,
                start_date=start_date,
                end_date=end_date,
                campaign_id=campaign_id,
                sheet_id=sheet_id,
                message="No data found for the specified date range",
            )

        # Transform to rows
        rows = self._transform_to_rows(spend_data)

        if dry_run:
            return SyncResult(
                success=True,
                rows_written=len(rows) - 1,  # Exclude header
                start_date=start_date,
                end_date=end_date,
                campaign_id=campaign_id,
                sheet_id=sheet_id,
                message=f"DRY RUN: Would write {len(rows)} rows (including header)",
            )

        # Write to Sheets
        sheet_range = SheetRange(
            sheet_id=sheet_id,
            sheet_name=sheet_name,
            range_spec="A1",
        )

        try:
            # Clear existing data
            await self._sheets.clear_range(sheet_range)

            # Write new data
            rows_written = await self._sheets.write_data(sheet_range, rows)
        except Exception as e:
            return SyncResult(
                success=False,
                rows_written=0,
                start_date=start_date,
                end_date=end_date,
                campaign_id=campaign_id,
                sheet_id=sheet_id,
                message=f"Failed to write to Google Sheets: {e}",
            )

        return SyncResult(
            success=True,
            rows_written=rows_written,
            start_date=start_date,
            end_date=end_date,
            campaign_id=campaign_id,
            sheet_id=sheet_id,
            message=f"Successfully synced {len(spend_data)} days of data",
        )

    def _transform_to_rows(
        self,
        spend_data: list[DailySpend],
    ) -> list[list[str | int | float]]:
        """Transform DailySpend objects to spreadsheet rows."""
        rows: list[list[str | int | float]] = [self.HEADERS]

        for day in spend_data:
            rows.append([
                day.date.isoformat(),
                day.campaign_id,
                day.campaign_name,
                day.spend_usd,
                day.impressions,
                day.clicks,
            ])

        return rows
