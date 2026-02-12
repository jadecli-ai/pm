# Blueprint: Updating Team Agents

> Init context for any request that modifies agent definitions in `agents/` or `pm/agents/`.
> Reference from CLAUDE.md: `@contributing-blueprint/001-init-context-update-team-agents.md`

## Feature Overview

The team agents system defines an Agent Teams hierarchy where each agent has a YAML
frontmatter schema controlling its model, memory scope, tool access, sub-agent restrictions,
and hook events. Changes here affect how Claude Code spawns and coordinates multi-agent work.

## File Map

### Organization-Level Agents (`agents/`)

| File | Role | Model | Spawned By |
|------|------|-------|------------|
| `agents/team-lead.md` | Coordination | Sonnet 4.5 | User / VP Product |
| `agents/implementer.md` | Feature dev | Sonnet 4.5 | Team Lead |
| `agents/tester.md` | QA | Sonnet 4.5 | Team Lead |
| `agents/reviewer.md` | Code review | Sonnet 4.5 | Team Lead |

### PM Agents (`pm/agents/`)

| File | Role | Model | Spawned By |
|------|------|-------|------------|
| `pm/agents/vp-product.md` | Strategy | Opus 4.6 | User |
| `pm/agents/sdm.md` | Domain management | Sonnet 4.5 | VP Product |
| `pm/agents/staff-engineer.md` | Implementation | Sonnet 4.5 | SDM |
| `pm/agents/sprint-master.md` | Ceremonies | Haiku 4.5 | VP Product |

### Hierarchy

```
VP Product (Opus 4.6) ─── Task(sdm), Task(sprint-master)
├── SDM (Sonnet 4.5) ─── Task(staff-engineer)
│   └── Staff Engineer (Sonnet 4.5)
└── Sprint Master (Haiku 4.5)

Team Lead (Sonnet 4.5) ─── Task(implementer), Task(tester), Task(reviewer)
├── Implementer (Sonnet 4.5)
├── Tester (Sonnet 4.5)
└── Reviewer (Sonnet 4.5)
```

## Frontmatter Schema

Every agent `.md` file has YAML frontmatter with these fields:

```yaml
---
name: <agent-name>              # Required: unique identifier
description: <one-liner>        # Required: what the agent does
model: <model-id>               # Required: claude-opus-4-6 | claude-sonnet-4-5-20250929 | claude-haiku-4-5-20251001
memory: <scope>                 # Required: project | local | user
tools:                          # Required: list of allowed tools
  - Task(agent-type)            # Restricts which sub-agents can be spawned
  - Read
  - Edit
  - Write
  - Bash
  - Glob
  - Grep
  - WebSearch
  - WebFetch
  - mcp__memory__*              # Wildcard MCP tool access
  - mcp__git__*
hooks:                          # Optional: lifecycle event handlers
  TeammateIdle:                 # Fires when a spawned agent has no queued work
    - command: "<shell command>"
  TaskCompleted:                # Fires when a spawned agent's task resolves
    - command: "<shell command>"
  PreToolUse:                   # Fires before a tool is invoked
    - matcher: "<tool-name>"
      command: "<shell command>"
  PostToolUse:                  # Fires after a tool completes
    - matcher: "<tool-name>"
      command: "<shell command>"
---
```

## Key Constraints

### Task(agent_type) Restrictions

Each agent can only spawn the sub-agent types listed in its `tools` frontmatter:

- VP Product: `Task(sdm)`, `Task(sprint-master)` only
- Team Lead: `Task(implementer)`, `Task(tester)`, `Task(reviewer)` only
- SDM: `Task(staff-engineer)` only

Adding a new agent type requires updating the parent's `tools` list to include `Task(new-agent)`.

### Memory Scopes

| Scope | Persistence | Use When |
|-------|------------|----------|
| `project` | Across sessions, per-project | Strategy, architecture, velocity data |
| `local` | Within session only | Implementation context, review findings |
| `user` | Across all projects | Personal preferences (not currently used) |

### Model IDs

Always use the full model identifier, never shorthand:

| Model | Full ID | Use For |
|-------|---------|---------|
| Opus 4.6 | `claude-opus-4-6` | Strategic reasoning (VP Product) |
| Sonnet 4.5 | `claude-sonnet-4-5-20250929` | Implementation, management |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Lightweight coordination (Sprint Master) |

## Checklist: Adding a New Agent

1. Create `agents/<name>.md` or `pm/agents/<name>.md` with full frontmatter
2. Choose appropriate model, memory scope, and tool restrictions
3. Update the parent agent's `tools` to include `Task(<name>)`
4. Add `hooks` if the agent coordinates sub-agents (TeammateIdle, TaskCompleted)
5. Add an "Agent Teams Context" section in the body explaining:
   - Where the agent sits in the hierarchy
   - What memory scope means for it
   - What hooks it reacts to
   - What Task metrics it should track
6. Regenerate merkle tree: `python3 pm/.index/generate-merkle.py`
7. Update `pm/.index/generate-merkle.py` `semanticIndex.agents` dict if PM agent
8. Run tests: `./pm/tests/run-tests.sh` (Test 5 validates agent schema)
9. Commit: `feat(agents): add <name> agent`

## Checklist: Modifying an Existing Agent

1. Read the current agent file fully before making changes
2. Preserve all existing frontmatter fields (don't remove fields)
3. If changing `tools`, verify parent/child Task(agent_type) consistency
4. If changing `model`, update the Agent Teams hierarchy in the body
5. If adding hooks, use existing naming patterns (`[agent-name] action`)
6. Regenerate merkle tree: `python3 pm/.index/generate-merkle.py`
7. Run tests: `./pm/tests/run-tests.sh`
8. Commit: `refactor(agents): <description>` or `feat(agents): <description>`

## Checklist: Upgrading Agent Models (Claude Code Release)

When a new Claude Code version adds model features:

1. Review the [CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) for agent-relevant features
2. Check for new frontmatter fields (e.g., `memory` was added in 2.1.33)
3. Check for new hook events (e.g., `TeammateIdle`/`TaskCompleted` added in 2.1.33)
4. Check for new Task tool capabilities (e.g., metrics added in 2.1.30)
5. Update model IDs if a new model is released (e.g., Opus 4.5 -> 4.6 in 2.1.32)
6. Add version-tagged sections in agent bodies (e.g., "## Task Metrics (2.1.30+)")
7. Update all agents consistently — don't leave some on old patterns
8. Regenerate merkle tree after all changes
9. Commit: `feat(agents): upgrade agents with Claude Code X.Y.Z features`

## Related Files

| File | Why It Matters |
|------|----------------|
| `pm/.index/generate-merkle.py` | `semanticIndex.agents` dict must include all PM agents |
| `pm/.index/AGENT-INDEX.md` | Hardcoded quick reference — update if agent list changes |
| `pm/ENTRYPOINT.md` | Agent team launch guide — references agent hierarchy |
| `pm/tests/run-tests.sh` | Test 5 validates agent schema (name field required) |
| `pm/CLAUDE.md` | References agents in Package Structure section |
| `docs/AGENT_EXPANSION_GUIDE.md` | Full guide for creating new agent implementations |

## Anti-Patterns

- Adding `Task` (unrestricted) when `Task(specific-type)` is appropriate
- Using shorthand model names (`opus`, `sonnet`) instead of full IDs
- Forgetting to update the merkle tree after agent changes
- Adding hooks that do heavy computation (hooks should be lightweight signals)
- Duplicating prompt content that belongs in CLAUDE.md or AGENT-INDEX.md
- Adding agents without updating the parent's Task(agent_type) list
