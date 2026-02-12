# Meta Ads Sync Team - Claude Code Instructions

> Pull Meta Ads daily spend → Export to Google Sheets

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests (all mocked)
pytest tests/

# Dry run (shows what would sync)
./sync-ads.sh --dry-run

# Real sync (requires credentials)
./sync-ads.sh
```

## Directory Structure

```
meta-ads-sync/
├── agents/
│   ├── meta-ads-sync-lead.md      # Sonnet, 15 turns - orchestration
│   └── meta-ads-sync-engineer.md  # Sonnet, 10 turns - implementation
├── lib/
│   ├── __init__.py
│   ├── get_env.py                 # Safe env accessor
│   ├── meta_client.py             # Meta Ads API client
│   ├── sheets_client.py           # Google Sheets client
│   ├── orchestrator.py            # Data pipeline
│   └── cli.py                     # User-facing CLI
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_meta_client.py
│   ├── test_sheets_client.py
│   └── test_orchestrator.py
├── CLAUDE.md                      # This file
├── env.template                   # API key registry
├── pyproject.toml                 # Dependencies
└── sync-ads.sh                    # User wrapper script
```

## Team Agents

| Agent | Model | Turns | Role |
|-------|-------|-------|------|
| `meta-ads-sync-lead` | claude-sonnet-4-5-20250929 | 15 | Orchestration, validation |
| `meta-ads-sync-engineer` | claude-sonnet-4-5-20250929 | 10 | Implementation, debugging |

## Environment Variables

Set these in `.env` (see `env.template`):

| Variable | Purpose |
|----------|---------|
| `META_ACCESS_TOKEN` | Marketing API access token |
| `META_AD_ACCOUNT_ID` | Ad account ID (act_123...) |
| `META_TEST_CAMPAIGN_ID` | Campaign for live testing |
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | Path to service account JSON |
| `GOOGLE_SHEET_ID` | Default sheet ID |
| `META_CAMPAIGN_ID` | Default campaign for wrapper |

## CLI Usage

```bash
# Default: last 7 days
python -m lib.cli --campaign 123456789 --sheet 1abc123xyz

# Custom date range
python -m lib.cli --campaign 123456789 --sheet 1abc123xyz \
    --start 2025-01-01 --end 2025-01-31

# Dry run (no writes)
python -m lib.cli --campaign 123456789 --sheet 1abc123xyz --dry-run
```

## Testing Strategy

| Component | Mock Strategy | Live Test Trigger |
|-----------|---------------|-------------------|
| Meta Ads API | `MockMetaAdsClient` | `META_ACCESS_TOKEN` set |
| Google Sheets | `MockSheetsClient` | `GOOGLE_SHEETS_CREDENTIALS_JSON` set |
| End-to-end | Both mocks | Both env vars set |

```python
# Conditional live test pattern
@pytest.mark.skipif(not os.environ.get("META_ACCESS_TOKEN"), reason="No token")
async def test_live_meta_fetch():
    ...
```

## Data Flow

```
User CLI          Orchestrator          Google Sheets
    |                  |                      |
    | --campaign       |                      |
    | --sheet          |                      |
    |----------------->|                      |
    |                  | fetch                |
    |                  |---------->           |
    |                  |    Meta Ads API      |
    |                  |<----------           |
    |                  |                      |
    |                  | transform            |
    |                  |                      |
    |                  | clear + write        |
    |                  |--------------------->|
    |                  |                      |
    | SUCCESS: N rows  |                      |
    |<-----------------|                      |
```

## Patterns to Follow

### Safe Environment Access
```python
from lib.get_env import env
token = env("META_ACCESS_TOKEN")  # Raises KeyError if missing
```

### Protocol-Based Clients
```python
class MetaAdsClient(Protocol):
    async def get_daily_spend(...) -> list[DailySpend]: ...
```

### Test-Driven Development
- **Red**: Write failing test first
- **Green**: Minimal code to pass
- **Refactor**: Clean up, maintain tests green

## Anti-Patterns to Avoid

- `os.environ` / `os.getenv` - use `env()` from `lib/get_env.py`
- Sync HTTP calls - use `httpx.AsyncClient`
- Hardcoded credentials - always use env vars
- Silent failures - raise and fix the root cause
