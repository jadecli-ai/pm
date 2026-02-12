# Backend Engineering Team - Claude Code Instructions

> Backend services, APIs, and database operations

## Quick Start

1. Read `.index/AGENT-INDEX.md` for instant context
2. Check `.index/merkle-tree.json` root hash for change detection
3. Run `tests/run-tests.sh` before any changes

## Package Structure

```
backend-engineering/
├── .index/           # Merkle tree (O(1) change detection)
├── agents/           # Backend Engineering team agents
├── entities/         # Work items (Claude Code aligned)
├── lib/              # Shared code
├── docs/             # Documentation
├── tests/            # Integration tests
└── CLAUDE.md         # This file
```

## Team Agents

| Agent | Model | Turns | Role |
|-------|-------|-------|------|
| `backend-engineering-lead` | claude-opus-4-5-20251101 | 25 | Team leadership, planning |
| `backend-engineering-engineer` | claude-sonnet-4-5-20250929 | 15 | Implementation |
| `backend-engineering-tester` | claude-haiku-3-5-20241022 | 10 | Testing, validation |

## Steering Integration

This team uses budget-aware steering. See `../steering/` for configuration.

**Wrap-up Threshold**: 0.8%

When budget ratio reaches 0.8%:
1. Stop new work
2. Synthesize findings
3. Generate `<handoff>` YAML block
4. Document incomplete items

## Entry Checklist

- [ ] Read this file completely
- [ ] Run `python3 .index/check-changes.py` to verify index freshness
- [ ] Run `./tests/run-tests.sh` to confirm system health
- [ ] Check `entities/examples/` for current states

## Patterns to Follow

### Test-Driven Development
- [ ] **Red**: Write failing test first
- [ ] **Green**: Minimal code to pass
- [ ] **Refactor**: Clean up, maintain tests green

### Fail Fast Philosophy
- [ ] **Crash early**: Throw on invalid state
- [ ] **Validate inputs**: Check at boundaries
- [ ] **Explicit errors**: Descriptive messages

## Contributing

### Conventional Commits
```
<type>(<scope>): <description>

feat(backend-engineering): add new capability
fix(backend-engineering): correct issue
test(backend-engineering): add integration tests
```

### PR Checklist
- [ ] All tests pass
- [ ] Index regenerated
- [ ] Frontmatter complete
- [ ] Version bumped
- [ ] Conventional commit message
