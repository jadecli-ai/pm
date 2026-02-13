#!/usr/bin/env python3
"""Check availability of secrets and variables without exposing values.

Usage:
    python3 scripts/check-secrets.py              # Check all scopes
    python3 scripts/check-secrets.py --env-only    # Only check local .env
    python3 scripts/check-secrets.py --gh-only     # Only check GitHub secrets/vars
    python3 scripts/check-secrets.py --json        # Output as JSON

Exit codes:
    0 = all required keys present
    1 = one or more required keys missing
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# ── Required keys by scope ──────────────────────────────────────────────
# Add new keys here. Format: (key_name, description)

ENV_KEYS = [
    ("PRJ_NEON_DATABASE_URL", "Neon PostgreSQL connection string"),
    ("OLLAMA_HOST", "Ollama embedding server"),
    ("OLLAMA_EMBED_MODEL", "Embedding model name"),
]

REPO_SECRETS = [
    ("NEON_API_KEY", "Neon API key for branch management"),
    ("CLAUDE_ACCESS_TOKEN", "Claude Code OAuth access token"),
    ("CLAUDE_REFRESH_TOKEN", "Claude Code OAuth refresh token"),
    ("CLAUDE_EXPIRES_AT", "Claude Code OAuth expiry timestamp"),
]

REPO_VARIABLES = [
    ("NEON_PROJECT_ID", "Neon project identifier"),
]

ORG_SECRETS: list[tuple[str, str]] = [
    # Add org-level secrets here as needed
]

ORG_VARIABLES: list[tuple[str, str]] = [
    # Add org-level variables here as needed
]

# ── Helpers ─────────────────────────────────────────────────────────────

REPO = os.environ.get("GITHUB_REPOSITORY", "jadecli-ai/pm")
ORG = REPO.split("/")[0] if "/" in REPO else "jadecli-ai"


def _check_env(keys: list[tuple[str, str]], env_file: Path | None = None) -> dict[str, bool]:
    """Check if keys exist in environment or .env file (value never read)."""
    env_vars: set[str] = set(os.environ.keys())
    if env_file and env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                env_vars.add(line.split("=", 1)[0].strip())
    return {k: k in env_vars for k, _ in keys}


def _gh_list(cmd: list[str]) -> set[str]:
    """Run a gh CLI command and extract names from the first column."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10
        )
        names: set[str] = set()
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if parts:
                names.add(parts[0])
        return names
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return set()


def _check_gh_secrets(keys: list[tuple[str, str]], scope: str = "repo") -> dict[str, bool]:
    """Check GitHub secrets exist by name (values never accessible)."""
    if scope == "org":
        existing = _gh_list(["gh", "secret", "list", "--org", ORG])
    else:
        existing = _gh_list(["gh", "secret", "list", "--repo", REPO])
    return {k: k in existing for k, _ in keys}


def _check_gh_variables(keys: list[tuple[str, str]], scope: str = "repo") -> dict[str, bool]:
    """Check GitHub variables exist by name."""
    if scope == "org":
        existing = _gh_list(["gh", "variable", "list", "--org", ORG])
    else:
        existing = _gh_list(["gh", "variable", "list", "--repo", REPO])
    return {k: k in existing for k, _ in keys}


# ── Main ────────────────────────────────────────────────────────────────

def check_all(
    *,
    env: bool = True,
    gh: bool = True,
    env_file: Path | None = None,
) -> dict[str, dict[str, bool]]:
    """Run all checks, return results by scope."""
    results: dict[str, dict[str, bool]] = {}
    if env:
        results["env"] = _check_env(ENV_KEYS, env_file)
    if gh:
        results["repo_secrets"] = _check_gh_secrets(REPO_SECRETS, "repo")
        results["repo_variables"] = _check_gh_variables(REPO_VARIABLES, "repo")
        if ORG_SECRETS:
            results["org_secrets"] = _check_gh_secrets(ORG_SECRETS, "org")
        if ORG_VARIABLES:
            results["org_variables"] = _check_gh_variables(ORG_VARIABLES, "org")
    return results


def _print_table(results: dict[str, dict[str, bool]]) -> bool:
    """Print a human-readable table. Returns True if all present."""
    all_ok = True
    # Collect all descriptions for lookup
    all_keys = {k: d for k, d in ENV_KEYS + REPO_SECRETS + REPO_VARIABLES + ORG_SECRETS + ORG_VARIABLES}

    for scope, checks in results.items():
        header = scope.upper().replace("_", " ")
        print(f"\n  {header}")
        print(f"  {'─' * 50}")
        for key, present in checks.items():
            status = "OK" if present else "MISSING"
            icon = "+" if present else "x"
            desc = all_keys.get(key, "")
            print(f"  [{icon}] {key:<30} {status:<8} {desc}")
            if not present:
                all_ok = False
    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env-only", action="store_true", help="Only check local .env")
    parser.add_argument("--gh-only", action="store_true", help="Only check GitHub secrets/vars")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--env-file", type=Path, default=None, help="Path to .env file")
    args = parser.parse_args()

    env_file = args.env_file
    if env_file is None:
        # Walk up to find .env
        for candidate in [Path(".env"), Path("pm/.env"), Path(__file__).resolve().parent.parent / ".env"]:
            if candidate.exists():
                env_file = candidate
                break

    do_env = not args.gh_only
    do_gh = not args.env_only

    results = check_all(env=do_env, gh=do_gh, env_file=env_file)

    if args.json:
        print(json.dumps(results, indent=2))
        sys.exit(0 if all(all(v.values()) for v in results.values()) else 1)

    print("\n  Secrets & Variables Audit")
    print(f"  Repo: {REPO}  |  Org: {ORG}")
    all_ok = _print_table(results)

    missing = sum(1 for checks in results.values() for v in checks.values() if not v)
    total = sum(len(checks) for checks in results.values())

    print(f"\n  {total - missing}/{total} keys configured")
    if not all_ok:
        print("  Run with --json for machine-readable output\n")
        sys.exit(1)
    print()


if __name__ == "__main__":
    main()
