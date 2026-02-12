# jadecli Product Management System

> Agent-driven iterative development using Claude Code

## Overview

This is the single entry point for running Claude Code agent teams as a product organization. Instead of human engineers, all development is done by Claude Code agents organized into a hierarchy:

```
VP Product (Opus 4.5) ─── Strategy, Prioritization
    │
    ├── SDM Frontend (Sonnet) ─── UI/UX development
    ├── SDM Backend (Sonnet) ─── API/Services development
    ├── SDM Infrastructure (Sonnet) ─── DevOps/Tooling
    │       │
    │       └── Staff Engineers (Sonnet × 3 each)
    │
    └── Sprint Master (Haiku) ─── Ceremonies, Tracking
```

## Quick Start

```bash
# Start VP Product agent
claude --agent ~/projects/.claude-org/pm/agents/vp-product.md

# Or use the full entry point docs
cat ~/projects/.claude-org/pm/ENTRYPOINT.md
```

## Files

| File | Purpose |
|------|---------|
| `ENTRYPOINT.md` | Complete guide to starting agent teams |
| `agents/vp-product.md` | VP Product Management agent |
| `agents/sdm.md` | Software Development Manager agent |
| `agents/staff-engineer.md` | Staff Engineer agent |
| `agents/sprint-master.md` | Sprint Master agent |
| `scripts/setup-github-project.sh` | GitHub project setup |

## Iteration Workflow

| Day | Activity | Agents |
|-----|----------|--------|
| Monday | Planning | VP PM + SDMs |
| Tue-Thu | Execution | SDMs + Staff Eng |
| Friday | Demo + Retro | All |

## Capacity

- **6 concurrent agents** (WezTerm 6-pane grid)
- **~200 agent-hours/iteration** (1 week)
- **80-100 story points/iteration** target velocity

## GitHub Project

Use **Iterative Development** template with:
- Priority labels (P0-P4)
- Size labels (XS-XL)
- Domain labels (Frontend/Backend/Infra/Data)
- Iteration milestones

Run setup script:
```bash
~/projects/.claude-org/pm/scripts/setup-github-project.sh <github-user>
```

## Dogfooding Principles

1. Build with Claude Code, not manual engineering
2. Iterate rapidly, ship early
3. Document everything
4. Measure and improve
5. Automate repetitive work
