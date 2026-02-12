---
source: https://github.com/asheshgoplani/agent-deck
fetched: 2026-02-11
type: github-repo
repo: asheshgoplani/agent-deck
stars: 749
language: Go
---

# agent-deck

Terminal session manager for AI coding agents. One TUI for Claude, Gemini, OpenCode, Codex, and more.

**Stars**: 749 | **Language**: Go | **License**: MIT License | **Last Updated**: 2026-02-12T04:16:09Z

## README

<div align="center">

<!-- Status Grid Logo -->
<img src="site/logo.svg" alt="Agent Deck Logo" width="120">

# Agent Deck

**Your AI agent command center**

[![GitHub Stars](https://img.shields.io/github/stars/asheshgoplani/agent-deck?style=for-the-badge&logo=github&color=yellow&labelColor=1a1b26)](https://github.com/asheshgoplani/agent-deck/stargazers)
[![Go Version](https://img.shields.io/badge/Go-1.24+-00ADD8?style=for-the-badge&logo=go&labelColor=1a1b26)](https://go.dev)
[![License](https://img.shields.io/badge/License-MIT-9ece6a?style=for-the-badge&labelColor=1a1b26)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20WSL-7aa2f7?style=for-the-badge&labelColor=1a1b26)](https://github.com/asheshgoplani/agent-deck)
[![Latest Release](https://img.shields.io/github/v/release/asheshgoplani/agent-deck?style=for-the-badge&color=e0af68&labelColor=1a1b26)](https://github.com/asheshgoplani/agent-deck/releases)
[![Discord](https://img.shields.io/discord/1469423271144587379?style=for-the-badge&logo=discord&logoColor=white&label=Discord&color=5865F2&labelColor=1a1b26)](https://discord.gg/e4xSs6NBN8)

[Features](#features) . [Conductor](#conductor) . [Install](#installation) . [Quick Start](#quick-start) . [Docs](#documentation) . [Discord](https://discord.gg/e4xSs6NBN8) . [FAQ](#faq)

</div>

## The Problem

Running Claude Code on 10 projects? OpenCode on 5 more? Another agent somewhere in the background?

**Managing multiple AI sessions gets messy fast.** Too many terminal tabs. Hard to track what's running, what's waiting, what's done. Switching between projects means hunting through windows.

## The Solution

**Agent Deck is mission control for your AI coding agents.**

One terminal. All your agents. Complete visibility.

- **See everything at a glance** — running, waiting, or idle status for every agent instantly
- **Switch in milliseconds** — jump between any session with a single keystroke
- **Stay organized** — groups, search, notifications, and git worktrees keep everything manageable

## Features

### Fork Sessions

Try different approaches without losing context. Fork any Claude conversation instantly. Each fork inherits the full conversation history.

- Press `f` for quick fork, `F` to customize name/group
- Fork your forks to explore as many branches as you need

### MCP Manager

Attach MCP servers without touching config files. Need web search? Browser automation? Toggle them on per project or globally. Agent Deck handles the restart automatically.

- Press `M` to open, `Space` to toggle, `Tab` to cycle scope (LOCAL/GLOBAL)
- Define your MCPs once in `~/.agent-deck/config.toml`, then toggle per session

### MCP Socket Pool

Running many sessions? Socket pooling shares MCP processes across all sessions via Unix sockets, reducing MCP memory usage by 85-90%. Connections auto-recover from MCP crashes in ~3 seconds via a reconnecting proxy. Enable with `pool_all = true` in config.toml.

### Search

Press `/` to fuzzy-search across all sessions. Filter by status with `!` (running), `@` (waiting), `#` (idle), `$` (error). Press `G` for global search across all Claude conversations.

### Status Detection

Smart polling detects what every agent is doing right now:

| Status | Symbol | What It Means |
|--------|--------|---------------|
| **Running** | `●` green | Agent is actively working |
| **Waiting** | `◐` yellow | Needs your input |
| **Idle** | `○` gray | Ready for commands |
| **Error** | `✕` red | Something went wrong |

### Notification Bar

Waiting sessions appear right in your tmux status bar. Press `Ctrl+b 1-6` to jump directly to them.

```
⚡ [1] frontend [2] api [3] backend
```

### Git Worktrees

Multiple agents can work on the same repo without conflicts. Each worktree is an isolated working directory with its own branch.

- `agent-deck add . -c claude --worktree feature/a --new-branch` creates a session in a new worktree
- `agent-deck add . --worktree feature/b -b --location subdirectory` places the worktree under `.worktrees/` inside the repo
- `agent-deck worktree finish "My Session"` merges the branch, removes the worktree, and deletes the session
- `agent-deck worktree cleanup` finds and removes orphaned worktrees

Configure the default worktree location in `~/.agent-deck/config.toml`:

```toml
[worktree]
default_location = "subdirectory"  # "sibling" (default), "subdirectory", or a custom path
```

### Conductor

Conductors are persistent Claude Code sessions that monitor and orchestrate all your other sessions. They watch for sessions that need help, auto-respond when confident, and escalate to you when they can't. Optionally connect Telegram for mobile control.

Create as many conductors as you need per profile:

```bash
# First-time setup (asks about Telegram, then creates the conductor)
agent-deck -p work conductor setup ops --description "Ops monitor"

# Add more conductors to the same profile (no prompts)
agent-deck -p work conductor setup infra --no-heartbeat --description "Infra watcher"
agent-deck conductor setup personal --description "Personal project monitor"
```

Each conductor gets its own directory, identity, and heartbeat settings.

**CLI commands:**

```bash
agent-deck conductor list                    # List all conductors
agent-deck conductor list --profile work     # Filter by profile
agent-deck conductor status                  # Health check (all)
agent-deck conductor status ops              # Health check (specific)
agent-deck conductor teardown ops            # Stop a conductor
agent-deck conductor teardown --all --remove # Remove everything
```

### Multi-Tool Support

Agent Deck works with any terminal-based AI tool:

| Tool | Integration Level |
|------|-------------------|
| **Claude Code** | Full (status, MCP, fork, resume) |
| **Gemini CLI** | Full (status, MCP, resume) |
| **OpenCode** | Status detection, organization |
| **Codex** | Status detection, organization |
| **Cursor** (terminal) | Status detection, organization |
| **Custom tools** | Configurable via `[tools.*]` in config.toml |

## Installation

**Works on:** macOS, Linux, Windows (WSL)

```bash
curl -fsSL https://raw.githubusercontent.com/asheshgoplani/agent-deck/main/install.sh | bash
```

Then run: `agent-deck`

**Other install methods:**

**Homebrew**
```bash
brew install asheshgoplani/tap/agent-deck
```

**Go**
```bash
go install github.com/asheshgoplani/agent-deck/cmd/agent-deck@latest
```

**From Source**
```bash
git clone https://github.com/asheshgoplani/agent-deck.git && cd agent-deck && make install
```

### Claude Code Skill

Install the agent-deck skill for AI-assisted session management:

```bash
/plugin marketplace add asheshgoplani/agent-deck
/plugin install agent-deck@agent-deck
```

## Quick Start

```bash
agent-deck                        # Launch TUI
agent-deck add . -c claude        # Add current dir with Claude
agent-deck session fork my-proj   # Fork a Claude session
agent-deck mcp attach my-proj exa # Attach MCP to session
```

### Key Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Attach to session |
| `n` | New session |
| `f` / `F` | Fork (quick / dialog) |
| `M` | MCP Manager |
| `/` / `G` | Search / Global search |
| `r` | Restart session |
| `d` | Delete |
| `?` | Full help |

## Documentation

| Guide | What's Inside |
|-------|---------------|
| [CLI Reference](skills/agent-deck/references/cli-reference.md) | Commands, flags, scripting examples |
| [Configuration](skills/agent-deck/references/config-reference.md) | config.toml, MCP setup, custom tools, socket pool |
| [TUI Reference](skills/agent-deck/references/tui-reference.md) | Keyboard shortcuts, status indicators, navigation |
| [Troubleshooting](skills/agent-deck/references/troubleshooting.md) | Common issues, debugging, recovery, uninstalling |

## FAQ

**How is this different from just using tmux?**

Agent Deck adds AI-specific intelligence on top of tmux: smart status detection (knows when Claude is thinking vs. waiting), session forking with context inheritance, MCP management, global search across conversations, and organized groups. Think of it as tmux plus AI awareness.

**Can I use it on Windows?**

Yes, via WSL (Windows Subsystem for Linux). Install WSL, then run the installer inside WSL. WSL2 is recommended for full feature support including MCP socket pooling.

**Will it interfere with my existing tmux setup?**

No. Agent Deck creates its own tmux sessions with the prefix `agentdeck_*`. Your existing sessions are untouched. The installer backs up your `~/.tmux.conf` before adding optional config, and you can skip it with `--skip-tmux-config`.

**Full README available at**: https://github.com/asheshgoplani/agent-deck

## License

MIT License — see [LICENSE](LICENSE)
