"""Kimi instant mode tools."""
# Stub implementation for instant mode (temp=0.6)

INSTANT_TOOLS = [
    {
        "name": "kimi_quick_answer",
        "description": "Fast response without extended reasoning (temp=0.6). ~50 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Quick question"}
            },
            "required": ["query"]
        }
    }
]


def kimi_quick_answer(query: str) -> dict:
    """Stub: Instant mode."""
    return {
        "success": False,
        "output": "Not implemented yet - install kimi-agent-sdk",
        "tokens": 0,
        "latency_ms": 0,
        "error": "Stub"
    }


class KimiInstantMode:
    """Stub for instant mode."""
    pass
