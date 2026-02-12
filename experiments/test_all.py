#!/usr/bin/env python3
"""Run all agent tests and generate report."""
import sys
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def run_test(script_path: Path, name: str) -> dict:
    """Run a test script and capture result.

    Args:
        script_path: Path to test script
        name: Test name

    Returns:
        dict with result info
    """
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60,
            env={"PYTHONPATH": str(script_path.parent.parent)}
        )

        success = result.returncode == 0

        return {
            "name": name,
            "success": success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "success": False,
            "error": "Timeout (60s)",
            "returncode": -1
        }
    except Exception as e:
        return {
            "name": name,
            "success": False,
            "error": str(e),
            "returncode": -1
        }


def main():
    """Run all tests."""
    print("="*80)
    print("Gemini/Kimi Agent Integration - Full Test Suite")
    print("="*80)
    print(f"Started: {datetime.now().isoformat()}")

    base = Path(__file__).parent

    tests = [
        (base / "test_setup.py", "Setup & Configuration"),
        (base / "gemini_variations" / "test_multimodal.py", "Gemini Multimodal"),
        (base / "gemini_variations" / "test_code_execution.py", "Gemini Code Execution"),
        (base / "kimi_variations" / "test_long_context.py", "Kimi Long Context"),
    ]

    results = []

    for script, name in tests:
        if not script.exists():
            print(f"\n⚠️  Skipping {name} - script not found: {script}")
            continue

        result = run_test(script, name)
        results.append(result)

        # Print result
        if result["success"]:
            print(f"\n✓ {name} PASSED")
        else:
            print(f"\n✗ {name} FAILED")
            if "error" in result:
                print(f"  Error: {result['error']}")
            if "stderr" in result and result["stderr"]:
                print(f"  Stderr: {result['stderr'][:200]}")

    # Summary
    print("\n" + "="*80)
    print("Test Suite Summary")
    print("="*80)

    passed = sum(1 for r in results if r["success"])
    total = len(results)

    for result in results:
        status = "✓ PASS" if result["success"] else "✗ FAIL"
        print(f"{status:8} {result['name']}")

    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"Completed: {datetime.now().isoformat()}")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
