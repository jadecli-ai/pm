# pm/lib/neon_docs/chunker.py
"""Text chunking with accurate token counting.

Splits on paragraph -> sentence -> word boundaries.
Uses tiktoken for accurate token counting.
"""

from __future__ import annotations

from .config import get_settings
from .tokenizer import count_tokens


def chunk_text(
    text: str,
    max_tokens: int | None = None,
    overlap_tokens: int | None = None,
) -> list[str]:
    """Split text into overlapping chunks."""
    settings = get_settings()
    max_tokens = max_tokens or settings.chunk_max_tokens
    overlap_tokens = overlap_tokens or settings.chunk_overlap_tokens

    if count_tokens(text) <= max_tokens:
        return [text]

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        if para_tokens > max_tokens:
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts = _get_overlap_parts(current_parts, overlap_tokens)
                current_tokens = sum(count_tokens(p) for p in current_parts)

            sentences = _split_sentences(para)
            for sent in sentences:
                sent_tokens = count_tokens(sent)
                if current_tokens + sent_tokens > max_tokens and current_parts:
                    chunks.append(" ".join(current_parts))
                    current_parts = _get_overlap_parts(current_parts, overlap_tokens)
                    current_tokens = sum(count_tokens(p) for p in current_parts)
                current_parts.append(sent)
                current_tokens += sent_tokens
            continue

        if current_tokens + para_tokens > max_tokens and current_parts:
            chunks.append("\n\n".join(current_parts))
            current_parts = _get_overlap_parts(current_parts, overlap_tokens)
            current_tokens = sum(count_tokens(p) for p in current_parts)

        current_parts.append(para)
        current_tokens += para_tokens

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return chunks


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def _get_overlap_parts(parts: list[str], overlap_tokens: int) -> list[str]:
    """Get trailing parts that fit within overlap_tokens."""
    if not parts or overlap_tokens <= 0:
        return []
    result: list[str] = []
    tokens = 0
    for part in reversed(parts):
        t = count_tokens(part)
        if tokens + t > overlap_tokens:
            break
        result.insert(0, part)
        tokens += t
    return result
