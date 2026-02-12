---
name: pm-workflow
description: Level 2 PM workflows - business logic automation
tools:
  - Bash
imports:
  - pm-atomic
---

# PM Workflows (Level 2)

Business logic workflows that compose Level 0-1 operations.

## PR Open Workflow

**Trigger**: PR opened against main
**Command**: `make -s l2-pr-open`

```
▶ PR Open Checks
  ✓ tests + index
  ✓ arch current
  ✓ conventional
  ✓ frontmatter
✓ PR ready
```

**Composed from**:
1. `l1-validate` (tests + index)
2. `l1-arch-check` (arch generation + diff)
3. `l0-commit-check` (conventional commit)
4. `l1-pr-lint` (frontmatter validation)

## PR Merge Workflow

**Trigger**: PR merged to main
**Command**: `make -s l2-pr-merge`

```
▶ PR Merge
  Generated: ARCHITECTURE.md
  ✓ arch committed
✓ merge complete
```

**Composed from**:
1. `l0-arch` (generate architecture)
2. Conditional git add/commit if changed
3. Auto-commit with conventional message

## Release Workflow

**Trigger**: Manual or tag push
**Command**: `make -s l2-release`

**Composed from**:
1. `l2-pr-open` (full validation)
2. Version extraction from CHANGELOG.md
3. Tag creation (future)

## Execution

```bash
cd /home/org-jadecli/projects/.claude-org/pm && make -s l2-<workflow>
```
