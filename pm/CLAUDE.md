# PM System - Claude Code Instructions

> Agent-driven iterative development with entity hierarchy and Merkle tree indexing

## Quick Start

1. Read `.index/AGENT-INDEX.md` for instant context (68 lines)
2. Check `.index/merkle-tree.json` root hash for change detection
3. Run `tests/run-tests.sh` before any changes

## Package Structure

```
pm/
├── .index/           # Merkle tree (O(1) change detection)
├── agents/           # VP Product → SDM → Staff Engineer → Sprint Master
├── entities/         # Epic → Story → Task → Subtask (Claude Code aligned)
├── lib/              # Shared code (SINGLE SOURCE - import, don't duplicate)
├── docs/fetch/       # Fetched external docs
├── docs/research/    # Compiled research
├── scripts/          # Automation (architecture generator)
├── tests/            # Integration tests (5 passing)
├── ARCHITECTURE.md   # Auto-generated system diagram
└── ARCHITECTURE.html # Interactive visualization
```

## Organization Context (jadecli-ai)

```
jadecli-ai/                    # GitHub Organization
├── pm/                        # This repo - PM System
└── (future repos)             # Will share lib/ patterns
```

## Entry Checklist

- [ ] Read this file completely
- [ ] Run `python3 .index/check-changes.py` to verify index freshness
- [ ] Run `./tests/run-tests.sh` to confirm system health
- [ ] Check `entities/examples/` for current entity states

---

## Patterns to Follow

### Engineering Approach (2026 Anthropic Style)

- [ ] **Agents first**: Spawn specialized subagents for complex tasks
- [ ] **Memory-aware**: Use `memory: project` frontmatter for cross-session learning
- [ ] **Pre-indexed**: Read `.index/AGENT-INDEX.md` before exploring
- [ ] **Parallel execution**: Launch independent agents concurrently
- [ ] **Context isolation**: Keep verbose output in subagent contexts

### Test-Driven Development

- [ ] **Red**: Write failing test first
- [ ] **Green**: Minimal code to pass
- [ ] **Refactor**: Clean up, maintain tests green
- [ ] **Live tests > mocks**: Prefer integration tests with real data
- [ ] **No mocks** unless external service unavailable

### Fail Fast Philosophy

- [ ] **Crash early**: Throw on invalid state, don't recover silently
- [ ] **Validate inputs**: Check at system boundaries immediately
- [ ] **No gradual degradation**: Fail completely rather than partially work
- [ ] **Explicit errors**: Descriptive error messages with context
- [ ] **Exit codes**: Non-zero on any failure

### Frontmatter Standard

Every `.md` file MUST have:

```yaml
---
id: "ENTITY-XXX"              # Unique identifier
version: "1.0.0"              # SemVer
type: epic|story|task|subtask # Entity type
status: pending|in_progress|completed
created: YYYY-MM-DD
updated: YYYY-MM-DD

# Dependencies (REQUIRED for change management)
dependsOn: []                 # What this file needs (npm:pkg@ver, TASK-XXX)
dependedBy: []                # What needs this file (auto-track consumers)
blocks: []                    # What can't start until this completes
blockedBy: []                 # What must complete before this starts
---
```

### Dependency Tracking

When adding dependency:
```yaml
dependsOn:
  - "npm:zod@3.22"           # Code dependency
  - "TASK-003"               # Entity dependency
  - "agents/sdm.md"          # File dependency
```

When consumed by another:
```yaml
dependedBy:
  - "TASK-005"               # Track consumers for impact analysis
```

---

## Anti-Patterns to Avoid

### Engineering

- [ ] ❌ **Don't explore without index**: Always read `.index/AGENT-INDEX.md` first
- [ ] ❌ **Don't mock when live works**: Use real integrations
- [ ] ❌ **Don't catch-and-continue**: Let errors propagate
- [ ] ❌ **Don't use try/except broadly**: Catch specific exceptions only
- [ ] ❌ **Don't log and ignore**: If it's worth logging, it's worth handling

### Code Quality

- [ ] ❌ **No silent failures**: `|| true`, empty catch blocks, swallowed errors
- [ ] ❌ **No magic strings**: Use constants or enums
- [ ] ❌ **No implicit state**: Make dependencies explicit in frontmatter
- [ ] ❌ **No backwards compat hacks**: Delete unused code completely
- [ ] ❌ **No TODO without issue**: Create entity or remove

