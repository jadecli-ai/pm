# Claude Code Memory System - Complete Research

> Compiled: 2026-02-11
> Sources: Official docs, GitHub, community guides

## Executive Summary

Claude Code has a **hierarchical memory system** with five distinct layers, from organization-wide policies to auto-generated session notes. The system prioritizes more specific instructions over general ones and supports modular organization via `.claude/rules/`.

**Key insight**: Memory is bidirectional - you write CLAUDE.md files for Claude, and Claude writes auto-memory for itself.

---

## 1. Memory Architecture

### 1.1 Five-Layer Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│  1. Managed Policy                                      │
│     /etc/claude-code/CLAUDE.md (Linux)                  │
│     Organization-wide • Managed by IT • All users       │
├─────────────────────────────────────────────────────────┤
│  2. User Memory                                         │
│     ~/.claude/CLAUDE.md                                 │
│     Personal preferences • All projects                 │
├─────────────────────────────────────────────────────────┤
│  3. Project Memory                                      │
│     ./CLAUDE.md or ./.claude/CLAUDE.md                  │
│     Team-shared • Version controlled                    │
├─────────────────────────────────────────────────────────┤
│  4. Project Rules                                       │
│     ./.claude/rules/*.md                                │
│     Modular • Path-specific • Conditional               │
├─────────────────────────────────────────────────────────┤
│  5. Local Memory                                        │
│     ./CLAUDE.local.md                                   │
│     Personal per-project • Not version controlled       │
└─────────────────────────────────────────────────────────┘

            ↓ More specific wins over less specific ↓

┌─────────────────────────────────────────────────────────┐
│  Auto Memory (Claude writes this)                       │
│     ~/.claude/projects/<project>/memory/                │
│     First 200 lines of MEMORY.md loaded                 │
│     Topic files loaded on-demand                        │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Loading Behavior

| Memory Type | When Loaded | Limit |
|-------------|-------------|-------|
| Managed policy | Session start | Full |
| User CLAUDE.md | Session start | Full |
| Project CLAUDE.md | Session start | Full |
| Project rules | Session start (unconditional) or on-demand (path-specific) | Full |
| Local CLAUDE.md | Session start | Full |
| Auto memory MEMORY.md | Session start | First 200 lines |
| Auto memory topic files | On-demand | Full |
| Child directory CLAUDE.md | When reading files in that directory | Full |

### 1.3 Import System

CLAUDE.md files can import other files:

```markdown
See @README for project overview and @package.json for npm commands.

# Workflows
- Git workflow: @docs/git-instructions.md
- API guidelines: @~/.claude/shared/api-standards.md
```

**Rules:**
- Relative paths resolve from the importing file
- Absolute paths and `~` supported
- Max depth: 5 hops
- Not evaluated inside code blocks
- First-time external imports require approval

---

## 2. Auto Memory System

### 2.1 What Claude Remembers

Claude automatically saves:
- **Project patterns**: Build commands, test conventions, code style
- **Debugging insights**: Solutions to tricky problems
- **Architecture notes**: Key files, module relationships
- **Your preferences**: Communication style, tool choices

### 2.2 Directory Structure

```
~/.claude/projects/<project>/memory/
├── MEMORY.md           # Index file (first 200 lines loaded)
├── debugging.md        # Topic: Debugging patterns
├── api-conventions.md  # Topic: API design decisions
├── performance.md      # Topic: Performance insights
└── ...                 # Any topic files Claude creates
```

**Project path derivation:**
- Git repo: Uses repository root path
- Git worktrees: Separate memory per worktree
- Non-git: Uses working directory

### 2.3 200-Line Constraint

The first 200 lines of `MEMORY.md` are injected into every session. Claude is instructed to:
- Keep `MEMORY.md` as a concise index
- Move detailed notes to topic files
- Reference topic files from `MEMORY.md`

### 2.4 Configuration

```bash
# Force on (opt-in to gradual rollout)
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=0

# Force off
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
```

---

## 3. Modular Rules System

### 3.1 Structure

```
.claude/rules/
├── frontend/
│   ├── react.md
│   └── styles.md
├── backend/
│   ├── api.md
│   └── database.md
├── testing.md
└── security.md
```

### 3.2 Path-Specific Rules

```yaml
---
paths:
  - "src/api/**/*.ts"
  - "lib/**/*.ts"
---

