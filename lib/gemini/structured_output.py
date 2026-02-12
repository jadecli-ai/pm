"""Gemini structured output tools."""
# Stub implementation

STRUCTURED_TOOLS = [
    {
        "name": "gemini_extract_json",
        "description": "Extract structured JSON with schema validation. ~100 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "schema": {"type": "object"}
            },
            "required": ["text", "schema"]
        }
    }
]


def gemini_extract_json(text: str, schema: dict) -> dict:
    """Stub: Extract JSON."""
    return {"success": False, "output": "Not implemented yet", "error": "Stub"}


class GeminiStructuredJSON:
    """Stub for structured JSON."""
    pass
