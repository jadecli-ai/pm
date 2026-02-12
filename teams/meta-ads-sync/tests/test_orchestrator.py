"""Tests for Meta → Sheets orchestrator.

depends_on:
  - lib/orchestrator.py
  - tests/conftest.py
depended_by: []
semver: patch
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from lib.meta_client import MockMetaAdsClient
from lib.orchestrator import MetaSheetsOrchestrator, SyncResult
from lib.sheets_client import MockSheetsClient


class TestSyncResult:
    """Tests for SyncResult dataclass."""

    def test_creation(self) -> None:
        """SyncResult can be created with valid data."""
        result = SyncResult(
            success=True,
            rows_written=7,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            campaign_id="123456789",
            sheet_id="1abc123xyz",
            message="Successfully synced 7 days of data",
        )

        assert result.success is True
        assert result.rows_written == 7
        assert result.message == "Successfully synced 7 days of data"


class TestMetaSheetsOrchestrator:
    """Tests for MetaSheetsOrchestrator."""

    @pytest.fixture
    def orchestrator(
        self,
        mock_meta_client: MockMetaAdsClient,
        mock_sheets_client: MockSheetsClient,
    ) -> MetaSheetsOrchestrator:
        """Create orchestrator with mock clients."""
        return MetaSheetsOrchestrator(
            meta=mock_meta_client,
            sheets=mock_sheets_client,
        )

    @pytest.mark.asyncio
    async def test_successful_sync(
        self,
        orchestrator: MetaSheetsOrchestrator,
        mock_sheets_client: MockSheetsClient,
        sample_campaign_id: str,
        sample_sheet_id: str,
    ) -> None:
        """Successful sync writes data to sheets."""
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 7)

        result = await orchestrator.sync_campaign_spend(
            campaign_id=sample_campaign_id,
            start_date=start_date,
            end_date=end_date,
            sheet_id=sample_sheet_id,
        )

        assert result.success is True
        assert result.rows_written == 8  # 7 days + header
        assert len(mock_sheets_client.writes) == 1
        assert len(mock_sheets_client.clears) == 1

    @pytest.mark.asyncio
    async def test_writes_header_row(
        self,
        orchestrator: MetaSheetsOrchestrator,
        mock_sheets_client: MockSheetsClient,
        sample_campaign_id: str,
        sample_sheet_id: str,
    ) -> None:
        """Sync includes header row."""
        result = await orchestrator.sync_campaign_spend(
            campaign_id=sample_campaign_id,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            sheet_id=sample_sheet_id,
        )

        assert result.success is True
        _, data = mock_sheets_client.writes[0]
        assert data[0] == MetaSheetsOrchestrator.HEADERS

    @pytest.mark.asyncio
    async def test_dry_run_no_write(
        self,
        orchestrator: MetaSheetsOrchestrator,
        mock_sheets_client: MockSheetsClient,
        sample_campaign_id: str,
        sample_sheet_id: str,
    ) -> None:
        """Dry run doesn't write to sheets."""
        result = await orchestrator.sync_campaign_spend(
            campaign_id=sample_campaign_id,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            sheet_id=sample_sheet_id,
            dry_run=True,
        )

        assert result.success is True
        assert "DRY RUN" in result.message
        assert len(mock_sheets_client.writes) == 0
        assert len(mock_sheets_client.clears) == 0

    @pytest.mark.asyncio
    async def test_invalid_date_range(
        self,
        orchestrator: MetaSheetsOrchestrator,
        sample_campaign_id: str,
        sample_sheet_id: str,
    ) -> None:
        """Invalid date range (end before start) returns error."""
        result = await orchestrator.sync_campaign_spend(
            campaign_id=sample_campaign_id,
            start_date=date(2025, 1, 7),
            end_date=date(2025, 1, 1),  # Before start
            sheet_id=sample_sheet_id,
        )

        assert result.success is False
        assert "Invalid date range" in result.message

    @pytest.mark.asyncio
    async def test_clears_before_write(
        self,
        orchestrator: MetaSheetsOrchestrator,
        mock_sheets_client: MockSheetsClient,
        sample_campaign_id: str,
        sample_sheet_id: str,
    ) -> None:
        """Orchestrator clears existing data before writing."""
        await orchestrator.sync_campaign_spend(
            campaign_id=sample_campaign_id,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 3),
            sheet_id=sample_sheet_id,
        )

        # Should clear before write
        assert len(mock_sheets_client.clears) == 1
        assert len(mock_sheets_client.writes) == 1

    @pytest.mark.asyncio
    async def test_custom_sheet_name(
        self,
        orchestrator: MetaSheetsOrchestrator,
        mock_sheets_client: MockSheetsClient,
        sample_campaign_id: str,
        sample_sheet_id: str,
    ) -> None:
        """Can specify custom sheet tab name."""
        await orchestrator.sync_campaign_spend(
            campaign_id=sample_campaign_id,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            sheet_id=sample_sheet_id,
            sheet_name="Custom Tab",
        )

        sheet_range, _ = mock_sheets_client.writes[0]
        assert sheet_range.sheet_name == "Custom Tab"

    @pytest.mark.asyncio
    async def test_data_transformation(
        self,
        orchestrator: MetaSheetsOrchestrator,
        mock_sheets_client: MockSheetsClient,
        sample_campaign_id: str,
        sample_sheet_id: str,
    ) -> None:
        """Data is correctly transformed to rows."""
        await orchestrator.sync_campaign_spend(
            campaign_id=sample_campaign_id,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            sheet_id=sample_sheet_id,
        )

        _, data = mock_sheets_client.writes[0]
        assert len(data) == 2  # Header + 1 data row

        # Check data row structure
        data_row = data[1]
        assert len(data_row) == 6  # Date, Campaign ID, Name, Spend, Impressions, Clicks
        assert data_row[0] == "2025-01-01"  # Date as ISO string
        assert data_row[1] == sample_campaign_id


class TestIntegration:
    """End-to-end integration tests with mocks."""

    @pytest.mark.asyncio
    async def test_full_sync_workflow(self) -> None:
        """Complete sync workflow with mock clients."""
        meta = MockMetaAdsClient(campaign_name="Integration Test Campaign")
        sheets = MockSheetsClient()
        orchestrator = MetaSheetsOrchestrator(meta=meta, sheets=sheets)

        result = await orchestrator.sync_campaign_spend(
            campaign_id="999888777666",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            sheet_id="integration_test_sheet",
            sheet_name="Integration Test",
        )

        # Verify success
        assert result.success is True
        assert result.rows_written == 8  # 7 days + header
        assert result.campaign_id == "999888777666"
        assert result.sheet_id == "integration_test_sheet"

        # Verify sheet operations
        assert len(sheets.clears) == 1
        assert len(sheets.writes) == 1

        # Verify data structure
        _, data = sheets.writes[0]
        assert data[0] == MetaSheetsOrchestrator.HEADERS
        assert len(data) == 8  # Header + 7 data rows

        # Verify data content
        for i, row in enumerate(data[1:], start=1):
            assert row[2] == "Integration Test Campaign"
            assert row[1] == "999888777666"
