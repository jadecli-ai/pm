# Blog Posts - Fetch Summary

**Fetched:** 2026-02-11
**Location:** `/home/org-jadecli/projects/.claude-org/research/sources/blog-posts/`

## Successfully Fetched (4 articles)

### 1. Addy Osmani - Claude Code Agent Teams
**File:** `addy-osmani-claude-code-agent-teams.md`
**URL:** https://addyosmani.com/blog/claude-code-agent-teams/
**Status:** Success
**Summary:** Comprehensive overview of Claude Code's agent teams (swarms) feature. Covers architecture (team lead, teammates, shared task list, mailbox system), practical applications, setup configuration, comparison with subagents, and important caveats about token costs and coordination overhead.

### 2. Prateek Karnal - Running 20 AI Agents in Parallel
**File:** `pkarnal-parallel-ai-agents.md`
**URL:** https://pkarnal.com/blog/parallel-ai-agents
**Status:** Success
**Summary:** Detailed architecture for orchestrating 20+ Claude Code agents simultaneously using git worktrees and tmux sessions. Covers session management, cost control ($2-5 per PR targets), workflow integration with GitHub/Linear/Slack, human attention layer design, and autonomy boundaries. Emphasizes 80/20 split between agent automation and human judgment.

### 3. paddo - Claude Code's Hidden Multi-Agent System
**File:** `paddo-claude-code-hidden-swarm.md`
**URL:** https://paddo.dev/blog/claude-code-hidden-swarm
**Status:** Success
**Summary:** Discovery of TeammateTool, a feature-flagged multi-agent system embedded in Claude Code's binary. Documents 13 operations across team lifecycle, coordination, and shutdown. Includes update about official release via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` environment variable.

### 4. Blue Leaf - Claude Code + tmux Terminal Workflow
**File:** `blle-claude-code-tmux-beautiful-terminal.md`
**URL:** https://blle.co/blog/claude-code-tmux-beautiful-terminal
**Status:** Success
**Summary:** Guide for combining Claude Code with tmux for persistent development sessions. Covers session persistence, multi-pane development, configuration details using Catppuccin Mocha color scheme, and practical workflows for monitoring long-running tasks.

## Partial Content (1 article)

### 5. marc0.dev - Qwen3-Coder Integration
**File:** `marc0-claude-code.md`
**URL:** https://marc0.dev
**Status:** Partial (no dedicated Claude Code article)
**Summary:** Claude Code mentioned within article about Qwen3-Coder local model integration. Discusses configuring Claude Code to work with Ollama-compatible models for local inference, environment variable setup, and privacy-focused development workflow.

## No Content Found (2 sites)

### 6. Javier Aguilar
**File:** `javieraguilar-claude-code.md`
**URL:** https://javieraguilar.ai
**Status:** No article found
**Reason:** Portfolio website with no Claude Code articles. Site focuses on AI consulting services and project showcases.

### 7. darasoba Medium
**File:** `darasoba-claude-code.md`
**URL:** https://darasoba.medium.com
**Status:** Fetch failed (403 Forbidden)
**Reason:** Medium.com blocking automated access. Requires browser-based access or authentication.

## Statistics

- **Total Requested:** 7
- **Successfully Fetched:** 4 (57%)
- **Partial Content:** 1 (14%)
- **Failed/Not Found:** 2 (29%)
- **Total Files Created:** 7 (includes error documentation)

## Key Themes Across Articles

1. **Multi-Agent Architecture:** Team leads, specialized agents, coordination mechanisms
2. **Infrastructure:** tmux sessions, git worktrees, persistent development environments
3. **Cost Control:** Token budget management, context window discipline
4. **Autonomy Boundaries:** 80/20 split between automation and human oversight
5. **Workflow Integration:** GitHub, Linear, Slack, CI/CD systems
6. **Configuration:** Feature flags, environment variables, MCP servers

## Related Research Topics

- Steering system integration with agent teams
- Token budget tracking across multiple agents
- Redis-based progress tracking for parallel agents
- Handoff protocols between team members
- Local model integration (Ollama, Qwen3-Coder)
