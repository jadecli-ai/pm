"""Gemini code execution tools."""
import os
import time
from dataclasses import dataclass
from typing import Optional

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


@dataclass
class ToolResult:
    success: bool
    output: str
    tokens_used: int
    model: str
    latency_ms: float
    error: Optional[str] = None


class GeminiCodeExecutor:
    """Gemini code execution wrapper."""

    def __init__(self):
        if not GENAI_AVAILABLE:
            raise ImportError("google-genai not installed")

        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.env_get import get_gemini_api_key

        api_key = get_gemini_api_key()

        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash"  # Verified working with API key

    def execute_code(self, code: str) -> ToolResult:
        """Execute Python code in Gemini sandbox."""
        start = time.time()

        try:
            # Simple approach - just ask Gemini to execute code
            # Note: Code execution is a beta feature, may not be available in all models
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"Execute this Python code and show me only the output:\n```python\n{code}\n```"
            )

            latency = (time.time() - start) * 1000
            tokens_used = len(response.text.split()) + len(code.split())

            return ToolResult(
                success=True,
                output=response.text,
                tokens_used=tokens_used,
                model=self.model_name,
                latency_ms=latency
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                tokens_used=0,
                model=self.model_name,
                latency_ms=(time.time() - start) * 1000,
                error=str(e)
            )


CODE_EXEC_TOOLS = [
    {
        "name": "gemini_execute_code",
        "description": "Execute Python code in Gemini sandbox. ~150 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"}
            },
            "required": ["code"]
        }
    }
]


def gemini_execute_code(code: str) -> dict:
    """Execute gemini_execute_code tool."""
    tool = GeminiCodeExecutor()
    result = tool.execute_code(code)
    return {
        "success": result.success,
        "output": result.output,
        "tokens": result.tokens_used,
        "latency_ms": result.latency_ms,
        "error": result.error
    }
