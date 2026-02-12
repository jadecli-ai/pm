"""Gemini function calling tools."""
# Stub implementation - expand as needed

FUNCTION_TOOLS = [
    {
        "name": "gemini_call_parallel_functions",
        "description": "Call multiple functions in parallel. ~200 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "functions": {"type": "array", "items": {"type": "object"}}
            },
            "required": ["functions"]
        }
    }
]


def gemini_call_parallel_functions(functions: list) -> dict:
    """Stub: Parallel function calling."""
    return {"success": False, "output": "Not implemented yet", "error": "Stub"}


class GeminiFunctionComposer:
    """Stub for function composer."""
    pass
