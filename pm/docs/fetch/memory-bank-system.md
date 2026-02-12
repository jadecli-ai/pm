# CLAUDE.md Memory Bank System

> Source: https://github.com/centminmod/my-claude-code-setup

## Overview

The memory bank system helps Claude Code retain context over many chat sessions through structured documentation files.

## Directory Structure

```
your-project/
├── .claude/
│   ├── settings.json          # Claude Code settings
│   └── statuslines/
│       └── statusline.sh      # Custom statusline script
├── CLAUDE.md                  # Primary memory bank
├── CLAUDE-cloudflare.md       # Supplementary reference
├── CLAUDE-cloudflare-mini.md  # Condensed documentation
└── CLAUDE-convex.md           # Platform-specific guide
```

## Configuration Patterns

### Statusline Configuration

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statuslines/statusline.sh",
    "padding": 0
  }
}
```

### Tool Requirements

Install faster tools for better performance:
```bash
brew install ripgrep fd jq  # macOS
```

## Best Practices

1. **Memory Bank Updates** - After task completion, use `/update memory bank` command
2. **Supplementary Documentation** - Keep platform-specific guides as separate files
3. **Modular Organization** - Remove unused sections from templates
4. **Git Worktree Support** - Include `.worktreeinclude` for Claude Code Desktop compatibility

## Key Principles

- **Iterative documentation**: AI updates understanding based on completed tasks
- **Architecture decisions**: Document key decisions for future reference
- **Modular files**: Separate concerns into focused documentation files
