# Blueprint: Updating Merkle Trees

> Init context for any request that modifies the merkle tree indexing system in `pm/.index/`.
> Reference from CLAUDE.md: `@contributing-blueprint/002-init-context-update-merkle-trees.md`

## Feature Overview

The merkle tree provides **O(1) change detection** for the entire PM system. Every tracked
file gets a SHA256 hash, directories hash their children, and a single root hash represents
the entire system state. Agents read the pre-computed index at session start instead of
exploring the filesystem — this saves tokens and time.

## File Map

```
pm/.index/
├── merkle-tree.json       # Generated output — the full index (DO NOT hand-edit)
├── AGENT-INDEX.md         # Generated output — human-readable summary for agents
├── generate-merkle.py     # Generator script — THE source of truth
├── generate-merkle.sh     # Bash alternative (legacy)
└── check-changes.py       # Change detector — compares current state to stored index
```

## Architecture

### Hash Tree Structure

```
Root Hash (SHA256 of all directory hashes)
├── agents/ hash (SHA256 of all agent file hashes)
│   ├── vp-product.md hash
│   ├── sdm.md hash
│   ├── staff-engineer.md hash
│   └── sprint-master.md hash
├── entities/ hash
│   ├── epic.schema.md hash
│   └── examples/ hash
│       ├── EPIC-001.md hash
│       └── TASK-004.md hash
├── tests/ hash
└── ... (all directories)
```

### How Hashing Works

1. **File hash**: `SHA256(file_bytes)` — any byte change produces a new hash
2. **Directory hash**: `SHA256(sorted(child_file_hashes).join(""))` — changes propagate up
3. **Root hash**: `SHA256(all_directory_hashes.join(""))` — single value represents entire state
4. **Change detection**: Compare stored root hash vs recomputed root hash → O(1)

### merkle-tree.json Schema

```json
{
  "version": "1.0.0",
  "generated": "ISO-8601 timestamp",
  "root": "SHA256 root hash",

  "files": {
    "relative/path.md": {
      "hash": "SHA256",
      "lines": 42,
      "type": "agent | entity | schema | test | script | doc",
      "purpose": "type:name:detail",
      "name": "optional — from frontmatter",
      "model": "optional — agents only",
      "id": "optional — entities only",
      "version": "optional — entities only",
      "status": "optional — entities only"
    }
  },

  "directories": {
    "relative/dir": {
      "hash": "SHA256",
      "files": 3,
      "dirs": 1
    }
  },

  "semanticIndex": {
    "entryPoints": ["ENTRYPOINT.md", "README.md"],
    "agents": {
      "agent-name": {
        "model": "opus | sonnet | haiku",
        "owns": ["epics"],
        "file": "agents/agent-name.md"
      }
    },
    "entityHierarchy": ["epic", "story", "task", "subtask"],
    "schemas": {
      "epic": "entities/epic.schema.md"
    },
    "claudeCodeAlignment": {
      "taskFields": ["subject", "activeForm", "status", "blockedBy", "blocks"],
      "tools": ["TaskCreate", "TaskUpdate", "TaskGet", "TaskList"]
    },
    "tests": {
      "runner": "tests/run-tests.sh",
      "validator": "tests/validate-entity.sh",
      "alignment": "tests/claude-code-alignment.md"
    }
  }
}
```

## Key Functions in generate-merkle.py

| Function | Purpose | When to Modify |
|----------|---------|---------------|
| `hash_file(path)` | SHA256 of file bytes | Never — this is stable |
| `hash_string(s)` | SHA256 of string | Never — this is stable |
| `get_frontmatter(path)` | Extract YAML frontmatter | When adding new frontmatter fields to extract |
| `classify_file(rel_path, fm)` | Determine file type + purpose string | When adding new file types or classification patterns |
| `build_index()` | Main index builder | When changing index schema or adding tracked extensions |
| `build_agent_summary()` | Generate AGENT-INDEX.md content | When changing agent hierarchy or entity mappings |

### File Classification Rules (classify_file)

```python
entities/examples/* → ("entity", "entity:{type}:{id}")
entities/*.schema.md → ("schema", "schema:{name}")
agents/*             → ("agent", "agent:{name}:{model}")
tests/*              → ("test", "test:{name}")
*.sh                 → ("script", "script:{name}")
*                    → ("doc", "doc:{name}")
```

### Tracked Extensions

Currently: `*.md`, `*.sh`

To add a new extension (e.g., `*.py`), modify the loop in `build_index()`:
```python
for ext in ["*.md", "*.sh", "*.py"]:  # Add here
```

### Excluded Paths

