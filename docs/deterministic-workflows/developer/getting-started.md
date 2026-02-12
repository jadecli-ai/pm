# Getting Started: Review Pipeline for Developers

> Step-by-step guide to navigating and using automated code review

## Prerequisites

- Claude Code CLI installed and authenticated
- Working in a git repository
- Access to `~/.claude-org/` organization directory

## Step 1: Navigate to Your Project

```bash
# Start in your project directory
cd /path/to/your/project

# Ensure you're on the right branch
git branch --show-current
# feat/my-feature

# Check recent commit
git log -1 --oneline
# abc123d Add authentication module
```

## Step 2: Launch Claude Code CLI

```bash
# Start Claude Code in your project
claude

# Or with specific directory
claude /path/to/your/project
```

## Step 3: Run Your First Review

In the Claude Code CLI prompt, type:

```
/review
```

This runs the default L2 pipeline which:
1. Spawns 3 Opus reviewers in parallel
2. Synthesizes findings
3. Generates tasks for critical issues

**Expected output:**
```
▶ Review Pipeline: feat/my-feature @ abc123d

Phase 1: Parallel Review
  ├─ test-reviewer ....... 2 findings (0 P0, 1 P1, 1 P2)
  ├─ value-reviewer ...... 1 findings (0 P0, 1 P1, 0 P2)
  └─ mlflow-analyzer ..... 0 findings

Phase 2: Synthesis
  ├─ Total findings: 3
  ├─ Unique (after dedup): 3
  ├─ Task eligible: 2 (P0/P1, conf >= 80)
  └─ Tasks created:
     ├─ TASK-101: Fix weak_assertion: Password Hash Check
     └─ TASK-102: Fix architectural_mismatch: Repository Pattern

✓ Review complete
```

## Step 4: View Review Results

Navigate to the review output:

```bash
# From terminal (not Claude Code)
cd ~/.claude-org/reviews/feat-my-feature/

ls -la
# REVIEW-test-abc123d.md
# REVIEW-value-abc123d.md
# REVIEW-mlflow-abc123d.md
# summary.json
```

Or in Claude Code:

```
Read the file at ~/.claude-org/reviews/feat-my-feature/REVIEW-test-abc123d.md
```

## Step 5: Review Individual Findings

Open a review file to see detailed findings:

```markdown
## Findings

### F-001: Weak Password Assertion (P1, Confidence: 88%)

**Category**: `weak_assertion`
**File**: `tests/auth/password.test.ts:23`

**Issue**: Test only checks that `hashPassword()` returns a string,
not that it produces a valid bcrypt hash.

**Suggestion**: Assert hash starts with `$2b$` and has correct length.
```

## Step 6: View Generated Tasks

Check generated tasks:

```bash
ls ~/.claude-org/pm/entities/examples/TASK-10*.md
```

Or in Claude Code:

```
Show me the task TASK-101
```

## Step 7: Work on a Task

In Claude Code:

```
Start working on TASK-101
```

The agent will:
1. Read the task entity
2. Apply the suggested fix
3. Update task status when complete

## Step 8: Re-Run After Fixes

After making changes, re-run the review:

```
/review --force
```

This creates a new review and supersedes the old one.

## Alternative: Using Make

If you prefer make commands:

```bash
# Navigate to pm directory
cd ~/.claude-org/pm

# Run review
make review

# Or specific level
make review-l0-test
make review-l1-parallel
make review-l3-implement

# See all options
make help
```

## Directory Navigation Reference

### From Project → Review Output

```
Your Project                   Organization
============                   ============
/my-project/                   ~/.claude-org/
├── src/                       ├── reviews/
│   └── auth/                  │   └── {your-branch}/
│       └── jwt.ts  ────────────────► REVIEW-test-*.md
└── tests/                     │       └── Findings about jwt.ts
    └── auth/                  └── pm/
                                   └── entities/examples/
                                       └── TASK-101.md
                                           └── Fix for jwt.ts
```

### From Review → Task → Implementation

```
1. Review identifies issue
   ~/.claude-org/reviews/{branch}/REVIEW-test-{commit}.md
   └── F-001: Missing JWT error tests (P1, 88%)
                    │
                    ▼
2. Task generated
   ~/.claude-org/pm/entities/examples/TASK-101.md
   └── source_review: REVIEW-test-{commit}
   └── source_finding: F-001
                    │
                    ▼
3. Agent implements fix
   /your-project/src/auth/jwt.ts
   └── Error handling added
```

## Common Workflows

### Pre-PR Review

```bash
# 1. Ensure all changes committed
git add -A && git commit -m "feat: add auth"

# 2. Run review
/review

# 3. Fix any P0/P1 issues
# 4. Re-run and verify
/review --force

# 5. Open PR
gh pr create
```

### Coverage-Focused Review

```bash
# Just test coverage
/review l0-test

# Review output
cat ~/.claude-org/reviews/{branch}/REVIEW-test-*.md
```

### Security-Focused Review

```bash
# Value reviewer includes security
/review l0-value

# Check for security findings
grep -i "security" ~/.claude-org/reviews/{branch}/REVIEW-value-*.md
```

## Next Steps

- Read [Quick Reference](./quick-reference.md) for command cheat sheet
- See [Review Schema](../../../reviews/review.schema.md) for output format
- Check [Agent Index](../../../pm/.index/AGENT-INDEX.md) for all agents
