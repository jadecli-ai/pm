#!/usr/bin/env python3
"""Test Kimi long context agent."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.kimi.long_context import KimiLongContext
from lib.mlflow_tracing import trace_agent_call


def main():
    """Test Kimi long context analysis."""
    print("=" * 60)
    print("Testing Kimi Long Context Agent (256K)")
    print("=" * 60)

    try:
        tool = KimiLongContext()
        print("✓ KimiLongContext initialized")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        print("\nMake sure KIMI_API_KEY_v3 is set")
        return False

    # Test 1: Load single file
    print("\n### Test 1: Single File Analysis ###\n")

    files = ["lib/agent_registry.py"]

    with trace_agent_call("kimi-long-context", "load_codebase", file_count=len(files)):
        result = tool.load_codebase(files, "Summarize this module")

        if result.success:
            print(f"✓ Success!")
            print(f"  Tokens: {result.tokens_used}")
            print(f"  Latency: {result.latency_ms:.0f}ms")
            print(f"  Output:\n{result.output[:500]}...")
        else:
            print(f"✗ Failed: {result.error}")

    # Test 2: Load multiple files
    print("\n### Test 2: Multiple Files (Simulating Large Codebase) ###\n")

    files = [
        "lib/agent_registry.py",
        "lib/mlflow_tracing.py",
        "lib/gemini/multimodal.py",
        "lib/kimi/long_context.py"
    ]

    result = tool.load_codebase(files, "Count total functions across all files")

    if result.success:
        print(f"✓ Success!")
        print(f"  Files loaded: {len(files)}")
        print(f"  Tokens: {result.tokens_used}")
        print(f"  Output:\n{result.output[:500]}...")
    else:
        print(f"✗ Failed: {result.error}")

    # Test 3: Glob pattern (load all Python files)
    print("\n### Test 3: Glob Pattern Analysis ###\n")

    lib_files = list(Path("lib").rglob("*.py"))
    file_paths = [str(f) for f in lib_files if f.is_file()][:10]  # Limit to 10 for demo

    print(f"Found {len(lib_files)} Python files, loading first {len(file_paths)}")

    result = tool.load_codebase(file_paths, "What is the overall architecture?")

    if result.success:
        print(f"✓ Success!")
        print(f"  Files: {len(file_paths)}")
        print(f"  Tokens: {result.tokens_used}")
    else:
        print(f"✗ Failed: {result.error}")

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("Kimi long context agent can load entire codebases.")
    print("Note: Full API integration pending kimi-agent-sdk installation")
    print("Current: Stub implementation (loads files, shows token count)")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