Currently: `.index/`, `.git/`

These are hardcoded in the `build_index()` rglob loop.

## Commands

```bash
# Check if index is current (O(1) root hash comparison)
python3 pm/.index/check-changes.py

# Regenerate the full index
python3 pm/.index/generate-merkle.py

# Makefile shortcut (check + regenerate if stale)
cd pm && make l1-index

# Full validation (tests + index freshness)
cd pm && make l1-validate
```

## Checklist: Modifying the Index Schema

When changing what the merkle tree tracks or how it structures data:

1. Read `pm/.index/generate-merkle.py` fully before making changes
2. Modify `build_index()` for structural changes to the JSON output
3. Update `classify_file()` if adding new file type classifications
4. Update `build_agent_summary()` if changing agent hierarchy or entity mappings
5. Run the generator: `python3 pm/.index/generate-merkle.py`
6. Verify output: read `pm/.index/merkle-tree.json` and spot-check entries
7. Run change detector to confirm clean state: `python3 pm/.index/check-changes.py`
8. Run tests: `./pm/tests/run-tests.sh`
9. Commit both the script AND generated files: `chore(index): <description>`

## Checklist: Adding a New File Type to Track

1. Add the glob extension to `build_index()`:
   ```python
   for ext in ["*.md", "*.sh", "*.new_ext"]:
   ```
2. Add a classification rule in `classify_file()` if needed
3. If the file type has frontmatter, update `get_frontmatter()` parsing
4. Regenerate: `python3 pm/.index/generate-merkle.py`
5. Verify the new files appear in `merkle-tree.json`
6. Commit: `feat(index): track *.new_ext files in merkle tree`

## Checklist: Adding a New Semantic Index Section

The `semanticIndex` provides structured metadata beyond raw hashes:

1. Add the new section in the `build_index()` return dict under `semanticIndex`
2. Populate it by reading frontmatter or scanning file patterns
3. Document the new section's schema in this blueprint
4. Update `AGENT-INDEX.md` template in `build_agent_summary()` if agents need it
5. Regenerate and verify
6. Commit: `feat(index): add <section> to semantic index`

## Checklist: Regenerating After Other Feature Changes

The merkle tree must be regenerated after ANY change to tracked files. Common triggers:

| Change | Why Regen Needed |
|--------|-----------------|
| Agent definition modified | Agent hash changes, possibly `semanticIndex.agents` |
| New entity example added | File hash added, directory hash changes |
| Schema file updated | Schema hash changes |
| Test script modified | Test hash changes |
| New agent added to `pm/agents/` | Must also update `semanticIndex.agents` dict |

After regenerating, the commit should include both the changed source files and the
regenerated index files (`merkle-tree.json`, `AGENT-INDEX.md`).

## Related Files

| File | Why It Matters |
|------|----------------|
| `pm/CLAUDE.md` | Entry Checklist tells agents to run `check-changes.py` |
| `pm/Makefile` | `l1-index` target wraps check + regenerate |
| `pm/.github/workflows/pr-checks.yml` | CI may validate index freshness |
| `pm/lib/frontmatter.py` | Shared frontmatter parser (generator has its own inline parser) |
| `pm/agents/*.md` | All PM agents reference `.index/AGENT-INDEX.md` in their headers |

## Anti-Patterns

- Hand-editing `merkle-tree.json` — always regenerate via the script
- Hand-editing `AGENT-INDEX.md` — always regenerate; edit `build_agent_summary()` instead
- Adding files without regenerating the index afterward
- Duplicating the frontmatter parser instead of extending the existing one
- Adding classification rules that overlap (first match wins in `classify_file`)
- Tracking generated files (ARCHITECTURE.md, ARCHITECTURE.html) in the merkle tree — these are outputs, not source
- Forgetting to update `semanticIndex.agents` when adding a new PM agent

## Design Decisions

### Why a Custom Merkle Tree (Not Git)

Git tracks all files but doesn't provide:
- Semantic classification (agent vs entity vs schema)
- Frontmatter extraction (name, model, status)
- Agent-readable summary generation
- O(1) "has anything in PM changed?" check without git operations

### Why SHA256

- Collision resistant for our scale
- Standard library (`hashlib`) — no dependencies
- Consistent across platforms
- Same algorithm as many integrity verification systems

### Why Inline Frontmatter Parser

`generate-merkle.py` has its own simple frontmatter parser (`get_frontmatter`) instead of
importing `lib/frontmatter.py`. This is intentional — the generator must work standalone
as a pre-commit or CI step without Python path configuration. The tradeoff is maintained
duplication; if frontmatter format changes, both parsers need updating.
