---
source: https://sw.kovidgoyal.net/kitty/overview/#sessions
fetched: 2026-02-11
type: documentation
project: Kitty
---

# Kitty Terminal Emulator - Overview Documentation

## Core Design Philosophy

Kitty is engineered for power keyboard users, emphasizing keyboard-driven controls throughout the interface. The architecture combines C for performance-critical components, Python for UI flexibility, and Go for command-line tools. Rather than relying on complex UI toolkits, it uses OpenGL for rendering. The project prioritizes simplicity, modularity, and hackability.

The terminal supports modern features including Unicode, true color support, multiple font weights, and text formatting. It extends standard escape codes to enable features like colored and styled underlines.

## Window Organization Structure

Kitty employs a three-tier organizational hierarchy:

1. **OS Windows** - Top-level containers
2. **Tabs** - Groups within OS windows
3. **Kitty Windows** - Individual panes arranged within tabs using layouts

### Available Layouts

Seven layout options exist:
- **Stack**: Single maximized window visible
- **Tall**: Full-height window(s) on left, others stacked right
- **Fat**: Full-width window(s) on top, others side-by-side below
- **Grid**: All windows in grid arrangement
- **Splits**: Custom patterns via horizontal/vertical divisions
- **Horizontal**: Side-by-side arrangement
- **Vertical**: Stacked arrangement

## Keyboard Navigation

The terminal provides extensive keyboard shortcuts for common operations:

**Scrolling**: Navigate history with `ctrl+shift+up/down/page_up/page_down/home/end`

**Tab Management**: Create (`ctrl+shift+t`), close (`ctrl+shift+q`), navigate (`ctrl+shift+left/right`)

**Window Operations**: Create (`ctrl+shift+enter`), close (`ctrl+shift+w`), resize (`ctrl+shift+r`)

## Configuration System

Users configure kitty through a single `kitty.conf` file, editable via `ctrl+shift+f2`. This approach facilitates version control and reproducibility.

## Extensibility Framework

Kitty supports scripting through "kittens" - small terminal programs enabling feature additions. Built-in kittens include image viewing, file diffing, Unicode input, and theme management.

Remote control capabilities allow manipulation of kitty from shell prompts, including over SSH connections, enabling dynamic window/tab management and text operations.

## Advanced Features

**Shell Integration**: Supports zsh, fish, and bash integration for prompt jumping and command output viewing.

**Scrollback Buffer**: Interactive history exploration via pager (`ctrl+shift+h`), with preserved formatting and color.

**Mouse Capabilities**: URL clicking, word/line selection, column selection with modifiers, clipboard integration.

**Multiple Copy Buffers**: Users can define arbitrary named buffers beyond system clipboard.

**Session Management**: Create saved session configurations specifying layouts, working directories, and startup programs.

**Marks**: Regex-based text highlighting in scrollback output.

**Font Control**: Granular font selection per style (regular, bold, italic) and Unicode ranges.
