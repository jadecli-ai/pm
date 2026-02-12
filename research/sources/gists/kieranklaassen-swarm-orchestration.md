---
source: https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea
fetched: 2026-02-11
type: gist
author: kieranklaassen
description: Claude Code Swarm Orchestration Skill - Complete guide to multi-agent coordination
---

# Claude Code Swarm Orchestration

Master multi-agent orchestration using Claude Code's TeammateTool and Task system.

## Primitives

| Primitive | What It Is | File Location |
|-----------|-----------|---------------|
| **Agent** | A Claude instance that can use tools. You are an agent. Subagents are agents you spawn. | N/A (process) |
| **Team** | A named group of agents working together. One leader, multiple teammates. | `~/.claude/teams/{name}/config.json` |
| **Teammate** | An agent that joined a team. Has a name, color, inbox. Spawned via Task with `team_name` + `name`. | Listed in team config |
| **Leader** | The agent that created the team. Receives teammate messages, approves plans/shutdowns. | First member in config |
| **Task** | A work item with subject, description, status, owner, and dependencies. | `~/.claude/tasks/{team}/N.json` |
| **Inbox** | JSON file where an agent receives messages from teammates. | `~/.claude/teams/{name}/inboxes/{agent}.json` |
| **Message** | A JSON object sent between agents. Can be text or structured (shutdown_request, idle_notification, etc). | Stored in inbox files |
| **Backend** | How teammates run. Auto-detected: `in-process` (same Node.js, invisible), `tmux` (separate panes, visible), `iterm2` (split panes in iTerm2). | Auto-detected based on environment |

## Core Architecture

### How Swarms Work

A swarm consists of:
- **Leader** (you) - Creates team, spawns workers, coordinates work
- **Teammates** (spawned agents) - Execute tasks, report back
- **Task List** - Shared work queue with dependencies
- **Inboxes** - JSON files for inter-agent messaging

### File Structure

```
~/.claude/teams/{team-name}/
├── config.json              # Team metadata and member list
└── inboxes/
    ├── team-lead.json       # Leader's inbox
    ├── worker-1.json        # Worker 1's inbox
    └── worker-2.json        # Worker 2's inbox

~/.claude/tasks/{team-name}/
├── 1.json                   # Task #1
├── 2.json                   # Task #2
└── 3.json                   # Task #3
```

## Two Ways to Spawn Agents

### Method 1: Task Tool (Subagents)

Use Task for **short-lived, focused work** that returns a result:

```javascript
Task({
  subagent_type: "Explore",
  description: "Find auth files",
  prompt: "Find all authentication-related files in this codebase",
  model: "haiku"  // Optional: haiku, sonnet, opus
})
```

**Characteristics:**
- Runs synchronously (blocks until complete) or async with `run_in_background: true`
- Returns result directly to you
- No team membership required
- Best for: searches, analysis, focused research

### Method 2: Task Tool + team_name + name (Teammates)

Use Task with `team_name` and `name` to **spawn persistent teammates**:

```javascript
// First create a team
Teammate({ operation: "spawnTeam", team_name: "my-project" })

// Then spawn a teammate into that team
Task({
  team_name: "my-project",        // Required: which team to join
  name: "security-reviewer",      // Required: teammate's name
  subagent_type: "security-sentinel",
  prompt: "Review all authentication code for vulnerabilities. Send findings to team-lead via Teammate write.",
  run_in_background: true         // Teammates usually run in background
})
```

**Characteristics:**
- Joins team, appears in `config.json`
- Communicates via inbox messages
- Can claim tasks from shared task list
- Persists until shutdown
- Best for: parallel work, ongoing collaboration, pipeline stages

### Key Difference

| Aspect | Task (subagent) | Task + team_name + name (teammate) |
|--------|-----------------|-----------------------------------|
| Lifespan | Until task complete | Until shutdown requested |
| Communication | Return value | Inbox messages |
| Task access | None | Shared task list |
| Team membership | No | Yes |
| Coordination | One-off | Ongoing |

## Built-in Agent Types

### Bash
```javascript
Task({
  subagent_type: "Bash",
  description: "Run git commands",
  prompt: "Check git status and show recent commits"
})
```
- **Tools:** Bash only
- **Best for:** Git operations, command execution, system tasks

