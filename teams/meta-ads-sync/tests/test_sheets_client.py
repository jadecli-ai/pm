"""Tests for Google Sheets API client.

depends_on:
  - lib/sheets_client.py
  - tests/conftest.py
depended_by: []
semver: patch
"""

from __future__ import annotations

import pytest

from lib.get_env import env
from lib.sheets_client import (
    LiveSheetsClient,
    MockSheetsClient,
    SheetRange,
    get_sheets_client,
)


class TestSheetRange:
    """Tests for SheetRange dataclass."""

    def test_creation(self) -> None:
        """SheetRange can be created with valid data."""
        sheet_range = SheetRange(
            sheet_id="1abc123xyz",
            sheet_name="Daily Spend",
            range_spec="A1:F100",
        )

        assert sheet_range.sheet_id == "1abc123xyz"
        assert sheet_range.sheet_name == "Daily Spend"
        assert sheet_range.range_spec == "A1:F100"

    def test_full_range(self) -> None:
        """full_range property returns A1 notation with sheet name."""
        sheet_range = SheetRange(
            sheet_id="1abc123xyz",
            sheet_name="Daily Spend",
            range_spec="A1:F100",
        )

        assert sheet_range.full_range == "'Daily Spend'!A1:F100"

    def test_default_range_spec(self) -> None:
        """range_spec defaults to A1."""
        sheet_range = SheetRange(
            sheet_id="1abc123xyz",
            sheet_name="Test",
        )

        assert sheet_range.range_spec == "A1"
        assert sheet_range.full_range == "'Test'!A1"

    def test_frozen(self) -> None:
        """SheetRange is immutable."""
        sheet_range = SheetRange(
            sheet_id="1abc123xyz",
            sheet_name="Test",
        )

        with pytest.raises(AttributeError):
            sheet_range.sheet_id = "new_id"  # type: ignore[misc]


class TestMockSheetsClient:
    """Tests for MockSheetsClient."""

    @pytest.mark.asyncio
    async def test_write_captures_data(
        self,
        mock_sheets_client: MockSheetsClient,
        sample_sheet_range: SheetRange,
    ) -> None:
        """Mock client captures write data in memory."""
        data = [["Header1", "Header2"], ["Value1", "Value2"]]

        rows_written = await mock_sheets_client.write_data(sample_sheet_range, data)

        assert rows_written == 2
        assert len(mock_sheets_client.writes) == 1
        assert mock_sheets_client.writes[0] == (sample_sheet_range, data)

    @pytest.mark.asyncio
    async def test_clear_captures_range(
        self,
        mock_sheets_client: MockSheetsClient,
        sample_sheet_range: SheetRange,
    ) -> None:
        """Mock client captures clear operations."""
        await mock_sheets_client.clear_range(sample_sheet_range)

        assert len(mock_sheets_client.clears) == 1
        assert mock_sheets_client.clears[0] == sample_sheet_range

    @pytest.mark.asyncio
    async def test_multiple_writes(
        self,
        mock_sheets_client: MockSheetsClient,
    ) -> None:
        """Mock client captures multiple writes."""
        range1 = SheetRange(sheet_id="sheet1", sheet_name="Tab1")
        range2 = SheetRange(sheet_id="sheet2", sheet_name="Tab2")
        data1 = [["A", "B"]]
        data2 = [["C", "D"], ["E", "F"]]

        await mock_sheets_client.write_data(range1, data1)
        await mock_sheets_client.write_data(range2, data2)

        assert len(mock_sheets_client.writes) == 2
        assert mock_sheets_client.writes[0] == (range1, data1)
        assert mock_sheets_client.writes[1] == (range2, data2)

    @pytest.mark.asyncio
    async def test_empty_data(
        self,
        mock_sheets_client: MockSheetsClient,
        sample_sheet_range: SheetRange,
    ) -> None:
        """Mock client handles empty data."""
        rows_written = await mock_sheets_client.write_data(sample_sheet_range, [])

        assert rows_written == 0


class TestGetSheetsClient:
    """Tests for factory function."""

    def test_returns_mock_when_requested(self) -> None:
        """get_sheets_client returns MockSheetsClient when use_mock=True."""
        client = get_sheets_client(use_mock=True)
        assert isinstance(client, MockSheetsClient)

    def test_returns_live_when_not_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """get_sheets_client returns LiveSheetsClient when use_mock=False."""
        monkeypatch.setenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "/tmp/test_creds.json")
        client = get_sheets_client(use_mock=False)
        assert isinstance(client, LiveSheetsClient)


# Live tests - only run when credentials are available


@pytest.mark.skipif(
    env("GOOGLE_SHEETS_CREDENTIALS_JSON", default=None) is None,
    reason="GOOGLE_SHEETS_CREDENTIALS_JSON not set",
)
@pytest.mark.skipif(
    env("GOOGLE_SHEET_ID", default=None) is None,
    reason="GOOGLE_SHEET_ID not set",
)
class TestLiveSheetsClient:
    """Live integration tests for Google Sheets API."""

    @pytest.mark.asyncio
    async def test_live_write_and_clear(self) -> None:
        """Write and clear data in a real Google Sheet."""
        sheet_id = env("GOOGLE_SHEET_ID")
        sheet_range = SheetRange(
            sheet_id=sheet_id,
            sheet_name="Test Sheet",
            range_spec="A1",
        )
        data = [["Test", "Data"], ["Row1", "Value1"]]

        client = LiveSheetsClient()

        # Write data
        rows_written = await client.write_data(sheet_range, data)
        assert rows_written >= 0

        # Clear data
        await client.clear_range(sheet_range)
