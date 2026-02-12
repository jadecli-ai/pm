---
source: https://github.com/anthropics/claude-code/issues/24189
fetched: 2026-02-11
type: github-issue
repo: anthropics/claude-code
issue: 24189
state: open
labels: [enhancement, platform:macos, area:tui, area:core]
---

# [Feature Request] Add Ghostty as a split-pane backend for agent teams (teammateMode)

**State**: open | **Author**: esakat | **Created**: 2026-02-08T14:18:45Z
**Labels**: enhancement, platform:macos, area:tui, area:core
**Reactions**: 👍 12
**Comments**: 1

## Body

### Preflight Checklist

- [x] I have searched [existing requests](https://github.com/anthropics/claude-code/issues?q=is%3Aissue%20label%3Aenhancement) and this feature hasn't been requested yet
- [x] This is a single feature request (not multiple features)

### Problem Statement

Ghostty users cannot use split-pane mode for agent teams. The current `teammateMode` setting only supports **tmux** and **iTerm2** as backends. [Ghostty](https://ghostty.org/) is a fast, GPU-accelerated, cross-platform terminal emulator with a growing user base — yet Ghostty users are forced to either:

1. Run tmux *inside* Ghostty (redundant overhead for a terminal that already has native splits)
2. Use in-process mode (no visual split panes)

### Proposed Solution

Add a **Ghostty backend** for `teammateMode` that spawns teammates in native Ghostty split panes.

#### Ghostty's split capabilities

Ghostty already has split-pane actions internally:

| Action | Description |
|--------|-------------|
| `new_split:right` / `new_split:down` | Create a new split in the specified direction |
| `goto_split:right` / `goto_split:previous` | Focus an adjacent split by direction or creation order |
| `resize_split:up,10` | Resize a split |
| `toggle_split_zoom` | Zoom a split to fill the tab |
| `equalize_splits` | Equalize all split sizes |

#### Current blocker: programmatic API

Ghostty's keybinding actions exist but **there is no stable CLI/IPC mechanism to invoke them programmatically yet**. The Ghostty team is actively working on platform-specific IPC approaches:

- **macOS**: AppleScript / App Intents framework (in development)
- **Linux**: D-Bus integration (planned)
- Tracking discussion: [ghostty-org/ghostty#2353](https://github.com/ghostty-org/ghostty/discussions/2353)

#### Suggested implementation approach

Once Ghostty exposes a programmatic API, integration would follow the same pattern as tmux/iTerm2:

| Operation | tmux | Ghostty (anticipated) |
|-----------|------|-----------------------|
| Split pane | `tmux split-window -h -- cmd` | AppleScript / D-Bus `new_split:right` + run command |
| Focus pane | `tmux select-pane -t N` | `goto_split:next` or pane ID targeting |
| Detection | `$TMUX` env var | `$TERM_PROGRAM=ghostty` (already set) |

**Detection** is straightforward — Ghostty sets `TERM_PROGRAM=ghostty` in the environment.

#### Phased approach

1. **Phase 1 (now)**: Track this as a known request; monitor Ghostty's IPC API progress
2. **Phase 2 (when Ghostty ships CLI/IPC)**: Implement the Ghostty backend for `teammateMode`
3. **Phase 3**: Update `"auto"` detection priority: `iTerm2 > tmux > ghostty > in-process`

### Alternative Solutions

- Running tmux inside Ghostty works but adds unnecessary complexity for users who chose Ghostty specifically to avoid tmux
- In-process mode works but loses the multi-pane visibility that makes agent teams compelling

### Priority

Medium - Significant impact on productivity

### Feature Category

CLI commands and flags

### Additional Context

**Related issues:**
- #23574 — WezTerm split-pane backend (same motivation, different terminal)
- #24122 — Zellij split-pane support
- #23572 — tmux/iTerm2 silent fallback bug

**Ghostty references:**
- Ghostty homepage: https://ghostty.org/
- Split keybind actions: https://ghostty.org/docs/config/keybind/reference
- Scripting API discussion: https://github.com/ghostty-org/ghostty/discussions/2353
- GitHub: https://github.com/ghostty-org/ghostty (50k+ stars)

**Environment:**
- Claude Code version: latest
- OS: macOS (Darwin 25.2.0, arm64)
- Terminal: Ghostty

## Comments

### Comment by github-actions[bot] (2026-02-08T14:21:55Z)

Found 2 possible duplicate issues:

1. https://github.com/anthropics/claude-code/issues/23574
2. https://github.com/anthropics/claude-code/issues/24122

This issue will be automatically closed as a duplicate in 3 days.

- If your issue is a duplicate, please close it and 👍 the existing issue instead
- To prevent auto-closure, add a comment or 👎 this comment

🤖 Generated with [Claude Code](https://claude.ai/code)

**Reactions**: 👍 1, 👎 6
