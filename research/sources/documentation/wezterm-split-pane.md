---
source: https://wezterm.org/cli/cli/split-pane.html
fetched: 2026-02-11
type: documentation
project: WezTerm
---

# WezTerm CLI split-pane Command

The `wezterm cli split-pane` command divides the current pane and spawns a command into the newly created split. It outputs the pane ID of the new pane upon successful execution.

## Basic Usage

```
wezterm cli split-pane [OPTIONS] [PROG]...
```

## Default Behavior

Without additional arguments, the command performs a vertical split with the new pane positioned at the bottom, occupying approximately 50% of available space.

## Direction Options

- `--bottom`: Creates a vertical split with the new pane below (default)
- `--top`: Creates a vertical split with the new pane above
- `--left`: Creates a horizontal split with the new pane on the left
- `--right`: Creates a horizontal split with the new pane on the right
- `--horizontal`: Equivalent to `--right`

## Size Configuration

- `--cells CELLS`: Specifies the exact cell count for the new split
- `--percent PERCENT`: Defines the split size as a percentage of available space

## Additional Options

- `--pane-id PANE_ID`: Targets a specific pane for splitting (defaults to the current pane via the WEZTERM_PANE environment variable)
- `--cwd CWD`: Sets the initial working directory for the spawned program
- `--move-pane-id MOVE_PANE_ID`: Moves an existing pane into the new split instead of spawning a fresh command
- `--top-level`: Splits the entire window rather than just the active pane

## Command Examples

**Basic split to the bottom:**
```bash
wezterm cli split-pane
```

**Launch bash as a login shell in a new bottom pane:**
```bash
wezterm cli split-pane -- bash -l
```

**Create a left split occupying 30% of space:**
```bash
wezterm cli split-pane --left --percent 30
```

## Notes

- Use `--` to separate wezterm arguments from program arguments to avoid parameter confusion
- Available since version 20220624-141144-bd1b7c5d
