# pm/lib/neon_docs/tokenizer.py
"""Accurate token counting via tiktoken.

Uses cl100k_base encoding (GPT-4/Claude compatible).
"""

from __future__ import annotations

import tiktoken

_encoder: tiktoken.Encoding | None = None


def _get_encoder() -> tiktoken.Encoding:
    """Get cached tiktoken encoder."""
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding("cl100k_base")
    return _encoder


def count_tokens(text: str) -> int:
    """Count tokens in text using cl100k_base encoding."""
    return len(_get_encoder().encode(text))
