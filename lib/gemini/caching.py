"""Gemini context caching tools."""
# Stub implementation

CACHING_TOOLS = [
    {
        "name": "gemini_cache_context",
        "description": "Cache large context for repeated queries. ~50 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "ttl_hours": {"type": "integer", "default": 1}
            },
            "required": ["content"]
        }
    }
]


def gemini_cache_context(content: str, ttl_hours: int = 1) -> dict:
    """Stub: Cache context."""
    return {"success": False, "output": "Not implemented yet", "error": "Stub"}


class GeminiCachedResearcher:
    """Stub for cached researcher."""
    pass
