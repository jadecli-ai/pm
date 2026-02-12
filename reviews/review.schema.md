# Review Entity Schema

> Automated code review results - **Aligned with Claude Code TaskCreate**

## Overview

Review entities store structured output from automated review agents (test coverage, business value, MLflow analysis). Each review generates findings that can be converted to Task entities.

## Claude Code Integration

Reviews integrate with Claude Code's task system for traceability:

| Review Field | TaskCreate Param | Purpose |
|--------------|------------------|---------|
| `subject` | `subject` | Brief review title |
| `activeForm` | `activeForm` | Review in progress indicator |
| `generated_tasks` | - | Links to created Tasks |

## Frontmatter

```yaml
---
id: "REVIEW-XXX"                     # Required: Unique identifier
version: "1.0.0"                     # Required: SemVer
type: review                         # Required: Always "review"
status: pending                      # Required: pending|in_progress|completed|superseded
created: YYYY-MM-DDTHH:MM:SSZ        # Required: ISO 8601
updated: YYYY-MM-DDTHH:MM:SSZ        # Required: ISO 8601

# Context
branch: "feat/auth-system"           # Required: Target branch
commit: "abc123def456..."            # Required: Short commit SHA
pr_number: 42                        # Optional: Linked PR

# Reviewer
reviewer_agent: "test-reviewer"      # Required: Agent that performed review
reviewer_model: "claude-opus-4-5"    # Required: Model used
review_type: test                    # Required: test|value|mlflow

# Results
findings_count: 5                    # Required: Total findings
p0_count: 1                          # Required: Critical issues
p1_count: 2                          # Required: High priority
p2_count: 2                          # Required: Medium priority

# Task generation
generated_tasks: []                  # Task IDs created from findings

# Claude Code alignment
subject: "Test coverage review"      # Brief imperative title
activeForm: "Reviewing test coverage"  # Present continuous for spinner
---
```

## Body Structure

```markdown
# [Review Title]

## Summary

[2-3 sentence overview of findings]

## Metrics

| Metric | Value |
|--------|-------|
| Files Reviewed | 12 |
| Review Duration | 45s |
| Coverage Delta | +3.2% |

## Findings

### F-001: [Title] (P0, Confidence: 92%)

**Category**: missing_test
**File**: `src/auth/jwt.ts:45-52`

**Issue**: [Detailed description of the problem]

**Suggestion**: [How to fix it]

**Generated Task**: TASK-101

---

### F-002: [Title] (P1, Confidence: 85%)

...

## Files Reviewed

- `src/auth/jwt.ts` - 3 findings
- `src/auth/middleware.ts` - 1 finding
- `src/api/routes.ts` - 1 finding

## Recommendations

[Overall recommendations based on patterns observed]
```

## Findings JSON Schema

Embedded in body as fenced JSON block:

```json
{
  "findings": [{
    "id": "F-001",
    "priority": "P0",
    "confidence": 92,
    "category": "missing_test",
    "file": "src/auth/jwt.ts",
    "lines": [45, 52],
    "title": "No error handling tests",
    "description": "The token validation function lacks tests for error cases",
    "suggestion": "Add test for TokenExpiredError and InvalidSignatureError",
    "generated_task": "TASK-101"
  }],
  "metrics": {
    "files_reviewed": 12,
    "review_duration_seconds": 45,
    "coverage_delta_percent": 3.2
  }
}
```

## Review Types

### test (Test Reviewer)

Focus areas:
- Coverage gaps - untested code paths
- Test quality - assertion strength, edge cases
- Test organization - structure, naming conventions
- Mock appropriateness - real vs mocked dependencies

Categories: `missing_test`, `weak_assertion`, `missing_edge_case`, `test_smell`, `coverage_gap`

### value (Value Reviewer)

Focus areas:
- Business alignment - solves stated problem?
- Architectural fit - follows established patterns?
- Maintainability - sustainable, readable code?
- Security - vulnerabilities, data handling?

Categories: `architectural_mismatch`, `security_vulnerability`, `maintainability`, `business_logic_error`, `code_smell`

### mlflow (MLflow Analyzer)

Focus areas:
- Cost analysis - token usage, API costs
- Latency patterns - slow operations, timeouts
- Error patterns - recurring failures
- Trace completeness - missing instrumentation

Categories: `high_cost`, `latency_issue`, `error_pattern`, `missing_instrumentation`, `inefficient_pattern`

## Priority Levels

| Priority | SLA | Description |
|----------|-----|-------------|
| P0 | Immediate | Critical bug, security issue, data loss |
| P1 | Same iteration | High impact, blocks other work |
| P2 | Next iteration | Moderate impact, quality improvement |
| P3 | Backlog | Low impact, nice to have |

