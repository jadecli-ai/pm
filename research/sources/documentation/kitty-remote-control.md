---
source: https://sw.kovidgoyal.net/kitty/remote-control/
fetched: 2026-02-11
type: documentation
project: Kitty
---

# Kitty Remote Control Documentation Summary

## Overview
Kitty provides comprehensive remote control capabilities allowing scripts and shell commands to control the terminal programmatically. This enables automation of window/tab management, text input, and terminal configuration.

## Key Capabilities

**Basic Control Methods:**
- Commands via `kitten @` when running inside kitty windows
- Socket-based control for external scripts using `--listen-on unix:/path/socket`
- Interactive kitty shell accessible via `Ctrl+Shift+Escape`

## Core Commands

The documentation outlines numerous remote control commands including:

- **Window Management:** `launch`, `close-window`, `focus-window`, `resize-window`
- **Tab Operations:** `close-tab`, `focus-tab`, `set-tab-title`, `detach-tab`
- **Text Control:** `send-text`, `send-key`, `get-text`
- **Configuration:** `set-colors`, `set-font-size`, `load-config`
- **Querying:** `ls` (lists windows/tabs in JSON format)

## Authentication & Security

**Permission Models:**
1. Enable via `allow_remote_control=yes` configuration
2. Password-based access with `remote_control_password` for granular permissions
3. Custom Python authorization scripts via `~/.config/kitty/my_rc_auth.py`
4. Encrypted communication support for remote connections

As noted: "For password based authentication to work over SSH, you must pass the [`KITTY_PUBLIC_KEY`](../glossary/#envvar-KITTY_PUBLIC_KEY) environment variable to the remote host."

## Matching Windows & Tabs

Sophisticated selection using expressions like `title:"My window" or id:43` with Boolean operators. Supports matching by title, ID, process ID, working directory, command line, environment variables, and state.

## Practical Examples

```
kitten @ launch --title Output --keep-focus cat
kitten @ send-text --match 'title:^Output' "Hello, World"
kitten @ ls  # JSON output of all windows/tabs
```

The documentation emphasizes that remote control works seamlessly over SSH and enables powerful automation for terminal workflows.
