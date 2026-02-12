"""Pytest fixtures for Meta Ads sync tests.

depends_on:
  - lib/meta_client.py
  - lib/sheets_client.py
depended_by:
  - tests/test_meta_client.py
  - tests/test_sheets_client.py
  - tests/test_orchestrator.py
semver: patch
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from lib.get_env import env
from lib.meta_client import MockMetaAdsClient
from lib.sheets_client import MockSheetsClient, SheetRange


@pytest.fixture
def mock_meta_client() -> MockMetaAdsClient:
    """Mock Meta Ads client for testing."""
    return MockMetaAdsClient(campaign_name="Test Campaign")


@pytest.fixture
def mock_sheets_client() -> MockSheetsClient:
    """Mock Sheets client for testing."""
    return MockSheetsClient()


@pytest.fixture
def sample_date_range() -> tuple[date, date]:
    """7-day date range for testing."""
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=6)
    return start_date, end_date


@pytest.fixture
def sample_campaign_id() -> str:
    """Sample campaign ID for testing."""
    return "123456789012345"


@pytest.fixture
def sample_sheet_id() -> str:
    """Sample Google Sheet ID for testing."""
    return "1abc123xyz_test_sheet_id"


@pytest.fixture
def sample_sheet_range(sample_sheet_id: str) -> SheetRange:
    """Sample sheet range for testing."""
    return SheetRange(
        sheet_id=sample_sheet_id,
        sheet_name="Daily Spend",
        range_spec="A1",
    )


# Live test fixtures - only used when credentials are available


@pytest.fixture
def has_meta_credentials() -> bool:
    """Check if Meta API credentials are available."""
    return env("META_ACCESS_TOKEN", default=None) is not None


@pytest.fixture
def has_sheets_credentials() -> bool:
    """Check if Google Sheets credentials are available."""
    return env("GOOGLE_SHEETS_CREDENTIALS_JSON", default=None) is not None


@pytest.fixture
def live_campaign_id() -> str | None:
    """Get test campaign ID from env, or None if not set."""
    return env("META_TEST_CAMPAIGN_ID", default=None)


@pytest.fixture
def live_sheet_id() -> str | None:
    """Get test sheet ID from env, or None if not set."""
    return env("GOOGLE_SHEET_ID", default=None)
