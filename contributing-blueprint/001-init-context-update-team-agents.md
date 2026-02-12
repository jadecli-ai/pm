# Blueprint: Team Agent Workflows

> Init context for operating and updating the agent team system.
> Reference from CLAUDE.md: `@contributing-blueprint/001-init-context-update-team-agents.md`

## Architecture: Uniform Opus 4.6

All agents run `claude-opus-4-6`. No mixed-model hierarchy. The rationale:

- **Adaptive thinking** calibrates depth automatically — Opus reasons deeply on
  architecture decisions and shallowly on status checks without explicit mode switching
- **Fast mode** (`/fast`) gives Opus 4.6 the throughput of lighter models when tasks are
  straightforward, eliminating the need for Haiku/Sonnet tiers
- **Uniform prompting** — one set of patterns works everywhere; no need to simplify
  prompts for weaker models or add guardrails for model-specific failure modes
- **Sub-agent quality** — Task tool spawns inherit the parent's model by default (2.1.0
  fix), so every layer of the hierarchy gets full reasoning capability

### Hierarchy

```
VP Product ─── Task(sdm), Task(sprint-master)
├── SDM ─── Task(staff-engineer)
│   └── Staff Engineer (leaf — no sub-agents)
└── Sprint Master (leaf — read-only observer)

Team Lead ─── Task(implementer), Task(tester), Task(reviewer)
├── Implementer (leaf)
├── Tester (leaf)
└── Reviewer (leaf — read-only)
```

Every node is `model: claude-opus-4-6`. Fast mode is toggled per-session, not per-agent.

---

## Context Management

Context is the scarcest resource. Every token in the window that isn't serving the current
task is waste. These techniques keep context lean.

### 1. Pre-Computed Index (Skip Exploration)

Every PM agent prompt starts with:
```
> Read `.index/AGENT-INDEX.md` for pre-computed system overview.
```

This 68-line file gives agents the full system map, entity schema, and workflow summary.
Without it, an agent spends 5-15 tool calls exploring the filesystem — each call adds
request/response tokens to the window. The index replaces ~2,000 tokens of exploration
with ~800 tokens of pre-computed context.

**Rule**: If you change agent hierarchy, entity schema, or directory structure, regenerate
the index (`python3 pm/.index/generate-merkle.py`) so agents don't encounter stale context.

### 2. Merkle Tree O(1) Change Detection

Before any agent begins work:
```python
python3 pm/.index/check-changes.py
```

If the root hash matches, nothing changed — skip re-reading files. If it doesn't, the
script reports exactly which files changed. The agent reads only those files instead of
re-scanning everything. This avoids filling context with unchanged file contents.

### 3. Task Prompt Scoping (Reference, Don't Inline)

When spawning sub-agents via Task, **reference files instead of inlining content**:

```
# Bad — inlines 200 lines of entity into the Task prompt, consuming parent + child tokens
Task(staff-engineer): "Implement this: [full TASK-004.md content pasted here]"

# Good — 40 tokens in the prompt, child reads the file itself (isolated context)
Task(staff-engineer): "Implement TASK-004. Read pm/entities/examples/TASK-004.md for
full spec. Files to modify: src/auth/jwt.ts, src/auth/keys.ts. Run tests when done."
```

The child agent's context is **isolated** from the parent. Content read by the child
doesn't consume the parent's window. This is the single most impactful context technique.

### 4. Compaction Strategy

- **Auto-compact** triggers at ~95% context usage — don't fight it
- **Manual `/compact`** before spawning a batch of Task calls — clears exploration
  artifacts so the parent has room for Task results
- **"Summarize from here"** (2.1.32) — use after a long planning phase to compress
  earlier reasoning before entering execution phase
- **Context percentage** is visible in the status line (`context_window.used_percentage`)
  — monitor it; if above 60% before spawning agents, compact first

### 5. MCP Tool Search Auto Mode

When many MCP tools are configured, their descriptions consume context on every turn.
Auto mode (default since 2.1.7) defers tool descriptions when they exceed 10% of the
context window, loading them on-demand via `MCPSearch` instead. Don't disable this.

If you configure new MCP servers, verify that auto mode is still reducing tool description
overhead by checking `/context` output.

