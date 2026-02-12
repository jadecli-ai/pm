"""Gemini embeddings tools."""
# Stub implementation

EMBEDDING_TOOLS = [
    {
        "name": "gemini_generate_embeddings",
        "description": "Generate embeddings for semantic search. ~50 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "texts": {"type": "array", "items": {"type": "string"}},
                "dimensions": {"type": "integer", "default": 768}
            },
            "required": ["texts"]
        }
    }
]


def gemini_generate_embeddings(texts: list, dimensions: int = 768) -> dict:
    """Stub: Generate embeddings."""
    return {"success": False, "output": "Not implemented yet", "error": "Stub"}


class GeminiEmbeddings:
    """Stub for embeddings."""
    pass
