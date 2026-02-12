# Task Entity Schema

> Implementation unit - **Aligned with Claude Code TaskCreate**

## Claude Code Integration

This entity maps directly to Claude Code's built-in task system:

| Entity Field | TaskCreate Param | TaskUpdate Param |
|--------------|------------------|------------------|
| `subject` | `subject` | `subject` |
| `description` | `description` | `description` |
| `activeForm` | `activeForm` | `activeForm` |
| `status` | (created as pending) | `status` |
| `blockedBy` | - | `addBlockedBy` |
| `blocks` | - | `addBlocks` |
| `owner` | - | `owner` |

## Frontmatter

```yaml
---
id: "TASK-XXX"                    # Required: Unique identifier
version: "1.0.0"                  # Required: SemVer
type: task                        # Required: Always "task"
status: pending                   # Required: pending|in_progress|completed|blocked
created: YYYY-MM-DD               # Required
updated: YYYY-MM-DD               # Required

# Hierarchy
parent: "STORY-XXX"               # Required: Parent story
children: []                      # Subtask IDs (optional)

# Dependencies
dependsOn: []                     # Code/external dependencies
blocks: []                        # Tasks this unblocks
blockedBy: []                     # Tasks blocking this

# Ownership
owner: "staff-engineer-1"         # Staff Engineer assigned
domain: "backend"                 # frontend|backend|infra|data

# Planning
priority: "P1-high"               # P0-P4
iteration: "iteration-5"          # Assigned iteration
size: "M"                         # XS|S|M|L|XL

# Sizing (aligned with ENTRYPOINT.md)
agentHours: 3                     # Estimated: XS=0.5-1, S=1-2, M=2-4, L=4-8, XL=8-16

# Claude Code TaskCreate fields (for agent use)
subject: "Implement JWT generation"        # Brief imperative title
activeForm: "Implementing JWT generation"  # Present continuous for spinner

# Metadata
tags: []
---
```

## Body Structure (description field)

```markdown
# [Task Title]

## Objective
[What this task accomplishes]

## Acceptance Criteria
- [ ] AC 1
- [ ] AC 2

## Implementation Notes
[Technical details, approach, files to modify]

## Files
- `src/auth/jwt.ts` - Create
- `src/middleware/auth.ts` - Modify

## Dependencies
<!-- Code dependencies -->
- jsonwebtoken@9

## Subtasks
<!-- Optional breakdown -->

## Test Requirements
[What tests to write]
```

## Example

```yaml
---
id: "TASK-004"
version: "1.0.0"
type: task
status: in_progress
created: 2025-02-10
updated: 2025-02-11

parent: "STORY-002"
children:
  - "SUBTASK-008"
  - "SUBTASK-009"

dependsOn:
  - "npm:jsonwebtoken@9.0"
  - "TASK-003"  # Login endpoint must exist

blocks:
  - "TASK-005"  # Rate limiting needs JWT

blockedBy: []

owner: "staff-engineer-2"
domain: "backend"

priority: "P1-high"
iteration: "iteration-5"
size: "M"
agentHours: 3

subject: "Implement JWT token generation"
activeForm: "Implementing JWT token generation"

tags: ["auth", "jwt", "security"]
---

# Implement JWT Token Generation

## Objective
Create JWT token generation utility for user authentication.

## Acceptance Criteria
- [ ] generateToken(user) returns signed JWT
- [ ] Token contains user ID, email, roles
- [ ] Token expires in 7 days
- [ ] Refresh token generated separately
- [ ] Secret loaded from environment

## Implementation Notes
- Use RS256 algorithm with key pair
- Store public key for verification
- Token payload: { sub, email, roles, iat, exp }

## Files
- `src/auth/jwt.ts` - Create: Token generation
- `src/auth/keys.ts` - Create: Key management
- `src/types/auth.ts` - Modify: Add token types
- `tests/auth/jwt.test.ts` - Create: Unit tests

## Dependencies
- jsonwebtoken@9.0 - JWT library
- TASK-003 - Login endpoint (provides user data)

## Subtasks
- SUBTASK-008: Create jwt.ts with generateToken
- SUBTASK-009: Write unit tests

## Test Requirements
- Token can be decoded
- Token contains correct claims
- Expired token fails verification
- Invalid signature fails verification
```

## Agent Usage

### Staff Engineer Starting Task

```javascript
// When Staff Engineer picks up task, use TaskUpdate
TaskUpdate({
  taskId: "claude-task-id",
  status: "in_progress",
  owner: "staff-engineer-2"
})
```

### Creating Task from Entity

```javascript
// SDM creates Claude Code task from entity
TaskCreate({
  subject: "Implement JWT token generation",  // From entity.subject
  description: `
    ## Objective
    Create JWT token generation utility...

    See: pm/entities/examples/TASK-004.md
  `,
  activeForm: "Implementing JWT token generation"  // From entity.activeForm
})
```

### Completing Task

```javascript
// Staff Engineer completes task
TaskUpdate({
  taskId: "claude-task-id",
  status: "completed"
})

// Then update entity version
// TASK-004 version: "1.0.0" -> "1.0.1" (patch: completed)
```

## Size Guidelines

| Size | Agent-Hours | Complexity | Examples |
|------|-------------|------------|----------|
| XS | 0.5-1 | Single function, config change | Add env var, fix typo |
| S | 1-2 | Small feature, simple test | Add validation, single endpoint |
| M | 2-4 | Moderate feature | JWT utils, middleware |
| L | 4-8 | Complex feature | OAuth flow, caching layer |
| XL | 8-16 | Large feature (consider splitting) | Full CRUD resource |