### 6. Large Output Handling

Since 2.1.2, large tool outputs are **saved to disk** instead of being truncated inline.
The agent receives a file path reference instead of the full content. This means:

- A `Bash` command producing 50K chars of test output -> ~200 tokens (path reference)
- A `Read` of a 2000-line file -> file content in context (expected)
- Background task output -> capped at 30K chars with file path for overflow

**Implication**: Prefer Bash for operations that produce large output (test runs, builds)
because the output gets externalized. But prefer dedicated tools (Read, Grep) for
operations where you need the content in-context for reasoning.

---

## Prompting Patterns

### Task Delegation Prompt Structure

Every Task call should follow this template for consistency and token efficiency:

```
Task(<agent-type>): "<imperative verb> <what>.
Read <file-path> for full spec.
Scope: <file1>, <file2>, <file3>.
Acceptance: <1-2 line criteria>.
Run <verification command> when done."
```

Example:
```
Task(staff-engineer): "Implement JWT token generation.
Read pm/entities/examples/TASK-004.md for full spec.
Scope: src/auth/jwt.ts (create), src/auth/keys.ts (create), src/types/auth.ts (modify).
Acceptance: generateToken(user) returns signed JWT with RS256, tests pass.
Run: pytest tests/auth/ -v"
```

This is ~80 tokens. The agent reads the entity file in its own context (~300 tokens there,
0 tokens in the parent). Total parent cost per delegation: ~80 tokens + ~200 token result.

### Prompt Token Budget by Role

| Agent | Prompt Budget | Why |
|-------|--------------|-----|
| VP Product | 200-400 tokens | Strategic direction, references entity files |
| SDM | 100-200 tokens | Task assignment, file scope, acceptance criteria |
| Staff Engineer | 80-150 tokens | Specific implementation task with file list |
| Sprint Master | 50-100 tokens | Status query, metrics aggregation |
| Team Lead | 150-300 tokens | Multi-task coordination, dependency ordering |
| Implementer | 80-150 tokens | Same pattern as Staff Engineer |
| Tester | 100-200 tokens | Test scope, coverage targets, framework |
| Reviewer | 100-200 tokens | Review scope, security checklist, severity |

### What NOT to Put in Task Prompts

