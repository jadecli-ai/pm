"""Kimi terminal expert tools."""
# Stub implementation for terminal expertise

TERMINAL_TOOLS = [
    {
        "name": "kimi_generate_commands",
        "description": "Generate shell commands for task. ~100 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_description": {"type": "string"},
                "shell": {"type": "string", "enum": ["bash", "zsh", "fish"], "default": "bash"}
            },
            "required": ["task_description"]
        }
    }
]


def kimi_generate_commands(task_description: str, shell: str = "bash") -> dict:
    """Stub: Terminal commands."""
    return {
        "success": False,
        "output": "Not implemented yet - install kimi-agent-sdk",
        "tokens": 0,
        "latency_ms": 0,
        "error": "Stub"
    }


class KimiTerminalExpert:
    """Stub for terminal expert."""
    pass
