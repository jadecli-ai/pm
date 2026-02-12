# Epic Entity Schema

> Strategic initiative spanning multiple iterations

## Frontmatter

```yaml
---
id: "EPIC-XXX"                    # Required: Unique identifier
version: "1.0.0"                  # Required: SemVer
type: epic                        # Required: Always "epic"
status: pending                   # Required: pending|in_progress|completed|blocked
created: YYYY-MM-DD               # Required: Creation date
updated: YYYY-MM-DD               # Required: Last modification

# Hierarchy
parent: null                      # Epics have no parent
children: []                      # Story IDs

# Dependencies
dependsOn: []                     # External dependencies (other epics, systems)
blocks: []                        # What this epic blocks

# Ownership
owner: "vp-product"               # VP PM owns epics
domain: null                      # null for cross-domain, or specific domain

# Planning
priority: "P1-high"               # P0-P4
targetIteration: "2025-Q1"        # Target completion
estimatedStories: 5               # Number of stories expected

# Metrics
completedStories: 0               # Stories completed
totalAgentHours: 0                # Sum of all child task hours

# Metadata
tags: []
businessValue: null               # Optional: ROI or strategic value
risks: []                         # Identified risks
---
```

## Body Structure

```markdown
# [Epic Title]

## Problem Statement
[What problem does this solve?]

## Success Criteria
- [ ] Measurable outcome 1
- [ ] Measurable outcome 2

## Scope

### In Scope
- Feature A
- Feature B

### Out of Scope
- Excluded item

## Stories
<!-- Auto-populated from children -->

## Dependencies
<!-- Rendered from dependsOn -->

## Risks
<!-- Expanded from risks array -->

## Notes
<!-- Additional context -->
```

## Example

```yaml
---
id: "EPIC-001"
version: "1.2.0"
type: epic
status: in_progress
created: 2025-02-01
updated: 2025-02-11

children:
  - "STORY-001"
  - "STORY-002"
  - "STORY-003"

dependsOn:
  - "EPIC-000"  # Foundation epic must be done

owner: "vp-product"
domain: null

priority: "P1-high"
targetIteration: "2025-Q1"
estimatedStories: 5
completedStories: 2
totalAgentHours: 48

tags: ["authentication", "security"]
businessValue: "Enable user accounts, required for monetization"
risks:
  - "OAuth provider rate limits"
  - "Session management complexity"
---

# User Authentication System

## Problem Statement
Users cannot create accounts or maintain sessions, blocking all personalization features.

## Success Criteria
- [ ] Users can register with email
- [ ] Users can login/logout
- [ ] Sessions persist across browser refresh
- [ ] OAuth integration with GitHub

## Scope

### In Scope
- Email/password auth
- GitHub OAuth
- JWT sessions
- Password reset flow

### Out of Scope
- Other OAuth providers (Google, Apple)
- Two-factor authentication
- Enterprise SSO

## Stories
- STORY-001: User Registration (completed)
- STORY-002: User Login (in_progress)
- STORY-003: Session Management (pending)

## Risks
1. **OAuth rate limits**: GitHub API has aggressive rate limiting
   - Mitigation: Implement token caching
```

## Agent Usage

VP Product creates and manages epics:

```bash
# Create epic in Claude Code
TaskCreate with:
  subject: "Create EPIC-002 for payment system"
  description: "Design epic for Stripe integration..."
```

SDMs break epics into stories during iteration planning.
