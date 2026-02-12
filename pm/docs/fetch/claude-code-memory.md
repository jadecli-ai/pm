# Claude Code Memory System

> Source: https://code.claude.com/docs/en/memory

## Overview

Claude Code has two kinds of memory that persist across sessions:

* **Auto memory**: Claude automatically saves useful context like project patterns, key commands, and your preferences. This persists across sessions.
* **CLAUDE.md files**: Markdown files you write and maintain with instructions, rules, and preferences for Claude to follow.

Both are loaded into Claude's context at the start of every session, though auto memory loads only the first 200 lines of its main file.

## Memory Types Hierarchy

| Memory Type | Location | Purpose | Shared With |
|-------------|----------|---------|-------------|
| **Managed policy** | macOS: `/Library/Application Support/ClaudeCode/CLAUDE.md` Linux: `/etc/claude-code/CLAUDE.md` Windows: `C:\Program Files\ClaudeCode\CLAUDE.md` | Organization-wide instructions managed by IT/DevOps | All users in organization |
| **Project memory** | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared instructions for the project | Team members via source control |
| **Project rules** | `./.claude/rules/*.md` | Modular, topic-specific project instructions | Team members via source control |
| **User memory** | `~/.claude/CLAUDE.md` | Personal preferences for all projects | Just you (all projects) |
| **Project memory (local)** | `./CLAUDE.local.md` | Personal project-specific preferences | Just you (current project) |
| **Auto memory** | `~/.claude/projects/<project>/memory/` | Claude's automatic notes and learnings | Just you (per project) |

### Priority Rules
- CLAUDE.md files in the directory hierarchy above the working directory are loaded in full at launch
- CLAUDE.md files in child directories load on demand when Claude reads files in those directories
- Auto memory loads only the first 200 lines of `MEMORY.md`
- More specific instructions take precedence over broader ones

## Auto Memory

Auto memory is a persistent directory where Claude records learnings, patterns, and insights as it works. Unlike CLAUDE.md files that contain instructions you write for Claude, auto memory contains notes Claude writes for itself based on what it discovers during sessions.

### What Claude Remembers
* Project patterns: build commands, test conventions, code style preferences
* Debugging insights: solutions to tricky problems, common error causes
* Architecture notes: key files, module relationships, important abstractions
* Your preferences: communication style, workflow habits, tool choices

### Storage Location
Each project gets its own memory directory at `~/.claude/projects/<project>/memory/`. The `<project>` path is derived from the git repository root, so all subdirectories within the same repo share one auto memory directory. Git worktrees get separate memory directories.

### Directory Structure
```
~/.claude/projects/<project>/memory/
├── MEMORY.md          # Concise index, loaded into every session
├── debugging.md       # Detailed notes on debugging patterns
├── api-conventions.md # API design decisions
└── ...                # Any other topic files Claude creates
```

### How It Works
* The first 200 lines of `MEMORY.md` are loaded into Claude's system prompt at the start of every session
* Content beyond 200 lines is not loaded automatically
* Claude is instructed to keep it concise by moving detailed notes into separate topic files
* Topic files like `debugging.md` or `patterns.md` are not loaded at startup
* Claude reads them on demand using its standard file tools when it needs the information

### Configuration
```bash
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1  # Force off
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=0  # Force on
```

## CLAUDE.md Imports

CLAUDE.md files can import additional files using `@path/to/import` syntax:

```markdown
See @README for project overview and @package.json for available npm commands.

# Additional Instructions
- git workflow @docs/git-instructions.md
```

- Both relative and absolute paths are allowed
- Relative paths resolve relative to the file containing the import
- Imported files can recursively import additional files, with a max-depth of 5 hops
- Imports are not evaluated inside markdown code spans and code blocks

## Modular Rules with `.claude/rules/`

For larger projects, organize instructions into multiple files:

```
your-project/
├── .claude/
│   ├── CLAUDE.md           # Main project instructions
│   └── rules/
│       ├── code-style.md   # Code style guidelines
│       ├── testing.md      # Testing conventions
│       └── security.md     # Security requirements
```

### Path-Specific Rules
Rules can be scoped to specific files using YAML frontmatter:

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API Development Rules
- All API endpoints must include input validation
```

### Glob Patterns

| Pattern | Matches |
|---------|---------|
| `**/*.ts` | All TypeScript files in any directory |
| `src/**/*` | All files under `src/` directory |
| `*.md` | Markdown files in the project root |
| `src/components/*.tsx` | React components in a specific directory |

## Best Practices

* **Be specific**: "Use 2-space indentation" is better than "Format code properly"
* **Use structure to organize**: Format each individual memory as a bullet point and group related memories under descriptive markdown headings
* **Review periodically**: Update memories as your project evolves
