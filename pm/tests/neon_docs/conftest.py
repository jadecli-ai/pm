# pm/tests/neon_docs/conftest.py
"""Shared test fixtures for neon_docs tests."""

from __future__ import annotations

import os

import pytest


@pytest.fixture
def neon_url() -> str:
    """Get Neon database URL, skip if not set."""
    url = os.environ.get("PRJ_NEON_DATABASE_URL")
    if not url:
        pytest.skip("PRJ_NEON_DATABASE_URL not set")
    return url


@pytest.fixture
def ollama_host() -> str:
    """Get Ollama host, skip if not reachable."""
    import httpx

    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    try:
        resp = httpx.get(f"{host}/api/tags", timeout=5.0)
        resp.raise_for_status()
    except Exception:
        pytest.skip(f"Ollama not reachable at {host}")
    return host


@pytest.fixture
def sample_text() -> str:
    """Sample document text for testing."""
    return (
        "Claude is an AI assistant made by Anthropic. "
        "It uses a technique called Constitutional AI (CAI) for alignment. "
        "Claude can help with analysis, writing, coding, and more. "
        "The API supports tool use, vision, and prompt caching."
    )


@pytest.fixture
def long_text() -> str:
    """Long document text that will require multiple chunks."""
    paragraphs = []
    for i in range(20):
        paragraphs.append(
            f"Section {i + 1}: This is paragraph {i + 1} of the test document. "
            f"It contains several sentences about topic {i + 1}. "
            f"The purpose is to test text chunking with realistic paragraph lengths. "
            f"Each paragraph has enough content to contribute meaningfully to token counts. "
            f"We include varied vocabulary to test embedding quality across chunks."
        )
    return "\n\n".join(paragraphs)
