---
source: https://pkarnal.com/blog/parallel-ai-agents
fetched: 2026-02-11
type: blog-post
author: Prateek
---

# Running 20 AI Agents in Parallel From My Home Directory

**By Prateek** | Published 2026-02-11 | 28 min read

## Overview

The author orchestrates 20+ Claude Code agents running simultaneously across multiple codebases from their home directory. Each agent operates independently on separate git worktrees with isolated tmux sessions, coordinated by a parent agent that manages the entire system.

## Core Architecture

The system uses a hierarchical agent structure:
- **Parent orchestrator** manages everything from `~/`
- **Child agents** work on individual issues in separate directories
- **Complete isolation** ensures agents never interfere with each other's work
- **Git worktrees** provide lightweight branch isolation sharing a single `.git` object store

The author chose tmux sessions over Claude Code's built-in subagents because persistent, interactive sessions enable human supervision. As they note: "subagents are fire-and-forget" whereas tmux allows real-time intervention and guidance.

## Key Infrastructure Components

**Session Management:**
- Scripts spawn, monitor, and clean up 25+ dedicated tools
- Live state extracted from Claude's internal JSONL files rather than relying on agent self-reporting
- Automated metadata tracking includes branch names, PR URLs, and activity timestamps

**Cost Control:**
- Explicit targets of "$2-5 per PR" combined with concrete rules
- Agents use subagents for exploration, filter all output, and avoid re-reading files
- Context window discipline prevents exponential token costs

**Workflow Integration:**
- Agents autonomously handle GitHub PRs, Linear tickets, and Slack drafts
- Datadog logging, Terraform CI/CD, and AWS access controlled via MCP server
- Review comments trigger automatic fix prompts through `claude-review-check`

## Human Attention Layer

Rather than attempting full autonomy, the system optimizes human oversight:

- **Notifications** alert when agents finish or need decisions
- **AppleScript navigation** instantly routes attention to relevant agent sessions
- **PR dashboard** provides unified visibility across all parallel work
- **Orchestrator recommendations** identify highest-leverage tasks

The orchestrator itself became the author's primary interface for thinking about work beyond just executing it—assessing workload, identifying high-impact tasks, and planning implementation strategies.

## Autonomy Boundaries

Fully autonomous:
- Code reading, writing, testing
- PR creation and management
- Review comment responses
- Ticket creation

Requiring permission:
- AWS/database access
- Slack messages
- Protected branch pushes
- Production Terraform changes

## What Worked Well

- Git worktrees provided perfect branch isolation with minimal overhead
- Bash scripts (~2,000 lines total) remained maintainable without frameworks
- Batched GraphQL queries for efficient PR monitoring
- Layered CLAUDE.md structure supporting different instruction audiences

## What Didn't Work

- Full git clones wasted disk space and network bandwidth
- Relying on agent self-reporting produced stale metadata
- Complex terminal escaping led to prompt truncation issues
- Overly elaborate approval workflows created excessive friction

## Broader Implications

The author critiques fully autonomous AI systems (citing the C compiler and Cursor browser projects) as inherently limited by edge cases requiring human judgment. Their 80/20 split—agents handling mechanical work, humans handling judgment calls—appears more sustainable than pure autonomy attempts.

The underlying argument: investment in the **tool layer** for agent-app integration matters more than model capability alone. Without effective connections to issue trackers, communication platforms, and infrastructure systems, agents remain expensive code-writing assistants rather than true team members.
