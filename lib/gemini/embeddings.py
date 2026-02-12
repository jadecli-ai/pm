"""Gemini text embeddings tools."""
import time
from dataclasses import dataclass
from typing import Optional, List

try:
    from google import genai
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
    embeddings: Optional[List[List[float]]] = None  # For embedding results


class GeminiEmbeddings:
    """Gemini text embeddings wrapper."""

    def __init__(self):
        if not GENAI_AVAILABLE:
            raise ImportError("google-genai not installed. Run: pip install google-genai")

        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.env_get import get_gemini_api_key

        api_key = get_gemini_api_key()

        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-embedding-001"  # Official Gemini embedding model

    def embed_text(self, text: str) -> ToolResult:
        """Generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            ToolResult with embedding vector (768 dimensions)
        """
        start = time.time()

        try:
            # Generate embedding
            response = self.client.models.embed_content(
                model=self.model_name,
                contents=text
            )

            latency = (time.time() - start) * 1000

            # Extract embedding vector
            embedding = response.embeddings[0].values

            # Tokens used (approximate)
            tokens_used = len(text.split()) + 10  # Rough estimate

            return ToolResult(
                success=True,
                output=f"Generated {len(embedding)}-dimensional embedding vector",
                tokens_used=tokens_used,
                model=self.model_name,
                latency_ms=latency,
                embeddings=[embedding]
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

    def embed_batch(self, texts: List[str]) -> ToolResult:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            ToolResult with list of embedding vectors
        """
        start = time.time()

        try:
            all_embeddings = []
            total_tokens = 0

            # Process each text (API doesn't support true batch yet)
            for text in texts:
                response = self.client.models.embed_content(
                    model=self.model_name,
                    contents=text
                )
                embedding = response.embeddings[0].values
                all_embeddings.append(embedding)
                total_tokens += len(text.split()) + 10

            latency = (time.time() - start) * 1000

            return ToolResult(
                success=True,
                output=f"Generated {len(all_embeddings)} embeddings (each {len(all_embeddings[0])}-dim)",
                tokens_used=total_tokens,
                model=self.model_name,
                latency_ms=latency,
                embeddings=all_embeddings
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

    def similarity_search(self, query: str, documents: List[str], top_k: int = 3) -> ToolResult:
        """Find most similar documents to query using cosine similarity.

        Args:
            query: Search query
            documents: List of documents to search
            top_k: Number of top results to return

        Returns:
            ToolResult with ranked document indices and scores
        """
        start = time.time()

        try:
            import numpy as np

            # Embed query
            query_response = self.client.models.embed_content(
                model=self.model_name,
                contents=query
            )
            query_embedding = np.array(query_response.embeddings[0].values)

            # Embed all documents
            doc_embeddings = []
            for doc in documents:
                doc_response = self.client.models.embed_content(
                    model=self.model_name,
                    contents=doc
                )
                doc_embeddings.append(np.array(doc_response.embeddings[0].values))

            # Calculate cosine similarities
            similarities = []
            for doc_emb in doc_embeddings:
                # Cosine similarity = dot product of normalized vectors
                cos_sim = np.dot(query_embedding, doc_emb) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_emb)
                )
                similarities.append(float(cos_sim))

            # Get top-k results
            top_indices = np.argsort(similarities)[::-1][:top_k]
            top_scores = [similarities[i] for i in top_indices]

            latency = (time.time() - start) * 1000
            tokens_used = len(query.split()) + sum(len(d.split()) for d in documents) + 20

            results = "\n".join([
                f"Rank {i+1}: Doc #{idx} (score: {score:.4f})"
                for i, (idx, score) in enumerate(zip(top_indices, top_scores))
            ])

            return ToolResult(
                success=True,
                output=f"Top {top_k} matches:\n{results}",
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
EMBEDDING_TOOLS = [
    {
        "name": "gemini_embed_text",
        "description": "Generate 768-dimensional embedding for text. ~50 tokens, ~200ms.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to embed"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "gemini_embed_batch",
        "description": "Generate embeddings for multiple texts. ~50 tokens each, ~200ms per text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "texts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of texts to embed"
                }
            },
            "required": ["texts"]
        }
    },
    {
        "name": "gemini_similarity_search",
        "description": "Find most similar documents using embeddings. Returns ranked results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "documents": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Documents to search"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of top results (default: 3)"
                }
            },
            "required": ["query", "documents"]
        }
    }
]


# Execution functions for agent registry
def gemini_embed_text(text: str) -> dict:
    """Execute gemini_embed_text tool."""
    tool = GeminiEmbeddings()
    result = tool.embed_text(text)
    return {
        "success": result.success,
        "output": result.output,
        "tokens": result.tokens_used,
        "latency_ms": result.latency_ms,
        "error": result.error,
        "embedding": result.embeddings[0] if result.embeddings else None
    }


def gemini_embed_batch(texts: List[str]) -> dict:
    """Execute gemini_embed_batch tool."""
    tool = GeminiEmbeddings()
    result = tool.embed_batch(texts)
    return {
        "success": result.success,
        "output": result.output,
        "tokens": result.tokens_used,
        "latency_ms": result.latency_ms,
        "error": result.error,
        "embeddings": result.embeddings
    }


def gemini_similarity_search(query: str, documents: List[str], top_k: int = 3) -> dict:
    """Execute gemini_similarity_search tool."""
    tool = GeminiEmbeddings()
    result = tool.similarity_search(query, documents, top_k)
    return {
        "success": result.success,
        "output": result.output,
        "tokens": result.tokens_used,
        "latency_ms": result.latency_ms,
        "error": result.error
    }
