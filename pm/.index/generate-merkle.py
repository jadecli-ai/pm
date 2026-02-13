#!/usr/bin/env python3
"""Generate Merkle tree index for PM system."""

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

PM_DIR = Path(__file__).parent.parent
INDEX_DIR = PM_DIR / ".index"


def hash_file(path: Path) -> str:
    """SHA256 hash of file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_string(s: str) -> str:
    """SHA256 hash of string."""
    return hashlib.sha256(s.encode()).hexdigest()


def get_frontmatter(path: Path) -> dict[str, Any]:
    """Extract YAML frontmatter from markdown file."""
    content = path.read_text(encoding="utf-8", errors="ignore")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    frontmatter = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            value = value.strip().strip('"').strip("'")
            frontmatter[key.strip()] = value
    return frontmatter


def classify_file(rel_path: str, frontmatter: dict) -> tuple[str, str]:
    """Classify file type and purpose."""
    if rel_path.startswith("entities/examples/"):
        entity_type = frontmatter.get("type", "unknown")
        entity_id = frontmatter.get("id", "unknown")
        return "entity", f"entity:{entity_type}:{entity_id}"
    elif rel_path.startswith("entities/") and rel_path.endswith(".schema.md"):
        name = Path(rel_path).stem.replace(".schema", "")
        return "schema", f"schema:{name}"
    elif rel_path.startswith("agents/"):
        name = frontmatter.get("name", "unknown")
        model = frontmatter.get("model", "unknown")
        return "agent", f"agent:{name}:{model}"
    elif rel_path.startswith("tests/"):
        name = Path(rel_path).stem
        return "test", f"test:{name}"
    elif rel_path.endswith(".sh"):
        name = Path(rel_path).stem
        return "script", f"script:{name}"
    else:
        name = Path(rel_path).stem
        return "doc", f"doc:{name}"


def build_index() -> dict:
    """Build the complete Merkle tree index."""
    files = {}
    directories = {}
    file_hashes = {}

    # Index all files
    for ext in ["*.md", "*.sh", "*.py"]:
        for path in PM_DIR.rglob(ext):
            if ".index" in str(path) or ".git" in str(path):
                continue

            rel_path = str(path.relative_to(PM_DIR))
            file_hash = hash_file(path)
            line_count = len(path.read_text(encoding="utf-8", errors="ignore").splitlines())

            frontmatter = {}
            if path.suffix == ".md":
                frontmatter = get_frontmatter(path)

            file_type, purpose = classify_file(rel_path, frontmatter)
            file_hashes[rel_path] = file_hash

            files[rel_path] = {
                "hash": file_hash,
                "lines": line_count,
                "type": file_type,
                "purpose": purpose,
            }

            # Add frontmatter fields for entities
            if file_type in ("entity", "agent"):
                if "id" in frontmatter:
                    files[rel_path]["id"] = frontmatter["id"]
                if "version" in frontmatter:
                    files[rel_path]["version"] = frontmatter["version"]
                if "status" in frontmatter:
                    files[rel_path]["status"] = frontmatter["status"]
                if "name" in frontmatter:
                    files[rel_path]["name"] = frontmatter["name"]
                if "model" in frontmatter:
                    files[rel_path]["model"] = frontmatter["model"]

    # Build directory hashes
    for dir_path in sorted(set(Path(f).parent for f in files.keys())):
        dir_str = str(dir_path) if str(dir_path) != "." else "."

        # Hash of all file hashes in this directory
        dir_file_hashes = sorted([
            file_hashes[f] for f in files.keys()
            if str(Path(f).parent) == dir_str
        ])

        if dir_file_hashes:
            dir_hash = hash_string("".join(dir_file_hashes))
        else:
            dir_hash = "empty"

        file_count = len([f for f in files if str(Path(f).parent) == dir_str])
        subdir_count = len([d for d in set(Path(f).parent for f in files)
                           if str(d.parent) == dir_str and d != dir_path])

        directories[dir_str] = {
            "hash": dir_hash,
            "files": file_count,
            "dirs": subdir_count,
        }

    # Compute root hash
    all_dir_hashes = "".join(d["hash"] for d in directories.values())
    root_hash = hash_string(all_dir_hashes)

    return {
        "version": "1.0.0",
        "generated": datetime.now().isoformat(),
        "root": root_hash,
        "files": dict(sorted(files.items())),
        "directories": dict(sorted(directories.items())),
        "semanticIndex": {
            "entryPoints": ["ENTRYPOINT.md", "README.md"],
            "agents": {
                "vp-product": {"model": "opus", "owns": ["epics"], "file": "agents/vp-product.md"},
                "sdm": {"model": "sonnet", "owns": ["stories", "tasks"], "file": "agents/sdm.md"},
                "staff-engineer": {"model": "sonnet", "owns": ["tasks", "subtasks"], "file": "agents/staff-engineer.md"},
                "sprint-master": {"model": "haiku", "owns": ["ceremonies"], "file": "agents/sprint-master.md"},
                "neon-specialist": {"model": "opus", "owns": ["documents"], "file": "agents/neon-specialist.md"},
            },
            "entityHierarchy": ["epic", "story", "task", "subtask"],
            "schemas": {
                "epic": "entities/epic.schema.md",
                "story": "entities/story.schema.md",
                "task": "entities/task.schema.md",
                "subtask": "entities/subtask.schema.md",
            },
            "claudeCodeAlignment": {
                "taskFields": ["subject", "activeForm", "status", "blockedBy", "blocks"],
                "tools": ["TaskCreate", "TaskUpdate", "TaskGet", "TaskList"],
            },
            "tests": {
                "runner": "tests/run-tests.sh",
                "validator": "tests/validate-entity.sh",
                "alignment": "tests/claude-code-alignment.md",
            },
        },
    }


def build_agent_summary() -> str:
    """Build a compact summary for agents to quickly understand the system."""
    return """# PM System Index (Pre-computed)

