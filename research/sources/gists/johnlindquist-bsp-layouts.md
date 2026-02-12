---
source: https://gist.github.com/johnlindquist/9b06a09125b03c59de53a397bbdf45dd
fetched: 2026-02-11
type: gist
author: johnlindquist
description: WezTerm + Claude Code Multi-Session Workflows with BSP Layouts
---

# WezTerm + Claude Code: Multi-Session Workflows with BSP Layouts

A guide to spawning multiple Claude Code sessions in WezTerm panes with BSP (Binary Space Partitioning) layouts.

## The Problem

When working with Claude Code, you often want to:
- Delegate subtasks to parallel Claude sessions
- Explore tangents without losing context
- Run multiple investigations simultaneously

WezTerm's CLI makes this possible, but there are several gotchas to navigate.

## Key Discoveries

### 1. PATH Preservation

**Never use `wezterm cli split-pane -- command`**

This bypasses your shell entirely, losing PATH additions from `.zshrc`/`.bashrc`. Tools installed via npm, homebrew, etc. won't be found.

```bash
# WRONG - bypasses shell, loses PATH
wezterm cli split-pane -- claude

# CORRECT - two-step approach preserves PATH
PANE_ID=$(wezterm cli split-pane)
printf 'claude\n' | wezterm cli send-text --pane-id "$PANE_ID"
```

### 2. Newline Handling

**Use `printf` pipe, not string escapes**

```bash
# WRONG - sends literal \n
wezterm cli send-text --pane-id "$PANE_ID" "command\n"
wezterm cli send-text --pane-id "$PANE_ID" $'command\n'  # Works alone, breaks in loops

# CORRECT - printf interprets \n properly
printf 'command\n' | wezterm cli send-text --pane-id "$PANE_ID"

# With variables
printf 'claude "$(cat /tmp/prompt-%d.md)"\n' "$i" | wezterm cli send-text --pane-id "$PANE_ID"
```

### 3. Tab Detection

**`is_active` returns one pane per tab, not the global focus**

Each tab has its own "active pane". Querying `is_active == true` returns multiple results.

```bash
# WRONG - returns active pane from FIRST tab, not YOUR tab
wezterm cli list --format json | jq '[.[] | select(.is_active == true)] | .[0]'

# CORRECT - use WEZTERM_PANE environment variable
CURRENT_TAB=$(wezterm cli list --format json | jq -r --arg pane "$WEZTERM_PANE" '
  .[] | select(.pane_id == ($pane | tonumber)) | .tab_id
')
```

### 4. BSP Layout Algorithm

To create balanced pane grids (like i3/bspwm), always split the largest pane:

```bash
# Find largest pane by area (rows × cols)
LARGEST=$(wezterm cli list --format json | jq -r --arg tab "$TAB" '
  map(select(.tab_id == ($tab | tonumber))) |
  sort_by(-(.size.rows * .size.cols)) |
  .[0]
')

# Split based on aspect ratio (matches WezTerm's tiled mode)
# ratio > 2.0 = split horizontally, else vertically
RATIO=$(cols / rows)
DIRECTION=$(ratio > 2.0 ? "--right" : "--bottom")
```

## The BSP Split Script

Save as `/tmp/bsp-split.sh`:

```bash
#!/bin/bash
# BSP Split: Find largest pane IN CURRENT TAB and bisect it

# Get current pane from WEZTERM_PANE env var (set by WezTerm for shells)
if [ -z "$WEZTERM_PANE" ]; then
  echo "Error: WEZTERM_PANE not set" >&2
  exit 1
fi

# Get tab ID for current pane
CURRENT_TAB=$(wezterm cli list --format json | jq -r --arg pane "$WEZTERM_PANE" '
  .[] | select(.pane_id == ($pane | tonumber)) | .tab_id
')

# Get largest pane in current tab only
LARGEST=$(wezterm cli list --format json | jq -r --arg tab "$CURRENT_TAB" '
  map(select(.tab_id == ($tab | tonumber) and .is_zoomed == false)) |
  sort_by(-(.size.rows * .size.cols)) |
  .[0] |
  "\(.pane_id) \(.size.cols) \(.size.rows)"
')

PANE_ID=$(echo "$LARGEST" | awk '{print $1}')
COLS=$(echo "$LARGEST" | awk '{print $2}')
ROWS=$(echo "$LARGEST" | awk '{print $3}')

RATIO=$(echo "$COLS $ROWS" | awk '{printf "%.2f", $1/$2}')
if (( $(echo "$RATIO > 2.0" | bc -l) )); then
  wezterm cli split-pane --pane-id "$PANE_ID" --right
else
  wezterm cli split-pane --pane-id "$PANE_ID" --bottom
fi
```

