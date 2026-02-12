"""Agent SDK tool definitions for PM System.

Register these tools with the Agent SDK for programmatic calling.

Usage:
    from anthropic import Anthropic
    from lib.agent_tools import PM_TOOLS, execute_tool

    # In tool_use response handling:
    result = execute_tool(tool_name, tool_input)
"""

from typing import Any
from .tools import get_tools

# Tool definitions for Agent SDK (Claude API format)
PM_TOOLS = [
    # Level 0: Atomic
    {
        "name": "pm_l0_test",
        "description": "Run PM system tests. Returns pass/fail summary. ~50 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "pm_l0_arch",
        "description": "Generate architecture docs. Returns generation status. ~30 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "pm_l0_lint",
        "description": "Lint single file frontmatter. Returns ✓ or ✗. ~5 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file": {
                    "type": "string",
                    "description": "Path to file to lint"
                }
            },
            "required": ["file"]
        }
    },
    {
        "name": "pm_l0_hash",
        "description": "Get file hash (16 chars). For change detection. ~20 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file": {
                    "type": "string",
                    "description": "Path to file"
                }
            },
            "required": ["file"]
        }
    },
    {
        "name": "pm_l0_commit_check",
        "description": "Validate last commit is conventional. ~5 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },

    # Level 1: Composed
    {
        "name": "pm_l1_index",
        "description": "Check Merkle index freshness, regenerate if stale. ~30 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "pm_l1_validate",
        "description": "Run tests + check index. Composed L0 ops. ~60 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "pm_l1_arch_check",
        "description": "Generate architecture + check for changes. ~40 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },

    # Level 2: Workflow
    {
        "name": "pm_l2_pr_open",
        "description": "Full PR open checks: tests, index, arch, commits, lint. ~150 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "pm_l2_pr_merge",
        "description": "PR merge automation: arch update + commit. ~100 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },

    # Level 3: Pipeline
    {
        "name": "pm_l3_ci",
        "description": "Full CI pipeline. Runs all PR checks. ~200 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "pm_l3_cd",
        "description": "Full CD pipeline. CI + merge automation. ~300 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
]


def execute_tool(name: str, input_data: dict[str, Any] = None) -> dict[str, Any]:
    """Execute a PM tool by name.

    Args:
        name: Tool name (e.g., "pm_l0_test")
        input_data: Tool input parameters

    Returns:
        Dict with success, output, level, tokens
    """
    input_data = input_data or {}
    tools = get_tools()

    # Map tool names to methods
    tool_map = {
        # Level 0
        "pm_l0_test": lambda: tools.l0_test(),
        "pm_l0_arch": lambda: tools.l0_arch(),
        "pm_l0_lint": lambda: tools.l0_lint(input_data.get("file", "")),
        "pm_l0_hash": lambda: tools.l0_hash(input_data.get("file", "")),
        "pm_l0_commit_check": lambda: tools.l0_commit_check(),

        # Level 1
        "pm_l1_index": lambda: tools.l1_index(),
        "pm_l1_validate": lambda: tools.l1_validate(),
        "pm_l1_arch_check": lambda: tools.l1_arch_check(),

        # Level 2
        "pm_l2_pr_open": lambda: tools.l2_pr_open(),
        "pm_l2_pr_merge": lambda: tools.l2_pr_merge(),

        # Level 3
        "pm_l3_ci": lambda: tools.l3_ci(),
        "pm_l3_cd": lambda: tools.l3_cd(),
    }

    if name not in tool_map:
        return {"success": False, "output": f"Unknown tool: {name}", "level": -1, "tokens": 5}

    result = tool_map[name]()
    return {
        "success": result.success,
        "output": result.output,
        "level": result.level,
        "tokens": result.tokens_approx
    }


# Convenience for Agent SDK integration
def get_tool_definitions() -> list[dict]:
    """Get all tool definitions for Claude API."""
    return PM_TOOLS


def get_tool_by_level(level: int) -> list[dict]:
    """Get tools at a specific level."""
    prefix = f"pm_l{level}_"
    return [t for t in PM_TOOLS if t["name"].startswith(prefix)]
