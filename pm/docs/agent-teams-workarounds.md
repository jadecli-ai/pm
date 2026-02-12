---
id: "DOC-WORKAROUNDS-001"
version: "1.0.0"
type: doc
status: active
created: 2026-02-11
updated: 2026-02-11
dependsOn:
  - "docs/fetch/claude-code-subagents.md"
dependedBy:
  - "agents/vp-product.md"
  - "agents/sdm.md"
---

# Agent Teams Workarounds

> Strategies to mitigate Claude Code agent teams limitations.

## Known Limitations

From [Claude Code Agent Teams docs](https://code.claude.com/docs/en/agent-teams):

| Limitation | Impact | Workaround |
|------------|--------|------------|
| No session resumption | Teammates lost on `/resume` | Persist state to entities |
| Task status can lag | Dependent tasks blocked | Manual status checks |
| Shutdown can be slow | Long cleanup times | Patient termination |
| One team per session | Can't run parallel teams | Sequential team execution |
| No nested teams | Teammates can't spawn teams | Flat team structure |
| Lead is fixed | Can't transfer leadership | Restart session for new lead |
| Permissions set at spawn | Limited runtime changes | Pre-configure permissions |
| Split panes need tmux/iTerm2 | VS Code terminal unsupported | Use WezTerm |

## Workaround Strategies

### 1. State Persistence (No Session Resumption)

**Problem**: `/resume` doesn't restore in-process teammates.

**Solution**: Persist all state to markdown entities that agents read on spawn.

```yaml
# Entity-based state persistence
---
id: "TASK-001"
status: in_progress
lastCheckpoint: "2026-02-11T10:30:00Z"
progress:
  - step: 1
    status: completed
    output: "Created migration file"
  - step: 2
    status: in_progress
    output: "Running tests..."
agentContext:
  lastAction: "test execution"
  nextAction: "verify test results"
---
```

**Agent Startup Pattern**:
```xml
<instructions>
  1. Read AGENT-INDEX.md for system overview
  2. Check entities/ for in_progress tasks assigned to you
  3. Read task entity for lastCheckpoint and progress
  4. Resume from last completed step, don't restart
</instructions>
```

### 2. Task Status Sync (Status Can Lag)

**Problem**: Teammates sometimes fail to mark tasks as completed.

**Solution**: Implement dual-sync with Neon and entity files.

```python
# lib/task_sync.py
def sync_task_status(task_id: str, status: str):
    """Sync to both entity file and Neon."""
    # 1. Update entity file
    update_entity_frontmatter(task_id, {'status': status})

    # 2. Sync to Neon (via Claude SDK hook)
    # This happens automatically via PreToolUse/PostToolUse

    # 3. Log to MLflow
    mlflow.log_param(f"task_{task_id}_status", status)
```

**Lead Nudge Pattern**:
```xml
<instructions>
  If a task appears stuck:
  1. Check entity file for actual status
  2. If work is done but status != completed:
     - Tell teammate: "Mark TASK-XXX as completed"
     - Or update manually: TaskUpdate(taskId, status="completed")
  3. Unblock dependent tasks
</instructions>
```

### 3. Sequential Team Execution (One Team Per Session)

**Problem**: Can only manage one team at a time per session.

**Solution**: Use multiple WezTerm sessions or sequential execution.

**Multi-Session Pattern** (WezTerm):
```lua
-- Ctrl+A Ctrl+4: Create 4 teams across 4 tabs
{ key = "4", mods = "LEADER|CTRL", action = wezterm.action_callback(function(window, pane)
    local teams = {"alpha", "beta", "gamma", "delta"}
    for i, team in ipairs(teams) do
      -- Each tab is independent session with own team
      local tab = mux_window:spawn_tab { cwd = cwd }
      tab:set_title("Team " .. team)
      -- 6-pane grid in each tab
      -- Each lead can manage its own team
    end
end)}
```

**Sequential Pattern** (Single Session):
```xml
<workflow>
  <phase name="backend">
    1. Spawn backend team (SDM + 3 SE)
    2. Execute backend sprint tasks
    3. Clean up team on completion
  </phase>
  <phase name="frontend">
    1. Spawn frontend team (SDM + 3 SE)
    2. Execute frontend sprint tasks
    3. Clean up team on completion
  </phase>
</workflow>
```

### 4. Flat Team Structure (No Nested Teams)

**Problem**: Teammates cannot spawn their own teams.

**Solution**: VP Product as lead spawns all agents directly.

**Anti-Pattern** (Don't Do This):
```
VP Product → SDM → Staff Engineers (FAILS: SDM can't spawn teams)
```

**Correct Pattern**:
```
VP Product (Lead)
├── spawns SDM-Frontend (teammate)
├── spawns SDM-Backend (teammate)
├── spawns SE-1 (teammate)
├── spawns SE-2 (teammate)
├── spawns SE-3 (teammate)
└── spawns Sprint-Master (teammate)
```

**Coordination Without Nesting**:
```xml
<instructions>
  VP Product coordinates through task assignments, not team spawning.
  SDMs assign work by updating entity files, not spawning agents.

  1. VP Product spawns all teammates at session start
  2. SDMs receive work via entity file updates
  3. SDMs assign to Staff Engineers via entity assignment field
  4. Staff Engineers read entity files to find their work
</instructions>
```

### 5. WezTerm Pane Setup (Split Panes Need tmux/iTerm2)

**Problem**: VS Code terminal, Windows Terminal, Ghostty don't support split panes.

**Solution**: Use WezTerm with custom keybindings.

**WezTerm Config** (already configured):
```lua
-- 6-pane grid: Ctrl+A Ctrl+6
{ key = "6", mods = "LEADER|CTRL", action = wezterm.action_callback(function(window, pane)
    -- Creates 3x2 grid, starts claude in each
end)}

-- 4 teams × 6 panes: Ctrl+A Ctrl+4
{ key = "4", mods = "LEADER|CTRL", action = wezterm.action_callback(function(window, pane)
    -- Creates 4 tabs, each with 6-pane grid
end)}
```

### 6. Permission Pre-Configuration (Permissions Set at Spawn)

**Problem**: All teammates inherit lead's permission mode at spawn.

**Solution**: Configure comprehensive permissions in settings before spawning.

**Settings Pattern** (`settings.json`):
```json
{
  "permissions": {
    "allow": [
      "Read(*)",
      "Edit(*)",
      "Write(*)",
      "Bash(git *)",
      "Bash(npm *)",
      "Bash(python3 *)",
      "Bash(pytest *)",
      "Bash(make *)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(sudo *)"
    ]
  }
}
```

**Launch with Bypass** (for trusted operations):
```bash
claude --dangerously-skip-permissions --agent vp-product.md
```

## PM System Integration

### Entity-Based Coordination

Instead of relying on in-process teammate state:

1. **Create entity files** for all work items
2. **Agents read entities** on startup to discover their work
3. **Agents update entities** to signal completion
4. **Other agents poll entities** for status

```
entities/
├── ORG-EPIC-001.md      # VP Product creates
├── SPRINT-001.md        # SDM creates (linked to epic)
├── TASK-001.md          # SDM creates (linked to sprint)
│   └── assignee: staff-eng-1
└── TASK-002.md
    └── assignee: staff-eng-2
```

### Merkle Tree for Change Detection

Agents use the Merkle tree for efficient state checking:

```python
# Quick check: has anything changed?
current_root = read_merkle_root()
if current_root != last_known_root:
    # Something changed, investigate
    check_changed_files()
```

### GitHub Project as Source of Truth

When entity files and agent memory are insufficient:

```bash
# Sync GitHub Project state
gh project item-list 1 --owner jadecli-ai --format json > project-state.json

# Agent reads project state
python3 lib/github_sync.py --read
```

## Summary

| Challenge | Solution |
|-----------|----------|
| Session resumption | Entity files with progress state |
| Task status lag | Dual-sync (entity + Neon) |
| One team per session | WezTerm multi-tab (4 teams) |
| No nested teams | Flat structure, entity-based coordination |
| No split panes | WezTerm with custom keybindings |
| Fixed permissions | Pre-configure in settings.json |

## References

- [Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents)
- [WezTerm Configuration](~/.wezterm.lua)
- [PM Entity Schemas](../entities/)