## Prompt File Organization

Store prompts in `/tmp/claude-sessions/` with structured names:

```bash
mkdir -p /tmp/claude-sessions

# Pattern: <cwd>-<timestamp>-<purpose>.md
CWD_NAME=$(basename "$PWD")
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
PURPOSE="write-tests"

PROMPT_FILE="/tmp/claude-sessions/${CWD_NAME}-${TIMESTAMP}-${PURPOSE}.md"
# Example: /tmp/claude-sessions/myapp-20260113-153045-write-tests.md
```

This makes it easy to find and debug session prompts later.

## Usage Examples

### Single Claude Session with Context

```bash
# Setup prompt file
mkdir -p /tmp/claude-sessions
PROMPT_FILE="/tmp/claude-sessions/$(basename $PWD)-$(date +%Y%m%d-%H%M%S)-review.md"

cat > "$PROMPT_FILE" << 'EOF'
## Context
We're building a REST API with authentication.
The main files are in src/api/ and src/auth/.

## Task
Review the auth middleware and suggest improvements.
EOF

# Spawn session
NEW_PANE=$(/tmp/bsp-split.sh)
printf 'claude "$(cat %s)"\n' "$PROMPT_FILE" | wezterm cli send-text --pane-id "$NEW_PANE"
```

### Multiple Parallel Sessions

```bash
# Setup
mkdir -p /tmp/claude-sessions
CWD_NAME=$(basename "$PWD")
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Create prompt files with structured names
TASKS=("write-tests" "add-error-handling" "update-docs" "refactor-utils")
PROMPT_FILES=()
for TASK in "${TASKS[@]}"; do
  PROMPT_FILE="/tmp/claude-sessions/${CWD_NAME}-${TIMESTAMP}-${TASK}.md"
  cat > "$PROMPT_FILE" << EOF
## Task
$TASK
EOF
  PROMPT_FILES+=("$PROMPT_FILE")
done

# Spawn all sessions with BSP layout
for PROMPT_FILE in "${PROMPT_FILES[@]}"; do
  NEW_PANE=$(/tmp/bsp-split.sh)
  printf 'claude "$(cat %s)"\n' "$PROMPT_FILE" | wezterm cli send-text --pane-id "$NEW_PANE"
done
```

### 12-Pane Grid for Parallel Hello Worlds

```bash
mkdir -p /tmp/claude-sessions
CWD_NAME=$(basename "$PWD")
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

LANGS=("python" "typescript" "rust" "go" "ruby" "bash" "lua" "javascript" "c" "elixir" "haskell" "ocaml")
PROMPT_FILES=()
for LANG in "${LANGS[@]}"; do
  PROMPT_FILE="/tmp/claude-sessions/${CWD_NAME}-${TIMESTAMP}-hello-${LANG}.md"
  cat > "$PROMPT_FILE" << EOF
Write and run a hello world in $LANG.
EOF
  PROMPT_FILES+=("$PROMPT_FILE")
done

# Spawn 12 sessions - creates balanced BSP grid
for PROMPT_FILE in "${PROMPT_FILES[@]}"; do
  NEW_PANE=$(/tmp/bsp-split.sh)
  printf 'claude "$(cat %s)"\n' "$PROMPT_FILE" | wezterm cli send-text --pane-id "$NEW_PANE"
done
```

## WezTerm CLI Reference

### Pane Operations

```bash
# Create pane (returns pane ID)
wezterm cli split-pane                    # Split current pane (bottom)
wezterm cli split-pane --right            # Split horizontally
wezterm cli split-pane --pane-id 123      # Split specific pane
wezterm cli split-pane --cwd ~/project    # With working directory

# Send text to pane
printf 'command\n' | wezterm cli send-text --pane-id "$PANE_ID"

# List all panes
wezterm cli list --format json
```