### Testing

- [ ] ❌ **No test without assertion**: Every test must assert something
- [ ] ❌ **No mock preference**: Only mock external services, not internal
- [ ] ❌ **No skipped tests**: Fix or delete, never skip

---

## Commands Reference

Use monotonically increasing complexity levels:

```bash
# Level 0: Atomic (~50 tokens, <1s)
make l0-test                    # Run tests
make l0-arch                    # Generate architecture
make l0-lint FILE=<path>        # Lint frontmatter
make l0-commit-check            # Validate commit

# Level 1: Composed (~60 tokens, <2s)
make l1-index                   # Check + regen index if stale
make l1-validate                # Tests + index
make l1-arch-check              # Arch + diff

# Level 2: Workflow (~150 tokens, <5s)
make l2-pr-open                 # Full PR checks
make l2-pr-merge                # Merge automation

# Level 3: Pipeline (~300 tokens, <10s)
make l3-ci                      # Full CI
make l3-cd                      # CI + merge

# Shortcuts
make test | make ci | make check
```

### Slash Commands

```
/pm test          # L0: Run tests
/pm check         # L2: PR open checks
/pm ci            # L3: Full CI pipeline
```

### Agent SDK

```python
from lib.tools import PMTools
tools = PMTools()
result = tools.l2_pr_open()  # Returns ToolResult
```

---

## Secrets & Environment Variables

**Never expose secret values.** Use the checker to audit presence only:

```bash
python3 scripts/check-secrets.py              # Human-readable audit
python3 scripts/check-secrets.py --json        # Machine-readable
python3 scripts/check-secrets.py --env-only    # Local .env only
python3 scripts/check-secrets.py --gh-only     # GitHub secrets/vars only
```

To add new keys, edit `scripts/check-secrets.py` — append to the appropriate list:

| Scope | List | Where to set |
|-------|------|--------------|
| Local `.env` | `ENV_KEYS` | `.env` file (never commit) |
| Repo secrets | `REPO_SECRETS` | `gh secret set -R jadecli-ai/pm` |
| Repo variables | `REPO_VARIABLES` | `gh variable set -R jadecli-ai/pm` |
| Org secrets | `ORG_SECRETS` | `gh secret set --org jadecli-ai` |
| Org variables | `ORG_VARIABLES` | `gh variable set --org jadecli-ai` |

Current required keys:

| Key | Scope | Purpose |
|-----|-------|---------|
| `PRJ_NEON_DATABASE_URL` | env | Neon PostgreSQL connection |
| `NEON_API_KEY` | repo secret | Neon branch management API |
| `NEON_PROJECT_ID` | repo variable | Neon project `jolly-morning-83487578` |
| `CLAUDE_ACCESS_TOKEN` | repo secret | Claude Code OAuth |
| `CLAUDE_REFRESH_TOKEN` | repo secret | Claude Code OAuth refresh |
| `CLAUDE_EXPIRES_AT` | repo secret | Claude Code OAuth expiry |

---

## Entity Index (Neon PostgreSQL)

Universal entity registry with CRUD event sourcing. Postgres 18 + native `uuidv7()`.

### Schema

```
entity_type_dict      → Reference dictionary (append-only, monotonic IDs)
entity_index          → Latest state per entity (one row = one entity)
entity_events_idx     → Append-only event log (CREATE/READ/UPDATE/DEACTIVATE)
```

### Entity Types (monotonically increasing — never reuse IDs)

| ID | Name | Description |
|----|------|-------------|
| 1 | `USERS` | User accounts and profiles |
| 2 | `REPOS` | Git repositories |
| 3 | `PROJECTS` | Neon or PM projects |
| 4 | `ORGS` | Organizations |
| 5 | `AUTH_PROCESS` | Authentication processes and tokens |
| 6 | `KEYS` | API keys, secrets, credentials metadata |
| 7 | `DOCUMENTS` | Documents, canvases, files |

To add a new type: `INSERT INTO entity_type_dict (id, name, description) VALUES (8, 'NEW_TYPE', '...');`

### JSON Blob Convention

Every `entity_json_blob` MUST contain `_v` (semver matching `entity_type_dict.schema_version`):