### Explore
```javascript
Task({
  subagent_type: "Explore",
  description: "Find API endpoints",
  prompt: "Find all API endpoints in this codebase. Be very thorough.",
  model: "haiku"  // Fast and cheap
})
```
- **Tools:** All read-only tools (no Edit, Write, NotebookEdit, Task)
- **Model:** Haiku (optimized for speed)
- **Best for:** Codebase exploration, file searches, code understanding

### Plan
```javascript
Task({
  subagent_type: "Plan",
  description: "Design auth system",
  prompt: "Create an implementation plan for adding OAuth2 authentication"
})
```
- **Tools:** All read-only tools
- **Best for:** Architecture planning, implementation strategies

### general-purpose
```javascript
Task({
  subagent_type: "general-purpose",
  description: "Research and implement",
  prompt: "Research React Query best practices and implement caching for the user API"
})
```
- **Tools:** All tools
- **Best for:** Multi-step tasks, research + action combinations

## TeammateTool Operations

### 1. spawnTeam - Create a Team

```javascript
Teammate({
  operation: "spawnTeam",
  team_name: "feature-auth",
  description: "Implementing OAuth2 authentication"
})
```

**Creates:**
- `~/.claude/teams/feature-auth/config.json`
- `~/.claude/tasks/feature-auth/` directory
- You become the team leader

### 2. write - Message One Teammate

```javascript
Teammate({
  operation: "write",
  target_agent_id: "security-reviewer",
  value: "Please prioritize the authentication module. The deadline is tomorrow."
})
```

**Important for teammates:** Your text output is NOT visible to the team. You MUST use `write` to communicate.

### 3. broadcast - Message ALL Teammates

```javascript
Teammate({
  operation: "broadcast",
  name: "team-lead",  // Your name
  value: "Status check: Please report your progress"
})
```

**WARNING:** Broadcasting is expensive - sends N separate messages for N teammates. Prefer `write` to specific teammates.

### 4. requestShutdown - Ask Teammate to Exit (Leader Only)

```javascript
Teammate({
  operation: "requestShutdown",
  target_agent_id: "security-reviewer",
  reason: "All tasks complete, wrapping up"
})
```

### 5. approveShutdown - Accept Shutdown (Teammate Only)

When you receive a `shutdown_request` message:

```javascript
Teammate({
  operation: "approveShutdown",
  request_id: "shutdown-123"
})
```

This sends confirmation and terminates your process.

### 6. cleanup - Remove Team Resources

```javascript
Teammate({ operation: "cleanup" })
```

**IMPORTANT:** Will fail if teammates are still active. Use `requestShutdown` first.

## Task System Integration

### TaskCreate - Create Work Items

```javascript
TaskCreate({
  subject: "Review authentication module",
  description: "Review all files in app/services/auth/ for security vulnerabilities",
  activeForm: "Reviewing auth module..."  // Shown in spinner when in_progress
})
```

### TaskList - See All Tasks

```javascript
TaskList()
```

Returns:
```
#1 [completed] Analyze codebase structure
#2 [in_progress] Review authentication module (owner: security-reviewer)
#3 [pending] Generate summary report [blocked by #2]
```

### TaskUpdate - Update Task Status

```javascript
// Claim a task
TaskUpdate({ taskId: "2", owner: "security-reviewer" })

// Start working
TaskUpdate({ taskId: "2", status: "in_progress" })

// Mark complete
TaskUpdate({ taskId: "2", status: "completed" })

// Set up dependencies
TaskUpdate({ taskId: "3", addBlockedBy: ["1", "2"] })
```

### Task Dependencies

When a blocking task is completed, blocked tasks are automatically unblocked:

```javascript
// Create pipeline
TaskCreate({ subject: "Step 1: Research" })        // #1
TaskCreate({ subject: "Step 2: Implement" })       // #2
TaskCreate({ subject: "Step 3: Test" })            // #3
TaskCreate({ subject: "Step 4: Deploy" })          // #4

// Set up dependencies
TaskUpdate({ taskId: "2", addBlockedBy: ["1"] })   // #2 waits for #1
TaskUpdate({ taskId: "3", addBlockedBy: ["2"] })   // #3 waits for #2
TaskUpdate({ taskId: "4", addBlockedBy: ["3"] })   // #4 waits for #3

// When #1 completes, #2 auto-unblocks
// When #2 completes, #3 auto-unblocks
// etc.
```

