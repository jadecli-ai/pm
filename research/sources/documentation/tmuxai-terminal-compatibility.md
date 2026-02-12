---
source: https://tmuxai.dev/terminal-compatibility
fetched: 2026-02-11
type: documentation
project: tmuxai
---

# Terminal Compatibility Matrix: Complete Documentation

## Overview
This page provides a comprehensive feature comparison across 9 terminal emulators (Alacritty, iTerm2, Kitty, WezTerm, Windows Terminal, Ghostty, Hyper, Tabby, and Wave Terminal) evaluating 12 key features.

## Core Features Evaluated

**Graphics & Colors:**
- TrueColor (24-bit RGB support) - all terminals supported
- Sixel Graphics protocol - supported by WezTerm and Windows Terminal
- Kitty Graphics Protocol - supported by Kitty, WezTerm, and Ghostty
- iTerm2 Inline Images - supported by iTerm2 and WezTerm

**Text & Fonts:**
- Font Ligatures - supported by most except Alacritty (intentional omission)
- Full Unicode support - universally supported
- Bold/Italic/Underline formatting - universally supported

**Integration & Clipboard:**
- "OSC 52 Clipboard" enables "clipboard sync in remote sessions. Essential for SSH workflows"
- Clickable Hyperlinks (OSC 8) - widely supported
- Desktop Notifications - supported by most terminals

**Performance:**
- GPU Acceleration - supported by most native terminals
- Low Memory Usage - Alacritty leads at ~30MB

## Best Terminal Recommendations

- **Image Previews:** WezTerm, Kitty, Ghostty
- **Remote SSH Work:** Alacritty, Kitty, WezTerm, iTerm2
- **Code Editing:** Kitty, WezTerm, iTerm2, Ghostty
- **Low Resource Usage:** Alacritty, Ghostty, Kitty
- **Cross-Platform:** WezTerm, Alacritty, Tabby, Hyper

## Terminal Profiles Summary

Each terminal includes strengths and gaps. For example, Alacritty offers "fastest terminal emulator" performance with minimal resource usage but lacks graphics protocols. WezTerm "supports ALL image protocols" with Lua scripting but requires higher memory allocation.

**Last Updated:** December 2025
