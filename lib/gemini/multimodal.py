"""Gemini multimodal analysis tools."""
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    output: str
    tokens_used: int
    model: str
    latency_ms: float
    error: Optional[str] = None


class GeminiMultimodal:
    """Gemini multimodal analysis wrapper."""

    def __init__(self):
        if not GENAI_AVAILABLE:
            raise ImportError("google-genai not installed. Run: pip install google-genai")

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"  # Latest flash model (2026)

    def analyze_image(self, image_path: str, query: str) -> ToolResult:
        """Analyze image with Gemini vision.

        Args:
            image_path: Path to image file
            query: Analysis question

        Returns:
            ToolResult with analysis
        """
        start = time.time()

        try:
            # Read image file
            image_file = Path(image_path)
            if not image_file.exists():
                return ToolResult(
                    success=False,
                    output="",
                    tokens_used=0,
                    model=self.model_name,
                    latency_ms=0,
                    error=f"Image file not found: {image_path}"
                )

            # Upload file
            uploaded_file = self.client.files.upload(path=image_path)

            # Generate content with image
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    query,
                    uploaded_file
                ]
            )

            latency = (time.time() - start) * 1000

            # Extract tokens (approximate)
            tokens_used = len(response.text.split()) + 100  # Rough estimate + image tokens

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

    def analyze_video(self, video_path: str, query: str) -> ToolResult:
        """Analyze video with Gemini.

        Args:
            video_path: Path to video file
            query: Analysis question

        Returns:
            ToolResult with analysis
        """
        start = time.time()

        try:
            # Upload video file
            uploaded_file = self.client.files.upload(path=video_path)

            # Wait for video processing
            while uploaded_file.state == "PROCESSING":
                time.sleep(1)
                uploaded_file = self.client.files.get(name=uploaded_file.name)

            if uploaded_file.state == "FAILED":
                raise ValueError(f"Video processing failed: {uploaded_file.error}")

            # Generate content with video
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[query, uploaded_file]
            )

            latency = (time.time() - start) * 1000
            tokens_used = len(response.text.split()) + 500  # Video tokens

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

    def extract_document(self, doc_path: str, query: str = "Extract all text") -> ToolResult:
        """Extract text from document (PDF, image with OCR).

        Args:
            doc_path: Path to document file
            query: Extraction instructions

        Returns:
            ToolResult with extracted text
        """
        start = time.time()

        try:
            # Upload document
            uploaded_file = self.client.files.upload(path=doc_path)

            # Extract content
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[query, uploaded_file]
            )

            latency = (time.time() - start) * 1000
            tokens_used = len(response.text.split()) + 200

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


# Agent SDK compatible tool definitions
MULTIMODAL_TOOLS = [
    {
        "name": "gemini_analyze_image",
        "description": "Analyze image using Gemini vision. Returns description, insights. ~100 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to image file"
                },
                "query": {
                    "type": "string",
                    "description": "Analysis question or instructions"
                }
            },
            "required": ["image_path", "query"]
        }
    },
    {
        "name": "gemini_analyze_video",
        "description": "Analyze video content using Gemini. Returns summary, insights. ~500 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "video_path": {
                    "type": "string",
                    "description": "Path to video file"
                },
                "query": {
                    "type": "string",
                    "description": "Analysis question"
                }
            },
            "required": ["video_path", "query"]
        }
    },
    {
        "name": "gemini_extract_document",
        "description": "Extract text from PDF or image with OCR. ~200 tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "doc_path": {
                    "type": "string",
                    "description": "Path to document file"
                },
                "query": {
                    "type": "string",
                    "description": "Extraction instructions (default: extract all text)"
                }
            },
            "required": ["doc_path"]
        }
    }
]


# Execution functions for agent registry
def gemini_analyze_image(image_path: str, query: str) -> dict:
    """Execute gemini_analyze_image tool."""
    tool = GeminiMultimodal()
    result = tool.analyze_image(image_path, query)
    return {
        "success": result.success,
        "output": result.output,
        "tokens": result.tokens_used,
        "latency_ms": result.latency_ms,
        "error": result.error
    }


def gemini_analyze_video(video_path: str, query: str) -> dict:
    """Execute gemini_analyze_video tool."""
    tool = GeminiMultimodal()
    result = tool.analyze_video(video_path, query)
    return {
        "success": result.success,
        "output": result.output,
        "tokens": result.tokens_used,
        "latency_ms": result.latency_ms,
        "error": result.error
    }


def gemini_extract_document(doc_path: str, query: str = "Extract all text") -> dict:
    """Execute gemini_extract_document tool."""
    tool = GeminiMultimodal()
    result = tool.extract_document(doc_path, query)
    return {
        "success": result.success,
        "output": result.output,
        "tokens": result.tokens_used,
        "latency_ms": result.latency_ms,
        "error": result.error
    }