## Orchestration Patterns

### Pattern 1: Parallel Specialists (Leader Pattern)

Multiple specialists review code simultaneously:

```javascript
// 1. Create team
Teammate({ operation: "spawnTeam", team_name: "code-review" })

// 2. Spawn specialists in parallel
Task({
  team_name: "code-review",
  name: "security",
  subagent_type: "security-sentinel",
  prompt: "Review the PR for security vulnerabilities. Send findings to team-lead.",
  run_in_background: true
})

Task({
  team_name: "code-review",
  name: "performance",
  subagent_type: "performance-oracle",
  prompt: "Review the PR for performance issues. Send findings to team-lead.",
  run_in_background: true
})

// 3. Wait for results (check inbox)
// 4. Synthesize findings and cleanup
Teammate({ operation: "requestShutdown", target_agent_id: "security" })
Teammate({ operation: "cleanup" })
```

### Pattern 2: Pipeline (Sequential Dependencies)

Each stage depends on the previous:

```javascript
// 1. Create team and task pipeline
Teammate({ operation: "spawnTeam", team_name: "feature-pipeline" })

TaskCreate({ subject: "Research", description: "Research best practices" })
TaskCreate({ subject: "Plan", description: "Create implementation plan" })
TaskCreate({ subject: "Implement", description: "Implement the feature" })
TaskCreate({ subject: "Test", description: "Write and run tests" })

// Set up sequential dependencies
TaskUpdate({ taskId: "2", addBlockedBy: ["1"] })
TaskUpdate({ taskId: "3", addBlockedBy: ["2"] })
TaskUpdate({ taskId: "4", addBlockedBy: ["3"] })

// 2. Spawn workers that claim and complete tasks
Task({
  team_name: "feature-pipeline",
  name: "researcher",
  subagent_type: "best-practices-researcher",
  prompt: "Claim task #1, research, complete it, send findings to team-lead.",
  run_in_background: true
})

// Tasks auto-unblock as dependencies complete
```

### Pattern 3: Swarm (Self-Organizing)

Workers grab available tasks from a pool:

```javascript
// 1. Create team and task pool
Teammate({ operation: "spawnTeam", team_name: "file-review-swarm" })

// Create many independent tasks (no dependencies)
for (const file of ["auth.rb", "user.rb", "api_controller.rb"]) {
  TaskCreate({
    subject: `Review ${file}`,
    description: `Review ${file} for security and code quality issues`
  })
}

// 2. Spawn worker swarm
Task({
  team_name: "file-review-swarm",
  name: "worker-1",
  subagent_type: "general-purpose",
  prompt: `
    You are a swarm worker. Your job:
    1. Call TaskList to see available tasks
    2. Find a task with status 'pending' and no owner
    3. Claim it with TaskUpdate (set owner to your name)
    4. Do the work
    5. Mark it completed with TaskUpdate
    6. Send findings to team-lead
    7. Repeat until no tasks remain
  `,
  run_in_background: true
})

// Spawn worker-2, worker-3 with same prompt
// Workers race to claim tasks, naturally load-balance
```

## Spawn Backends

A **backend** determines how teammate Claude instances actually run. Claude Code auto-detects the best one.

| Backend | How It Works | Visibility | Persistence | Speed |
|---------|-------------|------------|-------------|-------|
| **in-process** | Same Node.js process as leader | Hidden (background) | Dies with leader | Fastest |
| **tmux** | Separate terminal in tmux session | Visible in tmux | Survives leader exit | Medium |
| **iterm2** | Split panes in iTerm2 window | Visible side-by-side | Dies with window | Medium |

### Auto-Detection Logic

1. `$TMUX` environment variable → inside tmux
2. `$TERM_PROGRAM === "iTerm.app"` → in iTerm2
3. `which tmux` → tmux available
4. `which it2` → it2 CLI installed

### Forcing a Backend

