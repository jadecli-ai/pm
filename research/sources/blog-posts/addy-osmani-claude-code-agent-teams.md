---
source: https://addyosmani.com/blog/claude-code-agent-teams/
fetched: 2026-02-11
type: blog-post
author: Addy Osmani
---

# Claude Code Swarms

**Author:** Addy Osmani
**Date:** February 5, 2026

## Overview

Addy Osmani announces that Claude Code now supports agent teams (swarms)—a coordinated multi-agent system where "a lead agent can delegate to multiple teammates that work in parallel."

## Key Concepts

**What Are Agent Teams?**

Rather than sequential single-agent processing, agent teams introduce parallel specialists. The architecture comprises:

- **Team lead**: Coordinates and spawns teammates
- **Teammates**: Independent Claude Code instances with full context windows
- **Shared task list**: Dependency tracking and auto-unblocking
- **Mailbox system**: Direct inter-agent messaging (not just reporting to lead)

## Core Problem They Solve

Osmani identifies a fundamental limitation: "LLMs perform worse as context expands." Single agents struggle with complex multi-step tasks because "the more information in the context window, the harder it is for the model to focus on what matters right now."

Multi-agent patterns mimic human team specialization—each agent maintains narrow scope and clean context.

## Practical Applications

Osmani highlights effective use cases:

- **Competing hypotheses debugging**: Five agents investigate different theories simultaneously, debunking each other's assumptions
- **Parallel code review**: Different agents handle security, performance, and test coverage independently
- **Cross-layer features**: Frontend, backend, and tests owned by separate agents
- **Research and exploration**: Parallel investigation with findings flowing directly into implementation

## Setup and Configuration

Enable via settings:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Display modes include in-process (default) or split panes via tmux/iTerm2.

## Subagents vs. Agent Teams

| Aspect | Subagents | Agent Teams |
|--------|-----------|------------|
| Communication | Report back only | Direct teammate messaging |
| Coordination | Main agent manages | Self-coordination |
| Best for | Focused, isolated tasks | Complex collaborative work |
| Cost | Lower | Higher (separate instances) |

## Important Caveats

Osmani emphasizes practical limitations: task decomposition must be precise—vague briefs waste tokens. Token costs scale significantly since each teammate is an independent Claude instance. The feature requires careful problem scoping to avoid coordination overhead dominating the benefits.

## Philosophical Insight

Osmani notes that "activity doesn't always translate to value." Multi-agent systems risk producing high volumes of code without ensuring correctness or maintainability. "Let the problem guide the tooling, not the other way around."