### Useful jq Queries

```bash
# Count panes in current tab
wezterm cli list --format json | jq --arg tab "$TAB" '
  [.[] | select(.tab_id == ($tab | tonumber))] | length
'

# Get pane distribution across tabs
wezterm cli list --format json | jq '
  group_by(.tab_id) |
  map({tab_id: .[0].tab_id, pane_count: length})
'

# Find largest pane
wezterm cli list --format json | jq '
  sort_by(-(.size.rows * .size.cols)) | .[0]
'
```

## Swarm Mode (Multi-Session Coordination)

When spawning multiple sessions that need to coordinate, use **swarm mode**. Sessions can track each other's progress via shared state files.

### Environment Variables (passed to children)
- `CLAUDE_SWARM_ID` - Unique swarm identifier
- `CLAUDE_SWARM_DIR` - Path to shared state directory
- `CLAUDE_PARENT_SESSION` - Parent's session ID
- `CLAUDE_SESSION_ROLE` - "parent" or "child"
- `CLAUDE_SESSION_PURPOSE` - Task description for this session

### Swarm Directory Structure
```
./sessions/<swarm-id>/
├── manifest.json       # All sessions in this swarm
├── parent-<id>.md      # Parent session status
├── child-<id>-1.md     # Child session 1 status
└── child-<id>-2.md     # Child session 2 status
```

### Initialize Swarm (Parent Does This Once)
```bash
# Generate swarm ID
SWARM_ID="$(basename $PWD)-$(date +%Y%m%d-%H%M%S)"
SWARM_DIR="./sessions/$SWARM_ID"
mkdir -p "$SWARM_DIR"

# Create manifest
cat > "$SWARM_DIR/manifest.json" << EOF
{
  "swarm_id": "$SWARM_ID",
  "created_at": "$(date -Iseconds)",
  "swarm_dir": "$SWARM_DIR",
  "parent": {
    "session_id": "${CLAUDE_SESSION_ID:-parent}",
    "purpose": "Coordinate tasks",
    "status": "running"
  },
  "children": []
}
EOF

echo "Swarm initialized: $SWARM_ID"
```

### Spawn Child with Swarm Context
```bash
# Create prompt file
PURPOSE="write-tests"
PROMPT_FILE="/tmp/claude-sessions/${CWD_NAME}-${TIMESTAMP}-${PURPOSE}.md"
cat > "$PROMPT_FILE" << 'EOF'
## Context
You are part of a coordinated swarm session.

## Your Task
Write unit tests for the auth module.

## Coordination
- Update your progress in: $CLAUDE_SWARM_DIR/child-$CLAUDE_SESSION_ID.md
- Check sibling progress: ls $CLAUDE_SWARM_DIR/*.md
EOF

# Spawn with environment variables
NEW_PANE=$(/tmp/bsp-split.sh)
printf 'CLAUDE_SWARM_ID=%s CLAUDE_SWARM_DIR=%s CLAUDE_SESSION_ROLE=child CLAUDE_SESSION_PURPOSE="%s" CLAUDE_PARENT_SESSION=%s claude "$(cat %s)"\n' \
  "$SWARM_ID" "$SWARM_DIR" "$PURPOSE" "${CLAUDE_SESSION_ID:-parent}" "$PROMPT_FILE" \
  | wezterm cli send-text --pane-id "$NEW_PANE"
```

## Requirements

- WezTerm (with `wezterm cli` available)
- jq (for JSON parsing)
- bc (for floating point comparison in BSP ratio)

## Gotchas Summary

| Issue | Wrong | Right |
|-------|-------|-------|
| PATH missing | `split-pane -- cmd` | split-pane + send-text |
| Literal `\n` | `"cmd\n"` or `$'cmd\n'` in loops | `printf 'cmd\n' \|` |
| Wrong tab | `is_active == true` | `$WEZTERM_PANE` env var |
| Unbalanced splits | Always split current | BSP: split largest |

## Claude Code Skills

These patterns are packaged as Claude Code skills available in this gist:
- `wezterm-pane` - Create panes and run commands with PATH preserved
- `session` - Spawn Claude sessions with conversation context using BSP layout
- Power session mode: `--dangerously-skip-permissions` flag for trusted directories

## License

MIT - Use freely, attribute if you share.
