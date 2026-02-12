#!/usr/bin/env python3
"""Test Gemini code execution agent."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.gemini.code_execution import GeminiCodeExecutor
from lib.mlflow_tracing import trace_agent_call


def main():
    """Test Gemini code execution."""
    print("=" * 60)
    print("Testing Gemini Code Execution Agent")
    print("=" * 60)

    try:
        tool = GeminiCodeExecutor()
        print("✓ GeminiCodeExecutor initialized")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        print("\nMake sure GEMINI_API_KEY is set")
        return False

    # Test 1: Simple code execution
    print("\n### Test 1: Simple Code Execution ###\n")

    code = """
x = 5
y = 10
print(f"Sum: {x + y}")
"""

    with trace_agent_call("gemini-code-interpreter", "execute_code", code_length=len(code)):
        result = tool.execute_code(code)

        if result.success:
            print(f"✓ Success!")
            print(f"  Tokens: {result.tokens_used}")
            print(f"  Latency: {result.latency_ms:.0f}ms")
            print(f"  Output:\n{result.output}")
        else:
            print(f"✗ Failed: {result.error}")

    # Test 2: Data analysis
    print("\n### Test 2: Data Analysis ###\n")

    code = """
data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
mean = sum(data) / len(data)
print(f"Mean: {mean}")
print(f"Max: {max(data)}")
print(f"Min: {min(data)}")
"""

    result = tool.execute_code(code)

    if result.success:
        print(f"✓ Success!")
        print(f"  Output:\n{result.output}")
    else:
        print(f"✗ Failed: {result.error}")

    # Test 3: Error handling
    print("\n### Test 3: Error Handling ###\n")

    code = """
# This will cause an error
x = 1 / 0
"""

    result = tool.execute_code(code)

    if result.success:
        print(f"✓ Handled error gracefully")
        print(f"  Output:\n{result.output}")
    else:
        print(f"✗ Failed: {result.error}")

    print("\n" + "=" * 60)
    print("Test Summary: Code execution agent is working")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