```json
{"_v": "1.0.0", "name": "example", "status": "active"}
```

The `create_entity()` function auto-injects `_v` from the type dict. The `update_entity()` function shallow-merges new fields, preserving `_v`.

### SQL Functions

```sql
-- Create entity (returns entity_id, event_id)
SELECT * FROM create_entity(
    1::SMALLINT,                              -- entity_type (USERS)
    '{"name": "alice"}'::jsonb,               -- entity_json_blob
    '{"source": "api", "agent": "opus"}'::jsonb, -- system_json_blob
    FALSE                                      -- is_test
);

-- Update entity (returns event_id)
SELECT update_entity(
    '019c...'::uuid,                          -- entity_id
    '{"email": "alice@co.com"}'::jsonb,       -- merge into blob
    '{"source": "manual"}'::jsonb             -- system_json_blob
);

-- Deactivate entity (returns event_id)
SELECT deactivate_entity('019c...'::uuid, '{"reason": "removed"}'::jsonb);
```

### Migration: `V003_entity_index.sql`

Located at `pm/lib/neon_docs/migrations/V003_entity_index.sql`. Run via:

```bash
PRJ_NEON_DATABASE_URL=... python3 -m lib.neon_docs migrate
```

---

## Architecture

### Layers

| Layer | Purpose | Location |
|-------|---------|----------|
| **Frontend** | Documentation, UI | `docs/` |
| **Middleware** | Agents, orchestration | `agents/` |
| **Backend** | Scripts, tests, lib | `lib/`, `tests/`, `scripts/` |
| **Data** | Entities, index | `entities/`, `.index/` |

### Auto-Update

Architecture docs auto-regenerate on:
- PR merge to main (`.github/workflows/architecture.yml`)
- Push to main
- Manual: `python scripts/architecture/generate.py`

### Visualization

Open `ARCHITECTURE.html` for interactive exploration with:
- Layer filter buttons
- Component details on click
- Mermaid dependency graph
- Status indicators

### Code Reuse (lib/)

**Single source of truth** - import from `lib/`, never duplicate:

```python
# ✓ Good
from lib.frontmatter import parse_file
from lib.validators import validate_entity

# ✗ Bad - duplicating logic
def parse_frontmatter(content):  # Don't do this
    ...
```

---

## Contributing

### Conventional Commits (REQUIRED)

```
<type>(<scope>): <description>

feat(entities): add task dependency tracking
fix(tests): correct frontmatter validation regex
docs(readme): update quick start section
refactor(agents): extract common validation logic
test(integration): add live GitHub API tests
chore(index): regenerate merkle tree
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`

### SemVer Rules

| Change | Bump | Example |
|--------|------|---------|
| Breaking: change acceptance criteria, remove field | MAJOR | 1.0.0 → 2.0.0 |
| Feature: add field, new capability, complete task | MINOR | 1.0.0 → 1.1.0 |
| Fix: typo, clarification, status change | PATCH | 1.0.0 → 1.0.1 |

### Changelog (Auto-generated)

Conventional commits auto-generate CHANGELOG.md:
- `feat` → Added
- `fix` → Fixed
- `docs` → Documentation
- Breaking changes → Breaking Changes section

### PR Checklist

- [ ] All tests pass: `./tests/run-tests.sh`
- [ ] Index regenerated: `python3 .index/generate-merkle.py`
- [ ] Frontmatter complete with dependencies
- [ ] Version bumped per SemVer rules
- [ ] Conventional commit message
- [ ] No mocks where live tests possible

---

## Known Issues / Lessons Learned

> Add MLflow trace mistakes here to prevent recurrence

### 2026-02-11: Line ending issues
**Symptom**: `bad interpreter: /bin/bash^M`
**Cause**: Windows line endings in shell scripts
**Fix**: `sed -i 's/\r$//' <file>` or use `.gitattributes`
**Prevention**: Add to pre-commit hook

### 2026-02-11: Frontmatter extraction regex
**Symptom**: Empty frontmatter with `sed`
**Cause**: `sed` regex differs across platforms
**Fix**: Use `awk '/^---$/{p=1-p;next} p'` instead
**Prevention**: Test scripts on target platform

---

## Claude Code Integration

### TaskCreate Mapping

| Entity Field | TaskCreate Param |
|--------------|------------------|
| `subject` | `subject` |
| `description` | `description` (body content) |
| `activeForm` | `activeForm` |

