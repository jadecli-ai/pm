# jadecli Product Management - Agent Team Entry Point

> Single entry point for starting Claude Code agent-driven development

## Quick Start

```bash
# Start the PM agent team for an iteration
claude --agent ~/projects/.claude-org/pm/agents/vp-product.md
```

Then in Claude Code:
```
Start iteration planning for [project].
Spawn SDM agents for Frontend, Backend, and Infrastructure.
Review backlog and assign work.
```

## Agent Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│                  VP Product (Opus 4.6)                  │
│         Roadmap • Prioritization • Coordination         │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ SDM Frontend  │   │ SDM Backend   │   │ SDM Infra     │
│  (Opus 4.6)   │   │  (Opus 4.6)   │   │  (Opus 4.6)   │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
   ┌────┼────┐         ┌────┼────┐         ┌────┼────┐
   ▼    ▼    ▼         ▼    ▼    ▼         ▼    ▼    ▼
 ┌───┐┌───┐┌───┐     ┌───┐┌───┐┌───┐     ┌───┐┌───┐┌───┐
 │SE1││SE2││SE3│     │SE1││SE2││SE3│     │SE1││SE2││SE3│
 └───┘└───┘└───┘     └───┘└───┘└───┘     └───┘└───┘└───┘
   Staff Engineers (Opus 4.6) - 9 total across domains

                    ┌───────────────┐
                    │ Sprint Master │
                    │  (Opus 4.6)   │
                    │ Coordinates   │
                    └───────────────┘
```

## Iteration Flow

### Monday: Planning
```
VP PM: "Create iteration #N milestone, review P1 items, assign to SDMs"
     │
     ├── SDM Frontend: receives UI tasks
     ├── SDM Backend: receives API tasks
     └── SDM Infra: receives DevOps tasks
```

### Tue-Thu: Execution
```
SDMs: spawn Staff Engineers, monitor progress, review PRs
     │
     ├── SE1: implements feature A
     ├── SE2: implements feature B
     └── SE3: implements feature C

Sprint Master: tracks burndown, escalates blockers
```

### Friday: Demo + Retro
```
Sprint Master: "Facilitate demo, run retrospective"
     │
     ├── SDMs: demo completed work
     ├── VP PM: accept/reject items
     └── Team: identify improvements
```

## Capacity Model

| Role | Model | Concurrent | Hours/Day | Agent-Hours/Week |
|------|-------|------------|-----------|------------------|
| VP PM | Opus 4.6 | 1 | 2 | 10 |
| SDM × 3 | Opus 4.6 | 3 | 4 | 60 |
| Staff Eng × 9 | Opus 4.6 | 6* | 8 | 240 |
| Sprint Master | Opus 4.6 | 1 | 1 | 5 |

*6 concurrent due to WezTerm 6-pane grid

**Total Weekly Capacity**: ~315 agent-hours

## Estimation Formula

```
Story Points → Agent-Hours

XS (1 pt)  = 0.5-1 agent-hours
S  (2 pt)  = 1-2 agent-hours
M  (3 pt)  = 2-4 agent-hours
L  (5 pt)  = 4-8 agent-hours
XL (8 pt)  = 8-16 agent-hours
XXL (13 pt) = Split into smaller items
```

**Iteration Capacity**: ~200 agent-hours (accounting for overhead)
**Velocity Target**: 80-100 story points per iteration

## GitHub Project Setup

Create an **Iterative Development** project with these columns:

| Column | Purpose |
|--------|---------|
| **Backlog** | All prioritized items (P0-P4) |
| **Iteration N** | Committed items for current iteration |
| **In Progress** | Active work |
| **In Review** | Awaiting code review |
| **Done** | Completed and merged |

### Required Fields

| Field | Type | Values |
|-------|------|--------|
| Priority | Single select | P0-critical, P1-high, P2-medium, P3-low, P4-someday |
| Size | Single select | XS, S, M, L, XL |
| Domain | Single select | Frontend, Backend, Infrastructure, Data |
| Iteration | Iteration | Current + next 2 |
| Assignee | Person | SDM responsible |

### Automation

- When PR merged → Move to Done
- When PR opened → Move to In Review
- When started → Move to In Progress

## WezTerm Integration

Launch 6-pane agent grid:
```bash
# Press Ctrl+A Ctrl+6 in WezTerm
# Or use the alias:
cg6
```

Pane Layout:
```
┌─────────────┬─────────────┬─────────────┐
│ VP PM/SDM   │ Staff Eng 1 │ Staff Eng 2 │
├─────────────┼─────────────┼─────────────┤
│ Staff Eng 3 │ Tester      │ Reviewer    │
└─────────────┴─────────────┴─────────────┘
```

## Example Iteration

### Iteration Goals
```markdown
## Iteration 5: Authentication System

### Committed Items (45 points)
- [ ] [L] User login flow (#123) - Backend
- [ ] [M] Login form UI (#124) - Frontend
- [ ] [M] JWT middleware (#125) - Backend
- [ ] [S] Password hashing (#126) - Backend
- [ ] [M] Session management (#127) - Backend
- [ ] [S] Auth tests (#128) - Backend
- [ ] [L] OAuth integration (#129) - Backend
- [ ] [M] CI pipeline for auth (#130) - Infra

### Capacity
- Frontend: 1 SDM + 3 SE = 40 agent-hours
- Backend: 1 SDM + 3 SE = 40 agent-hours
- Infra: 1 SDM + 3 SE = 40 agent-hours
- Buffer: 20%
```

## Dogfooding Anthropic

Always ask:
1. Would Anthropic use this approach?
2. Are we maximizing Claude Code capabilities?
3. Is this automatable vs manual?
4. Does this scale?

### Anthropic Engineering Principles
- Ship fast, iterate faster
- Measure everything
- Automate repetitive work
- Documentation is essential
- Tests are non-negotiable
- Security by default
