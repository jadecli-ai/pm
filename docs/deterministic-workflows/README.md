# Deterministic Workflows

> Automated, repeatable workflows for Claude Code CLI

## Overview

Deterministic workflows provide structured, repeatable automation for common development tasks. Each workflow follows predictable patterns with consistent outputs.

## Available Workflows

### Review Pipeline

Automated 3-agent code review with task generation.

| Level | Command | Description |
|-------|---------|-------------|
| L0 | `/review l0-{type}` | Single reviewer |
| L1 | `/review l1-parallel` | 3 reviewers parallel |
| L2 | `/review l2-full` | + synthesis + tasks |
| L3 | `/review l3-implement` | + parallel implementation |

**Documentation:**
- [Developer Guide](./developer/README.md) - Full navigation guide
- [Getting Started](./developer/getting-started.md) - Step-by-step tutorial
- [Quick Reference](./developer/quick-reference.md) - Command cheat sheet

## Workflow Principles

### 1. Monotonically Increasing Complexity

Workflows follow a level system:
- **L0**: Atomic operations (single tool/agent)
- **L1**: Composed operations (2-3 atomics)
- **L2**: Business workflows (multiple L1s)
- **L3**: Full pipelines (orchestrated L2s)

### 2. Predictable Output

Each workflow produces consistent artifacts:
- Structured markdown with YAML frontmatter
- JSON for machine-readable data
- Version-controlled entity files

### 3. Idempotency

Workflows can be safely re-run:
- Existing outputs detected and skipped
- `--force` flag to override
- Clear supersession semantics

### 4. Traceability

Full audit trail:
- Source references in generated artifacts
- Version bumps on changes
- Merkle tree indexing for change detection

## Directory Structure

```
deterministic-workflows/
├── README.md                 # This file
└── developer/                # Developer-facing docs
    ├── README.md             # Full navigation guide
    ├── getting-started.md    # Step-by-step tutorial
    └── quick-reference.md    # Command cheat sheet
```

## Related Documentation

- [PM System](../../pm/README.md) - Project management
- [Reviews](../../reviews/review.schema.md) - Review entity schema
- [Agent Index](../../pm/.index/AGENT-INDEX.md) - All agents
