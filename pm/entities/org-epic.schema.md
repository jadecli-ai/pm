---
id: "SCHEMA-ORG-EPIC"
version: "1.0.0"
type: schema
status: active
created: 2026-02-11
updated: 2026-02-11
dependsOn:
  - "entities/epic.schema.md"
dependedBy:
  - "entities/repo-sprint.schema.md"
---

# Org-Level Epic Schema

> Strategic initiatives that span multiple repositories within the jadecli-ai organization.

## Overview

Org-level epics are the highest-level work items. They represent cross-repo initiatives that require coordination across `team-agents-sdk`, `pm`, and future repositories.

**Key Principle**: Think at the org level (`jadecli-ai`), execute at the repo level.

## YAML Frontmatter

```yaml
---
id: "ORG-EPIC-001"              # Unique ID with ORG-EPIC prefix
version: "1.0.0"                 # SemVer (MAJOR for scope, MINOR for progress)
type: org-epic                   # Entity type
status: pending | in_progress | completed | blocked
created: 2026-02-11              # ISO date
updated: 2026-02-11              # Last modified

# Ownership
owner: "vp-product"              # VP PM owns org-level epics
organization: "jadecli-ai"       # GitHub org

# Repository Scope
repos:                           # Which repos are involved
  - name: "team-agents-sdk"
    role: primary | supporting   # Primary = main implementation
    sprints:                     # Sprints created for this repo
      - "SPRINT-001"
  - name: "pm"
    role: supporting
    sprints:
      - "SPRINT-002"

# Timeline
targetIteration: 6               # Target completion iteration
startIteration: 4                # When work began

# Dependencies (org-level)
dependsOn:                       # Other org-epics this depends on
  - "ORG-EPIC-000"
blockedBy:                       # Blocking org-epics
  - []
blocks:                          # What this blocks
  - []

# Metrics
progress: 0.35                   # 0.0 to 1.0
totalStoryPoints: 89             # Sum across all repos
completedPoints: 31              # Points completed

# GitHub Integration
githubProject: "jadecli-ai/projects/1"  # Org-level project board
labels:
  - "org-epic"
  - "cross-repo"
---
```

## Body Structure

```markdown
# [ORG-EPIC-XXX] Epic Title

## Vision
One-paragraph description of what this epic achieves across the organization.

## Success Criteria
- [ ] Criterion 1 (measurable outcome)
- [ ] Criterion 2 (measurable outcome)
- [ ] Criterion 3 (measurable outcome)

## Repository Breakdown

### team-agents-sdk
- **Role**: Primary implementation
- **Scope**: Core SDK changes, database schema, API endpoints
- **Sprints**: SPRINT-001, SPRINT-003

### pm
- **Role**: Supporting
- **Scope**: Agent definitions, entity schemas, documentation
- **Sprints**: SPRINT-002

## Architecture Decisions

### Decision 1: [Title]
- **Context**: Why this decision is needed
- **Decision**: What was decided
- **Consequences**: Impact on repos

## Risks
1. [Risk] - [Mitigation]
2. [Risk] - [Mitigation]

## Notes
Additional context, links to research, references.
```

## Examples

### ORG-EPIC-001: Agent Teams Task Tracking

```yaml
---
id: "ORG-EPIC-001"
version: "1.2.0"
type: org-epic
status: in_progress
created: 2026-02-11
updated: 2026-02-11
owner: "vp-product"
organization: "jadecli-ai"
repos:
  - name: "team-agents-sdk"
    role: primary
    sprints: ["SPRINT-001", "SPRINT-003"]
  - name: "pm"
    role: supporting
    sprints: ["SPRINT-002"]
targetIteration: 6
startIteration: 4
dependsOn: []
blockedBy: []
blocks: []
progress: 0.35
totalStoryPoints: 89
completedPoints: 31
githubProject: "jadecli-ai/projects/1"
labels: ["org-epic", "agent-teams"]
---

# [ORG-EPIC-001] Agent Teams Task Tracking

## Vision
Enable Claude Code agent teams to persist task state to Neon database with MLflow tracing, providing visibility into agent work across all jadecli-ai repos.

## Success Criteria
- [ ] Task state persists to Neon with real-time sync
- [ ] MLflow traces capture all agent operations
- [ ] Dashboard shows live task status across repos
- [ ] Agent teams can resume work after session restart
```

## Agent Team Limitations Addressed

This schema addresses Claude Code agent team limitations:

| Limitation | Mitigation |
|------------|------------|
| No session resumption | Persist task state to Neon; agents read state on spawn |
| Task status can lag | Hooks auto-sync entity status to Neon |
| One team per session | Org-epic tracks work across sessions |
| Lead is fixed | VP Product agent reads org-epic state on startup |

## Org-Level Thinking Principles

1. **Epics span repos** - Work flows across team-agents-sdk and pm
2. **Sprints are repo-specific** - Each repo has its own sprint cadence
3. **GitHub Projects at org level** - Single board for cross-repo visibility
4. **VP Product owns org-epics** - SDMs own repo-specific sprints
