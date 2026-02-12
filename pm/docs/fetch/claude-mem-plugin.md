# Claude-Mem: Persistent Memory Plugin

> Source: https://github.com/thedotmack/claude-mem

## Overview

Claude-Mem is a plugin by Alex Newman that automatically captures and compresses coding session context, enabling Claude to maintain knowledge continuity across separate sessions.

## Core Features

- **Automatic capture**: Records observations from all tool usage
- **AI compression**: Compresses session data for efficient storage
- **Semantic search**: Chroma vector database enables natural language queries
- **Progressive disclosure**: Layered context injection with token cost visibility
- **Privacy control**: `<private>` tags exclude sensitive content

## Installation

```bash
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

Context automatically appears in subsequent sessions after restart.

## Architecture

### Lifecycle Hooks
- SessionStart
- UserPromptSubmit
- PostToolUse
- Stop
- SessionEnd

### Storage
- SQLite for persistence
- Chroma vector database for semantic search
- Three-layer retrieval workflow optimizes token usage

### Memory Retrieval
1. Start with compact indexes
2. Fetch full details only for relevant results
3. Inject context with token cost visibility

## MCP Tools

| Tool | Purpose |
|------|---------|
| `search` | Query session history |
| `timeline` | View chronological events |
| `get_observations` | Retrieve specific observations |
| `save_memory` | Manually save context |

## Configuration

Settings managed in `~/.claude-mem/settings.json`

## Web Interface

Real-time memory viewing at `localhost:37777`

## Requirements

- Node.js 18.0.0+
- Bun (auto-installed)
- SQLite 3
- Latest Claude Code with plugin support
