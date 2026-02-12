"""Kimi long context analysis tools."""
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

try:
    # Kimi agent SDK (when installed)
    # from kimi_agent_sdk import Session, prompt
    KIMI_AVAILABLE = False  # Set to True when kimi-agent-sdk installed
except ImportError:
    KIMI_AVAILABLE = False


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    output: str
    tokens_used: int
    model: str
    latency_ms: float
    error: Optional[str] = None


class KimiLongContext:
    """Kimi 256K context window wrapper."""

    def __init__(self):
        api_key = os.getenv("KIMI_API_KEY_v3") or os.getenv("KIMI_API_KEY")
        if not api_key:
            raise ValueError("KIMI_API_KEY_v3 or KIMI_API_KEY not set")

        self.api_key = api_key
        self.model_name = "kimi-k2.5"

    def load_codebase(self, files: List[str], query: str) -> ToolResult:
        """Load entire codebase into 256K context and analyze.

        Args:
            files: List of file paths to load
            query: Analysis question

        Returns:
            ToolResult with analysis
        """
        start = time.time()

        try:
            # Load all files
            content_parts = []
            total_lines = 0

            for file_path in files:
                path = Path(file_path)
                if path.exists() and path.is_file():
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            lines = content.count('\n')
                            total_lines += lines
                            content_parts.append(f"## File: {file_path}\n\n```\n{content}\n```\n")
                    except Exception as e:
                        content_parts.append(f"## File: {file_path}\n\nError reading: {e}\n")

            # Combine all content
            full_context = "\n\n".join(content_parts)

            # For now, return stub (will use Kimi API when SDK installed)
            if not KIMI_AVAILABLE:
                output = f"Loaded {len(files)} files ({total_lines} total lines) into context.\n\n"
                output += f"Query: {query}\n\n"
                output += "[STUB] Kimi SDK not installed. Install with: pip install kimi-agent-sdk\n"
                output += f"Context size: ~{len(full_context.split())} tokens\n"

                latency = (time.time() - start) * 1000

                return ToolResult(
                    success=True,
                    output=output,
                    tokens_used=len(full_context.split()),
                    model=self.model_name,
                    latency_ms=latency
                )

            # TODO: When SDK installed, use:
            # async with await Session.create() as session:
            #     response = await session.prompt(f"{full_context}\n\n{query}")
            #     return ToolResult(...)

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                tokens_used=0,
                model=self.model_name,
                latency_ms=(time.time() - start) * 1000,
                error=str(e)
            )


LONG_CONTEXT_TOOLS = [
    {
        "name": "kimi_load_codebase",
        "description": "Load entire codebase into Kimi's 256K context. ~5000+ tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of file paths to load"
                },
                "query": {
                    "type": "string",
                    "description": "Analysis question or task"
                }
            },
            "required": ["files", "query"]
        }
    }
]


def kimi_load_codebase(files: List[str], query: str) -> dict:
    """Execute kimi_load_codebase tool."""
    tool = KimiLongContext()
    result = tool.load_codebase(files, query)
    return {
        "success": result.success,
        "output": result.output,
        "tokens": result.tokens_used,
        "latency_ms": result.latency_ms,
        "error": result.error
    }
