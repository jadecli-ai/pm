# pm/lib/neon_docs/log.py
"""Structured logging for neon_docs.

Configures Python logging with consistent format.
"""

from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the neon_docs logger.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Configured logger for neon_docs.
    """
    logger = logging.getLogger("neon_docs")

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under neon_docs namespace.

    Args:
        name: Module name (e.g., 'db', 'embedder').

    Returns:
        Logger instance.
    """
    return logging.getLogger(f"neon_docs.{name}")
