"""MLflow tracing for agent performance tracking."""
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


@contextmanager
def trace_agent_call(agent_name: str, tool_name: str, **params):
    """Trace agent tool execution with MLflow.

    Args:
        agent_name: Name of agent (e.g., 'gemini-multimodal')
        tool_name: Name of tool called (e.g., 'analyze_image')
        **params: Additional parameters to log

    Usage:
        with trace_agent_call("gemini-multimodal", "analyze_image", image="test.png"):
            result = tool.analyze_image("test.png", "Describe this")
            mlflow.log_metrics({
                "success": 1,
                "tokens": result.tokens_used,
                "latency_ms": result.latency_ms
            })
    """
    if not MLFLOW_AVAILABLE:
        # Fallback: just yield without tracing
        print(f"[TRACE] {agent_name}.{tool_name} (MLflow not installed)")
        yield None
        return

    mlflow.set_experiment(f"agents/{agent_name}")

    start = time.time()
    with mlflow.start_run(run_name=f"{agent_name}_{tool_name}_{int(time.time())}") as run:
        # Log parameters
        mlflow.log_params({
            "agent": agent_name,
            "tool": tool_name,
            "timestamp": datetime.now().isoformat(),
            **params
        })

        try:
            yield run

            # Log success metric (caller should log additional metrics)
            mlflow.log_metrics({
                "duration_s": time.time() - start
            })

        except Exception as e:
            # Log error
            mlflow.log_params({
                "error": str(e),
                "error_type": type(e).__name__
            })
            mlflow.log_metrics({
                "success": 0,
                "duration_s": time.time() - start
            })
            raise


def log_comparison(
    gemini_result: Dict[str, Any],
    kimi_result: Dict[str, Any],
    task: str
):
    """Compare Gemini vs Kimi performance on same task.

    Args:
        gemini_result: Result dict with keys: success, tokens, latency_ms, output
        kimi_result: Result dict with same keys
        task: Task description

    Usage:
        g_result = gemini.analyze_image(...)
        k_result = kimi.analyze_image(...)
        log_comparison(
            {"success": True, "tokens": 100, "latency_ms": 500, "output": "..."},
            {"success": True, "tokens": 120, "latency_ms": 300, "output": "..."},
            "image_analysis"
        )
    """
    if not MLFLOW_AVAILABLE:
        print(f"[COMPARISON] {task}")
        print(f"  Gemini: {gemini_result.get('latency_ms', 0)}ms, {gemini_result.get('tokens', 0)} tokens")
        print(f"  Kimi: {kimi_result.get('latency_ms', 0)}ms, {kimi_result.get('tokens', 0)} tokens")
        return

    mlflow.set_experiment("agent_comparison")

    with mlflow.start_run(run_name=f"comparison_{task}_{int(time.time())}"):
        # Log metrics
        mlflow.log_metrics({
            "gemini_latency_ms": gemini_result.get("latency_ms", 0),
            "kimi_latency_ms": kimi_result.get("latency_ms", 0),
            "gemini_tokens": gemini_result.get("tokens", 0),
            "kimi_tokens": kimi_result.get("tokens", 0),
            "gemini_success": 1 if gemini_result.get("success") else 0,
            "kimi_success": 1 if kimi_result.get("success") else 0,
        })

        # Calculate speedup/cost ratios
        if kimi_result.get("latency_ms", 0) > 0:
            speedup = gemini_result.get("latency_ms", 0) / kimi_result.get("latency_ms", 1)
            mlflow.log_metrics({"speedup_ratio": speedup})

        # Log parameters
        mlflow.log_params({
            "task": task,
            "gemini_model": gemini_result.get("model", "unknown"),
            "kimi_model": kimi_result.get("model", "unknown"),
            "timestamp": datetime.now().isoformat()
        })

        # Log outputs as artifacts
        with open("/tmp/gemini_output.txt", "w") as f:
            f.write(gemini_result.get("output", ""))
        with open("/tmp/kimi_output.txt", "w") as f:
            f.write(kimi_result.get("output", ""))

        mlflow.log_artifact("/tmp/gemini_output.txt")
        mlflow.log_artifact("/tmp/kimi_output.txt")


def get_mlflow_status() -> Dict[str, Any]:
    """Get MLflow availability and configuration status.

    Returns:
        Dict with status info
    """
    return {
        "available": MLFLOW_AVAILABLE,
        "tracking_uri": mlflow.get_tracking_uri() if MLFLOW_AVAILABLE else None,
        "message": "MLflow is available" if MLFLOW_AVAILABLE else "Install with: pip install mlflow"
    }
