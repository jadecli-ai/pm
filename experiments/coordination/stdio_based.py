#!/usr/bin/env python3
"""Stdio-based agent coordination pattern.

This pattern uses stdin/stdout for direct, synchronous communication.

Pros:
- Fast, no I/O overhead
- Synchronous (easy to reason about)
- No external dependencies

Cons:
- Blocking (no parallelism)
- No persistence
- Single agent at a time
"""
import json
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.agent_registry import get_registry
from lib.mlflow_tracing import trace_agent_call


def stdio_agent_handler():
    """Handle agent requests from stdin, write to stdout.

    Input format (JSON):
    {
        "tool": "gemini_analyze_image",
        "params": {"image_path": "...", "query": "..."}
    }

    Output format (JSON):
    {
        "success": true,
        "output": "...",
        "tokens": 123,
        "latency_ms": 456
    }
    """
    registry = get_registry()

    # Read from stdin
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())

            tool_name = request.get("tool")
            params = request.get("params", {})

            if not tool_name:
                response = {
                    "success": False,
                    "error": "Missing 'tool' field"
                }
                print(json.dumps(response), flush=True)
                continue

            # Execute tool
            with trace_agent_call("stdio", tool_name):
                result = registry.execute_tool(tool_name, **params)

            # Write to stdout
            print(json.dumps(result), flush=True)

        except json.JSONDecodeError as e:
            response = {
                "success": False,
                "error": f"Invalid JSON: {e}"
            }
            print(json.dumps(response), flush=True)

        except Exception as e:
            response = {
                "success": False,
                "error": str(e)
            }
            print(json.dumps(response), flush=True)


def demo_stdio_coordination():
    """Demonstrate stdio-based coordination."""
    import subprocess

    print("=" * 60)
    print("Stdio-Based Agent Coordination Demo")
    print("=" * 60)

    # Example 1: Single request
    print("\n### Example 1: Single Request ###\n")

    request = {
        "tool": "kimi_load_codebase",
        "params": {
            "files": ["lib/agent_registry.py"],
            "query": "Summarize"
        }
    }

    print(f"Request: {json.dumps(request, indent=2)}")

    # Simulate piping to agent handler
    proc = subprocess.Popen(
        [sys.executable, __file__, "--handler"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = proc.communicate(json.dumps(request) + "\n")

    if stdout:
        result = json.loads(stdout.strip())
        print(f"\nResponse: {json.dumps(result, indent=2)}")

    # Example 2: Multiple requests
    print("\n### Example 2: Multiple Requests ###\n")

    requests = [
        {"tool": "kimi_load_codebase", "params": {"files": ["lib/gemini/multimodal.py"], "query": "Count functions"}},
        {"tool": "kimi_load_codebase", "params": {"files": ["lib/kimi/long_context.py"], "query": "Count classes"}}
    ]

    for i, req in enumerate(requests):
        print(f"\nRequest {i+1}: {req['tool']}")

        proc = subprocess.Popen(
            [sys.executable, __file__, "--handler"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )

        stdout, _ = proc.communicate(json.dumps(req) + "\n")

        if stdout:
            result = json.loads(stdout.strip())
            status = "✓" if result.get("success") else "✗"
            print(f"{status} Response: {result.get('success', False)}")

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--handler":
        # Run as handler (read from stdin)
        stdio_agent_handler()
    else:
        # Run demo
        demo_stdio_coordination()
