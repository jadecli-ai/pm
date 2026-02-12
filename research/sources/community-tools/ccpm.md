---
source: https://github.com/automazeio/ccpm
fetched: 2026-02-11
type: github-repo
repo: automazeio/ccpm
stars: 7196
language: Shell
---

# ccpm (Claude Code PM)

Project management system for Claude Code using GitHub Issues and Git worktrees for parallel agent execution.

**Stars**: 7196 | **Language**: Shell | **License**: MIT License | **Last Updated**: 2026-02-12T07:05:29Z

## README

# Claude Code PM

[![Automaze](https://img.shields.io/badge/By-automaze.io-4b3baf)](https://automaze.io)
&nbsp;
[![Claude Code](https://img.shields.io/badge/+-Claude%20Code-d97757)](https://github.com/automazeio/ccpm/blob/main/README.md)
[![GitHub Issues](https://img.shields.io/badge/+-GitHub%20Issues-1f2328)](https://github.com/automazeio/ccpm)
&nbsp;
[![Mentioned in Awesome Claude Code](https://awesome.re/mentioned-badge.svg)](https://github.com/hesreallyhim/awesome-claude-code?tab=readme-ov-file#general-)
&nbsp;
[![MIT License](https://img.shields.io/badge/License-MIT-28a745)](https://github.com/automazeio/ccpm/blob/main/LICENSE)
&nbsp;
[![Follow on 𝕏](https://img.shields.io/badge/𝕏-@aroussi-1c9bf0)](http://x.com/intent/follow?screen_name=aroussi)
&nbsp;
[![Star this repo](https://img.shields.io/github/stars/automazeio/ccpm.svg?style=social&label=Star%20this%20repo&maxAge=60)](https://github.com/automazeio/ccpm)

### Claude Code workflow to ship ~~faster~~ _better_ using spec-driven development, GitHub issues, Git worktrees, and multiple AI agents running in parallel.

**[中文文档 (Chinese Documentation)](zh-docs/README_ZH.md)**

Stop losing context. Stop blocking on tasks. Stop shipping bugs. This battle-tested system turns PRDs into epics, epics into GitHub issues, and issues into production code – with full traceability at every step.

## Background

Every team struggles with the same problems:
- **Context evaporates** between sessions, forcing constant re-discovery
- **Parallel work creates conflicts** when multiple developers touch the same code
- **Requirements drift** as verbal decisions override written specs
- **Progress becomes invisible** until the very end

This system solves all of that.

## The Workflow

```mermaid
graph LR
    A[PRD Creation] --> B[Epic Planning]
    B --> C[Task Decomposition]
    C --> D[GitHub Sync]
    D --> E[Parallel Execution]
```

### See It In Action (60 seconds)

```bash
# Create a comprehensive PRD through guided brainstorming
/pm:prd-new memory-system

# Transform PRD into a technical epic with task breakdown
/pm:prd-parse memory-system

# Push to GitHub and start parallel execution
/pm:epic-oneshot memory-system
/pm:issue-start 1235
```

## What Makes This Different?

| Traditional Development | Claude Code PM System |
|------------------------|----------------------|
| Context lost between sessions | **Persistent context** across all work |
| Serial task execution | **Parallel agents** on independent tasks |
| "Vibe coding" from memory | **Spec-driven** with full traceability |
| Progress hidden in branches | **Transparent audit trail** in GitHub |
| Manual task coordination | **Intelligent prioritization** with `/pm:next` |

## Why GitHub Issues?

Most Claude Code workflows operate in isolation – a single developer working with AI in their local environment. This creates a fundamental problem: **AI-assisted development becomes a silo**.

By using GitHub Issues as our database, we unlock something powerful:

### True Team Collaboration
- Multiple Claude instances can work on the same project simultaneously
- Human developers see AI progress in real-time through issue comments
- Team members can jump in anywhere – the context is always visible
- Managers get transparency without interrupting flow

### Seamless Human-AI Handoffs
- AI can start a task, human can finish it (or vice versa)
- Progress updates are visible to everyone, not trapped in chat logs
- Code reviews happen naturally through PR comments
- No "what did the AI do?" meetings

### Scalable Beyond Solo Work
- Add team members without onboarding friction
- Multiple AI agents working in parallel on different issues
- Distributed teams stay synchronized automatically
- Works with existing GitHub workflows and tools

### Single Source of Truth
- No separate databases or project management tools
- Issue state is the project state
- Comments are the audit trail
- Labels provide organization

This isn't just a project management system – it's a **collaboration protocol** that lets humans and AI agents work together at scale, using infrastructure your team already trusts.

## Core Principle: No Vibe Coding

> **Every line of code must trace back to a specification.**

We follow a strict 5-phase discipline:

1. **Brainstorm** - Think deeper than comfortable
2. **Document** - Write specs that leave nothing to interpretation
3. **Plan** - Architect with explicit technical decisions
4. **Execute** - Build exactly what was specified
5. **Track** - Maintain transparent progress at every step

No shortcuts. No assumptions. No regrets.

## System Architecture

```
.claude/
├── CLAUDE.md          # Always-on instructions (copy content to your project's CLAUDE.md file)
├── agents/            # Task-oriented agents (for context preservation)
├── commands/          # Command definitions
│   ├── context/       # Create, update, and prime context
│   ├── pm/            # ← Project management commands (this system)
│   └── testing/       # Prime and execute tests (edit this)
├── context/           # Project-wide context files
├── epics/             # ← PM's local workspace (place in .gitignore)
│   └── [epic-name]/   # Epic and related tasks
│       ├── epic.md    # Implementation plan
│       ├── [#].md     # Individual task files
│       └── updates/   # Work-in-progress updates
├── prds/              # ← PM's PRD files
├── rules/             # Place any rule files you'd like to reference here
└── scripts/           # Place any script files you'd like to use here
```

## Workflow Phases

### 1. Product Planning Phase

```bash
/pm:prd-new feature-name
```
Launches comprehensive brainstorming to create a Product Requirements Document capturing vision, user stories, success criteria, and constraints.

**Output:** `.claude/prds/feature-name.md`

### 2. Implementation Planning Phase

```bash
/pm:prd-parse feature-name
```
Transforms PRD into a technical implementation plan with architectural decisions, technical approach, and dependency mapping.

**Output:** `.claude/epics/feature-name/epic.md`

### 3. Task Decomposition Phase

```bash
/pm:epic-decompose feature-name
```
Breaks epic into concrete, actionable tasks with acceptance criteria, effort estimates, and parallelization flags.

**Output:** `.claude/epics/feature-name/[task].md`

### 4. GitHub Synchronization

```bash
/pm:epic-sync feature-name
# Or for confident workflows:
/pm:epic-oneshot feature-name
```
Pushes epic and tasks to GitHub as issues with appropriate labels and relationships.

### 5. Execution Phase

```bash
/pm:issue-start 1234  # Launch specialized agent
/pm:issue-sync 1234   # Push progress updates
/pm:next             # Get next priority task
```
Specialized agents implement tasks while maintaining progress updates and an audit trail.

## Command Reference

> Type `/pm:help` for a concise command summary

### Initial Setup
- `/pm:init` - Install dependencies and configure GitHub

### PRD Commands
- `/pm:prd-new` - Launch brainstorming for new product requirement
- `/pm:prd-parse` - Convert PRD to implementation epic
- `/pm:prd-list` - List all PRDs
- `/pm:prd-edit` - Edit existing PRD
- `/pm:prd-status` - Show PRD implementation status

### Epic Commands
- `/pm:epic-decompose` - Break epic into task files
- `/pm:epic-sync` - Push epic and tasks to GitHub
- `/pm:epic-oneshot` - Decompose and sync in one command
- `/pm:epic-list` - List all epics
- `/pm:epic-show` - Display epic and its tasks
- `/pm:epic-close` - Mark epic as complete
- `/pm:epic-edit` - Edit epic details
- `/pm:epic-refresh` - Update epic progress from tasks

### Issue Commands
- `/pm:issue-show` - Display issue and sub-issues
- `/pm:issue-status` - Check issue status
- `/pm:issue-start` - Begin work with specialized agent
- `/pm:issue-sync` - Push updates to GitHub
- `/pm:issue-close` - Mark issue as complete
- `/pm:issue-reopen` - Reopen closed issue
- `/pm:issue-edit` - Edit issue details

### Workflow Commands
- `/pm:next` - Show next priority issue with epic context
- `/pm:status` - Overall project dashboard
- `/pm:standup` - Daily standup report
- `/pm:blocked` - Show blocked tasks
- `/pm:in-progress` - List work in progress

### Sync Commands
- `/pm:sync` - Full bidirectional sync with GitHub
- `/pm:import` - Import existing GitHub issues

### Maintenance Commands
- `/pm:validate` - Check system integrity
- `/pm:clean` - Archive completed work
- `/pm:search` - Search across all content

## The Parallel Execution System

### Issues Aren't Atomic

Traditional thinking: One issue = One developer = One task

**Reality: One issue = Multiple parallel work streams**

A single "Implement user authentication" issue isn't one task. It's...

- **Agent 1**: Database tables and migrations
- **Agent 2**: Service layer and business logic
- **Agent 3**: API endpoints and middleware
- **Agent 4**: UI components and forms
- **Agent 5**: Test suites and documentation

All running **simultaneously** in the same worktree.

### The Math of Velocity

**Traditional Approach:**
- Epic with 3 issues
- Sequential execution

**This System:**
- Same epic with 3 issues
- Each issue splits into ~4 parallel streams
- **12 agents working simultaneously**

We're not assigning agents to issues. We're **leveraging multiple agents** to ship faster.

## Key Features & Benefits

### Context Preservation
Never lose project state again. Each epic maintains its own context, agents read from `.claude/context/`, and updates locally before syncing.

### Parallel Execution
Ship faster with multiple agents working simultaneously. Tasks marked `parallel: true` enable conflict-free concurrent development.

### GitHub Native
Works with tools your team already uses. Issues are the source of truth, comments provide history, and there is no dependency on the Projects API.

### Agent Specialization
Right tool for every job. Different agents for UI, API, and database work. Each reads requirements and posts updates automatically.

### Full Traceability
Every decision is documented. PRD → Epic → Task → Issue → Code → Commit. Complete audit trail from idea to production.

### Developer Productivity
Focus on building, not managing. Intelligent prioritization, automatic context loading, and incremental sync when ready.

## Proven Results

Teams using this system report:
- **89% less time** lost to context switching – you'll use `/compact` and `/clear` a LOT less
- **5-8 parallel tasks** vs 1 previously – editing/testing multiple files at the same time
- **75% reduction** in bug rates – due to the breaking down features into detailed tasks
- **Up to 3x faster** feature delivery – based on feature size and complexity

## Get Started Now

### Quick Setup (2 minutes)

1. **Install this repository into your project**:

   #### Unix/Linux/macOS

   ```bash
   cd path/to/your/project/
   curl -sSL https://automaze.io/ccpm/install | bash
   # or: wget -qO- https://automaze.io/ccpm/install | bash
   ```

   #### Windows (PowerShell)
   ```bash
   cd path/to/your/project/
   iwr -useb https://automaze.io/ccpm/install | iex
   ```
   > If you already have a `.claude` directory, clone this repository to a different directory and copy the contents of the cloned `.claude` directory to your project's `.claude` directory.

2. **Initialize the PM system**:
   ```bash
   /pm:init
   ```
   This command will:
   - Install GitHub CLI (if needed)
   - Authenticate with GitHub
   - Install [gh-sub-issue extension](https://github.com/yahsan2/gh-sub-issue) for proper parent-child relationships
   - Create required directories
   - Update .gitignore

3. **Create `CLAUDE.md`** with your repository information
   ```bash
   /init include rules from .claude/CLAUDE.md
   ```
   > If you already have a `CLAUDE.md` file, run: `/re-init` to update it with important rules from `.claude/CLAUDE.md`.

4. **Prime the system**:
   ```bash
   /context:create
   ```

### Start Your First Feature

```bash
/pm:prd-new your-feature-name
```

Watch as structured planning transforms into shipped code.

**Full README and documentation available at**: https://github.com/automazeio/ccpm

## License

MIT License
