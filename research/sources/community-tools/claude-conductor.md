---
source: https://github.com/superbasicstudio/claude-conductor
fetched: 2026-02-11
type: github-repo
repo: superbasicstudio/claude-conductor
stars: 300
language: JavaScript
license: BSD-2-Clause
---

# Claude Conductor

Claude Conductor - a simple Claude Code framework. A lightweight + modular documentation framework designed for AI-assisted development with Claude Code.

**Stars**: 300 | **Language**: JavaScript | **License**: BSD-2-Clause | **Last Updated**: 2026-02-11

## README

Create a comprehensive, interconnected scaffolded documentation system that helps Claude Code understand and navigate your codebase more effectively, and retain better context.

### Requirements
- Node.js >= 18.0.0

### Quick Start

```bash
# Initialize with core templates (recommended)
npx claude-conductor
# Or use the shorthand
npx claude-conduct

# Initialize with all 13 documentation templates
npx claude-conductor --full

# Force overwrite existing files
npx claude-conductor --force

# Perform deep codebase analysis (slower but more detailed)
npx claude-conductor --deepscan
```

### What It Does

Claude Conductor creates a structured documentation framework that:
- **Organizes** your project documentation into focused, interconnected modules
- **Optimizes** for AI navigation with line numbers, anchors, and keywords
- **Tracks** development history with an auto-archiving journal system
- **Monitors** critical errors with a dedicated error ledger
- **Analyzes** your codebase to pre-populate documentation
- **Manages** active tasks with phase tracking and context preservation

### Core Templates (Default)
- **CONDUCTOR.md** - Master navigation hub and framework reference
- **CLAUDE.md** - AI assistant guidance tailored to your project
- **ARCHITECTURE.md** - System design and tech stack
- **BUILD.md** - Build, test, and deployment commands
- **JOURNAL.md** - Development changelog (auto-created)

### Full Template Set (--full flag)
All core templates plus:
- API.md, CONFIG.md, DATA_MODEL.md, DESIGN.md, UIUX.md, TEST.md, CONTRIBUTING.md, ERRORS.md
- PLAYBOOKS/DEPLOY.md - Deployment procedures
- TASKS.md - Active task management and phase tracking

### Features
- Intelligent Codebase Analysis (default scan + deep scan)
- Framework Detection (React, Vue, Angular, Express, Next.js)
- API Mapping, Component Discovery, Database Schema Detection
- Modular Documentation with cross-linking
- Development Journal with auto-archiving (500 lines)
- P0/P1 critical error ledger
- Ultra-safe upgrade system (backup -> clean install -> restore)
- Security checkup command

### CLI Commands

```bash
claude-conductor [options] [target-dir]

Options:
  -f, --force        Overwrite existing files
  --full             Create all 13 documentation templates
  --deepscan         Perform comprehensive codebase analysis
  --no-analyze       Skip codebase analysis

# Security & Health Checkup
claude-conductor checkup

# Upgrade System
claude-conductor backup
claude-conductor upgrade --clean
claude-conductor restore
```

### Companion Project
- [Claude Anchor](https://github.com/superbasicstudio/claude-anchor) - Behavioral framework
