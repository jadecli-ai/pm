#!/usr/bin/env python3
"""Dashboard data generator.

Collects data from multiple sources (git, neon CLI, filesystem) and outputs
a single JSON file (pm/DASHBOARD.json) that the HTML dashboard consumes.

Usage:
    cd <repo-root>
    python3 pm/scripts/dashboard/generate.py
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path("/home/alex-jadecli/projects/refs/jadecli-ai/pm")
PM_ROOT = REPO_ROOT / "pm"
OUTPUT_PATH = PM_ROOT / "DASHBOARD.json"
MERKLE_TREE_PATH = PM_ROOT / ".index" / "merkle-tree.json"
ARCHITECTURE_MD_PATH = PM_ROOT / "ARCHITECTURE.md"

BASE_REF = "origin/main"

# ---------------------------------------------------------------------------
# Conventional-commit regex
# ---------------------------------------------------------------------------
CC_RE = re.compile(r"^(\w+)(?:\(([^)]+)\))?!?:\s+(.+)$")

# Phase definitions: scope keywords -> phase
PHASE_DEFINITIONS = {
    0: {"name": "Infrastructure", "keywords": {"infra", "infrastructure"}},
    1: {"name": "Database Layer", "keywords": {"db", "migration", "migrations", "database"}},
    2: {"name": "Embedder & Chunker", "keywords": {"embedder", "chunker", "worker", "embedding"}},
    3: {"name": "Neon CLI", "keywords": {"neon", "neon-docs", "neon_docs", "cli"}},
    4: {"name": "Tracing", "keywords": {"tracing", "trace", "mlflow"}},
    5: {"name": "Hooks", "keywords": {"hooks", "hook", "pre-commit", "pre-push"}},
    6: {"name": "Makefile", "keywords": {"makefile", "make", "build"}},
    7: {"name": "Agents", "keywords": {"agents", "agent", "sdm", "staff-eng"}},
    8: {"name": "Bootstrap", "keywords": {"bootstrap", "setup", "init"}},
    9: {"name": "CI", "keywords": {"ci", "github-actions", "actions", "workflow"}},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a command, returning the CompletedProcess (never raises)."""
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd or REPO_ROOT,
            timeout=30,
        )
    except Exception as exc:
        # Return a synthetic failed result
        fake = subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr=str(exc))
        return fake


def run_ok(cmd: list[str], **kwargs) -> str | None:
    """Run a command, return stdout on success or None on failure."""
    result = run(cmd, **kwargs)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


# ---------------------------------------------------------------------------
# Data collectors
# ---------------------------------------------------------------------------

def collect_neon_stats() -> dict:
    """Collect Neon database stats via the neon_docs CLI."""
    result = run(
        ["python3", "-m", "lib.neon_docs", "status"],
        cwd=PM_ROOT,
    )

    placeholder = {
        "documents": 0,
        "chunks": 0,
        "queue_pending": 0,
        "queue_failed": 0,
        "available": False,
    }

    if result.returncode != 0:
        return placeholder

    try:
        data = json.loads(result.stdout)
        return {
            "documents": data.get("documents", 0),
            "chunks": data.get("chunks", 0),
            "queue_pending": data.get("queue_pending", 0),
            "queue_failed": data.get("queue_failed", 0),
            "available": True,
        }
    except (json.JSONDecodeError, TypeError):
        return placeholder


