# Story Entity Schema

> User-facing feature that delivers value

## Frontmatter

```yaml
---
id: "STORY-XXX"                   # Required: Unique identifier
version: "1.0.0"                  # Required: SemVer
type: story                       # Required: Always "story"
status: pending                   # Required: pending|in_progress|completed|blocked
created: YYYY-MM-DD               # Required
updated: YYYY-MM-DD               # Required

# Hierarchy
parent: "EPIC-XXX"                # Required: Parent epic
children: []                      # Task IDs

# Dependencies
dependsOn: []                     # External dependencies
blocks: []                        # What this story blocks
blockedBy: []                     # Internal: sibling stories

# Ownership
owner: "sdm-backend"              # SDM owns stories
domain: "backend"                 # frontend|backend|infra|data

# Planning
priority: "P1-high"               # P0-P4
iteration: "iteration-5"          # Assigned iteration
size: "L"                         # Aggregate size: XS|S|M|L|XL

# Sizing
estimatedTasks: 4                 # Number of tasks expected
agentHours: 12                    # Total estimated hours

# Metrics
completedTasks: 0                 # Tasks completed
actualAgentHours: 0               # Actual hours spent

# Metadata
tags: []
acceptanceCriteria: []            # AC list
---
```

## Body Structure

```markdown
# [Story Title]

## User Story
As a [persona], I want [feature], so that [benefit].

## Acceptance Criteria
<!-- Rendered from acceptanceCriteria array -->
- [ ] AC 1
- [ ] AC 2

## Technical Notes
[Implementation guidance for SDM/Staff Engineers]

## Tasks
<!-- Auto-populated from children -->

## Dependencies
<!-- External dependencies -->

## Test Plan
[How to verify this story is complete]
```

## Example

```yaml
---
id: "STORY-002"
version: "1.1.0"
type: story
status: in_progress
created: 2025-02-05
updated: 2025-02-11

parent: "EPIC-001"
children:
  - "TASK-003"
  - "TASK-004"
  - "TASK-005"

dependsOn:
  - "npm:bcrypt@5.1"
  - "STORY-001"  # Registration must be done

blocks:
  - "STORY-003"  # Session management needs login

owner: "sdm-backend"
domain: "backend"

priority: "P1-high"
iteration: "iteration-5"
size: "L"

estimatedTasks: 4
agentHours: 12
completedTasks: 1
actualAgentHours: 4

tags: ["auth", "api"]
acceptanceCriteria:
  - "User can login with email/password"
  - "Invalid credentials return 401"
  - "Successful login returns JWT token"
  - "Login attempts are rate-limited"
---

# User Login Flow

## User Story
As a registered user, I want to login with my credentials, so that I can access my account.

## Acceptance Criteria
- [ ] User can login with email/password
- [ ] Invalid credentials return 401
- [ ] Successful login returns JWT token
- [ ] Login attempts are rate-limited (5/minute)

## Technical Notes
- Use bcrypt for password comparison
- JWT should expire in 7 days
- Store refresh token in httpOnly cookie
- Log failed attempts for security monitoring

## Tasks
- TASK-003: POST /auth/login endpoint (completed)
- TASK-004: JWT token generation (in_progress)
- TASK-005: Rate limiting middleware (pending)
- TASK-006: Integration tests (pending)

## Dependencies
- bcrypt@5.1 - Password hashing
- jsonwebtoken@9 - JWT generation
- STORY-001 - User registration (users must exist)

## Test Plan
1. Login with valid credentials → 200 + JWT
2. Login with invalid password → 401
3. Login with non-existent email → 401
4. 6th login attempt in 1 minute → 429
```

## Agent Usage

SDMs create stories from epics:

```bash
# In Claude Code, SDM creates task to track story work
TaskCreate with:
  subject: "Implement STORY-002 login flow"
  description: "Break down into tasks, assign to Staff Engineers"
  activeForm: "Implementing login flow"
```