# API Development Rules
- All endpoints must include input validation
- Use the standard error response format
```

**Glob patterns supported:**
- `**/*.ts` - All TypeScript files
- `src/**/*` - All files under src/
- `*.{ts,tsx}` - Brace expansion
- `{src,lib}/**/*.ts` - Multiple directories

### 3.3 User-Level Rules

Personal rules in `~/.claude/rules/` apply to all projects with lower priority than project rules.

---

## 4. Subagent Memory (v2.1.33+)

### 4.1 Memory Frontmatter Field

```yaml
---
name: code-reviewer
description: Reviews code for quality
memory: user  # or project, local
---

You are a code reviewer. Update your agent memory with
patterns and issues you discover.
```

### 4.2 Scope Options

| Scope | Location | Shared | Version Controlled |
|-------|----------|--------|-------------------|
| `user` | `~/.claude/agent-memory/<agent>/` | No | No |
| `project` | `.claude/agent-memory/<agent>/` | Yes | Yes |
| `local` | `.claude/agent-memory-local/<agent>/` | No | No |

### 4.3 How It Works

When `memory` is set:
1. First 200 lines of agent's `MEMORY.md` injected into system prompt
2. Read, Write, Edit tools auto-enabled for memory management
3. Agent curates `MEMORY.md` and creates topic files as needed
4. Memory persists across invocations

### 4.4 Comparison with Other Systems

| System | Who Writes | Who Reads | Scope |
|--------|------------|-----------|-------|
| CLAUDE.md | You | All agents | Project |
| Auto-memory | Main Claude | Main Claude only | Per-project |
| `/memory` command | You (via editor) | Main Claude only | Per-project |
| Agent memory | The agent | That specific agent | Configurable |

---

## 5. Third-Party Memory Solutions

### 5.1 Claude-Mem Plugin

**What it does:**
- Captures all tool usage automatically
- Compresses with AI for efficient storage
- Semantic search via Chroma vector database
- Progressive disclosure with token cost visibility

**Installation:**
```bash
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

**MCP Tools:** `search`, `timeline`, `get_observations`, `save_memory`

### 5.2 Memory Bank Pattern

Community pattern using multiple CLAUDE.md files:
- `CLAUDE.md` - Primary memory bank
- `CLAUDE-<topic>.md` - Supplementary references
- `/update memory bank` command to refresh

---

## 6. Best Practices

### 6.1 Writing Effective CLAUDE.md

**DO:**
- Be specific: "Use 2-space indentation" not "Format code properly"
- Use bullet points and markdown headings
- Include frequently used commands
- Document code style and naming conventions
- Add architectural patterns

**DON'T:**
- Include temporary sprint instructions
- Add frequently changing requirements
- Store sensitive information (API keys)

**The Test:** Include what you'd want Claude knowing in 6 months.

### 6.2 Organizing Rules

```
.claude/rules/
├── code-style.md      # One topic per file
├── testing.md         # Descriptive filenames
├── security.md        # Focused content
└── frontend/          # Subdirectories for grouping
    └── react.md
```

### 6.3 Auto Memory Curation

Claude keeps `MEMORY.md` under 200 lines by:
- Moving details to topic files
- Keeping index entries concise
- Referencing topic files: "See debugging.md for error patterns"

### 6.4 Agent Memory Tips

- Use `user` scope as default (cross-project learning)
- Use `project` for team-shareable knowledge
- Use `local` for personal notes
- Prompt agents: "Check your memory before starting; update it after completing"

---

## 7. Environment Variables

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` | Force auto-memory off |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY=0` | Force auto-memory on |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50` | Trigger compaction earlier |

---

## 8. Commands Reference

| Command | Purpose |
|---------|---------|
| `/memory` | Open memory file selector |
| `/init` | Bootstrap CLAUDE.md for codebase |
| `/agents` | Manage subagents |

---

## Sources

- [Official Memory Documentation](https://code.claude.com/docs/en/memory)
- [Subagents Documentation](https://code.claude.com/docs/en/sub-agents)
- [Claude-Mem Plugin](https://github.com/thedotmack/claude-mem)
- [Memory Bank System](https://github.com/centminmod/my-claude-code-setup)
- [Agent Memory Best Practices](https://github.com/shanraisshan/claude-code-best-practice/blob/main/reports/claude-agent-memory.md)
- [Claude Code for PMs - Project Memory](https://ccforpms.com/fundamentals/project-memory)
