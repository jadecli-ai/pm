---
name: review-pipeline
description: Full review pipeline execution - coordinates reviewers, synthesis, and implementation
tools:
  - Task
  - Read
  - Write
  - Glob
  - Bash
---

# Review Pipeline Skill

Orchestrates the complete automated review pipeline from code review through task generation and parallel implementation.

## Quick Reference

| Level | Command | Output |
|-------|---------|--------|
| L0 | `/review l0-{test\|value\|mlflow}` | Single REVIEW-*.md |
| L1 | `/review l1-parallel` | 3 REVIEW-*.md files |
| L2 | `/review l2-full` | + summary.json + TASK-*.md |
| L3 | `/review l3-implement` | + assignments.json + agent execution |

## Pipeline Phases

### Phase 1: Context Gathering

Collect branch, commit, and PR information:

```bash
# Get current branch
BRANCH=$(git branch --show-current)

# Get short commit hash
COMMIT=$(git rev-parse --short HEAD)

# Sanitize branch name for directory
BRANCH_SAFE=$(echo "$BRANCH" | tr '/' '-' | tr '[:upper:]' '[:lower:]')

# Get PR number if available
PR_NUMBER=$(gh pr view --json number -q '.number' 2>/dev/null || echo "null")
```

### Phase 2: Existing Review Check

Skip if review exists (unless --force):

```python
review_dir = Path(f"reviews/{branch_safe}")
existing = list(review_dir.glob(f"REVIEW-*-{commit}.md"))

if existing and not force:
    print(f"Review exists at {existing[0]}. Use --force to re-run.")
    return
```

### Phase 3: Parallel Review (L1+)

Spawn 3 Opus reviewers simultaneously:

```python
# All three spawned in single message for true parallelism
reviewers = [
    Task(
        subagent_type="test-reviewer",
        model="opus",
        prompt=f"""
        Review branch: {branch}
        Commit: {commit}
        PR: {pr_number or 'N/A'}

        Focus on test coverage gaps and test quality.
        Write output to: reviews/{branch_safe}/REVIEW-test-{commit}.md

        Follow the schema at reviews/review.schema.md
        """,
        run_in_background=True
    ),
    Task(
        subagent_type="value-reviewer",
        model="opus",
        prompt=f"""
        Review branch: {branch}
        Commit: {commit}
        PR: {pr_number or 'N/A'}

        Focus on business value, architecture, security.
        Write output to: reviews/{branch_safe}/REVIEW-value-{commit}.md

        Follow the schema at reviews/review.schema.md
        """,
        run_in_background=True
    ),
    Task(
        subagent_type="mlflow-analyzer",
        model="opus",
        prompt=f"""
        Review branch: {branch}
        Commit: {commit}
        PR: {pr_number or 'N/A'}

        Focus on cost, latency, error patterns.
        Write output to: reviews/{branch_safe}/REVIEW-mlflow-{commit}.md

        Follow the schema at reviews/review.schema.md
        """,
        run_in_background=True
    )
]

# Wait for all reviewers to complete
for reviewer in reviewers:
    result = TaskOutput(task_id=reviewer.id, block=True)
```

### Phase 4: Synthesis (L2+)

Merge findings and generate tasks:

```python
Task(
    subagent_type="review-synthesizer",
    model="sonnet",
    prompt=f"""
    Synthesize reviews in reviews/{branch_safe}/

    1. Read all REVIEW-*.md files
    2. Extract and deduplicate findings
    3. Filter: P0/P1 with confidence >= 80
    4. Generate Task entities to pm/entities/examples/
    5. Write summary.json

    Use lib/review_generator.py for task generation logic.
    """
)
```

### Phase 5: Assignment (L3)

Map files to agents:

```python
Task(
    subagent_type="assignment-manager",
    model="haiku",
    prompt=f"""
    Create file assignments for reviews/{branch_safe}/

    1. Read summary.json for generated tasks
    2. Extract files from each task
    3. Assign to agents by domain
    4. Detect and serialize conflicts
    5. Write assignments.json

    Use lib/assignment_algorithm.py for assignment logic.
    """
)
```

### Phase 6: Implementation (L3)

Spawn Staff Engineers based on assignments:

```python
# Read assignments
assignments = json.loads(Path(f"reviews/{branch_safe}/assignments.json").read_text())

# Spawn agents for each assignment
for agent, assignment in assignments["assignments"].items():
    Task(
        subagent_type="staff-engineer",
        model="sonnet",
        prompt=f"""
        You are assigned: {agent}
        Domain: {assignment['domain']}
        Tasks: {assignment['tasks']}
        Files: {assignment['files']}

        IMPORTANT: Only modify files in your assignment.
        Do not touch files outside your scope.

        For each task:
        1. Read the task entity from pm/entities/examples/
        2. Implement the fix following the suggestion
        3. Update task status when complete
        """,
        run_in_background=True
    )
```

## Directory Structure

```
reviews/
├── review.schema.md              # Schema definition
├── .index/
│   └── merkle-tree.json          # Change detection
└── {branch}/                     # e.g., feat-auth-system
    ├── REVIEW-test-abc123d.md    # Test reviewer output
    ├── REVIEW-value-abc123d.md   # Value reviewer output
    ├── REVIEW-mlflow-abc123d.md  # MLflow analyzer output
    ├── summary.json              # Synthesized findings
    └── assignments.json          # File → Agent mapping
```

## Summary.json Structure

```json
{
  "branch": "feat/auth-system",
  "commit": "abc123d",
  "generated": "2026-02-11T10:35:00Z",
  "reviews": [...],
  "aggregated": {
    "total_findings": 7,
    "unique_findings": 6,
    "p0_count": 2,
    "p1_count": 3,
    "p2_count": 2
  },
  "task_generation": {
    "eligible_findings": 4,
    "tasks_created": 4,
    "tasks": [...]
  }
}
```

## Assignments.json Structure

```json
{
  "branch": "feat/auth-system",
  "assignments": {
    "staff-engineer-1": {
      "domain": "auth",
      "files": ["src/auth/jwt.ts"],
      "tasks": ["TASK-101"],
      "estimated_hours": 0.5
    }
  },
  "conflicts": [...],
  "parallel_groups": [...]
}
```

## Error Handling

### Review Agent Timeout
If a reviewer doesn't complete within budget:
- Capture partial output
- Mark review as incomplete
- Continue with other reviewers

### No Findings
If all reviewers return 0 findings:
- Create summary.json with empty results
- Skip task generation phase
- Report "No issues found"

### Conflict in Assignments
If file assignment has conflicts:
- Serialize execution order
- Add blockedBy to later tasks
- Report conflict resolution

## Idempotency

The pipeline is idempotent:
- Existing reviews are skipped (unless --force)
- Task IDs are generated to avoid collisions
- Summary regeneration overwrites previous

## Metrics

Track across reviews:
- Average findings per reviewer
- P0/P1 catch rate
- Task completion rate
- Time to resolution
