---
name: pm-atomic
description: Level 0 atomic PM operations - single tool calls
tools:
  - Bash
---

# PM Atomic Operations (Level 0)

Execute single-responsibility PM operations. Each returns in <1s.

## Available Operations

| Op | Command | Output |
|----|---------|--------|
| test | `make -s l0-test` | Test summary |
| arch | `make -s l0-arch` | "Generated: ..." |
| lint | `make -s l0-lint FILE=<path>` | ✓ or ✗ |
| hash | `make -s l0-hash FILE=<path>` | 16-char hash |
| commit | `make -s l0-commit-check` | ✓ conventional or ✗ |
| frontmatter | `make -s l0-frontmatter FILE=<path>` | JSON |

## Execution Pattern

```bash
cd /home/org-jadecli/projects/.claude-org/pm && make -s l0-<op>
```

## Chaining

Atomic ops can be chained with `&&`:
```bash
make -s l0-test && make -s l0-arch
```

Or piped:
```bash
make -s l0-frontmatter FILE=CLAUDE.md | jq .version
```

## Token Efficiency

- Each op: ~50 tokens output max
- No verbose logging
- Exit codes for success/failure
