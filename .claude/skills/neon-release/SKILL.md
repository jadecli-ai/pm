---
name: neon-release
description: Create traced, conventional-commit PR releases for the Neon Specialist Agent. Use when preparing a GitHub pull request for completed phases, organizing commits by subtask, and tracking progress via MLflow 3.9 CLI/SDK tracing. Triggers on PR creation, release preparation, or phase completion workflows.
---

# Neon Release Skill

Create GitHub PRs with conventional commits mapped to plan subtasks, traced via MLflow 3.9.

## Prerequisites

- MLflow 3.9+ with Claude CLI tracing enabled (`mlflow autolog claude`)
- `gh` CLI authenticated
- Conventional commits already on branch (from subagent-driven-development)

## Workflow

### 1. Verify MLflow Tracing

```bash
mlflow autolog claude --status
```

Tracing must be ENABLED before any PR work. If disabled:

```bash
mlflow autolog claude
```

### 2. Organize Commits by Phase

Map existing commits to plan tasks. Each commit should follow:

```
<type>(<scope>): <description>

Refs: Task N, Phase P
```

Types: `feat`, `fix`, `test`, `docs`, `ci`, `chore`, `refactor`, `perf`
Scope: `neon`, `agents`, `infra`, `deps`, `index`, `tracing`

### 3. Create Feature Branch

```bash
# Branch from current HEAD (all phase work included)
git checkout -b feat/<feature-name>
git push -u origin feat/<feature-name>
```

### 4. Create PR with Phase Summary

```bash
gh pr create --title "<type>(<scope>): <summary>" --body "$(cat <<'EOF'
## Summary
<Goal and what was built>

## Phases Included
- [ ] Phase 0: Infrastructure (Tasks 1-8)
- [ ] Phase 1: Database Layer (Tasks 9-15)
- [ ] Phase 2: Embeddings Pipeline (Tasks 16-20)
- [ ] Phase 3: CLI (Tasks 21-22)
- [ ] Phase 4: MLflow Tracing (Tasks 23-26)
- [ ] Phase 5: Hooks + Deps (Tasks 27-30)
- [ ] Phase 6: Makefile Targets (Tasks 31-33)
- [ ] Phase 7: Agent Integration (Tasks 34-41)

## Key Files
<List of new/modified files by category>

## Test Plan
- [ ] `pytest pm/tests/neon_docs/ -v` — all pass
- [ ] `ruff check pm/lib/neon_docs/` — clean
- [ ] `make l0-doc-status` — documents indexed
- [ ] Existing PM tests still pass

## MLflow Tracing
- Experiment: `<experiment-name>`
- @trace_operation on: upsert, search, migrate, worker
- CLI autolog: enabled

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### 5. Track Progress via MLflow

The MLflow experiment captures:
- Claude Code conversation traces (via CLI autolog)
- Python function spans (via @trace_operation decorator)
- Phase 8 bootstrap metrics (via phase8_bootstrap.py)

View traces:

```bash
mlflow ui --port 5001
# Navigate to experiment in browser
```

### 6. Subtask-to-Commit Mapping

When reviewing PR, verify each plan task has a corresponding commit:

```bash
# List commits with task references
git log --oneline origin/main..HEAD | grep -i "task\|phase"
```

## MLflow 3.9 Integration

### CLI Tracing (conversation-level)

Already configured via `.claude/settings.json`:

```json
{
  "environment": {
    "MLFLOW_CLAUDE_TRACING_ENABLED": "true",
    "MLFLOW_TRACKING_URI": "file://./mlruns",
    "MLFLOW_EXPERIMENT_NAME": "<experiment>"
  }
}
```

### SDK Tracing (function-level)

```python
from lib.neon_docs.tracer import trace_operation

@trace_operation("neon.<operation>")
async def my_function():
    ...
```

### Progress Hooks

PostToolUse hooks in `.claude/settings.json` log task events automatically.
Stop hooks flush MLflow traces on session end.

## Conventional Commits Reference

| Type | Use |
|------|-----|
| `feat` | New functionality |
| `fix` | Bug fix |
| `test` | Test additions |
| `docs` | Documentation |
| `ci` | CI/CD workflows |
| `chore` | Maintenance (lint, format) |
| `refactor` | Code restructuring |
| `perf` | Performance improvement |
