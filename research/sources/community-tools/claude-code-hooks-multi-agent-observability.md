---
source: https://github.com/disler/claude-code-hooks-multi-agent-observability
fetched: 2026-02-11
type: github-repo
repo: disler/claude-code-hooks-multi-agent-observability
stars: 1083
language: Python
---

# Multi-Agent Observability System

Real-time monitoring and visualization for Claude Code agents through comprehensive hook event tracking. With Claude Opus 4.6 and multi-agent orchestration, you can spin up teams of specialized agents that work in parallel, and this observability system lets you trace every tool call, task handoff, and agent lifecycle event across the entire swarm.

**Stars**: 1083 | **Language**: Python | **License**: N/A | **Last Updated**: 2026-02-12

## Architecture

```
Claude Agents -> Hook Scripts -> HTTP POST -> Bun Server -> SQLite -> WebSocket -> Vue Client
```

## Setup Requirements

- Claude Code - Anthropic's official CLI
- Astral uv - Fast Python package manager (for hook scripts)
- Bun, npm, or yarn - For running server and client
- just (optional) - Command runner
- Anthropic API Key

## Quick Start

```bash
# 1. Start both server and client
just start          # or: ./scripts/start-system.sh

# 2. Open http://localhost:5173 in your browser

# 3. Open Claude Code and run a command

# 4. Watch events stream in the client

# 5. Copy .claude folder to other projects
cp -R .claude <directory of your codebase>
```

## Hook System

12 hook event types supported:

| Event Type | Emoji | Purpose |
|---|---|---|
| PreToolUse | 🔧 | Before tool execution |
| PostToolUse | ✅ | After tool completion |
| PostToolUseFailure | ❌ | Tool execution failed |
| PermissionRequest | 🔐 | Permission requested |
| Notification | 🔔 | User interactions |
| Stop | 🛑 | Response completion |
| SubagentStart | 🟢 | Subagent started |
| SubagentStop | 👥 | Subagent finished |
| PreCompact | 📦 | Context compaction |
| UserPromptSubmit | 💬 | User prompt submission |
| SessionStart | 🚀 | Session started |
| SessionEnd | 🏁 | Session ended |

## Project Structure

```
claude-code-hooks-multi-agent-observability/
├── apps/
│   ├── server/          # Bun TypeScript server (SQLite, WebSocket)
│   └── client/          # Vue 3 TypeScript client (real-time dashboard)
├── .claude/
│   ├── hooks/           # 12+ Python hook scripts
│   ├── agents/team/     # Agent team definitions (builder, validator)
│   ├── commands/        # Custom slash commands
│   └── settings.json    # Hook configuration
├── justfile             # Task runner recipes
└── scripts/             # Start/stop/test utilities
```

## Agent Teams

- **Builder** (`builder.md`): Engineering agent, one task at a time, includes PostToolUse hooks for ruff and ty validation
- **Validator** (`validator.md`): Read-only validation agent, cannot use Write/Edit/NotebookEdit

## Key Features

- Real-time WebSocket updates to Vue dashboard
- Multi-criteria filtering (app, session, event type)
- Live pulse chart with session-colored bars
- Chat transcript viewer with syntax highlighting
- Dual-color system: App colors + Session colors
- Tool emoji system for visual event identification
- MCP tool detection with `mcp_server` and `mcp_tool_name` fields
- `stop_hook_active` guard to prevent infinite hook loops
- Stop hook validators for plan file validation
- Blocks dangerous `rm -rf` commands via `deny_tool()` JSON pattern

## Technical Stack

- **Server**: Bun, TypeScript, SQLite (WAL mode)
- **Client**: Vue 3, TypeScript, Vite, Tailwind CSS
- **Hooks**: Python 3.11+, Astral uv
- **Communication**: HTTP REST, WebSocket

## Integration

Copy the event sender to any project:
```bash
cp .claude/hooks/send_event.py YOUR_PROJECT/.claude/hooks/
```

Add to your `.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": ".*",
      "hooks": [{
        "type": "command",
        "command": "uv run .claude/hooks/send_event.py --source-app YOUR_APP --event-type PreToolUse"
      }]
    }]
  }
}
```
