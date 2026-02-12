---
source: https://github.com/anthropics/claude-code/issues/23574
fetched: 2026-02-11
type: github-issue
repo: anthropics/claude-code
issue: 23574
state: open
labels: [enhancement, area:tui, area:core]
---

# [FEATURE] Add WezTerm as a split-pane backend for agent teams (teammateMode)

**State**: open | **Author**: mertkaradayi | **Created**: 2026-02-06T04:32:41Z
**Labels**: enhancement, area:tui, area:core
**Reactions**: 👍 15, 🚀 4
**Comments**: 2

## Body

### Preflight Checklist

- [x] I have searched [existing requests](https://github.com/anthropics/claude-code/issues?q=is%3Aissue%20label%3Aenhancement) and this feature hasn't been requested yet
- [x] This is a single feature request (not multiple features)

### Problem Statement

WezTerm users cannot use split-pane mode for agent teams. The current `teammateMode: "tmux"` setting only supports tmux and iTerm2 as backends. WezTerm is a popular GPU-accelerated, cross-platform terminal emulator with a **full CLI for programmatic pane management** — making it a natural fit as a third split-pane backend.

Currently, WezTerm users are forced to either:
1. Run tmux *inside* WezTerm (redundant — WezTerm is already a multiplexer)
2. Use in-process mode (no visual split panes)

### Proposed Solution

Add a **WezTerm backend** for `teammateMode` that uses WezTerm's CLI to spawn teammates in native split panes.

WezTerm's CLI provides direct equivalents to every tmux command Claude Code needs:

| Operation | tmux | WezTerm CLI |
|-----------|------|-------------|
| Split horizontally | `tmux split-window -h -- cmd` | `wezterm cli split-pane --right -- cmd` |
| Split vertically | `tmux split-window -v -- cmd` | `wezterm cli split-pane --bottom -- cmd` |
| List panes | `tmux list-panes` | `wezterm cli list` |
| Focus a pane | `tmux select-pane -t N` | `wezterm cli activate-pane --pane-id N` |
| Get pane info | `tmux display -p '#{pane_id}'` | `WEZTERM_PANE` env var (auto-set per pane) |
| Top-level split | N/A | `wezterm cli split-pane --top-level --bottom -- cmd` |

**Detection** is straightforward — WezTerm sets `TERM_PROGRAM=WezTerm` in the environment.

**Key implementation detail:** `wezterm cli split-pane` returns the new pane ID on success, and each spawned pane automatically receives a `WEZTERM_PANE` environment variable. This makes tracking and targeting teammate panes trivial.

**Suggested behavior:**
- When `teammateMode` is `"tmux"` or `"auto"`, check for `TERM_PROGRAM=WezTerm` alongside existing tmux/iTerm2 detection
- Or add `"wezterm"` as an explicit `teammateMode` value

### Alternative Solutions

- Running tmux inside WezTerm works but is redundant since WezTerm is itself a multiplexer with full pane management
- In-process mode works but lacks the visual benefit of seeing all teammates simultaneously

### Priority

Medium - Significant impact on productivity

### Feature Category

CLI commands and flags

### Use Case Example

```bash
# WezTerm CLI pane management works out of the box:
$ wezterm cli split-pane --right -- echo "hello from new pane"
3    # returns new pane ID

$ wezterm cli split-pane --bottom -- bash -l
5    # returns new pane ID

$ wezterm cli list
WINID TABID PANEID WORKSPACE SIZE   TITLE      CWD
0     0     0      default   120x40 zsh        /Users/me
0     0     3      default   60x40  zsh        /Users/me
0     0     5      default   120x20 zsh        /Users/me

$ wezterm cli activate-pane --pane-id 3
# focuses the specified pane
```

Agent teams would use this the same way they use tmux:

```bash
# Claude Code spawns teammates in native WezTerm panes:
wezterm cli split-pane --right -- claude --resume <session-id> --teammate
wezterm cli split-pane --bottom -- claude --resume <session-id> --teammate
```

### Additional Context

**Environment:**
- Claude Code version: 2.1.33
- OS: macOS Darwin 25.3.0 (arm64)
- Terminal: WezTerm 20240203-110809-5046fc22
- `TERM_PROGRAM=WezTerm` is set automatically

**References:**
- WezTerm CLI split-pane docs: https://wezfurlong.org/wezterm/cli/cli/split-pane.html
- WezTerm CLI list docs: https://wezfurlong.org/wezterm/cli/cli/list.html
- Related: #19555 (built-in multiplexer vision), #23572 (tmux/iTerm2 silent fallback bug)
- WezTerm is written in Rust, GPU-accelerated, supports macOS/Linux/Windows
- WezTerm has a growing user base and is commonly used by developers who prefer it over iTerm2

## Comments

### Comment by SalzerRefinedLeads (2026-02-06T12:23:26Z)

Please add this.

**Reactions**: 👍 8

### Comment by zendevio (2026-02-08T08:30:39Z)

I've moved to WezTerm as my main terminal. I find it works more effectively than relying on tmux, so I'm wondering if anyone has started work on an integration for this.

**Reactions**: 👍 4
