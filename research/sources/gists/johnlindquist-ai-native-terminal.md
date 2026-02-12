---
source: https://gist.github.com/johnlindquist/53b5638e82e1932cfc762ad23ad99d87
fetched: 2026-02-11
type: gist
author: johnlindquist
description: Why WezTerm - The AI-Native Terminal for the Agentic Era
---

# Why WezTerm: The AI-Native Terminal for the Agentic Era

## The Thesis

We are entering an era where AI agents can read, write, and modify configuration files on your behalf. In this new paradigm, **the best tool is no longer the one with the prettiest GUI or the most menu options—it's the one with the most programmable surface area.**

WezTerm is that tool for terminals.

## The Terminal Landscape in 2025

| Terminal | Configuration | Scriptable Actions | AI-Friendly |
|----------|--------------|-------------------|-------------|
| **iTerm2** | Plist/GUI | AppleScript (limited) | ❌ Binary prefs |
| **Alacritty** | YAML | None | ⚠️ Config only |
| **Kitty** | Custom format | Limited scripting | ⚠️ Partial |
| **Hyper** | JavaScript | Plugin system | ⚠️ Electron bloat |
| **Terminal.app** | Plist/GUI | AppleScript | ❌ Binary prefs |
| **WezTerm** | **Lua** | **Full Lua runtime** | ✅ **Complete** |

The difference isn't incremental. It's categorical.

## What Makes WezTerm Different

### 1. Configuration IS Code

Most terminals separate "configuration" from "behavior." You set some options in a config file, and that's it. WezTerm's config file is a **full Lua program** that executes when the terminal starts.

```lua
-- This isn't configuration. This is code.
local function smart_split(window, pane)
  local dims = pane:get_dimensions()
  if dims.cols > dims.viewport_rows * 2.2 then
    pane:split({ direction = "Right", size = 0.5 })
  else
    pane:split({ direction = "Bottom", size = 0.5 })
  end
end
```

An AI can write this. An AI can modify this. An AI can extend this. Try doing that with iTerm2's binary preference files.

### 2. Runtime Access to Everything

WezTerm exposes its entire internal state to Lua:

- **Panes**: Query dimensions, running processes, working directories
- **Tabs**: List panes, get/set titles, manage layouts
- **Windows**: Control appearance, override settings dynamically
- **Events**: React to focus changes, key presses, window resizes
- **External tools**: Shell out to any CLI tool (`zoxide`, `git`, `fzf`)

```lua
-- Query the current process to change behavior
local function is_vim(pane)
  local process = pane:get_foreground_process_info()
  return process and process.executable:find("vim") ~= nil
end

-- Now keybindings can be context-aware
if is_vim(pane) then
  -- Pass through to Vim
else
  -- Handle in WezTerm
end
```

### 3. Action Callbacks: Where AI Shines

The killer feature is `wezterm.action_callback()`. Any keybinding can execute arbitrary Lua code:

```lua
{
  key = "d",
  mods = "CMD",
  action = wezterm.action_callback(function(window, pane)
    -- Literally any logic you want
    -- An AI can write this for you based on your description
  end),
}
```

This is the unlock. When you say to an AI:

> "Make Cmd+D create smart splits that respect a layout mode like Zellij"

The AI can actually implement that. Not "here's how you'd do it if WezTerm supported it" but actual working code that does exactly what you asked.

### 4. Event-Driven Architecture

WezTerm fires events that you can hook into:

```lua
wezterm.on('format-tab-title', function(tab, tabs, panes, config, hover, max_width)
  -- Complete control over tab rendering
end)

wezterm.on('update-status', function(window, pane)
  -- Build any status bar you want
end)

wezterm.on('window-resized', function(window, pane)
  -- React to window changes
end)
```

Every event is a hook where AI-generated code can live.

## The AI Advantage

### Before: The GUI Trap

Traditional workflow for customizing iTerm2:
1. Open Preferences
2. Click through tabs
3. Find the setting (if it exists)
4. Toggle it
5. Realize you need something more complex
6. Search for "iTerm2 smart splits"
7. Find out it's not possible
8. Give up or switch tools

### After: The Conversational Workflow

