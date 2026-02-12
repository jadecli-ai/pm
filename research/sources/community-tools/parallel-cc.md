---
source: https://github.com/frankbria/parallel-cc
fetched: 2026-02-11
type: github-repo
repo: frankbria/parallel-cc
stars: 6
language: TypeScript
---

# parallel-cc

Automated parallel management of Claude Code versions using Git worktrees and autonomous coordination between agents in separate terminals

**Stars**: 6 | **Language**: TypeScript | **License**: MIT License | **Last Updated**: 2026-02-05T22:10:51Z

## README

# parallel-cc

[![Follow on X](https://img.shields.io/twitter/follow/FrankBria18044?style=social)](https://x.com/FrankBria18044)
[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/frankbria/parallel-cc)
[![Node.js](https://img.shields.io/badge/node-%3E%3D20.0.0-brightgreen.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Coordinate parallel Claude Code sessions using git worktrees + E2B cloud sandboxes for autonomous execution.

**parallel-cc** enables both interactive and autonomous Claude Code workflows:
- **Local mode**: Parallel worktree coordination for interactive development
- **E2B Sandbox mode**: Long-running autonomous execution in isolated cloud VMs
- **Parallel Sandbox mode** (NEW): Execute multiple tasks simultaneously across sandboxes

## Table of Contents

- [Features](#-features)
- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [How It Works](#how-it-works)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [CLI Commands](#-cli-commands)
- [How Sessions Work](#-how-sessions-work)
- [Configuration](#️-configuration)
- [Merging Work from Worktrees](#-merging-work-from-worktrees)
- [E2B Sandbox Integration](#-e2b-sandbox-integration)
- [What's New](#-whats-new)
- [Roadmap](#️-roadmap)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## Features

### Local Parallel Sessions
- **Automatic worktree creation** - No manual setup required
- **SQLite-based coordination** - Fast, reliable session tracking
- **Auto-cleanup** - Worktrees removed when sessions end
- **Heartbeat monitoring** - Detect and clean up stale sessions
- **Zero configuration** - Works out of the box
- **Merge detection** - Know when parallel branches are merged
- **Conflict checking** - Preview rebase conflicts before they happen
- **MCP integration** - Claude can query session status and assist with rebases
- **File claims** - Coordinate exclusive/shared file access across parallel sessions
- **Conflict resolution** - Track and resolve semantic, structural, and concurrent edit conflicts
- **Auto-fix suggestions** - AI-generated conflict resolutions with confidence scores
- **AST analysis** - Deep semantic conflict detection using abstract syntax trees

### E2B Sandbox Execution
- **Cloud sandboxes** - Execute Claude Code in isolated E2B VMs
- **Long-running tasks** - Up to 1 hour of uninterrupted execution
- **Security hardened** - Shell injection prevention, input validation, resource cleanup
- **Intelligent file sync** - Compressed upload/download with selective sync
- **Cross-process reconnection** - Access sandboxes created in separate CLI invocations
- **Full CLI control** - Run, monitor, download, and kill sandbox sessions
- **Cost tracking** - Automatic warnings at 30min and 50min usage marks
- **Branch management** - Auto-generate branches, custom naming, or uncommitted changes
- **Git Live mode** - Push directly to remote and create PRs automatically
- **Dual authentication** - Support for both API key and OAuth methods

### Parallel Sandbox Execution (NEW in v2.1)
- **Multi-task execution** - Run multiple tasks simultaneously across E2B sandboxes
- **Configurable concurrency** - Control max parallel sandboxes (default: 3)
- **Fail-fast mode** - Stop all tasks on first failure
- **Progress monitoring** - Real-time status updates for each task
- **Per-task isolation** - Each task gets its own worktree and sandbox
- **Result aggregation** - Summary reports with timing and success metrics
- **Time savings** - Execute tasks in parallel vs sequentially

## The Problem

When you open multiple Claude Code sessions in the same repository, they can step on each other:
- Git index locks when both try to commit
- Build artifacts conflict
- Dependencies get corrupted
- General chaos ensues

## The Solution

`parallel-cc` automatically detects when you're starting a parallel session and creates an isolated git worktree for you. Each Claude Code instance works in its own space, then changes merge cleanly.

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Session Startup Flow                      │
├─────────────────────────────────────────────────────────────┤
│  1. You run: claude-parallel (or aliased 'claude')           │
│  2. Wrapper checks for existing sessions in this repo        │
│  3. If parallel session exists → creates worktree via gtr    │
│  4. Wrapper cd's into worktree, then launches claude         │
│  5. Claude Code works in isolated worktree                   │
│  6. On exit → session released, worktree cleaned up          │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

- **Node.js** 20+
- **[gtr](https://github.com/coderabbitai/git-worktree-runner)** - Git worktree management
- **jq** - JSON parsing in wrapper script

## Installation

```bash
# Clone and install (interactive)
git clone https://github.com/frankbria/parallel-cc.git
cd parallel-cc
./scripts/install.sh

# Or non-interactive installation with all features
./scripts/install.sh --all
```

The install script will:
1. Check all dependencies (Node.js 20+, git, jq, gtr)
2. Build the TypeScript project
3. Install CLI and wrapper scripts to `~/.local/bin`
4. Create the database directory
5. Verify installation with `parallel-cc doctor`
6. **Prompt to install heartbeat hooks** (global or local) - or install automatically with `--all`
7. Provide shell-specific setup instructions

**Non-interactive installation:**
Use `./scripts/install.sh --all` to install everything automatically:
- Installs heartbeat hooks globally (`~/.claude/settings.json`)
- Configures shell alias (`claude=claude-parallel`)
- Sets up MCP server integration
- No prompts, ideal for automation/CI/CD

### Advanced Installation

**Custom installation directory:**
```bash
export PARALLEL_CC_INSTALL_DIR="$HOME/bin"
export PARALLEL_CC_DATA_DIR="$HOME/.config/parallel-cc"
./scripts/install.sh
```

**Uninstall:**
```bash
./scripts/uninstall.sh
```

The uninstall script offers to remove configurations (hooks, alias, MCP) before removing installed files. Session data is preserved unless manually deleted.

### Recommended: Create an alias

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias claude='claude-parallel'
```

Now every time you run `claude`, it automatically handles parallel coordination!

### Optional: Complete Setup with One Command

For the best experience, run the full installation which sets up both the heartbeat hook and shell alias:

```bash
# Full installation (recommended)
parallel-cc install --all

# Or step-by-step:
parallel-cc install --hooks --global  # Heartbeat hook
parallel-cc install --alias           # Shell alias

# Interactive mode - prompts for each option
parallel-cc install --interactive

# Check installation status
parallel-cc install --status
```

Or add manually to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "~/.local/bin/parallel-cc-heartbeat.sh"
          }
        ]
      }
    ]
  }
}
```

## Usage

Just open multiple terminals and run `claude` (or `claude-parallel`) in each:

```bash
# Terminal 1
cd ~/projects/myrepo
claude  # Gets the main repo

# Terminal 2
cd ~/projects/myrepo
claude  # Automatically gets a worktree!
# Output: 📂 Parallel session detected - working in worktree
#         Path: /home/user/projects/myrepo-worktrees/parallel-m4x2k9...
```

That's it! Each session is isolated. When you're done, just exit claude normally - the worktree is cleaned up automatically.

**Full README available at**: https://github.com/frankbria/parallel-cc
