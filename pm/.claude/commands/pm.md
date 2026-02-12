---
name: pm
description: PM System commands - monotonically increasing automation
---

# /pm - PM System Commands

Run PM automation at the appropriate complexity level.

## Usage

```
/pm <level>-<command>
/pm <shortcut>
```

## Levels

### Level 0: Atomic (single tool call)
- `/pm l0-test` - Run tests
- `/pm l0-arch` - Generate architecture
- `/pm l0-lint FILE=<path>` - Lint frontmatter
- `/pm l0-hash FILE=<path>` - Get file hash
- `/pm l0-commit-check` - Validate commit message
- `/pm l0-frontmatter FILE=<path>` - Extract frontmatter

### Level 1: Composed (2-3 atomic ops)
- `/pm l1-index` - Check + regenerate index if stale
- `/pm l1-validate` - Tests + index check
- `/pm l1-arch-check` - Generate arch + check diff
- `/pm l1-pr-lint` - Lint all changed files

### Level 2: Workflow (business logic)
- `/pm l2-pr-open` - Full PR open checks
- `/pm l2-pr-merge` - PR merge automation
- `/pm l2-release` - Release workflow

### Level 3: Pipeline (full automation)
- `/pm l3-ci` - Full CI pipeline
- `/pm l3-cd` - Full CD pipeline
- `/pm l3-full` - CI + CD + release

### Shortcuts
- `/pm test` → l0-test
- `/pm index` → l1-index
- `/pm arch` → l0-arch
- `/pm validate` → l1-validate
- `/pm check` → l2-pr-open
- `/pm ci` → l3-ci
- `/pm cd` → l3-cd

## Execution

```bash
cd pm && make $ARGS
```
