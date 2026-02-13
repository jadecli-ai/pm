# pm/lib/neon_docs/embedder.py
"""Local embeddings via Ollama API with retry.

Uses httpx for async HTTP and tenacity for retry with exponential backoff.
"""

from __future__ import annotations

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import get_settings
from .exceptions import EmbeddingError, OllamaConnectionError, OllamaModelError
from .log import get_logger

logger = get_logger("embedder")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(OllamaConnectionError),
    reraise=True,
)
async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts via Ollama."""
    settings = get_settings()
    embeddings: list[list[float]] = []

    # nomic-embed-text has 8192 token context; truncate aggressively for
    # safety since JSON/URL content can have ~1 token per char
    max_chars = 7500

    async with httpx.AsyncClient(base_url=settings.ollama_host, timeout=120.0) as client:
        for text in texts:
            if len(text) > max_chars:
                logger.warning("Truncating text from %d to %d chars for embedding", len(text), max_chars)
                text = text[:max_chars]
            try:
                resp = await client.post(
                    "/api/embed",
                    json={"model": settings.ollama_model, "input": text},
                )
            except httpx.ConnectError as e:
                raise OllamaConnectionError(f"Cannot connect to Ollama at {settings.ollama_host}", cause=e) from e
            except httpx.TimeoutException as e:
                raise OllamaConnectionError("Ollama request timed out", cause=e) from e

            if resp.status_code == 404:
                raise OllamaModelError(
                    f"Model '{settings.ollama_model}' not found. Run: ollama pull {settings.ollama_model}"
                )

            if resp.status_code != 200:
                raise EmbeddingError(f"Ollama returned {resp.status_code}: {resp.text[:200]}")

            data = resp.json()
            embedding = data["embeddings"][0]

            if len(embedding) != settings.embedding_dimensions:
                raise EmbeddingError(f"Expected {settings.embedding_dimensions} dims, got {len(embedding)}")

            embeddings.append(embedding)

    logger.info("Embedded %d texts (%d dims)", len(texts), settings.embedding_dimensions)
    return embeddings


async def embed_single(text: str) -> list[float]:
    """Embed a single text string."""
    results = await embed_texts([text])
    return results[0]
