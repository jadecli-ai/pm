---
id: "FR-001"
version: "1.0.0"
type: feature-recommendation
status: proposed
created: 2026-02-11
updated: 2026-02-11
author: "steering-orchestrator"
priority: P1-high
labels:
  - "documentation"
  - "developer-experience"
  - "steering"
---

# FR-001: Steering System Usage Guides

> Deterministic developer navigation index for budget-aware agent execution

## Summary

Create a `/usage-guides/developer/` directory with monotonically increasing index entries that map features to navigation paths and Claude Code prompts. This enables developers to quickly discover, navigate to, and activate steering system features.

---

## Usage Guide Index

### Root Structure

```
jadecli-ai/                              # GitHub Organization root
└── .claude-org/                         # This repo: jadecli-ai/.claude-org
```

### Monotonic Feature Index

| IDX | Feature | Path | Claude Code Prompt |
|-----|---------|------|-------------------|
| 001 | Budget Tracker | `.claude-org/steering/lib/budget_tracker.py` | `@steering-orchestrator Track my budget for this session` |
| 002 | Handoff Generator | `.claude-org/steering/lib/handoff_generator.py` | `@steering-orchestrator Generate handoff document` |
| 003 | Model Budgets Config | `.claude-org/steering/config/budgets.yaml` | `Read steering/config/budgets.yaml and explain token limits` |
| 004 | Wrap-up Thresholds | `.claude-org/steering/config/thresholds.yaml` | `What are the wrap-up thresholds for agents?` |
| 005 | Steering Orchestrator Agent | `.claude-org/pm/agents/steering-orchestrator.md` | `claude --agent pm/agents/steering-orchestrator.md` |
| 006 | Team Template System | `.claude-org/templates/create-team.py` | `python3 templates/create-team.py --help` |
| 007 | Backend Engineering Team | `.claude-org/teams/backend-engineering/` | `claude --agent teams/backend-engineering/agents/backend-engineering-lead.md` |
| 008 | Prompt Adapter | `.claude-org/pm/lib/prompt_adapter.py` | `python3 pm/lib/prompt_adapter.py "fix the auth bug"` |
| 009 | Chain Detector | `.claude-org/pm/lib/chain_detector.py` | `python3 pm/lib/chain_detector.py "continue the research"` |
| 010 | Org-Epic Schema | `.claude-org/pm/entities/org-epic.schema.md` | `Create an org-epic following pm/entities/org-epic.schema.md` |
| 011 | Repo-Sprint Schema | `.claude-org/pm/entities/repo-sprint.schema.md` | `Create a sprint following pm/entities/repo-sprint.schema.md` |
| 012 | /ask Command | `.claude-org/pm/.claude/commands/ask.md` | `/ask add user authentication to the API` |

---

## Navigation Guide

### 001: Budget Tracker

**Path**: `jadecli-ai/.claude-org/steering/lib/budget_tracker.py`

**Navigate**:
```bash
cd ~/projects/.claude-org
code steering/lib/budget_tracker.py
```

**Claude Code Prompt**:
```
Read steering/lib/budget_tracker.py and create a BudgetTracker
for my current session using claude-opus-4-5-20251101
```

**Expected Output**: Budget state with turn/token ratios and phase detection.

---

### 002: Handoff Generator

**Path**: `jadecli-ai/.claude-org/steering/lib/handoff_generator.py`

**Navigate**:
```bash
cd ~/projects/.claude-org
code steering/lib/handoff_generator.py
```

**Claude Code Prompt**:
```
I'm at 80% budget. Use HandoffGenerator from steering/lib/handoff_generator.py
to create a handoff document for my current task.
```

**Expected Output**: YAML or XML handoff document with completed/incomplete items.

---

### 003: Model Budgets Config

**Path**: `jadecli-ai/.claude-org/steering/config/budgets.yaml`

**Navigate**:
```bash
cat ~/projects/.claude-org/steering/config/budgets.yaml
```

**Claude Code Prompt**:
```
What's the token budget for Sonnet 4.5 according to steering/config/budgets.yaml?
```

