---
name: review
description: Automated code review pipeline - run reviewers, generate tasks, assign work
---

# /review - Automated Review Pipeline

Run automated code review with 3 Opus agents in parallel, synthesize findings, and optionally spawn implementation agents.

## Usage

```
/review                    # Shortcut for /review l2-full
/review l0-test            # Just test reviewer
/review l0-value           # Just value reviewer
/review l0-mlflow          # Just MLflow analyzer
/review l1-parallel        # All 3 reviewers in parallel
/review l2-full            # Review + synthesize + generate tasks
/review l3-implement       # Full pipeline + spawn implementation agents
```

## Options

```
--branch=<name>            # Target branch (default: current)
--pr=<number>              # Link to PR number
--dry-run                  # Show tasks without creating
--force                    # Re-run even if review exists
```

## Levels

### Level 0: Individual Reviewers

Each reviewer runs independently and produces a REVIEW-*.md file.

| Command | Agent | Model | Focus |
|---------|-------|-------|-------|
| `l0-test` | test-reviewer | Opus | Test coverage gaps |
| `l0-value` | value-reviewer | Opus | Business value, architecture |
| `l0-mlflow` | mlflow-analyzer | Opus | Cost, latency, errors |

Output: `reviews/{branch}/REVIEW-{type}-{commit}.md`

### Level 1: Parallel Review

Spawns all 3 reviewers simultaneously using Task tool with parallel invocations.

```python
# Parallel spawn
Task(subagent_type="test-reviewer", ...)
Task(subagent_type="value-reviewer", ...)
Task(subagent_type="mlflow-analyzer", ...)
```

Output: 3 REVIEW-*.md files

### Level 2: Full Pipeline (Default)

1. Parallel review (L1)
2. Synthesize findings → `summary.json`
3. Deduplicate overlapping issues
4. Generate Task entities for P0/P1 findings

Output:
- `reviews/{branch}/REVIEW-*.md` (3 files)
- `reviews/{branch}/summary.json`
- `pm/entities/examples/TASK-*.md` (generated tasks)

### Level 3: Implementation Pipeline

1. Full review (L2)
2. Assign files to agents
3. Spawn Staff Engineer agents in parallel
4. Monitor completion

Output:
- All L2 outputs
- `reviews/{branch}/assignments.json`
- Parallel agent execution

## Execution Flow

```
/review l2-full --branch=feat/auth
    │
    ├─► Get current branch + commit
    │
    ├─► Check for existing review (skip if found, unless --force)
    │
    ├─► L1: Spawn 3 reviewers in parallel
    │   ├─► test-reviewer → REVIEW-test-{commit}.md
    │   ├─► value-reviewer → REVIEW-value-{commit}.md
    │   └─► mlflow-analyzer → REVIEW-mlflow-{commit}.md
    │
    ├─► Wait for all reviewers
    │
    ├─► Spawn review-synthesizer
    │   ├─► Read all REVIEW-*.md
    │   ├─► Deduplicate findings
    │   ├─► Generate tasks for P0/P1 with confidence >= 80
    │   └─► Write summary.json
    │
    └─► Report results
```

## Example Output

```
▶ Review Pipeline: feat/auth-system @ abc123d

Phase 1: Parallel Review
  ├─ test-reviewer ....... 3 findings (1 P0, 1 P1, 1 P2)
  ├─ value-reviewer ...... 2 findings (0 P0, 2 P1, 0 P2)
  └─ mlflow-analyzer ..... 2 findings (1 P0, 0 P1, 1 P2)

Phase 2: Synthesis
  ├─ Total findings: 7
  ├─ Unique (after dedup): 6
  ├─ Task eligible: 4 (P0/P1, conf >= 80)
  └─ Tasks created:
     ├─ TASK-101: Fix missing_test: JWT Error Handling
     ├─ TASK-102: Fix weak_assertion: Password Hash Check
     ├─ TASK-103: Fix architectural_mismatch: Repository Pattern
     └─ TASK-104: Fix high_cost: Excessive Token Usage

✓ Review complete
  Output: reviews/feat-auth-system/
  Tasks: pm/entities/examples/TASK-10{1-4}.md
```

## Implementation

When executing this command:

1. **Get context**:
   ```bash
   BRANCH=$(git branch --show-current)
   COMMIT=$(git rev-parse --short HEAD)
   BRANCH_SAFE=$(echo "$BRANCH" | tr '/' '-')
   ```

2. **Check existing**:
   ```bash
   if [ -f "reviews/$BRANCH_SAFE/REVIEW-test-$COMMIT.md" ] && [ -z "$FORCE" ]; then
     echo "Review exists. Use --force to re-run."
     exit 0
   fi
   ```

3. **Spawn reviewers** (parallel Task calls):
   ```python
   Task(
     subagent_type="test-reviewer",
     prompt=f"Review branch {BRANCH} commit {COMMIT}. Output to reviews/{BRANCH_SAFE}/REVIEW-test-{COMMIT}.md"
   )
   # ... same for value-reviewer, mlflow-analyzer
   ```

4. **Synthesize**:
   ```python
   Task(
     subagent_type="review-synthesizer",
     prompt=f"Synthesize reviews in reviews/{BRANCH_SAFE}/ and generate tasks"
   )
   ```

5. **For L3 - Assign and implement**:
   ```python
   Task(
     subagent_type="assignment-manager",
     prompt=f"Create assignments for reviews/{BRANCH_SAFE}/"
   )
   # Then spawn staff engineers based on assignments
   ```
