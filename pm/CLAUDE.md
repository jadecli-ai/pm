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
├── docs/fetch/       # Fetched external docs
├── docs/research/    # Compiled research
└── tests/            # Integration tests (5 passing)
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

```bash
# Index Management
python3 .index/check-changes.py      # Check if index stale
python3 .index/generate-merkle.py    # Regenerate index

# Testing
./tests/run-tests.sh                 # Run all tests (must pass)
./tests/validate-entity.sh <file>    # Validate single entity

# Git
git add <specific-files>             # Never git add -A
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

## Steering Principles

> When uncertain, ask: "How would Anthropic's 2026 engineering team solve this?"

1. **Agents over monoliths**: Spawn focused subagents
2. **Memory over repetition**: Use persistent agent memory
3. **Index over exploration**: Pre-compute what's queryable
4. **Live over mock**: Test against real systems
5. **Fail over degrade**: Crash cleanly, don't limp along
6. **Explicit over implicit**: Dependencies in frontmatter
7. **Delete over deprecate**: Remove unused code completely
