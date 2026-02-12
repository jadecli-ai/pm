"""Meta Ads API client for fetching campaign spend data.

depends_on:
  - lib/get_env.py
depended_by:
  - lib/orchestrator.py
  - tests/test_meta_client.py
semver: minor
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

import httpx

from lib.get_env import env


@dataclass(frozen=True)
class DailySpend:
    """Single day of campaign spend data."""

    date: date
    campaign_id: str
    campaign_name: str
    spend_usd: float
    impressions: int
    clicks: int


class MetaAdsClient(Protocol):
    """Protocol for Meta Ads API clients."""

    async def get_daily_spend(
        self,
        campaign_id: str,
        start_date: date,
        end_date: date,
    ) -> list[DailySpend]:
        """Fetch daily spend data for a campaign in the given date range."""
        ...


class LiveMetaAdsClient:
    """Real Meta Marketing API client.

    Uses the Facebook Marketing API v18.0 insights endpoint.
    Requires META_ACCESS_TOKEN and META_AD_ACCOUNT_ID env vars.
    """

    API_VERSION = "v18.0"
    BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

    def __init__(self, access_token: str | None = None) -> None:
        self._access_token = access_token or env("META_ACCESS_TOKEN")

    async def get_daily_spend(
        self,
        campaign_id: str,
        start_date: date,
        end_date: date,
    ) -> list[DailySpend]:
        """Fetch daily spend data from Meta Ads API."""
        url = f"{self.BASE_URL}/{campaign_id}/insights"
        params = {
            "access_token": self._access_token,
            "fields": "campaign_id,campaign_name,spend,impressions,clicks",
            "time_range": f'{{"since":"{start_date}","until":"{end_date}"}}',
            "time_increment": 1,  # Daily breakdown
            "level": "campaign",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        results: list[DailySpend] = []
        for row in data.get("data", []):
            results.append(
                DailySpend(
                    date=date.fromisoformat(row["date_start"]),
                    campaign_id=row["campaign_id"],
                    campaign_name=row["campaign_name"],
                    spend_usd=float(row.get("spend", 0)),
                    impressions=int(row.get("impressions", 0)),
                    clicks=int(row.get("clicks", 0)),
                )
            )

        return sorted(results, key=lambda x: x.date)


class MockMetaAdsClient:
    """Mock client for testing - returns 7 days of deterministic data."""

    def __init__(self, campaign_name: str = "Test Campaign") -> None:
        self._campaign_name = campaign_name

    async def get_daily_spend(
        self,
        campaign_id: str,
        start_date: date,
        end_date: date,
    ) -> list[DailySpend]:
        """Generate deterministic mock data for the date range."""
        results: list[DailySpend] = []
        current = start_date

        while current <= end_date:
            day_num = (current - start_date).days + 1
            results.append(
                DailySpend(
                    date=current,
                    campaign_id=campaign_id,
                    campaign_name=self._campaign_name,
                    spend_usd=round(100.0 + day_num * 10.0, 2),
                    impressions=1000 * day_num,
                    clicks=50 * day_num,
                )
            )
            current += timedelta(days=1)

        return results


def get_meta_client(*, use_mock: bool = False) -> MetaAdsClient:
    """Factory function to get the appropriate Meta Ads client."""
    if use_mock:
        return MockMetaAdsClient()
    return LiveMetaAdsClient()
