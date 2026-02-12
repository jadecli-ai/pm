# Deterministic Workflows: Developer Guide

> Navigate and trigger automated review pipelines in Claude Code CLI

## Overview

This guide shows developers how to use the automated review pipeline to get code reviews, generate fix tasks, and coordinate parallel implementation.

## Quick Start

```bash
# From any project directory
cd /path/to/your/project

# Run the review pipeline
/review

# Or use make from the pm directory
cd ~/.claude-org/pm && make review
```

## Navigation Path

```
Organization Structure
======================

~/.claude-org/                      # Organization root
├── pm/                             # Project Management system
│   ├── agents/                     # Agent definitions
│   │   ├── test-reviewer.md        # Test coverage reviewer
│   │   ├── value-reviewer.md       # Business value reviewer
│   │   ├── mlflow-analyzer.md      # Performance analyzer
│   │   ├── review-synthesizer.md   # Findings merger
│   │   └── assignment-manager.md   # File assignment
│   ├── .claude/
│   │   ├── commands/
│   │   │   └── review.md           # /review command definition
│   │   └── skills/
│   │       └── review-pipeline.md  # Pipeline skill
│   ├── lib/
│   │   ├── review_generator.py     # Task generation library
│   │   └── assignment_algorithm.py # File assignment logic
│   └── Makefile                    # make review targets
├── reviews/                        # Review output storage
│   ├── review.schema.md            # Review entity schema
│   └── {branch}/                   # Per-branch results
│       ├── REVIEW-test-*.md        # Test findings
│       ├── REVIEW-value-*.md       # Value findings
│       ├── REVIEW-mlflow-*.md      # MLflow findings
│       ├── summary.json            # Aggregated results
│       └── assignments.json        # Agent assignments
└── docs/
    └── deterministic-workflows/
        └── developer/              # This documentation
```

## Triggering Reviews

### Method 1: Slash Command (Recommended)

In Claude Code CLI, use the `/review` command:

```
/review                    # Full pipeline (L2) - default
/review l0-test            # Test reviewer only
/review l0-value           # Value reviewer only
/review l0-mlflow          # MLflow analyzer only
/review l1-parallel        # All 3 reviewers in parallel
/review l2-full            # Review + synthesis + tasks
/review l3-implement       # Full pipeline + implementation
```

**Options:**
```
--branch=<name>            # Target specific branch
--pr=<number>              # Link to PR
--dry-run                  # Preview without creating files
--force                    # Re-run even if review exists
```

### Method 2: Make Targets

From the pm directory:

```bash
cd ~/.claude-org/pm

make review                # Alias for review-l2-full
make review-l0-test        # Test reviewer only
make review-l0-value       # Value reviewer only
make review-l0-mlflow      # MLflow analyzer only
make review-l1-parallel    # Parallel reviewers
make review-l2-full        # Full pipeline
make review-l3-implement   # With implementation

# See all options
make help
```

### Method 3: Direct Agent Invocation

For advanced usage, invoke agents directly via Task tool:

```javascript
Task({
  subagent_type: "test-reviewer",
  model: "opus",
  prompt: "Review branch feat/auth commit abc123d"
})
```

## Workflow Examples

### Example 1: Quick Review Before PR

```bash
# Ensure you're on your feature branch
git checkout feat/my-feature

# Run full review
/review

# Output appears in:
# ~/.claude-org/reviews/feat-my-feature/
```

### Example 2: Test Coverage Check Only

```bash
# Just check test coverage gaps
/review l0-test

# Review findings at:
# ~/.claude-org/reviews/{branch}/REVIEW-test-{commit}.md
```

### Example 3: Full Pipeline with Auto-Fix

```bash
# Run review, generate tasks, and implement fixes
/review l3-implement

# This will:
# 1. Run all 3 reviewers in parallel
# 2. Synthesize findings
# 3. Generate TASK-*.md for P0/P1 issues
# 4. Assign files to agents
# 5. Spawn parallel implementation agents
```

### Example 4: Review Specific Branch

```bash
# Review a different branch without switching
/review l2-full --branch=develop

# Or with PR linkage
/review l2-full --branch=feat/auth --pr=42
```

## Understanding Output

### Review Files

Each reviewer creates a markdown file:

```markdown
---
id: "REVIEW-test-abc123d"
type: review
status: completed
branch: "feat/auth"
commit: "abc123d"
findings_count: 3
p0_count: 1
p1_count: 1
p2_count: 1
---

# Test Coverage Review

## Summary
Found 3 issues...

## Findings

### F-001: Missing JWT Error Tests (P0, Confidence: 95%)
...
```

### Summary JSON

Aggregated results in `summary.json`:

```json
{
  "branch": "feat/auth",
  "aggregated": {
    "total_findings": 7,
    "unique_findings": 6,
    "p0_count": 2,
    "p1_count": 3
  },
  "task_generation": {
    "tasks_created": 4,
    "tasks": ["TASK-101", "TASK-102", ...]
  }
}
```

### Generated Tasks

Tasks appear in `pm/entities/examples/`:

```markdown
---
id: "TASK-101"
type: task
status: pending
source_review: "REVIEW-test-abc123d"
source_finding: "F-001"
subject: "Fix missing_test: JWT Error Tests"
---
```

## Priority Levels

| Priority | SLA | Description | Auto-Task? |
|----------|-----|-------------|------------|
| P0 | Immediate | Critical security/bugs | Yes |
| P1 | Same iteration | High impact issues | Yes |
| P2 | Next iteration | Quality improvements | No |
| P3 | Backlog | Nice to have | No |

Tasks are only auto-generated for P0/P1 with confidence >= 80%.

## Confidence Thresholds

| Confidence | Meaning |
|------------|---------|
| 90-100% | Clear evidence, cite specific code |
| 80-89% | Strong evidence, some inference |
| 70-79% | Likely issue, needs verification |
| <70% | Hypothesis, investigate further |

## Best Practices

### When to Run Reviews

- Before opening a PR
- After significant changes
- When coverage drops
- Before release

### Interpreting Results

1. **Focus on P0 first** - Critical issues that must be fixed
2. **Check confidence** - High confidence = clear evidence
3. **Review suggestions** - Actionable fixes provided
4. **Cross-reference** - Multiple reviewers may flag same issue

### Handling Conflicts

When multiple reviewers flag the same issue:
- Findings are deduplicated automatically
- Merged finding keeps highest confidence
- Sources tracked for traceability

### Iterating on Fixes

1. Fix issues from generated tasks
2. Run `/review --force` to re-check
3. New review supersedes old one
4. Old tasks remain linked to original finding

## Troubleshooting

### "Review exists" Message

```bash
# Force re-run
/review --force
```

### No Findings Generated

- Check if branch has recent commits
- Verify files are in supported languages
- Review may have found no issues (good!)

### Tasks Not Created

Tasks only generate when:
- Priority is P0 or P1
- Confidence >= 80%
- Suggestion is provided

Lower priority findings stay in review file only.

## Related Documentation

- [Review Schema](../../../reviews/review.schema.md) - Full entity schema
- [Agent Index](../../../pm/.index/AGENT-INDEX.md) - All agent definitions
- [Task Schema](../../../pm/entities/task.schema.md) - Task entity format
