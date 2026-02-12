"""Kimi tool library for Claude Code agent integration."""

from .long_context import KimiLongContext, LONG_CONTEXT_TOOLS
from .thinking_mode import KimiThinkingMode, THINKING_TOOLS
from .instant_mode import KimiInstantMode, INSTANT_TOOLS
from .swarm import KimiSwarmCoordinator, SWARM_TOOLS
from .vibe_coding import KimiVibeCoder, VIBE_TOOLS
from .terminal import KimiTerminalExpert, TERMINAL_TOOLS

# Aggregate all tools
ALL_KIMI_TOOLS = (
    LONG_CONTEXT_TOOLS +
    THINKING_TOOLS +
    INSTANT_TOOLS +
    SWARM_TOOLS +
    VIBE_TOOLS +
    TERMINAL_TOOLS
)

__all__ = [
    "KimiLongContext",
    "KimiThinkingMode",
    "KimiInstantMode",
    "KimiSwarmCoordinator",
    "KimiVibeCoder",
    "KimiTerminalExpert",
    "ALL_KIMI_TOOLS",
]
