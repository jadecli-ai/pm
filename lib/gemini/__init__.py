"""Gemini tool library for Claude Code agent integration."""

from .multimodal import GeminiMultimodal, MULTIMODAL_TOOLS
from .code_execution import GeminiCodeExecutor, CODE_EXEC_TOOLS
from .function_calling import GeminiFunctionComposer, FUNCTION_TOOLS
from .caching import GeminiCachedResearcher, CACHING_TOOLS
from .structured_output import GeminiStructuredJSON, STRUCTURED_TOOLS
from .embeddings import GeminiEmbeddings, EMBEDDING_TOOLS

# Aggregate all tools
ALL_GEMINI_TOOLS = (
    MULTIMODAL_TOOLS +
    CODE_EXEC_TOOLS +
    FUNCTION_TOOLS +
    CACHING_TOOLS +
    STRUCTURED_TOOLS +
    EMBEDDING_TOOLS
)

__all__ = [
    "GeminiMultimodal",
    "GeminiCodeExecutor",
    "GeminiFunctionComposer",
    "GeminiCachedResearcher",
    "GeminiStructuredJSON",
    "GeminiEmbeddings",
    "ALL_GEMINI_TOOLS",
]