**Expected Output**: Token budget (160K), default turns (15), cost per 1K tokens.

---

### 004: Wrap-up Thresholds

**Path**: `jadecli-ai/.claude-org/steering/config/thresholds.yaml`

**Navigate**:
```bash
cat ~/projects/.claude-org/steering/config/thresholds.yaml
```

**Claude Code Prompt**:
```
When should I start wrapping up my work according to the steering thresholds?
```

**Expected Output**: Warning at 70%, wrap-up at 80%, critical at 90%.

---

### 005: Steering Orchestrator Agent

**Path**: `jadecli-ai/.claude-org/pm/agents/steering-orchestrator.md`

**Navigate**:
```bash
cd ~/projects/.claude-org
```

**Claude Code Prompt**:
```bash
claude --agent pm/agents/steering-orchestrator.md

# Then in session:
Research the best approach for implementing WebSocket support in our API.
Track your budget and generate a handoff when you reach 80%.
```

**Expected Output**: Deep research with budget tracking and handoff at 80%.

---

### 006: Team Template System

**Path**: `jadecli-ai/.claude-org/templates/create-team.py`

**Navigate**:
```bash
cd ~/projects/.claude-org
```

**Claude Code Prompt**:
```
Create a new team called "Frontend Engineering" using templates/create-team.py
with Sonnet for the lead and Haiku for the tester.
```

**Expected Output**: New team directory at `teams/frontend-engineering/` with agents.

---

### 007: Backend Engineering Team

**Path**: `jadecli-ai/.claude-org/teams/backend-engineering/`

**Navigate**:
```bash
cd ~/projects/.claude-org/teams/backend-engineering
```

**Claude Code Prompt**:
```bash
# Launch team lead
claude --agent agents/backend-engineering-lead.md

# Or launch engineer
claude --agent agents/backend-engineering-engineer.md
```

**Expected Output**: Agent session with team-specific context and steering.

---

### 008: Prompt Adapter

**Path**: `jadecli-ai/.claude-org/pm/lib/prompt_adapter.py`

**Navigate**:
```bash
cd ~/projects/.claude-org/pm
```

**Claude Code Prompt**:
```bash
# CLI usage
python3 lib/prompt_adapter.py "add caching to the API endpoints"

# Or in Claude Code session:
Use lib/prompt_adapter.py to analyze: "fix the memory leak in the worker pool"
```

**Expected Output**: Structured XML with intent, commit type, repos, scope.

---

### 009: Chain Detector

**Path**: `jadecli-ai/.claude-org/pm/lib/chain_detector.py`

**Navigate**:
```bash
cd ~/projects/.claude-org/pm
```

**Claude Code Prompt**:
```bash
# CLI usage
python3 lib/chain_detector.py "continue working on the auth feature"

# Or in Claude Code session:
Should I extend EPIC-001 or start a new epic for this request?
```

**Expected Output**: Chain decision (NEW_EPIC, EXTEND_EPIC, SUBTASK, etc.) with confidence.

---

### 010: Org-Epic Schema

**Path**: `jadecli-ai/.claude-org/pm/entities/org-epic.schema.md`

**Navigate**:
```bash
code ~/projects/.claude-org/pm/entities/org-epic.schema.md
```

**Claude Code Prompt**:
```
Create ORG-EPIC-002 for "Unified Authentication System" spanning
team-agents-sdk and pm repos, following the org-epic schema.
```

**Expected Output**: New epic entity file with proper frontmatter.

---

### 011: Repo-Sprint Schema

**Path**: `jadecli-ai/.claude-org/pm/entities/repo-sprint.schema.md`

**Navigate**:
```bash
code ~/projects/.claude-org/pm/entities/repo-sprint.schema.md
```

**Claude Code Prompt**:
```
Create SPRINT-003 for team-agents-sdk linked to ORG-EPIC-001,
starting 2026-02-17, following the sprint schema.
```

**Expected Output**: New sprint entity file with tasks and capacity.

---

