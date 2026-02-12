---
source: https://zellij.dev/documentation/layouts
fetched: 2026-02-11
type: documentation
project: Zellij
---

# Zellij User Guide: Layouts Documentation

## Overview
The Layouts section of the Zellij User Guide explains how to define pane and tab arrangements using configuration files. As stated in the documentation, "Layouts are text files that define an arrangement of Zellij panes and tabs."

## Key Concepts

**Layout Format**: The system uses KDL (KDL Document Language) as its configuration language for defining layouts.

**Basic Example**: A sample configuration demonstrates the structure:
```
layout {
    pane
    pane split_direction="vertical" {
        pane
        pane command="htop"
    }
}
```

## Applying Layouts

Users can implement layouts through multiple methods:

1. **At startup**: `zellij --layout /path/to/layout_file.kdl`
2. **Via configuration file settings**
3. **Within active sessions**: The same command creates new tabs rather than replacing the current session
4. **Remote URLs**: "zellij --layout https://example.com/layout_file.kdl"

**Security Note**: Remote layouts have commands suspended behind a "Waiting to run <command>" prompt, requiring user approval before execution.

## Default Behavior

By default, Zellij searches for `default.kdl` in the `config/layouts` directory. If unavailable, the application launches with a single pane and tab. Layouts stored in the default directory can be referenced by name alone.

## Additional Resources

The guide references related documentation on creating layouts and configuration options for comprehensive setup details.