WezTerm workflow with AI:
1. Tell AI what you want
2. AI writes the Lua code
3. Paste into config
4. Reload
5. It works (or AI debugs it)

**The terminal becomes as customizable as your imagination.**

### Real Examples from This Config

Every one of these features was built by describing the desired behavior:

| Request | Result |
|---------|--------|
| "Zellij-style layout modes" | 200 lines of layout management code |
| "Fuzzy tab picker showing directory and process" | Custom InputSelector with dynamic choices |
| "Status bar showing layout mode, workspace, and time" | Event handler with formatted segments |
| "Cmd+T should open zoxide picker in new tab" | Chained actions: spawn tab → query zoxide → show picker |
| "Different color schemes per project directory" | Dynamic config overrides based on cwd |

None of these are "features" of WezTerm. They're **programs** that run inside WezTerm.

## Why Not the Others?

### iTerm2
The gold standard for macOS terminals, but:
- Configuration stored in binary plists
- AppleScript integration is clunky and limited
- No way to script pane/tab behavior
- AI would need to generate AppleScript + GUI instructions

### Alacritty
Fast and minimal, but:
- YAML config only—no scripting
- No event system
- No action callbacks
- AI can only change static settings

### Kitty
Closer to WezTerm in capability, but:
- Custom config format (not a real language)
- Scripting requires external "kittens" (Python scripts)
- Less cohesive API
- Split between config file and external scripts

### Hyper
JavaScript-based, which sounds good, but:
- Electron-based (resource heavy)
- Plugin system is more about theming
- Less terminal-native functionality
- Performance issues

## The Compounding Effect

Here's what happens over time:

**Month 1**: You ask AI to set up basic splits and styling.

**Month 3**: You've accumulated custom layouts, smart navigation, project-specific configs.

**Month 6**: Your terminal has features that don't exist in any other terminal—because you (with AI) invented them.

**Month 12**: Your WezTerm config is a personalized terminal multiplexer that exactly matches your workflow.

This is only possible when the tool is programmable enough to grow with you.

## The Future is Scriptable

We're moving toward a world where:

1. **AI agents edit config files** as part of their workflow
2. **Natural language becomes the interface** for customization
3. **The best tools are the most AI-accessible** ones

WezTerm is built for this future:

- **Plain text config**: AI can read and write it
- **Real programming language**: AI can reason about it
- **Full API access**: AI can build anything
- **Event system**: AI can react to anything
- **No GUI dependency**: Everything is code

## Conclusion

The question isn't "which terminal has the best features today?"

The question is "which terminal can have any feature I need tomorrow?"

With GUI-based terminals, you're limited to what the developers imagined. With WezTerm, you're limited only by what you can describe—and AI can describe a lot.

**WezTerm isn't just a terminal. It's a terminal construction kit. And in the age of AI, that's exactly what you want.**

---

## WezTerm's Superpower: Lua Scripting

Unlike most terminal emulators that only offer static configuration, WezTerm embeds a full Lua interpreter. This means you can:

1. **DEFINE CUSTOM FUNCTIONS** - Write reusable logic for complex behaviors
2. **CREATE EVENT HANDLERS** - React to terminal events (focus, resize, etc.)
3. **USE wezterm.action_callback()** - Build keybindings that execute ANY Lua code
4. **ACCESS RUNTIME STATE** - Query panes, tabs, windows, processes dynamically
5. **INTEGRATE EXTERNAL TOOLS** - Shell out to zoxide, git, or any CLI tool

This transforms configuration from "set some options" to "program your terminal."

## Key Capabilities Enabled by Lua

### Custom Functions (reusable logic):
- `is_vim()` - Detect Neovim for smart keybindings
- `get_layout_mode() / set_layout_mode()` - Track layout state per tab
- `cycle_layout_mode()` - Cycle through layout options
- `get_smart_split_direction()` - Calculate optimal split direction
- `smart_new_pane()` - Zellij-style intelligent pane creation
- `layouts.dev(), layouts.quad(), etc.` - Programmatic layout templates
- `apply_layout()` - Apply layouts by name
- `short_cwd()` - Format paths for display
- `scheme_for_cwd()` - Dynamic theming based on directory

