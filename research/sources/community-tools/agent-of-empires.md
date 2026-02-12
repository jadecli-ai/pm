---
source: https://github.com/njbrake/agent-of-empires
fetched: 2026-02-11
type: github-repo
repo: njbrake/agent-of-empires
stars: 627
language: Rust
license: MIT
---

# Agent of Empires (AoE)

Claude Code, OpenCode, Mistral Vibe, Codex CLI, Gemini CLI Coding Agent Terminal Session manager via tmux and git Worktrees. A terminal session manager for AI coding agents on Linux and macOS. Built on tmux, written in Rust.

**Stars**: 627 | **Language**: Rust | **License**: MIT | **Last Updated**: 2026-02-12

## README

Run multiple AI agents in parallel across different branches of your codebase, each in its own isolated session with optional Docker sandboxing.

### Features

- **Multi-agent support** -- Claude Code, OpenCode, Mistral Vibe, Codex CLI, and Gemini CLI
- **TUI dashboard** -- visual interface to create, monitor, and manage sessions
- **Agent + terminal views** -- toggle between AI agents and paired shell terminals with `t`
- **Status detection** -- see which agents are running, waiting for input, or idle
- **Git worktrees** -- run parallel agents on different branches of the same repo
- **Docker sandboxing** -- isolate agents in containers with shared auth volumes
- **Diff view** -- review git changes and edit files without leaving the TUI
- **Per-repo config** -- `.aoe/config.toml` for project-specific settings and hooks
- **Profiles** -- separate workspaces for different projects or clients
- **CLI and TUI** -- full functionality from both interfaces

### How It Works

AoE wraps tmux. Each session is a tmux session, so agents keep running when you close the TUI. Reopen `aoe` and everything is still there.

Key tmux shortcut: **`Ctrl+b d`** detaches from a session and returns to the TUI.

### Installation

Prerequisites: tmux (required), Docker (optional, for sandboxing)

```bash
# Quick install (Linux & macOS)
curl -fsSL \
  https://raw.githubusercontent.com/njbrake/agent-of-empires/main/scripts/install.sh \
  | bash

# Homebrew
brew install njbrake/aoe/aoe

# Build from source
git clone https://github.com/njbrake/agent-of-empires
cd agent-of-empires && cargo build --release
```

### Quick Start

```bash
# Launch the TUI
aoe

# Add a session from CLI
aoe add /path/to/project

# Add a session on a new git branch
aoe add . -w feat/my-feature -b

# Add a sandboxed session
aoe add --sandbox .
```

In the TUI: `n` to create a session, `Enter` to attach, `t` to toggle terminal view, `D` for diff view, `d` to delete, `?` for help.

### Documentation

- [Installation](https://njbrake.github.io/agent-of-empires/installation)
- [Quick Start](https://njbrake.github.io/agent-of-empires/quick-start)
- [Workflow Guide](https://njbrake.github.io/agent-of-empires/guides/workflow) - bare repos and worktrees
- [Docker Sandbox](https://njbrake.github.io/agent-of-empires/guides/sandbox) - container isolation
- [Repo Config & Hooks](https://njbrake.github.io/agent-of-empires/guides/repo-config) - per-project settings
- [Configuration Reference](https://njbrake.github.io/agent-of-empires/guides/configuration)
- [CLI Reference](https://njbrake.github.io/agent-of-empires/cli/reference)

### FAQ

**What happens when I close aoe?**
Nothing. Sessions are tmux sessions running in the background. Open and close `aoe` as often as you like.

**Which AI tools are supported?**
Claude Code, OpenCode, Mistral Vibe, Codex CLI, and Gemini CLI. AoE auto-detects which are installed.

### Development

```bash
cargo check          # Type-check
cargo test           # Run tests
cargo fmt            # Format
cargo clippy         # Lint
cargo build --release  # Release build

# Debug logging
AGENT_OF_EMPIRES_DEBUG=1 cargo run
```

Inspired by [agent-deck](https://github.com/asheshgoplani/agent-deck) (Go + Bubble Tea).