def collect_branch_info() -> dict:
    """Collect current branch name and commits-ahead count."""
    branch_name = run_ok(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"

    ahead_output = run_ok(["git", "log", "--oneline", f"{BASE_REF}..HEAD"])
    if ahead_output is not None and ahead_output:
        commits_ahead = len(ahead_output.splitlines())
    else:
        commits_ahead = 0

    return {
        "name": branch_name,
        "base": BASE_REF,
        "commits_ahead": commits_ahead,
    }


def collect_commits() -> dict:
    """Parse conventional commits from git log."""
    log_output = run_ok(["git", "log", f"--format=%H|%s", f"{BASE_REF}..HEAD"])

    commits_list: list[dict] = []
    by_type: dict[str, int] = {}
    by_scope: dict[str, int] = {}

    if log_output:
        for line in log_output.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("|", 1)
            if len(parts) != 2:
                continue
            full_hash, subject = parts
            short_hash = full_hash[:7]

            match = CC_RE.match(subject)
            if match:
                commit_type = match.group(1)
                scope = match.group(2) or ""
                description = match.group(3)
            else:
                commit_type = "other"
                scope = ""
                description = subject

            commits_list.append({
                "hash": short_hash,
                "type": commit_type,
                "scope": scope,
                "description": description,
            })

            by_type[commit_type] = by_type.get(commit_type, 0) + 1
            if scope:
                by_scope[scope] = by_scope.get(scope, 0) + 1

    return {
        "total": len(commits_list),
        "by_type": dict(sorted(by_type.items(), key=lambda x: -x[1])),
        "by_scope": dict(sorted(by_scope.items(), key=lambda x: -x[1])),
        "list": commits_list,
    }


def collect_architecture() -> dict:
    """Read merkle-tree.json and ARCHITECTURE.md for architecture data."""
    result: dict = {
        "root_hash": "",
        "file_count": 0,
        "agents": [],
        "layers": {},
    }

    # Parse merkle-tree.json
    if MERKLE_TREE_PATH.exists():
        try:
            data = json.loads(MERKLE_TREE_PATH.read_text())
            result["root_hash"] = data.get("root", data.get("rootHash", data.get("root_hash", "")))
            files_section = data.get("files", {})
            result["file_count"] = len(files_section) if isinstance(files_section, dict) else 0

            # Extract agents from semanticIndex
            semantic = data.get("semanticIndex", {})
            agents = []
            for key, value in semantic.items():
                if "agent" in key.lower() or "agent" in str(value).lower():
                    agents.append(key)
            # If agents are stored differently, try alternative paths
            if not agents:
                agents_section = semantic.get("agents", [])
                if isinstance(agents_section, list):
                    agents = agents_section
                elif isinstance(agents_section, dict):
                    agents = list(agents_section.keys())
            result["agents"] = agents

            # Extract layers
            layers = data.get("layers", {})
            if isinstance(layers, dict):
                result["layers"] = layers
        except (json.JSONDecodeError, OSError):
            pass

    # Note presence of ARCHITECTURE.md
    if ARCHITECTURE_MD_PATH.exists():
        result["architecture_md_exists"] = True

    return result


def collect_impact() -> dict:
    """Analyse branch impact: files changed, insertions, deletions, by directory."""
    result: dict = {
        "files_changed": 0,
        "insertions": 0,
        "deletions": 0,
        "by_directory": {},
        "files": [],
    }

    # --stat summary
    stat_output = run_ok(["git", "diff", "--stat", f"{BASE_REF}..HEAD"])
    if stat_output:
        # Last line is the summary: " 55 files changed, 7414 insertions(+), 116 deletions(-)"
        lines = stat_output.strip().splitlines()
        if lines:
            summary_line = lines[-1].strip()
            m_files = re.search(r"(\d+)\s+files?\s+changed", summary_line)
            m_ins = re.search(r"(\d+)\s+insertions?\(\+\)", summary_line)
            m_del = re.search(r"(\d+)\s+deletions?\(-\)", summary_line)
            if m_files:
                result["files_changed"] = int(m_files.group(1))
            if m_ins:
                result["insertions"] = int(m_ins.group(1))
            if m_del:
                result["deletions"] = int(m_del.group(1))

    # --name-status for per-file info
    ns_output = run_ok(["git", "diff", "--name-status", f"{BASE_REF}..HEAD"])
    by_directory: dict[str, int] = {}
    files_list: list[dict] = []

    if ns_output:
        for line in ns_output.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) < 2:
                continue
            status = parts[0][0]  # A, M, D, R -> first char
            filepath = parts[-1]  # for renames, take the destination

            files_list.append({"status": status, "path": filepath})

            # Group by top-level directory (up to second level for pm/)
            path_parts = filepath.split("/")
            if len(path_parts) >= 2:
                dir_key = "/".join(path_parts[:2]) + "/"
            else:
                dir_key = path_parts[0]
            by_directory[dir_key] = by_directory.get(dir_key, 0) + 1

    result["by_directory"] = dict(sorted(by_directory.items(), key=lambda x: -x[1]))
    result["files"] = files_list

    return result


def collect_pr_info(branch_name: str) -> dict | None:
    """Try to find an existing PR for this branch via gh CLI."""
    output = run_ok([
        "gh", "pr", "list",
        "--head", branch_name,
        "--json", "number,title,url,state",
    ])

    if output:
        try:
            prs = json.loads(output)
            if prs and isinstance(prs, list) and len(prs) > 0:
                pr = prs[0]
                return {
                    "number": pr.get("number"),
                    "title": pr.get("title", ""),
                    "url": pr.get("url", ""),
                    "state": pr.get("state", ""),
                }
        except (json.JSONDecodeError, TypeError):
            pass

    return None


