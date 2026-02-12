---
id: "SCHEMA-REPO-SPRINT"
version: "1.0.0"
type: schema
status: active
created: 2026-02-11
updated: 2026-02-11
dependsOn:
  - "entities/org-epic.schema.md"
  - "entities/task.schema.md"
dependedBy:
  - "entities/examples/"
---

# Repo-Specific Sprint Schema

> Time-boxed iteration of work scoped to a single repository.

## Overview

Sprints are repo-specific groupings of tasks that contribute to an org-level epic. Each repo has independent sprints that can be planned and executed by that repo's SDM.

**Key Principle**: Sprints execute at repo level, epics coordinate at org level.

## YAML Frontmatter

```yaml
---
id: "SPRINT-001"                 # Unique ID with SPRINT prefix
version: "1.0.0"                 # SemVer
type: sprint                     # Entity type
status: planned | active | completed | cancelled

# Ownership
owner: "sdm-backend"             # SDM owns the sprint
repo: "team-agents-sdk"          # Single repo scope
organization: "jadecli-ai"       # GitHub org

# Parent Epic
parentEpic: "ORG-EPIC-001"       # Which org-epic this contributes to

# Timeline
iteration: 5                     # Iteration number
startDate: 2026-02-10            # Sprint start
endDate: 2026-02-14              # Sprint end (typically 1 week)

# Capacity
capacityHours: 120               # Total agent-hours available
allocatedHours: 98               # Hours allocated to tasks
bufferPercent: 20                # Buffer for unexpected work

# Tasks
tasks:                           # Tasks in this sprint
  - id: "TASK-001"
    status: completed
    points: 5
  - id: "TASK-002"
    status: in_progress
    points: 3
  - id: "TASK-003"
    status: pending
    points: 8

# Metrics
velocity: 35                     # Story points per sprint (rolling avg)
completedPoints: 5               # Points done this sprint
totalPoints: 16                  # Total points committed
burndownRate: 0.8                # Actual vs planned rate

# Dependencies
dependsOn:                       # Other sprints this depends on
  - "SPRINT-000"                 # Cross-repo sprint dependency
blockedBy: []
blocks: []

# GitHub Integration
milestone: "Iteration 5"         # GitHub milestone
labels:
  - "sprint-5"
  - "backend"
---
```

## Body Structure

```markdown
# [SPRINT-XXX] Sprint Title

## Goal
One sentence describing what this sprint achieves for the parent epic.

## Committed Items

| ID | Title | Size | Owner | Status |
|----|-------|------|-------|--------|
| TASK-001 | Implement JWT hooks | L | staff-eng-1 | completed |
| TASK-002 | Add MLflow tracing | M | staff-eng-2 | in_progress |
| TASK-003 | Create Neon tables | XL | staff-eng-3 | pending |

## Capacity

- **Available**: 120 agent-hours (3 Staff Engineers × 40 hours)
- **Allocated**: 98 agent-hours (82%)
- **Buffer**: 22 agent-hours (18%)

## Daily Progress

### Day 1 (Mon)
- [x] Sprint planning complete
- [x] TASK-001 started
- [ ] Blocked: waiting on schema review

### Day 2 (Tue)
- [x] TASK-001 completed
- [x] TASK-002 started

## Blockers
1. [BLOCKER] Schema migration not approved → Escalate to VP PM

## Retrospective
(Filled at sprint end)

### What Went Well
-

### What Could Improve
-

### Action Items
-
```

## Examples

### SPRINT-001: team-agents-sdk Hooks Integration

```yaml
---
id: "SPRINT-001"
version: "1.1.0"
type: sprint
status: active
owner: "sdm-backend"
repo: "team-agents-sdk"
organization: "jadecli-ai"
parentEpic: "ORG-EPIC-001"
iteration: 5
startDate: 2026-02-10
endDate: 2026-02-14
capacityHours: 120
allocatedHours: 98
bufferPercent: 20
tasks:
  - id: "TASK-001"
    status: completed
    points: 5
  - id: "TASK-002"
    status: in_progress
    points: 3
  - id: "TASK-003"
    status: pending
    points: 8
velocity: 35
completedPoints: 5
totalPoints: 16
burndownRate: 0.8
dependsOn: []
blockedBy: []
blocks: ["SPRINT-002"]
milestone: "Iteration 5"
labels: ["sprint-5", "backend", "hooks"]
---

# [SPRINT-001] Hooks Integration Sprint

## Goal
Implement Claude Agent SDK hooks that persist task events to Neon database.
```

## Sprint-Epic Relationship

```
jadecli-ai (org)
├── ORG-EPIC-001: Agent Teams Task Tracking
│   │
│   ├── team-agents-sdk (repo)
│   │   ├── SPRINT-001: Hooks Integration
│   │   │   ├── TASK-001: Implement PreToolUse hook
│   │   │   ├── TASK-002: Add MLflow span context
│   │   │   └── TASK-003: Create activities table
│   │   └── SPRINT-003: Dashboard Integration
│   │
│   └── pm (repo)
│       └── SPRINT-002: Entity Schemas
│           ├── TASK-004: Define org-epic schema
│           └── TASK-005: Add sprint tracking
```

## Agent Team Limitations Addressed

| Limitation | Sprint-Level Mitigation |
|------------|-------------------------|
| Task status can lag | Sprint tracks independent task status |
| No session resumption | Sprint state persists in markdown |
| One team per session | Each sprint can have its own team |
| No nested teams | SDM spawns flat team for sprint |

## Workflow

1. **VP PM** creates org-epic, identifies involved repos
2. **SDM** creates repo-specific sprint linked to epic
3. **SDM** breaks sprint into tasks, spawns Staff Engineers
4. **Staff Engineers** execute tasks, update status
5. **Sprint Master** tracks burndown, escalates blockers
6. **SDM** closes sprint, reports to VP PM
7. **VP PM** updates org-epic progress

## GitHub Integration

```bash
# Create sprint milestone
gh api repos/jadecli-ai/team-agents-sdk/milestones \
  -f title="Iteration 5" \
  -f due_on="2026-02-14T23:59:59Z"

# Link tasks to sprint
gh issue edit TASK-001 --milestone "Iteration 5"
```
