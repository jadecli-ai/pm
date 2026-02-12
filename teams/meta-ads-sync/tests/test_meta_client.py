"""Tests for Meta Ads API client.

depends_on:
  - lib/meta_client.py
  - tests/conftest.py
depended_by: []
semver: patch
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from lib.get_env import env
from lib.meta_client import (
    DailySpend,
    LiveMetaAdsClient,
    MockMetaAdsClient,
    get_meta_client,
)


class TestDailySpend:
    """Tests for DailySpend dataclass."""

    def test_creation(self) -> None:
        """DailySpend can be created with valid data."""
        spend = DailySpend(
            date=date(2025, 1, 15),
            campaign_id="123456789",
            campaign_name="Test Campaign",
            spend_usd=150.50,
            impressions=10000,
            clicks=500,
        )

        assert spend.date == date(2025, 1, 15)
        assert spend.campaign_id == "123456789"
        assert spend.campaign_name == "Test Campaign"
        assert spend.spend_usd == 150.50
        assert spend.impressions == 10000
        assert spend.clicks == 500

    def test_frozen(self) -> None:
        """DailySpend is immutable."""
        spend = DailySpend(
            date=date(2025, 1, 15),
            campaign_id="123456789",
            campaign_name="Test",
            spend_usd=100.0,
            impressions=1000,
            clicks=50,
        )

        with pytest.raises(AttributeError):
            spend.spend_usd = 200.0  # type: ignore[misc]


class TestMockMetaAdsClient:
    """Tests for MockMetaAdsClient."""

    @pytest.mark.asyncio
    async def test_returns_data_for_date_range(
        self,
        mock_meta_client: MockMetaAdsClient,
        sample_campaign_id: str,
        sample_date_range: tuple[date, date],
    ) -> None:
        """Mock client returns data for each day in range."""
        start_date, end_date = sample_date_range
        expected_days = (end_date - start_date).days + 1

        result = await mock_meta_client.get_daily_spend(
            campaign_id=sample_campaign_id,
            start_date=start_date,
            end_date=end_date,
        )

        assert len(result) == expected_days
        assert all(isinstance(r, DailySpend) for r in result)

    @pytest.mark.asyncio
    async def test_returns_sorted_by_date(
        self,
        mock_meta_client: MockMetaAdsClient,
        sample_campaign_id: str,
    ) -> None:
        """Mock client returns data sorted by date."""
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 7)

        result = await mock_meta_client.get_daily_spend(
            campaign_id=sample_campaign_id,
            start_date=start_date,
            end_date=end_date,
        )

        dates = [r.date for r in result]
        assert dates == sorted(dates)

    @pytest.mark.asyncio
    async def test_deterministic_data(
        self,
        sample_campaign_id: str,
    ) -> None:
        """Mock client returns deterministic data."""
        client1 = MockMetaAdsClient()
        client2 = MockMetaAdsClient()
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 3)

        result1 = await client1.get_daily_spend(
            campaign_id=sample_campaign_id,
            start_date=start_date,
            end_date=end_date,
        )
        result2 = await client2.get_daily_spend(
            campaign_id=sample_campaign_id,
            start_date=start_date,
            end_date=end_date,
        )

        assert result1 == result2

    @pytest.mark.asyncio
    async def test_single_day_range(
        self,
        mock_meta_client: MockMetaAdsClient,
        sample_campaign_id: str,
    ) -> None:
        """Mock client handles single-day range."""
        single_date = date(2025, 1, 15)

        result = await mock_meta_client.get_daily_spend(
            campaign_id=sample_campaign_id,
            start_date=single_date,
            end_date=single_date,
        )

        assert len(result) == 1
        assert result[0].date == single_date


class TestGetMetaClient:
    """Tests for factory function."""

    def test_returns_mock_when_requested(self) -> None:
        """get_meta_client returns MockMetaAdsClient when use_mock=True."""
        client = get_meta_client(use_mock=True)
        assert isinstance(client, MockMetaAdsClient)

    def test_returns_live_when_not_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """get_meta_client returns LiveMetaAdsClient when use_mock=False."""
        monkeypatch.setenv("META_ACCESS_TOKEN", "test_token")
        client = get_meta_client(use_mock=False)
        assert isinstance(client, LiveMetaAdsClient)


# Live tests - only run when credentials are available


@pytest.mark.skipif(
    env("META_ACCESS_TOKEN", default=None) is None,
    reason="META_ACCESS_TOKEN not set",
)
@pytest.mark.skipif(
    env("META_TEST_CAMPAIGN_ID", default=None) is None,
    reason="META_TEST_CAMPAIGN_ID not set",
)
class TestLiveMetaAdsClient:
    """Live integration tests for Meta Ads API."""

    @pytest.mark.asyncio
    async def test_live_fetch(self) -> None:
        """Fetch real data from Meta Ads API."""
        campaign_id = env("META_TEST_CAMPAIGN_ID")
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=6)

        client = LiveMetaAdsClient()
        result = await client.get_daily_spend(
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Should return some data (may be empty if campaign has no spend)
        assert isinstance(result, list)
        if result:
            assert all(isinstance(r, DailySpend) for r in result)
