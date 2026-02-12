"""Google Sheets API client for writing data.

depends_on:
  - lib/get_env.py
depended_by:
  - lib/orchestrator.py
  - tests/test_sheets_client.py
semver: minor
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Protocol

from lib.get_env import env


@dataclass(frozen=True)
class SheetRange:
    """Reference to a range in a Google Sheet."""

    sheet_id: str
    sheet_name: str
    range_spec: str = "A1"  # e.g., "A1:F100" or just "A1" for auto-expand

    @property
    def full_range(self) -> str:
        """Full A1 notation including sheet name."""
        return f"'{self.sheet_name}'!{self.range_spec}"


class SheetsClient(Protocol):
    """Protocol for Google Sheets API clients."""

    async def write_data(
        self,
        sheet_range: SheetRange,
        data: list[list[str | int | float]],
    ) -> int:
        """Write data to the specified range. Returns rows written."""
        ...

    async def clear_range(self, sheet_range: SheetRange) -> None:
        """Clear all data in the specified range."""
        ...


class LiveSheetsClient:
    """Real Google Sheets API v4 client.

    Uses service account credentials from GOOGLE_SHEETS_CREDENTIALS_JSON.
    """

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self, credentials_path: str | None = None) -> None:
        self._credentials_path = credentials_path or env("GOOGLE_SHEETS_CREDENTIALS_JSON")
        self._service = None

    def _get_service(self):
        """Lazy-initialize the Google Sheets service."""
        if self._service is None:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            credentials = Credentials.from_service_account_file(
                self._credentials_path,
                scopes=self.SCOPES,
            )
            self._service = build("sheets", "v4", credentials=credentials)
        return self._service

    async def write_data(
        self,
        sheet_range: SheetRange,
        data: list[list[str | int | float]],
    ) -> int:
        """Write data to the specified range."""
        service = self._get_service()
        body = {"values": data}

        def _execute() -> dict:
            return (
                service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=sheet_range.sheet_id,
                    range=sheet_range.full_range,
                    valueInputOption="USER_ENTERED",
                    body=body,
                )
                .execute()
            )

        result = await asyncio.to_thread(_execute)
        return result.get("updatedRows", 0)

    async def clear_range(self, sheet_range: SheetRange) -> None:
        """Clear all data in the specified range."""
        service = self._get_service()

        def _execute() -> None:
            service.spreadsheets().values().clear(
                spreadsheetId=sheet_range.sheet_id,
                range=sheet_range.full_range,
                body={},
            ).execute()

        await asyncio.to_thread(_execute)


@dataclass
class MockSheetsClient:
    """Mock client for testing - captures writes in memory."""

    writes: list[tuple[SheetRange, list[list]]] = field(default_factory=list)
    clears: list[SheetRange] = field(default_factory=list)

    async def write_data(
        self,
        sheet_range: SheetRange,
        data: list[list[str | int | float]],
    ) -> int:
        """Capture write in memory."""
        self.writes.append((sheet_range, data))
        return len(data)

    async def clear_range(self, sheet_range: SheetRange) -> None:
        """Capture clear in memory."""
        self.clears.append(sheet_range)


def get_sheets_client(*, use_mock: bool = False) -> SheetsClient:
    """Factory function to get the appropriate Sheets client."""
    if use_mock:
        return MockSheetsClient()
    return LiveSheetsClient()
