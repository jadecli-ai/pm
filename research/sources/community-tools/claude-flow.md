---
source: https://github.com/ruvnet/claude-flow
fetched: 2026-02-11
type: github-repo
repo: ruvnet/claude-flow
stars: 13980
language: TypeScript
---

# claude-flow

The leading agent orchestration platform for Claude. Deploy intelligent multi-agent swarms, coordinate autonomous workflows, and build conversational AI systems. Features enterprise-grade architecture, distributed swarm intelligence, RAG integration, and native Claude Code support via MCP protocol.

**Stars**: 13980 | **Language**: TypeScript | **License**: MIT License | **Last Updated**: 2026-02-12T07:22:51Z

## README

# Claude-Flow v3: Enterprise AI Orchestration Platform

**Production-ready multi-agent AI orchestration for Claude Code**

*Deploy 60+ specialized agents in coordinated swarms with self-learning capabilities, fault-tolerant consensus, and enterprise-grade security.*

## Getting into the Flow

Claude-Flow is a comprehensive AI agent orchestration framework that transforms Claude Code into a powerful multi-agent development platform. It enables teams to deploy, coordinate, and optimize specialized AI agents working together on complex software engineering tasks.

### Self-Learning/Self-Optimizing Agent Architecture

```
User → Claude-Flow (CLI/MCP) → Router → Swarm → Agents → Memory → LLM Providers
                       ↑                          ↓
                       └──── Learning Loop ←──────┘
```

### Get Started Fast

```bash
# One-line install (recommended)
curl -fsSL https://cdn.jsdelivr.net/gh/ruvnet/claude-flow@main/scripts/install.sh | bash

# Or full setup with MCP + diagnostics
curl -fsSL https://cdn.jsdelivr.net/gh/ruvnet/claude-flow@main/scripts/install.sh | bash -s -- --full

# Or via npx
npx claude-flow@alpha init --wizard
```

### Key Capabilities

**60+ Specialized Agents** - Ready-to-use AI agents for coding, code review, testing, security audits, documentation, and DevOps. Each agent is optimized for its specific role.

**Coordinated Agent Teams** - Run unlimited agents simultaneously in organized swarms. Agents spawn sub-workers, communicate, share context, and divide work automatically using hierarchical (queen/workers) or mesh (peer-to-peer) patterns.

**Learns From Your Workflow** - The system remembers what works. Successful patterns are stored and reused, routing similar tasks to the best-performing agents. Gets smarter over time.

**Works With Any LLM** - Switch between Claude, GPT, Gemini, Cohere, or local models like Llama. Automatic failover if one provider is unavailable. Smart routing picks the cheapest option that meets quality requirements.

**Plugs Into Claude Code** - Native integration via MCP (Model Context Protocol). Use claude-flow commands directly in your Claude Code sessions with full tool access.

**Production-Ready Security** - Built-in protection against prompt injection, input validation, path traversal prevention, command injection blocking, and safe credential handling.

**Extensible Plugin System** - Add custom capabilities with the plugin SDK. Create workers, hooks, providers, and security modules. Share plugins via the decentralized IPFS marketplace.

## Architecture Overview

### Core Flow

Every request flows through four layers: from your CLI or Claude Code interface, through intelligent routing, to specialized agents, and finally to LLM providers for reasoning.

| Layer | Components | What It Does |
|-------|------------|--------------|
| User | Claude Code, CLI | Your interface to control and run commands |
| Orchestration | MCP Server, Router, Hooks | Routes requests to the right agents |
| Agents | 60+ types | Specialized workers (coder, tester, reviewer...) |
| Providers | Anthropic, OpenAI, Google, Ollama | AI models that power reasoning |

### Swarm Coordination

Agents organize into swarms led by queens that coordinate work, prevent drift, and reach consensus on decisions—even when some agents fail.