## Confidence Threshold

Only findings with confidence >= 80 are eligible for automatic task generation.

## Version Bumps

- PATCH (+0.0.1): Metadata update, typo fix
- MINOR (+0.1.0): New finding added, task generated
- MAJOR (+1.0.0): Review superseded, scope change

## Example

```yaml
---
id: "REVIEW-test-001"
version: "1.0.0"
type: review
status: completed
created: 2026-02-11T10:30:00Z
updated: 2026-02-11T10:31:45Z

branch: "feat/auth-system"
commit: "abc123d"
pr_number: 42

reviewer_agent: "test-reviewer"
reviewer_model: "claude-opus-4-5-20251101"
review_type: test

findings_count: 3
p0_count: 1
p1_count: 1
p2_count: 1

generated_tasks:
  - "TASK-101"
  - "TASK-102"

subject: "Test coverage review for auth module"
activeForm: "Reviewing test coverage for auth"
---

# Test Coverage Review: Auth Module

## Summary

Review identified 3 findings in the authentication module. One critical gap in JWT error handling requires immediate attention. Test coverage can be improved from 72% to estimated 85%.

## Metrics

| Metric | Value |
|--------|-------|
| Files Reviewed | 4 |
| Review Duration | 38s |
| Current Coverage | 72% |
| Estimated After Fix | 85% |

## Findings

### F-001: Missing JWT Error Tests (P0, Confidence: 95%)

**Category**: `missing_test`
**File**: `src/auth/jwt.ts:45-67`

**Issue**: The `verifyToken()` function handles 4 error types but only TokenExpiredError is tested. InvalidSignatureError, JsonWebTokenError, and NotBeforeError are uncovered.

**Suggestion**: Add tests for each error type:
- TokenExpiredError - already tested
- InvalidSignatureError - test with tampered token
- JsonWebTokenError - test with malformed string
- NotBeforeError - test with future nbf claim

**Generated Task**: TASK-101

---

### F-002: Weak Password Assertion (P1, Confidence: 88%)

**Category**: `weak_assertion`
**File**: `tests/auth/password.test.ts:23`

**Issue**: Test only checks that `hashPassword()` returns a string, not that it produces a valid bcrypt hash.

**Suggestion**: Assert hash starts with `$2b$` and has correct length (60 chars).

**Generated Task**: TASK-102

---

### F-003: Missing Rate Limit Edge Case (P2, Confidence: 82%)

**Category**: `missing_edge_case`
**File**: `src/middleware/rateLimit.ts`

**Issue**: No test for behavior when rate limit is exactly reached (boundary condition).

**Suggestion**: Add test for request at exactly the limit threshold.

**Generated Task**: (Not generated - P2)

## Files Reviewed

- `src/auth/jwt.ts` - 1 finding (P0)
- `tests/auth/password.test.ts` - 1 finding (P1)
- `src/middleware/rateLimit.ts` - 1 finding (P2)
- `src/auth/session.ts` - 0 findings

## Recommendations

1. **Immediate**: Address F-001 before merging - untested error paths are security risk
2. **This PR**: Strengthen password hash assertion (F-002)
3. **Follow-up**: Add boundary tests for rate limiting
```

## Agent Usage

### Creating Review

```javascript
// Write review file
Write({
  file_path: "reviews/{branch}/REVIEW-test-{commit}.md",
  content: reviewMarkdown
})
```

### Generating Tasks from Findings

```python
# Filter eligible findings
eligible = [f for f in findings
            if f.priority in ["P0", "P1"]
            and f.confidence >= 80]

# Generate task for each
for finding in eligible:
    task = TaskCreate({
        subject: f"Fix {finding.category}: {finding.title}",
        description: f"{finding.description}\n\nSuggestion: {finding.suggestion}",
        activeForm: f"Fixing {finding.category} in {finding.file}"
    })
    finding.generated_task = task.id
```

### Superseding Reviews

When a new review is run on the same branch:

1. Mark old review: `status: superseded`
2. Bump old review version: `1.0.0 → 1.1.0`
3. Create new review with fresh findings
4. Tasks from old review remain (linked to old finding IDs)

## Storage Structure

```
reviews/
├── review.schema.md              # This file
├── .index/
│   └── merkle-tree.json          # Change detection
└── {branch}/                     # Sanitized branch name
    ├── REVIEW-test-{commit}.md   # Test reviewer output
    ├── REVIEW-value-{commit}.md  # Value reviewer output
    ├── REVIEW-mlflow-{commit}.md # MLflow analyzer output
    ├── summary.json              # Aggregated findings
    └── assignments.json          # File→Agent mapping
```

Branch name sanitization: Replace `/` with `-`, lowercase.
Example: `feat/auth-system` → `feat-auth-system`
