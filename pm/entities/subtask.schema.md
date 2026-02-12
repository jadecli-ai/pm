# Subtask Entity Schema

> Atomic work item - smallest trackable unit

## Purpose

Subtasks are used when a Task needs to be broken down further:
- Task is size L or XL
- Multiple distinct implementation steps
- Parallel work by same or different agent

## Frontmatter

```yaml
---
id: "SUBTASK-XXX"                 # Required: Unique identifier
version: "1.0.0"                  # Required: SemVer
type: subtask                     # Required: Always "subtask"
status: pending                   # Required: pending|in_progress|completed
created: YYYY-MM-DD               # Required
updated: YYYY-MM-DD               # Required

# Hierarchy
parent: "TASK-XXX"                # Required: Parent task
children: []                      # Subtasks have no children

# Dependencies
blockedBy: []                     # Other subtasks in same task
blocks: []                        # Subtasks this unblocks

# Ownership
owner: "staff-engineer-1"         # Usually same as parent task
domain: "backend"                 # Inherited from parent

# Sizing
size: "XS"                        # XS or S only
agentHours: 0.5                   # 0.5-2 hours max

# Claude Code fields
subject: "Create jwt.ts module"
activeForm: "Creating jwt.ts module"

# Metadata
tags: []
---
```

## Body Structure

```markdown
# [Subtask Title]

## What
[Single clear objective]

## How
[Implementation steps]

## Files
- `path/to/file.ts` - Action

## Done When
[Single verification criterion]
```

## Example

```yaml
---
id: "SUBTASK-008"
version: "1.0.0"
type: subtask
status: completed
created: 2025-02-11
updated: 2025-02-11

parent: "TASK-004"
children: []

blockedBy: []
blocks:
  - "SUBTASK-009"  # Tests need the module

owner: "staff-engineer-2"
domain: "backend"

size: "XS"
agentHours: 1

subject: "Create jwt.ts with generateToken"
activeForm: "Creating jwt.ts with generateToken"

tags: ["jwt"]
---

# Create jwt.ts with generateToken

## What
Create the JWT generation utility module.

## How
1. Create `src/auth/jwt.ts`
2. Import jsonwebtoken
3. Load secret from env
4. Implement `generateToken(user: User): string`
5. Implement `generateRefreshToken(user: User): string`

## Files
- `src/auth/jwt.ts` - Create

## Done When
`generateToken({ id: '1', email: 'test@example.com' })` returns valid JWT string
```

## When to Use Subtasks

### Use Subtasks When
- Task is L or XL size
- Clear sequential steps
- Want checkpoint tracking
- Multiple files need atomic commits

### Don't Use Subtasks When
- Task is XS, S, or M
- Work is naturally atomic
- Overhead of tracking exceeds benefit

## Agent Workflow

```javascript
// Staff Engineer working on parent task
// Creates subtask tracking in Claude Code

TaskCreate({
  subject: "Create jwt.ts with generateToken",
  description: "Part of TASK-004. Create src/auth/jwt.ts...",
  activeForm: "Creating jwt.ts with generateToken"
})

// Work on subtask...

TaskUpdate({ taskId: "id", status: "completed" })

// Continue to next subtask
TaskCreate({
  subject: "Write JWT unit tests",
  description: "Part of TASK-004. Tests for src/auth/jwt.ts...",
  activeForm: "Writing JWT unit tests"
})
```

## Size Limits

Subtasks must be **XS or S** only:

| Size | Hours | Scope |
|------|-------|-------|
| XS | 0.5-1 | Single file, single function |
| S | 1-2 | 2-3 files, simple feature |

If a subtask seems larger, it should be a Task instead.