### TaskUpdate Mapping

| Entity Field | TaskUpdate Param |
|--------------|------------------|
| `status` | `status` |
| `blockedBy` | `addBlockedBy` |
| `blocks` | `addBlocks` |

### Workflow

1. Read entity from `entities/examples/`
2. `TaskCreate({ subject, description, activeForm })`
3. `TaskUpdate({ status: "in_progress" })` + entity version +0.0.1
4. Work...
5. `TaskUpdate({ status: "completed" })` + entity version +0.1.0
6. Commit with conventional message

---

## Steering System

### Budget-Aware Agent Execution

Agents in this PM system track token/turn consumption and hand off context when approaching limits. This enables long-running research and complex planning tasks.

**Budget Calculation**:
```
budget_ratio = max(turn_ratio, token_ratio)
turn_ratio = current_turn / max_turns
token_ratio = tokens_consumed / token_budget
```

### PM Agent Budgets

| Agent | Model | Turns | Use Case |
|-------|-------|-------|----------|
| `steering-orchestrator` | Opus 4.5 | 25 | Deep research, extended thinking |
| `vp-product` | Opus 4.5 | 25 | Strategic planning, roadmap |
| `sdm` | Sonnet 4.5 | 15 | Sprint planning, task breakdown |
| `staff-engineer` | Sonnet 4.5 | 15 | Implementation, coding |
| `sprint-master` | Haiku 3.5 | 10 | Coordination, status tracking |

### Wrap-up Thresholds

| Phase | Ratio | Agent Action |
|-------|-------|--------------|
| Normal | < 70% | Continue work |
| Warning | 70-79% | Prioritize critical items |
| Wrap-up | 80-89% | Stop new work, synthesize, handoff |
| Critical | 90%+ | Immediate handoff |

### Handoff Protocol

When `budget_ratio >= 0.80`:

1. **Stop new exploration** - Don't start new research threads
2. **Synthesize findings** - Consolidate what you've learned
3. **Document incomplete** - List remaining work items
4. **Generate handoff** - Create `<handoff>` YAML block

```yaml
<handoff>
reason: "budget_wrap_up_80_percent"
completed:
  - "Research topic A - summary"
  - "Created entity TASK-XXX"
incomplete:
  - "Topic B research - 60% done"
  - "Integration testing"
context:
  active_entities:
    epic: "ORG-EPIC-001"
    task: "TASK-005"
  key_files:
    - "lib/prompt_adapter.py"
    - "entities/examples/TASK-005.md"
  decisions:
    - "Use YAML for handoff format"
    - "State machine over regex for intent"
successor:
  agent: "staff-engineer"
  prompt_hint: "Continue Topic B research from handoff"
metrics:
  turns_used: 20
  budget_ratio: 0.80
</handoff>
```

### Chain Decisions

After handoff, decide chain continuation:

**Continue** when:
- Incomplete items exist AND successor is available
- Research requires multiple agent sessions
- Task explicitly requests multi-agent execution

**Terminate** when:
- All acceptance criteria met
- No incomplete items remain
- Error state requires human intervention

### Steering Configuration

Configuration files in `../steering/`:

```
steering/
├── config/
│   ├── budgets.yaml      # Token/turn limits by model
│   └── thresholds.yaml   # Wrap-up thresholds
└── lib/
    ├── budget_tracker.py    # BudgetTracker class
    └── handoff_generator.py # HandoffDocument generation
```

### Agent Integration

Agents with steering support include frontmatter:

```yaml
---
name: steering-orchestrator
steering:
  token_budget: 160000
  turn_budget: 25
  wrap_up_threshold: 0.80
  extended_thinking: true
---
```

---

## Design Principles

> When uncertain, ask: "How would Anthropic's 2026 engineering team solve this?"

1. **Agents over monoliths**: Spawn focused subagents
2. **Memory over repetition**: Use persistent agent memory
3. **Index over exploration**: Pre-compute what's queryable
4. **Live over mock**: Test against real systems
5. **Fail over degrade**: Crash cleanly, don't limp along
6. **Explicit over implicit**: Dependencies in frontmatter
7. **Delete over deprecate**: Remove unused code completely
8. **Budget-aware**: Track consumption, handoff gracefully
