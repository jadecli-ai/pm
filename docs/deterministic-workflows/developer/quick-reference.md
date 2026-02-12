# Review Pipeline Quick Reference

> Cheat sheet for developers using automated code review

## Commands at a Glance

| Command | What it Does | Output |
|---------|-------------|--------|
| `/review` | Full pipeline (default) | 3 reviews + summary + tasks |
| `/review l0-test` | Test coverage only | REVIEW-test-*.md |
| `/review l0-value` | Business/security only | REVIEW-value-*.md |
| `/review l0-mlflow` | Performance only | REVIEW-mlflow-*.md |
| `/review l1-parallel` | All reviewers | 3 REVIEW-*.md files |
| `/review l2-full` | + synthesis + tasks | + summary.json + TASK-*.md |
| `/review l3-implement` | + auto-fix | + assignments + agents |

## Common Options

```bash
/review --branch=main         # Review specific branch
/review --pr=42               # Link to PR number
/review --dry-run             # Preview without writing
/review --force               # Re-run existing review
```

## Output Locations

```
~/.claude-org/reviews/{branch}/
├── REVIEW-test-{commit}.md      # Test findings
├── REVIEW-value-{commit}.md     # Value findings
├── REVIEW-mlflow-{commit}.md    # MLflow findings
├── summary.json                 # Aggregated
└── assignments.json             # Agent map
```

## Finding Priority Quick Guide

| Priority | Action | Auto-Task |
|----------|--------|-----------|
| **P0** | Fix immediately | Yes |
| **P1** | Fix this sprint | Yes |
| **P2** | Fix next sprint | No |
| **P3** | Backlog | No |

## Confidence Quick Guide

| Range | Meaning |
|-------|---------|
| 90-100 | Definite issue |
| 80-89 | Very likely |
| 70-79 | Probable |
| <70 | Investigate |

## Make Targets

```bash
cd ~/.claude-org/pm

make review              # Full pipeline
make review-l0-test      # Test only
make review-l1-parallel  # All parallel
make review-l3-implement # With auto-fix
make help                # All options
```

## Reviewers

| Agent | Model | Focus |
|-------|-------|-------|
| `test-reviewer` | Opus | Coverage, test quality |
| `value-reviewer` | Opus | Architecture, security |
| `mlflow-analyzer` | Opus | Cost, latency, errors |

## Task Generation Rules

Tasks auto-created when ALL true:
- Priority: P0 or P1
- Confidence: >= 80%
- Has suggestion

## One-Liner Workflows

```bash
# Quick check before PR
/review l0-test

# Full review with fixes
/review l3-implement

# Re-run after changes
/review --force

# Review main branch
/review --branch=main
```