## Quick Reference

```
pm/
├── ENTRYPOINT.md          # Start here - agent team launch guide
├── README.md              # System overview
├── agents/                # Agent definitions
│   ├── vp-product.md      # Opus - owns Epics
│   ├── sdm.md             # Sonnet - owns Stories/Tasks
│   ├── staff-engineer.md  # Sonnet - owns Tasks/Subtasks
│   ├── sprint-master.md   # Haiku - ceremonies
│   ├── neon-specialist.md # Opus - document caching
├── entities/              # Work item schemas
│   ├── epic.schema.md     # Strategic initiatives
│   ├── story.schema.md    # User features
│   ├── task.schema.md     # Implementation units (Claude Code aligned)
│   ├── subtask.schema.md  # Atomic work
│   └── examples/          # Live entity instances
└── tests/                 # Integration tests
    └── run-tests.sh       # Validates all entities
```

## Entity → Claude Code Mapping

| Entity Field | TaskCreate | TaskUpdate |
|--------------|------------|------------|
| subject | subject | subject |
| description | description | description |
| activeForm | activeForm | activeForm |
| status | - | status |
| blockedBy | - | addBlockedBy |
| blocks | - | addBlocks |

## Frontmatter Template (Task)

```yaml
---
id: "TASK-XXX"
version: "1.0.0"
type: task
status: pending
parent: "STORY-XXX"
dependsOn: []
blockedBy: []
blocks: []
owner: null
size: M
agentHours: 3
subject: "Implement feature X"
activeForm: "Implementing feature X"
---
```

## Version Bumps

- PATCH (+0.0.1): status change, typo fix
- MINOR (+0.1.0): completion, new dependency
- MAJOR (+1.0.0): scope change, breaking AC

## Workflow

1. VP Product creates Epic → `entities/examples/EPIC-XXX.md`
2. SDM breaks into Stories → creates Task entities
3. Staff Engineer: `TaskCreate(subject, description, activeForm)`
4. Work → `TaskUpdate(status="in_progress")`
5. Done → `TaskUpdate(status="completed")` + entity version bump
"""


if __name__ == "__main__":
    INDEX_DIR.mkdir(exist_ok=True)

    # Generate JSON index
    index = build_index()
    output_json = INDEX_DIR / "merkle-tree.json"
    output_json.write_text(json.dumps(index, indent=2))
    print(f"Generated: {output_json}")
    print(f"Root hash: {index['root']}")
    print(f"Files indexed: {len(index['files'])}")

    # Generate agent-readable summary
    summary = build_agent_summary()
    output_summary = INDEX_DIR / "AGENT-INDEX.md"
    output_summary.write_text(summary)
    print(f"Generated: {output_summary}")
