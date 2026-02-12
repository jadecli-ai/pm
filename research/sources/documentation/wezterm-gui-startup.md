---
source: https://wezterm.org/config/lua/gui-events/gui-startup.html
fetched: 2026-02-11
type: documentation
project: WezTerm
---

# WezTerm gui-startup Event

The `gui-startup` event is a WezTerm callback that executes when the GUI server initializes during `wezterm start`.

## Key Characteristics

- **Timing**: Fires before any default program launches and before the `gui-attached` event
- **Scope**: Does not trigger for `wezterm connect` invocations
- **Command Argument**: Since version 20220807-113146-c2fee766, receives an optional `SpawnCommand` argument representing parameters passed to `wezterm start`
- **Window Creation**: If no explicit program was passed to `wezterm start`, and if the `gui-startup` event causes any panes to be created, those will take precedence over the default program configuration

## Use Cases

Establishing standardized window layouts and workspace configurations at startup, eliminating manual setup repetition.

## Code Examples

### Basic Split Configuration

Creates a three-way pane division:

```lua
wezterm.on('gui-startup', function(cmd)
  local tab, pane, window = mux.spawn_window(cmd or {})
  pane:split { size = 0.3 }
  pane:split { size = 0.5 }
end)
```

### Maximized Window

Launches with the window maximized:

```lua
wezterm.on('gui-startup', function(cmd)
  local tab, pane, window = mux.spawn_window(cmd or {})
  window:gui_window():maximize()
end)
```

### Multi-Workspace Setup

Configures separate development and automation workspaces with distinct purposes and auto-starts relevant tools.

## Related Resources

- `wezterm.mux` module for window spawning
- `gui-attached` event for post-attachment hooks
