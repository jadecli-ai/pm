# Claude Code Subagents

> Source: https://code.claude.com/docs/en/sub-agents

## Overview

Subagents are specialized AI assistants that handle specific types of tasks. Each subagent runs in its own context window with a custom system prompt, specific tool access, and independent permissions.

## Built-in Subagents

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| **Explore** | Haiku | Read-only | File discovery, code search, codebase exploration |
| **Plan** | Inherits | Read-only | Codebase research for planning mode |
| **General-purpose** | Inherits | All tools | Complex research, multi-step operations |
| **Bash** | Inherits | Terminal | Running terminal commands in separate context |
| **Claude Code Guide** | Haiku | - | Questions about Claude Code features |

## Subagent Scope Priority

| Location | Scope | Priority |
|----------|-------|----------|
| `--agents` CLI flag | Current session | 1 (highest) |
| `.claude/agents/` | Current project | 2 |
| `~/.claude/agents/` | All your projects | 3 |
| Plugin's `agents/` directory | Where plugin is enabled | 4 (lowest) |

## Subagent File Format

```yaml
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep
model: sonnet
---

You are a code reviewer. When invoked, analyze the code and provide
specific, actionable feedback on quality, security, and best practices.
```

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier using lowercase letters and hyphens |
| `description` | Yes | When Claude should delegate to this subagent |
| `tools` | No | Tools the subagent can use. Inherits all if omitted |
| `disallowedTools` | No | Tools to deny |
| `model` | No | `sonnet`, `opus`, `haiku`, or `inherit` |
| `permissionMode` | No | `default`, `acceptEdits`, `delegate`, `dontAsk`, `bypassPermissions`, or `plan` |
| `maxTurns` | No | Maximum number of agentic turns |
| `skills` | No | Skills to preload into context |
| `mcpServers` | No | MCP servers available to this subagent |
| `hooks` | No | Lifecycle hooks scoped to this subagent |
| `memory` | No | Persistent memory scope: `user`, `project`, or `local` |

## Persistent Memory for Subagents

The `memory` field gives the subagent a persistent directory that survives across conversations.

### Memory Scopes

| Scope | Location | Use when |
|-------|----------|----------|
| `user` | `~/.claude/agent-memory/<name>/` | subagent should remember learnings across all projects |
| `project` | `.claude/agent-memory/<name>/` | knowledge is project-specific and shareable via version control |
| `local` | `.claude/agent-memory-local/<name>/` | knowledge is project-specific but shouldn't be version controlled |

### Memory Structure

```
~/.claude/agent-memory/code-reviewer/
├── MEMORY.md           # Primary file, first 200 lines loaded
├── react-patterns.md   # Topic-specific files
└── security-checklist.md
```

### How Memory Works

When memory is enabled:
- The subagent's system prompt includes instructions for reading and writing to the memory directory
- The first 200 lines of `MEMORY.md` are injected into the agent's system prompt
- Read, Write, and Edit tools are automatically enabled for memory management
- Agents organize details into topic-specific files when exceeding 200 lines

### Memory Example

```yaml
---
name: code-reviewer
description: Reviews code for quality and best practices
memory: user
---

You are a code reviewer. As you review code, update your agent memory with
patterns, conventions, and recurring issues you discover.
```

## Hooks for Subagents

### In Subagent Frontmatter

```yaml
---
name: code-reviewer
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
---
```

### In settings.json

```json
{
  "hooks": {
    "SubagentStart": [
      {
        "matcher": "db-agent",
        "hooks": [
          { "type": "command", "command": "./scripts/setup-db.sh" }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          { "type": "command", "command": "./scripts/cleanup.sh" }
        ]
      }
    ]
  }
}
```

## Foreground vs Background Subagents

- **Foreground**: Block main conversation until complete. Permission prompts pass through to user.
- **Background**: Run concurrently. Pre-approve permissions before launch. Auto-deny unpermitted actions.

## Best Practices

* **Design focused subagents**: Each should excel at one specific task
* **Write detailed descriptions**: Claude uses this to decide when to delegate
* **Limit tool access**: Grant only necessary permissions
* **Check into version control**: Share project subagents with your team
