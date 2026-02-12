"""Kimi thinking mode tools."""
# Stub implementation for thinking mode (temp=1.0)

THINKING_TOOLS = [
    {
        "name": "kimi_think_deeply",
        "description": "Extended reasoning with step-by-step thinking (temp=1.0). ~300 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "problem": {"type": "string", "description": "Complex problem to solve"}
            },
            "required": ["problem"]
        }
    }
]


def kimi_think_deeply(problem: str) -> dict:
    """Stub: Thinking mode."""
    return {
        "success": False,
        "output": "Not implemented yet - install kimi-agent-sdk",
        "tokens": 0,
        "latency_ms": 0,
        "error": "Stub"
    }


class KimiThinkingMode:
    """Stub for thinking mode."""
    pass