### Event Handlers (react to terminal events):
- `wezterm.on('format-tab-title', ...)` - Custom tab title formatting
- `wezterm.on('format-window-title', ...)` - Custom window title
- `wezterm.on('update-status', ...)` - Dynamic status bar with live data

### Action Callbacks (keybindings that run Lua):
- **Cmd+T** → Spawns tab + shows zoxide picker (two actions chained)
- **Cmd+P** → Builds dynamic tab list with process info for fuzzy search
- **Cmd+K** → Vim-aware scrollback clear (passes through in Neovim)
- **Alt+N** → Calls smart_new_pane() for layout-aware splitting
- **Alt+]/[** → Cycles layout modes with toast notifications
- **Alt+Space** → Builds layout mode picker dynamically
- **Leader+Z** → Zen mode toggle (hide UI for focus)

### Key Tables (modal keybindings):
- **resize_pane** → Enter resize mode with Leader+R, use hjkl freely

### Plugins:
- **workspace_switcher** - zoxide-powered workspace switching
- **resurrect** - Session persistence (save/restore workspaces)

This level of customization is simply impossible in terminals like iTerm2, Alacritty, or Kitty. WezTerm lets you BUILD your ideal terminal workflow.

## Getting Started

1. Install WezTerm: `brew install --cask wezterm`
2. Create `~/.config/wezterm/wezterm.lua`
3. Start with a basic config
4. Ask an AI to customize it for you

The future of terminal customization is conversational. WezTerm is ready for it.

## Example: Zellij-Style Layout Modes

One of the most powerful features is implementing Zellij-style layout modes entirely in Lua:

```lua
-- Layout modes control how new panes are created
local LAYOUT_MODES = {
  'standard',        -- Follow natural splits
  'main-vertical',   -- One main left, stack right
  'main-horizontal', -- One main top, stack bottom
  'tiled',          -- Automatic tiling
}

-- Track mode per tab
local layout_mode_state = wezterm.GLOBAL

function get_layout_mode(tab_id)
  return layout_mode_state[tab_id] or 'standard'
end

function smart_new_pane(window, pane)
  local tab = window:active_tab()
  local mode = get_layout_mode(tab:tab_id())
  local panes = tab:panes()

  -- Implement different splitting logic based on mode
  if mode == 'main-vertical' then
    -- Create main pane + stacked terminals
  elseif mode == 'tiled' then
    -- Find largest pane and bisect it
  end
end
```

This feature doesn't exist in iTerm2, Alacritty, or most other terminals. In WezTerm, you just describe it to AI and it writes the code.

## AI Integration Example

Here's a real conversation that generated working code:

**User**: "I want Cmd+D to create smart splits. If the window is wide, split vertically. If it's tall, split horizontally. Also, respect a layout mode that I can cycle through with Alt+]."

**AI**: *Generates 50 lines of Lua implementing:*
- Layout mode state tracking
- Smart split direction calculation
- Keybinding with action_callback
- Mode cycling with visual feedback

**User**: *Pastes into config, reloads WezTerm*

**Result**: Works immediately.

This is the AI-native terminal workflow.

## Multi-Agent Workflows

WezTerm's CLI makes it perfect for multi-agent Claude Code workflows:

```bash
# Spawn multiple Claude sessions in BSP layout
for task in "research" "implement" "test"; do
  NEW_PANE=$(wezterm cli split-pane)
  printf 'claude "$(cat /tmp/prompt-%s.md)"\n' "$task" | wezterm cli send-text --pane-id "$NEW_PANE"
done
```

See the BSP layouts gist for complete multi-session coordination examples.

## Links

- [WezTerm Documentation](https://wezfurlong.org/wezterm/)
- [Example Config](https://gist.github.com/johnlindquist/346e18fd6875ae4207a9b69c62071e9a)
- [BSP Layouts for Claude Code](https://gist.github.com/johnlindquist/9b06a09125b03c59de53a397bbdf45dd)

---

*This gist includes a complete WezTerm configuration with over 2000 lines of Lua implementing features like Zellij-style layouts, smart splits, fuzzy navigation, workspace management, and more. The full config demonstrates what's possible when you have a fully programmable terminal.*