```bash
# Force in-process (fastest, no visibility)
export CLAUDE_CODE_SPAWN_BACKEND=in-process

# Force tmux (visible panes, persistent)
export CLAUDE_CODE_SPAWN_BACKEND=tmux

# Auto-detect (default)
unset CLAUDE_CODE_SPAWN_BACKEND
```

## Message Formats

### Regular Message

```json
{
  "from": "team-lead",
  "text": "Please prioritize the auth module",
  "timestamp": "2026-01-25T23:38:32.588Z",
  "read": false
}
```

### Structured Messages

#### Shutdown Request
```json
{
  "type": "shutdown_request",
  "requestId": "shutdown-abc123@worker-1",
  "from": "team-lead",
  "reason": "All tasks complete",
  "timestamp": "2026-01-25T23:38:32.588Z"
}
```

#### Idle Notification (auto-sent when teammate stops)
```json
{
  "type": "idle_notification",
  "from": "worker-1",
  "timestamp": "2026-01-25T23:40:00.000Z",
  "completedTaskId": "2",
  "completedStatus": "completed"
}
```

#### Task Completed
```json
{
  "type": "task_completed",
  "from": "worker-1",
  "taskId": "2",
  "taskSubject": "Review authentication module",
  "timestamp": "2026-01-25T23:40:00.000Z"
}
```

## Environment Variables

Spawned teammates automatically receive these:

```bash
CLAUDE_CODE_TEAM_NAME="my-project"
CLAUDE_CODE_AGENT_ID="worker-1@my-project"
CLAUDE_CODE_AGENT_NAME="worker-1"
CLAUDE_CODE_AGENT_TYPE="Explore"
CLAUDE_CODE_AGENT_COLOR="#4A90D9"
CLAUDE_CODE_PLAN_MODE_REQUIRED="false"
CLAUDE_CODE_PARENT_SESSION_ID="session-xyz"
```

## Best Practices

### 1. Always Cleanup
Don't leave orphaned teams. Always call `cleanup` when done.

### 2. Use Meaningful Names
```javascript
// Good
name: "security-reviewer"
name: "oauth-implementer"

// Bad
name: "worker-1"
```

### 3. Write Clear Prompts
Tell workers exactly what to do:
```javascript
// Good
prompt: `
  1. Review app/models/user.rb for N+1 queries
  2. Check all ActiveRecord associations have proper includes
  3. Document any issues found
  4. Send findings to team-lead via Teammate write
`

// Bad
prompt: "Review the code"
```

### 4. Use Task Dependencies
Let the system manage unblocking:
```javascript
// Good: Auto-unblocking
TaskUpdate({ taskId: "2", addBlockedBy: ["1"] })

// Bad: Manual polling
"Wait until task #1 is done, check every 30 seconds..."
```

### 5. Check Inboxes for Results
Workers send results to your inbox:
```bash
cat ~/.claude/teams/{team}/inboxes/team-lead.json | jq '.'
```

### 6. Prefer write Over broadcast
`broadcast` sends N messages for N teammates. Use `write` for targeted communication.

### 7. Match Agent Type to Task
- **Explore** for searching/reading
- **Plan** for architecture design
- **general-purpose** for implementation
- **Specialized reviewers** for specific review types

## Quick Reference

### Spawn Subagent (No Team)
```javascript
Task({ subagent_type: "Explore", description: "Find files", prompt: "..." })
```

### Spawn Teammate (With Team)
```javascript
Teammate({ operation: "spawnTeam", team_name: "my-team" })
Task({ team_name: "my-team", name: "worker", subagent_type: "general-purpose", prompt: "...", run_in_background: true })
```

### Message Teammate
```javascript
Teammate({ operation: "write", target_agent_id: "worker-1", value: "..." })
```

### Create Task Pipeline
```javascript
TaskCreate({ subject: "Step 1", description: "..." })
TaskCreate({ subject: "Step 2", description: "..." })
TaskUpdate({ taskId: "2", addBlockedBy: ["1"] })
```

### Shutdown Team
```javascript
Teammate({ operation: "requestShutdown", target_agent_id: "worker-1" })
// Wait for approval...
Teammate({ operation: "cleanup" })
```

---

*Based on Claude Code v2.1.19 - Tested and verified 2026-01-25*
