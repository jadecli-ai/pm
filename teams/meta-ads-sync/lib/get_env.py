"""Safe environment variable accessor.

All env var access goes through this module. Values are never logged or
included in error messages — only the key name is shown on failure.

depends_on:
  - env.template
depended_by:
  - lib/meta_client.py
  - lib/sheets_client.py
  - lib/cli.py
semver: major

Usage:
    from lib.get_env import env

    token = env("META_ACCESS_TOKEN")              # raises if missing
    sheet = env("GOOGLE_SHEET_ID", default=None)  # returns None if missing

    # Check which keys are set (without showing values)
    env.check()  # prints status table: KEY ... SET/MISSING
"""

from __future__ import annotations

import os
from pathlib import Path

_SENTINEL = object()

_dotenv_loaded = False


def _ensure_dotenv() -> None:
    global _dotenv_loaded
    if not _dotenv_loaded:
        try:
            from dotenv import load_dotenv

            env_path = Path(__file__).resolve().parent.parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        except ImportError:
            pass  # python-dotenv not installed, rely on OS env
        _dotenv_loaded = True


class _EnvAccessor:
    """Callable env var accessor that never exposes values."""

    def __call__(self, key: str, *, default: str | None = _SENTINEL) -> str:  # type: ignore[assignment]
        """Get an env var by key. Raises KeyError with key name only (no value leak)."""
        _ensure_dotenv()
        value = os.environ.get(key)
        if value is not None:
            return value
        if default is not _SENTINEL:
            return default  # type: ignore[return-value]
        raise KeyError(
            f"Required environment variable '{key}' is not set. "
            f"Add it to your .env file (see env.template for all keys)."
        )

    def check(self) -> dict[str, bool]:
        """Print status of all known keys. Returns {key: is_set}."""
        _ensure_dotenv()
        template = Path(__file__).resolve().parent.parent / "env.template"
        keys = self._parse_template(template)
        status = {}
        for key in keys:
            is_set = key in os.environ and os.environ[key] != ""
            marker = "SET" if is_set else "MISSING"
            print(f"  {key:40s} {marker}")
            status[key] = is_set
        return status

    @staticmethod
    def _parse_template(path: Path) -> list[str]:
        """Extract key names from env.template (lines matching KEY=)."""
        keys: list[str] = []
        if path.exists():
            for line in path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    keys.append(line.split("=", 1)[0].strip())
        return keys


env = _EnvAccessor()