- CLAUDE.md content (agents inherit it automatically)
- Full file contents (agents can Read files themselves)
- Coding standards (already in the agent definition's body)
- Tool usage instructions (already in the system prompt)
- History of prior decisions (use `memory: project` for cross-session context)

### Subject / ActiveForm Convention

Every task entity and TaskCreate call uses two forms:

```yaml
subject: "Implement JWT generation"        # Imperative — what to do
activeForm: "Implementing JWT generation"  # Progressive — shown in spinner/status
```

Keep both under 60 characters. They appear in UI elements with limited width.

---

## Tool Optimization

### Dedicated Tools vs Bash

Dedicated tools produce **structured, compact output**. Bash produces **raw terminal
output** that is often verbose, includes ANSI codes, and consumes more context tokens.

| Operation | Dedicated Tool | Bash Equivalent | Token Savings |
|-----------|---------------|-----------------|---------------|
| Read file | `Read(path)` | `cat path` | ~10% (structured vs raw) |
| Edit file | `Edit(path, old, new)` | `sed -i 's/old/new/' path` | ~40% (diff vs full file echo) |
| Create file | `Write(path, content)` | `cat <<'EOF' > path` | ~20% (no shell overhead) |
| Find files | `Glob("**/*.ts")` | `find . -name "*.ts"` | ~30% (clean paths vs verbose find) |
| Search code | `Grep(pattern)` | `grep -rn pattern` | ~25% (structured matches) |
| Read PDF | `Read(path, pages="1-5")` | N/A | Only option for PDFs |

**Rule**: Reserve Bash exclusively for: running tests, building, installing deps, git
operations, and any command that requires shell execution.

### Tool Call Parallelism

Multiple independent tool calls in a single message execute in parallel:

```
# These run concurrently — total latency = max(individual latencies)
Read("src/auth/jwt.ts")
Read("src/auth/keys.ts")
Grep("generateToken", path="src/")
```

vs sequential:
```
# Turn 1: Read jwt.ts -> wait for response
# Turn 2: Read keys.ts -> wait for response
# Turn 3: Grep -> wait for response
# Total latency = sum of all latencies
```

**Prompt agents to batch independent reads at the start of a task**. A single turn with 5
parallel Reads costs the same latency as 1 Read, but 5 sequential Reads cost 5x the
round-trip time.

### Glob Before Grep

When searching for code patterns, use Glob first to narrow the file set, then Grep with
a path filter:

```
# Fast: Glob to find candidate files, then targeted Grep
Glob("src/auth/**/*.ts")                  -> 4 files
Grep("generateToken", path="src/auth/")   -> 2 matches

# Slow: Grep the entire repo
Grep("generateToken")  -> scans everything, returns many irrelevant matches
```

### Read with Pages for PDFs

Since 2.1.30, `Read` accepts a `pages` parameter for PDFs. Large PDFs (>10 pages) without
the parameter will fail. Always specify a range:

```
Read("docs/spec.pdf", pages="1-5")    # First 5 pages
Read("docs/spec.pdf", pages="12-15")  # Specific section
```

---

## MCP Server Usage

### Required Servers

| Server | Tool Pattern | Purpose | Token Impact |
|--------|-------------|---------|-------------|
| `memory` | `mcp__memory__*` | Knowledge graph persistence | Low — small JSON payloads |
| `git` | `mcp__git__*` | Git operations without Bash | Medium — diff output |

### MCP Wildcard Permissions

Use `mcp__<server>__*` in agent tool lists to allow all tools from a server without
enumerating them. This is more maintainable and lets MCP servers add new tools via
`list_changed` notifications (2.1.0) without requiring agent definition updates.

### Memory Server Patterns

The `memory` MCP server maintains a knowledge graph across sessions. Use it for:

- **Architecture decisions**: Store "chose X over Y because Z" so future sessions
  don't re-debate settled decisions
- **Dependency quirks**: Store "package X requires flag Y" so agents don't hit the
  same issue twice
- **Velocity baselines**: Store iteration metrics for trend analysis

**Token impact**: Memory queries return small JSON — typically 100-300 tokens per read.
Memory writes are even cheaper. The ROI is high because they prevent re-discovery cycles
that can cost 2,000+ tokens.

### Git Server vs Bash Git

`mcp__git__*` provides structured git operations. Use it for:
- Status checks (cleaner output than `git status`)
- Diffs (structured, easier to reason about)
- Log queries (formatted, less parsing overhead)

Use Bash git for:
- Push/pull (MCP git may not support all remote operations)
- Complex operations (rebase, cherry-pick)
- Operations requiring flags not exposed by the MCP server

---

## Token Reduction Strategies

### Strategy 1: Context Isolation via Task Tool

Every Task call creates an **isolated context**. The sub-agent's file reads, tool calls,
and reasoning don't consume the parent's window. The parent only pays for:

- The prompt (~80-200 tokens)
- The result summary (~200-500 tokens)

A Staff Engineer that reads 10 files and makes 20 edits might use 50,000 tokens in its
own context, but the SDM parent only sees ~300 tokens (prompt + result).

**Implication**: Aggressively delegate to sub-agents. Even small tasks benefit from context
isolation if the parent has a long session.

### Strategy 2: Minimal Tool Lists

Each agent's `tools` frontmatter restricts what tools are available. Fewer tools = fewer
tool descriptions in the system prompt = fewer tokens per turn.

| Agent Role | Tools Needed | Tools NOT Needed |
|-----------|-------------|-----------------|
| VP Product | Read, Write, Glob, Grep, WebSearch, WebFetch, Task | Edit, Bash (delegates implementation) |
| SDM | Read, Write, Edit, Glob, Grep, Bash, Task | WebSearch, WebFetch (delegates research) |
| Staff Engineer | Read, Write, Edit, Bash, Glob, Grep | Task (leaf node), WebSearch |
| Sprint Master | Read, Glob, Grep, Task | Write, Edit, Bash (read-only observer) |
| Reviewer | Read, Glob, Grep, WebSearch | Write, Edit, Bash (read-only) |

### Strategy 3: Pre-Computed Context

| Context Source | Tokens | Replaces |
|---------------|--------|----------|
| `.index/AGENT-INDEX.md` | ~800 | 5-15 exploration tool calls (~2,000+ tokens) |
| Merkle tree check | ~100 | Full filesystem re-scan (~3,000+ tokens) |
| Entity file reference | ~40 | Inlined entity content (~300+ tokens in parent) |
| Memory server query | ~200 | Re-discovery conversation (~2,000+ tokens) |

### Strategy 4: Avoid Conversational Overhead

Agents should not:
- Explain what they're about to do before doing it (just do it)
- Ask permission for actions within their scope (tools list is the permission)
- Summarize intermediate results unless asked (the Task result is the summary)
- Re-read files they've already read in the same session

### Strategy 5: Compact Before Fan-Out

Before an SDM spawns 3 Staff Engineers, compact the conversation:
```
/compact  ->  frees ~40-60% of context  ->  spawn 3 Task(staff-engineer) calls
```

This ensures the SDM has room for all 3 result summaries without hitting auto-compact
mid-execution (which interrupts flow and adds compaction tokens).

---

## Latency Reduction Strategies

### Strategy 1: Fast Mode for Throughput Tasks

Opus 4.6 fast mode (2.1.36) produces output faster without switching models. Toggle it
for throughput-bound work:

| Phase | Mode | Why |
|-------|------|-----|
| Planning, architecture | Normal | Deep reasoning needed |
| Task delegation (fan-out) | Fast | Prompt construction is formulaic |
| Status checks, metrics | Fast | Simple aggregation |
| Code review | Normal | Nuanced analysis needed |
| Entity updates, commits | Fast | Mechanical operations |

Agents can't toggle their own mode, but the human operator can toggle per-session.
For Agent Teams (tmux multi-session), set fast mode on sessions doing mechanical work.

### Strategy 2: Parallel Task Spawning

Launch all independent sub-agents in a **single message** with multiple Task calls:

```
# Single message, 3 parallel Tasks — total latency ~ slowest task
Task(staff-engineer): "Implement jwt.ts. Scope: src/auth/jwt.ts"
Task(staff-engineer): "Implement keys.ts. Scope: src/auth/keys.ts"
Task(staff-engineer): "Write auth tests. Scope: tests/auth/"
```

vs sequential:
```
# 3 turns, 3 serial Tasks — total latency = sum of all tasks
Turn 1: Task(staff-engineer): "Implement jwt.ts" -> wait -> result
Turn 2: Task(staff-engineer): "Implement keys.ts" -> wait -> result
Turn 3: Task(staff-engineer): "Write tests" -> wait -> result
```

Parallel spawning is **the highest-impact latency optimization**. A 3-task fan-out that
takes 5 minutes sequentially takes ~2 minutes in parallel.

### Strategy 3: Background Tasks (Ctrl+B)

For long-running operations in interactive sessions, press `Ctrl+B` to background:

- The task continues running without blocking the session
- Completion triggers a notification (and `TaskCompleted` hook if configured)
- Output is capped at 30K chars with a file path for the full result
- Multiple foreground tasks can be backgrounded simultaneously (2.1.0)

Use this for: test suites, builds, large file generation, anything >30 seconds.

### Strategy 4: Pre-Warm with AGENT-INDEX.md

An agent that reads AGENT-INDEX.md as its first action skips the filesystem exploration
phase entirely. This saves 3-5 round trips (10-20 seconds) at the start of every session.

### Strategy 5: Hook Events for Reactive Scheduling

Instead of polling sub-agents for completion, use hook events:

- `TaskCompleted` -> immediately assign next task (no idle gap)
- `TeammateIdle` -> immediately check backlog (no waiting for the parent to notice)

This eliminates the latency between one task ending and the next beginning.

---

## Parallelization Without Worktrees

### Technique 1: File-Scope Partitioning

Assign each sub-agent a **non-overlapping set of files** at spawn time:

```
Task(staff-engineer): "Implement auth service.
Scope: src/auth/jwt.ts (create), src/auth/keys.ts (create).
DO NOT modify files outside this scope."

Task(staff-engineer): "Implement auth middleware.
Scope: src/middleware/auth.ts (create), src/middleware/validate.ts (create).
DO NOT modify files outside this scope."
```

Agents working on disjoint file sets can run in parallel on the **same branch** without
conflicts. The key is making scope explicit in the prompt — don't leave it implicit.

### Technique 2: Domain Directory Isolation

Structure the codebase so each domain owns a directory:

```
src/
├── auth/         <- Backend SDM scope
├── ui/           <- Frontend SDM scope
├── infra/        <- Infrastructure SDM scope
└── shared/       <- Coordinated (no parallel writes)
```

SDMs assign agents within their domain directory. Cross-domain changes go through the
`shared/` directory with explicit coordination (one agent at a time for shared files).

### Technique 3: Branch-Per-Agent with Sequential Merge

When file-scope isolation isn't possible:

1. Each agent works on its own branch: `feat/<task-id>-<description>`
2. Agents run in parallel, each committing to their branch
3. A coordinator (SDM or Team Lead) merges branches sequentially
4. Merge conflicts are resolved by the coordinator, not the agents

This requires the coordinator to have Bash + git access. The merge step is serial but
fast (typically <1 minute per branch).

### Technique 4: Entity-Based Coordination

Use entity files as lightweight coordination primitives:

```yaml
# entities/examples/TASK-004.md
status: in_progress
owner: "staff-engineer-1"     # Lock — other agents skip this task
```

Before starting work, an agent reads the entity and checks:
- Is `status` already `in_progress`? -> Skip, pick another task
- Is `owner` set? -> Skip, someone else has it

After completing, the agent updates:
- `status: completed`
- `owner: null` (release the lock)
- `version: +0.1.0`

This is optimistic concurrency — no explicit locking, just convention. It works because
agents read-before-write and entity files are small (no merge conflicts on status changes).

### Technique 5: Pipeline Parallelism (Staggered Fan-Out)

Instead of waiting for all implementation to finish before testing:

```
Phase 1: Spawn 3 implementers (parallel)
Phase 2: As each implementer completes (TaskCompleted hook), immediately spawn a tester
          for that specific feature — don't wait for all 3 to finish
Phase 3: As each tester completes, spawn a reviewer for that feature
```

This creates a **pipeline** where testing begins as soon as the first implementation lands,
rather than waiting for the slowest implementer. Total wall-clock time approaches the
critical path length instead of the sum of all phases.

### Technique 6: Read-Only Agents in Parallel

Agents that only read (Reviewer, Sprint Master) can run concurrently with agents that
write, because they don't create conflicts:

```
# These can all run simultaneously
Task(staff-engineer): "Implement feature X" (writes src/feature.ts)
Task(reviewer): "Review existing auth module" (reads src/auth/)
Task(sprint-master): "Calculate current velocity" (reads entities/)
```

Restrict read-only agents to `Read`, `Glob`, `Grep` tools (no Write, Edit, Bash) to
guarantee they can't accidentally mutate state.

---

## Multi-Team Coordination Patterns

### Pattern 1: Hub-and-Spoke (Default)

```
       VP Product (hub)
      / |  |  \
   SDM  SDM  SDM  Sprint Master
   /|\  /|\  /|\
  SE SE SE SE SE SE SE SE SE (spokes)
```

All coordination flows through the VP Product. SDMs don't communicate directly with each
other — they report up to VP Product, who resolves cross-domain issues.

**Pros**: Simple, clear ownership, no cross-talk overhead
**Cons**: VP Product is a bottleneck for cross-domain decisions

### Pattern 2: Shared-Nothing Domains

Each SDM gets a fully independent scope:

```
SDM-Frontend:  src/ui/**, tests/ui/**, docs/frontend/**
SDM-Backend:   src/api/**, tests/api/**, docs/backend/**
SDM-Infra:     infra/**, .github/**, Dockerfile, docker-compose.yml
```

No shared files. Cross-domain integration happens through well-defined interfaces (API
contracts, event schemas) that are agreed upon before parallel execution begins.

**Pros**: Maximum parallelism, zero merge conflicts
**Cons**: Requires upfront interface design

### Pattern 3: Integration Branch

For work that must touch shared files:

1. Each domain works on `feat/<domain>-<task>`
2. An integration branch `integration/<iteration>` collects domain work
3. The Team Lead merges domains into the integration branch one at a time
4. CI runs on the integration branch to catch cross-domain issues
5. Integration branch merges to main once green

This separates "parallel domain work" from "serial integration" cleanly.

### Pattern 4: Event-Driven Coordination

Use hooks and entity status changes as an event bus:

```
Staff Engineer completes TASK-004
  -> TaskCompleted hook fires in SDM
  -> SDM updates TASK-004.md status to completed
  -> SDM checks: all tasks in STORY-002 complete?
    -> Yes: SDM updates STORY-002 status, notifies VP Product
    -> No: SDM assigns next task from STORY-002 to idle engineer
```

No polling, no manual status checks. The hook chain drives execution forward
automatically.

---

## Frontmatter Schema Reference

```yaml
---
name: <agent-name>              # Required: unique identifier
description: <one-liner>        # Required: agent purpose
model: claude-opus-4-6          # Required: always Opus 4.6
memory: project                 # Required: project | local | user
tools:                          # Required: minimal set for the role
  - Task(agent-type)            # Restricts sub-agent types
  - Read                        # Structured file reading
  - Edit                        # Precise string replacement
  - Write                       # Full file creation
  - Bash                        # Shell execution (tests, build, git)
  - Glob                        # File pattern matching
  - Grep                        # Content search
  - WebSearch                   # Web search
  - WebFetch                    # URL content retrieval
  - mcp__memory__*              # Memory server (all tools)
  - mcp__git__*                 # Git server (all tools)
hooks:                          # Optional: event handlers
  TeammateIdle:
    - command: "<lightweight shell command>"
  TaskCompleted:
    - command: "<lightweight shell command>"
  PreToolUse:
    - matcher: "<tool-name>"
      command: "<validation command>"
  PostToolUse:
    - matcher: "<tool-name>"
      command: "<post-action command>"
---
```

---

## Checklists

### Adding a New Agent

1. Create file with frontmatter (all fields required, model is always `claude-opus-4-6`)
2. Determine minimal tool set — fewer tools = less context overhead per turn
3. Update parent agent's `tools` to include `Task(<new-agent>)`
4. Add `hooks` only if the agent coordinates sub-agents
5. Keep the body prompt under 2,000 tokens — reference CLAUDE.md and AGENT-INDEX.md
6. Regenerate merkle tree: `python3 pm/.index/generate-merkle.py`
7. Run tests: `./pm/tests/run-tests.sh`
8. Commit: `feat(agents): add <name> agent`

### Modifying Agent Prompts for Token Efficiency

1. Measure: count tokens in the agent body (approximate: words * 1.3)
2. Remove anything already covered by CLAUDE.md or AGENT-INDEX.md
3. Replace inline examples with file references
4. Convert prose paragraphs to bullet lists (typically 30% shorter)
5. Remove version tags in section headers if the feature is now standard
6. Verify the agent still works by running a test task

---

## Anti-Patterns

| Anti-Pattern | Why It's Bad | What to Do Instead |
|-------------|-------------|-------------------|
| Mixed model hierarchy | Different prompt patterns per tier, weaker sub-agents | Uniform Opus 4.6 + fast mode for throughput |
| Inlining file content in Task prompts | Doubles token cost (parent + child) | Reference file paths, child reads in its own context |
| Unrestricted `Task` (no agent_type) | Sub-agents can spawn anything, wasting tokens on wrong types | Always use `Task(specific-type)` |
| Sequential Task spawning | N tasks = N * latency | Parallel Task calls in a single message |
| Agents explaining before acting | Wastes tokens on narration | Configure agents to act, report results only |
| Shared file writes without scope | Merge conflicts, corrupted files | File-scope partitioning in every Task prompt |
| Polling for sub-agent completion | Wastes parent tokens on status checks | Use TeammateIdle / TaskCompleted hooks |
| Heavy computation in hooks | Blocks the event loop, adds latency | Hooks should be lightweight signals only |
| Re-reading unchanged files | Wastes context on known content | Check merkle tree first, read only changed files |
| Git worktrees for parallelism | Complex setup, state management overhead | File-scope partitioning + branch-per-agent |