| Layer | Components | What It Does |
|-------|------------|--------------|
| Coordination | Queen, Swarm, Consensus | Manages agent teams (Raft, Byzantine, Gossip) |
| Drift Control | Hierarchical topology, Checkpoints | Prevents agents from going off-task |
| Hive Mind | Queen-led hierarchy, Collective memory | Strategic/tactical/adaptive queens coordinate workers |
| Consensus | Byzantine, Weighted, Majority | Fault-tolerant decisions (2/3 majority for BFT) |

**Hive Mind Capabilities:**
- Queen Types: Strategic (planning), Tactical (execution), Adaptive (optimization)
- 8 Worker Types: Researcher, Coder, Analyst, Tester, Architect, Reviewer, Optimizer, Documenter
- 3 Consensus Algorithms: Majority, Weighted (Queen 3x), Byzantine (f < n/3)
- Collective Memory: Shared knowledge, LRU cache, SQLite persistence with WAL
- Performance: 10-20x faster batch spawning, 84.8% SWE-Bench solve rate

### Intelligence & Memory

The system stores successful patterns in vector memory, learns from outcomes via neural networks, and adapts routing based on what works best.

| Layer | Components | What It Does |
|-------|------------|--------------|
| Memory | HNSW, AgentDB, Cache | Stores and retrieves patterns 150x faster |
| Embeddings | ONNX Runtime, MiniLM | Local vectors without API calls (75x faster) |
| Learning | SONA, MoE, ReasoningBank | Self-improves from results (<0.05ms adaptation) |
| Fine-tuning | MicroLoRA, EWC++ | Lightweight adaptation without full retraining |

### Optimization

Skip expensive LLM calls for simple tasks using WebAssembly transforms, and compress tokens to reduce API costs by 30-50%.

| Layer | Components | What It Does |
|-------|------------|--------------|
| Agent Booster | WASM, AST analysis | Skips LLM for simple edits (<1ms) |
| Token Optimizer | Compression, Caching | Reduces token usage 30-50% |

### Task Routing - Extend your Claude Code subscription by 250%

Smart routing skips expensive LLM calls when possible. Simple edits use WASM (free), medium tasks use cheaper models. This can extend your Claude Code usage by 250% or save significantly on direct API costs.

| Complexity | Handler | Speed |
|------------|---------|-------|
| Simple | Agent Booster (WASM) | <1ms |
| Medium | Haiku/Sonnet | ~500ms |
| Complex | Opus + Swarm | 2-5s |

### Agent Booster (WASM) — 352x faster code transforms, skip LLM entirely

Agent Booster uses WebAssembly to handle simple code transformations without calling the LLM at all. When the hooks system detects a simple task, it routes directly to Agent Booster for instant results.

**Supported Transform Intents:**

| Intent | What It Does | Example |
|--------|--------------|---------|
| `var-to-const` | Convert var/let to const | `var x = 1` → `const x = 1` |
| `add-types` | Add TypeScript type annotations | `function foo(x)` → `function foo(x: string)` |
| `add-error-handling` | Wrap in try/catch | Adds proper error handling |
| `async-await` | Convert promises to async/await | `.then()` chains → `await` |
| `add-logging` | Add console.log statements | Adds debug logging |
| `remove-console` | Strip console.* calls | Removes all console statements |

**Performance:**

| Metric | Agent Booster | LLM Call |
|--------|---------------|----------|
| Latency | <1ms | 2-5s |
| Cost | $0 | $0.0002-$0.015 |
| Speedup | **352x faster** | baseline |

### Token Optimizer — 30-50% token reduction

The Token Optimizer integrates agentic-flow optimizations to reduce API costs by compressing context and caching results.

**Savings Breakdown:**

| Optimization | Token Savings | How It Works |
|--------------|---------------|--------------|
| ReasoningBank retrieval | -32% | Fetches relevant patterns instead of full context |
| Agent Booster edits | -15% | Simple edits skip LLM entirely |
| Cache (95% hit rate) | -10% | Reuses embeddings and patterns |
| Optimal batch size | -20% | Groups related operations |
| **Combined** | **30-50%** | Stacks multiplicatively |