def collect_phases(commits_list: list[dict]) -> dict:
    """Determine phase completion based on commit scopes and types."""
    phases: dict[str, dict] = {}

    for phase_id, phase_def in PHASE_DEFINITIONS.items():
        phase_commits = 0
        keywords = phase_def["keywords"]

        for commit in commits_list:
            scope = commit.get("scope", "").lower()
            description = commit.get("description", "").lower()

            # Check if commit scope or description matches any phase keyword
            if scope in keywords:
                phase_commits += 1
            elif any(kw in description for kw in keywords):
                phase_commits += 1

        if phase_commits > 0:
            status = "completed"
        else:
            status = "pending"

        phases[str(phase_id)] = {
            "name": phase_def["name"],
            "status": status,
            "commits": phase_commits,
        }

    return phases


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate() -> dict:
    """Collect all data sources and return the dashboard JSON structure."""
    print("Collecting branch info...", file=sys.stderr)
    branch = collect_branch_info()

    print("Collecting Neon database stats...", file=sys.stderr)
    neon = collect_neon_stats()

    print("Collecting conventional commits...", file=sys.stderr)
    commits = collect_commits()

    print("Collecting architecture data...", file=sys.stderr)
    architecture = collect_architecture()

    print("Collecting branch impact analysis...", file=sys.stderr)
    impact = collect_impact()

    print("Collecting PR info...", file=sys.stderr)
    pr = collect_pr_info(branch["name"])

    print("Calculating phase completion...", file=sys.stderr)
    phases = collect_phases(commits.get("list", []))

    # Reshape into the format the HTML dashboard expects
    phases_list = [
        {"id": int(k), "name": v["name"], "status": v["status"], "commits": v["commits"]}
        for k, v in sorted(phases.items(), key=lambda x: int(x[0]))
    ]

    # Reshape architecture agents into {name, model} objects
    arch_agents = []
    if MERKLE_TREE_PATH.exists():
        try:
            data = json.loads(MERKLE_TREE_PATH.read_text())
            files = data.get("files", {})
            for path, info in files.items():
                if path.startswith("agents/") and path.endswith(".md"):
                    meta = info.get("metadata", {})
                    name = meta.get("id", path.replace("agents/", "").replace(".md", ""))
                    model = meta.get("model", "")
                    arch_agents.append({"name": name, "model": model})
        except (json.JSONDecodeError, OSError):
            pass

    dashboard = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "database": {
            "connected": neon.get("available", False),
            "documents": neon.get("documents", 0),
            "chunks": neon.get("chunks", 0),
            "queue_pending": neon.get("queue_pending", 0),
            "queue_failed": neon.get("queue_failed", 0),
        },
        "architecture": {
            "merkle_root": architecture.get("root_hash", ""),
            "file_count": architecture.get("file_count", 0),
            "agents": arch_agents or [{"name": a, "model": ""} for a in architecture.get("agents", [])],
            "layers": architecture.get("layers", {}),
        },
        "branch": {
            "name": branch.get("name", "unknown"),
            "base": branch.get("base", BASE_REF),
            "commits_ahead": branch.get("commits_ahead", 0),
            "commit_types": commits.get("by_type", {}),
            "scopes": commits.get("by_scope", {}),
            "insertions": impact.get("insertions", 0),
            "deletions": impact.get("deletions", 0),
            "files_changed": impact.get("files_changed", 0),
            "directories": impact.get("by_directory", {}),
            "files": impact.get("files", []),
        },
        "pr": {
            "number": pr.get("number") if pr else None,
            "title": pr.get("title", "") if pr else "",
            "url": pr.get("url", "") if pr else "",
            "state": pr.get("state", "") if pr else "",
            "phases": phases_list,
            "commit_types": commits.get("by_type", {}),
        },
    }

    return dashboard


def main() -> None:
    dashboard = generate()

    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(dashboard, indent=2) + "\n")
    print(f"Dashboard data written to {OUTPUT_PATH}", file=sys.stderr)

    # Also write to stdout for piping
    print(json.dumps(dashboard, indent=2))


if __name__ == "__main__":
    main()
