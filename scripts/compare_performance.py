#!/usr/bin/env python3
"""Compare Gemini vs Kimi performance on same tasks."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.gemini.multimodal import GeminiMultimodal
from lib.kimi.long_context import KimiLongContext
from lib.mlflow_tracing import log_comparison


def compare_code_analysis():
    """Compare Gemini vs Kimi on code analysis task."""
    print("=" * 60)
    print("Performance Comparison: Gemini vs Kimi")
    print("=" * 60)

    print("\n### Task: Analyze Python code files ###\n")

    files = ["lib/agent_registry.py"]

    # Gemini (Note: Gemini doesn't have direct codebase loading like Kimi)
    # We'll simulate with document extraction
    print("Gemini approach: Would need to implement code analysis tool")
    gemini_result = {
        "success": False,
        "output": "Not implemented - Gemini needs custom code analysis tool",
        "tokens": 0,
        "latency_ms": 0,
        "model": "gemini-2.0-flash-exp",
        "error": "Stub - implement code analysis"
    }

    # Kimi
    print("Kimi approach: Using kimi_load_codebase (256K context)")
    kimi_tool = KimiLongContext()
    start = time.time()
    kimi_result_obj = kimi_tool.load_codebase(files, "Summarize this code")
    kimi_result = {
        "success": kimi_result_obj.success,
        "output": kimi_result_obj.output,
        "tokens": kimi_result_obj.tokens_used,
        "latency_ms": kimi_result_obj.latency_ms,
        "model": kimi_result_obj.model,
        "error": kimi_result_obj.error
    }

    # Log comparison
    log_comparison(gemini_result, kimi_result, "code_analysis")

    # Display results
    print("\n### Results ###\n")

    print("Gemini:")
    print(f"  Success: {gemini_result['success']}")
    print(f"  Latency: {gemini_result['latency_ms']:.0f}ms")
    print(f"  Tokens: {gemini_result['tokens']}")

    print("\nKimi:")
    print(f"  Success: {kimi_result['success']}")
    print(f"  Latency: {kimi_result['latency_ms']:.0f}ms")
    print(f"  Tokens: {kimi_result['tokens']}")

    if kimi_result['success'] and gemini_result['success']:
        print(f"\nSpeedup: {gemini_result['latency_ms'] / kimi_result['latency_ms']:.2f}x")
    elif kimi_result['success']:
        print("\n✓ Kimi succeeded (Gemini not implemented)")

    print("\n" + "=" * 60)
    print("Comparison logged to MLflow")
    print("=" * 60)
    print("\nView results:")
    print("  mlflow ui")
    print("  http://localhost:5000")


def compare_context_windows():
    """Compare context window capabilities."""
    print("\n\n" + "=" * 60)
    print("Context Window Comparison")
    print("=" * 60)

    comparisons = [
        ("Gemini 3 Pro", "~1M tokens", "Variable, very large"),
        ("Kimi K2.5", "256K tokens", "~200K lines of code"),
        ("Claude 4.5", "200K tokens", "~160K lines of code"),
    ]

    print("\n| Model | Context Window | Code Capacity |")
    print("|-------|---------------|---------------|")
    for model, window, capacity in comparisons:
        print(f"| {model} | {window} | {capacity} |")

    print("\nKimi Advantage:")
    print("  - 28% larger than Claude")
    print("  - Load entire mid-sized projects")
    print("  - No chunking/fragmentation needed")


def compare_costs():
    """Compare API costs."""
    print("\n\n" + "=" * 60)
    print("Cost Comparison")
    print("=" * 60)

    print("\nRelative Costs (approximate):")
    print("  - Kimi: ~9x cheaper than Claude")
    print("  - Gemini: Competitive pricing")
    print("  - Claude: Premium pricing")

    print("\nBest for:")
    print("  - Gemini: Multimodal tasks, code execution")
    print("  - Kimi: Long context, cost-sensitive, high volume")
    print("  - Claude: Complex reasoning, orchestration")


if __name__ == "__main__":
    try:
        compare_code_analysis()
        compare_context_windows()
        compare_costs()

        print("\n\n✅ Performance comparison complete!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