### 012: /ask Command

**Path**: `jadecli-ai/.claude-org/pm/.claude/commands/ask.md`

**Navigate**:
```bash
cd ~/projects/.claude-org/pm
```

**Claude Code Prompt**:
```
/ask implement rate limiting for the API with Redis backing
```

**Expected Output**: Structured analysis with intent, repos, chain decision, and routing recommendation.

---

## Implementation Details

### Directory Structure

```
jadecli-ai/.claude-org/
├── usage-guides/
│   └── developer/
│       ├── INDEX.md                    # Master index (this content)
│       ├── 001-budget-tracker.md       # Deep dive per feature
│       ├── 002-handoff-generator.md
│       ├── 003-model-budgets.md
│       ├── ...
│       └── 012-ask-command.md
```

### Index File Format

Each guide follows:

```markdown
---
idx: 001
feature: "Budget Tracker"
path: "steering/lib/budget_tracker.py"
prompt: "@steering-orchestrator Track my budget"
---

# 001: Budget Tracker

## Overview
[What it does]

## Navigation
[How to get there]

## Usage
[Claude Code prompts]

## Examples
[Real usage examples]

## Related
[Links to related guides]
```

### Monotonic Index Rules

1. **Never reuse numbers** - Deleted features keep their index (marked deprecated)
2. **Append only** - New features get next available index
3. **Stable URLs** - Index number is permanent identifier
4. **Changelog** - Track additions/deprecations in INDEX.md header

---

## Benefits

### 1. Discoverability
- Developers find features via numbered index
- Single source of truth for "what's available"
- Reduces onboarding time from hours to minutes

### 2. Consistency
- Standardized navigation paths
- Predictable prompt patterns
- Same experience across all features

### 3. Automation-Ready
- Monotonic index enables scripting
- Can generate navigation menus
- Supports future IDE integrations

### 4. Institutional Knowledge
- Documents tribal knowledge
- Survives team transitions
- Self-documenting system

### 5. Claude Code Optimization
- Pre-written prompts reduce trial-and-error
- Tested prompts ensure reliable activation
- Context-aware guidance

---

## Follow-up Tasks

### Immediate (This Sprint)

| ID | Task | Owner | Size |
|----|------|-------|------|
| TASK-010 | Create `usage-guides/developer/INDEX.md` with full index | staff-engineer | M |
| TASK-011 | Create individual guide files (001-012) | staff-engineer | L |
| TASK-012 | Add `make guides` command to generate/validate index | staff-engineer | S |
| TASK-013 | Update pm/CLAUDE.md to reference usage guides | staff-engineer | XS |

### Next Sprint

| ID | Task | Owner | Size |
|----|------|-------|------|
| TASK-014 | Create `/usage-guides/operator/` for ops tasks | staff-engineer | M |
| TASK-015 | Add search functionality to INDEX.md | staff-engineer | M |
| TASK-016 | Create GitHub Action to validate index on PR | staff-engineer | S |
| TASK-017 | Generate HTML version of guides for web access | staff-engineer | M |

### Future (Backlog)

| ID | Task | Owner | Size |
|----|------|-------|------|
| TASK-018 | IDE extension to surface guides in VS Code | staff-engineer | XL |
| TASK-019 | `/guide <feature>` slash command in Claude Code | staff-engineer | L |
| TASK-020 | Auto-generate guides from agent frontmatter | staff-engineer | L |
| TASK-021 | Interactive tutorial mode with guided prompts | staff-engineer | XL |

---

## Acceptance Criteria

- [ ] `usage-guides/developer/INDEX.md` exists with 12+ entries
- [ ] Each entry has: idx, feature, path, prompt
- [ ] Individual guide files exist for each entry
- [ ] `make guides` validates index consistency
- [ ] All paths resolve to actual files
- [ ] All prompts are tested and working
- [ ] pm/CLAUDE.md references the usage guides

---

## References

- Steering system: `steering/`
- PM agents: `pm/agents/`
- Templates: `templates/`
- Existing entities: `pm/entities/examples/`
