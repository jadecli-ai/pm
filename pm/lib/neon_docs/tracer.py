# pm/lib/neon_docs/tracer.py
"""MLflow 3.9 tracing for neon_docs operations.

Provides @trace_operation decorator that creates MLflow spans with
inputs, outputs, duration, and error tracking.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

from .log import get_logger

logger = get_logger("tracer")

try:
    import mlflow

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

F = TypeVar("F", bound=Callable[..., Any])


def trace_operation(name: str) -> Callable[[F], F]:
    """Decorator to trace a function as an MLflow span.

    Args:
        name: Span name (e.g., 'neon.cache_check').

    Returns:
        Decorated function.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.monotonic()

            if not MLFLOW_AVAILABLE:
                result = await func(*args, **kwargs)
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.debug("[TRACE] %s: %.0fms", name, elapsed_ms)
                return result

            with mlflow.start_span(name=name) as span:
                safe_kwargs = {k: str(v)[:200] for k, v in kwargs.items()}
                span.set_inputs(safe_kwargs)

                try:
                    result = await func(*args, **kwargs)
                    elapsed_ms = (time.monotonic() - start) * 1000
                    span.set_attributes({"duration_ms": elapsed_ms})

                    if isinstance(result, dict):
                        span.set_outputs({k: str(v)[:200] for k, v in result.items()})
                    elif isinstance(result, list):
                        span.set_outputs({"count": len(result)})
                    else:
                        span.set_outputs({"result": str(result)[:200]})

                    return result
                except Exception as e:
                    span.set_status("ERROR")
                    span.set_attributes({"error": str(e), "error_type": type(e).__name__})
                    raise

        return wrapper  # type: ignore[return-value]

    return decorator


def setup_autolog() -> None:
    """Enable MLflow 3.9 Anthropic autolog if available."""
    if MLFLOW_AVAILABLE and hasattr(mlflow, "anthropic"):
        mlflow.anthropic.autolog()
        logger.info("MLflow Anthropic autolog enabled")
    elif MLFLOW_AVAILABLE:
        logger.warning("mlflow.anthropic.autolog not available — upgrade to mlflow>=3.9")