### Anti-Drift Swarm Configuration — Prevent goal drift in multi-agent work

Complex swarms can drift from their original goals. Claude-Flow V3 includes anti-drift defaults that prevent agents from going off-task.

**Recommended Configuration:**

```javascript
// Anti-drift defaults (ALWAYS use for coding tasks)
swarm_init({
  topology: "hierarchical",  // Single coordinator enforces alignment
  maxAgents: 8,              // Smaller team = less drift surface
  strategy: "specialized"    // Clear roles reduce ambiguity
})
```

**Why This Prevents Drift:**

| Setting | Anti-Drift Benefit |
|---------|-------------------|
| `hierarchical` | Coordinator validates each output against goal, catches divergence early |
| `maxAgents: 6-8` | Fewer agents = less coordination overhead, easier alignment |
| `specialized` | Clear boundaries - each agent knows exactly what to do, no overlap |
| `raft` consensus | Leader maintains authoritative state, no conflicting decisions |

## Claude Code: With vs Without Claude-Flow

| Capability | Claude Code Alone | Claude Code + Claude-Flow |
|------------|-------------------|---------------------------|
| **Agent Collaboration** | Agents work in isolation, no shared context | Agents collaborate via swarms with shared memory and consensus |
| **Coordination** | Manual orchestration between tasks | Queen-led hierarchy with 5 consensus algorithms (Raft, Byzantine, Gossip) |
| **Hive Mind** | ⛔ Not available | 🐝 Queen-led swarms with collective intelligence, 3 queen types, 8 worker types |
| **Consensus** | ⛔ No multi-agent decisions | Byzantine fault-tolerant voting (f < n/3), weighted, majority |
| **Memory** | Session-only, no persistence | HNSW vector memory with 150x-12,500x faster retrieval |
| **Vector Database** | ⛔ No native support | 🐘 RuVector PostgreSQL with 77+ SQL functions, ~61µs search, 16,400 QPS |
| **Collective Memory** | ⛔ No shared knowledge | Shared knowledge base with LRU cache, SQLite persistence, 8 memory types |
| **Learning** | Static behavior, no adaptation | SONA self-learning with <0.05ms adaptation, improves over time |
| **Task Routing** | You decide which agent to use | Intelligent routing based on learned patterns (89% accuracy) |
| **Complex Tasks** | Manual breakdown required | Automatic decomposition across 5 domains (Security, Core, Integration, Support) |
| **Background Workers** | Nothing runs automatically | 12 context-triggered workers auto-dispatch on file changes, patterns, sessions |
| **LLM Provider** | Anthropic only | 6 providers with automatic failover and cost-based routing (85% savings) |
| **Security** | Standard protections | CVE-hardened with bcrypt, input validation, path traversal prevention |
| **Performance** | Baseline | 2.8-4.4x faster tasks, 10-20x faster swarm spawning, 84.8% SWE-Bench |

## Quick Start

### Prerequisites

- **Node.js 20+** (required)
- **npm 9+** / **pnpm** / **bun** package manager

**IMPORTANT**: Claude Code must be installed first:

```bash
# 1. Install Claude Code globally
npm install -g @anthropic-ai/claude-code

# 2. (Optional) Skip permissions check for faster setup
claude --dangerously-skip-permissions
```

### Installation

#### One-Line Install (Recommended)

```bash
# curl-style installer with progress display
curl -fsSL https://cdn.jsdelivr.net/gh/ruvnet/claude-flow@main/scripts/install.sh | bash

# Full setup (global + MCP + diagnostics)
curl -fsSL https://cdn.jsdelivr.net/gh/ruvnet/claude-flow@main/scripts/install.sh | bash -s -- --full
```

#### npm/npx Install

```bash
# Quick start (no install needed)
npx claude-flow@alpha init

# Or install globally
npm install -g claude-flow@alpha
claude-flow init

# With Bun (faster)
bunx claude-flow@alpha init
```

**Full README and extensive documentation available at**: https://github.com/ruvnet/claude-flow

## License

MIT License
