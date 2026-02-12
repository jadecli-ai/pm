#!/usr/bin/env python3
"""Test setup and verify agent integration."""
import os
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from lib.agent_registry import get_registry
        print("✓ agent_registry")
    except Exception as e:
        print(f"✗ agent_registry: {e}")
        return False

    try:
        from lib.mlflow_tracing import trace_agent_call, get_mlflow_status
        status = get_mlflow_status()
        print(f"✓ mlflow_tracing (available: {status['available']})")
    except Exception as e:
        print(f"✗ mlflow_tracing: {e}")
        return False

    try:
        from lib.gemini import ALL_GEMINI_TOOLS
        print(f"✓ gemini tools ({len(ALL_GEMINI_TOOLS)} tools)")
    except Exception as e:
        print(f"✗ gemini tools: {e}")
        return False

    try:
        from lib.kimi import ALL_KIMI_TOOLS
        print(f"✓ kimi tools ({len(ALL_KIMI_TOOLS)} tools)")
    except Exception as e:
        print(f"✗ kimi tools: {e}")
        return False

    return True


def test_api_keys():
    """Check if API keys are set."""
    print("\nChecking API keys...")

    gemini_key = os.getenv("GEMINI_API_KEY")
    kimi_key = os.getenv("KIMI_API_KEY_v3") or os.getenv("KIMI_API_KEY")

    if gemini_key:
        print(f"✓ GEMINI_API_KEY set ({gemini_key[:20]}...)")
    else:
        print("✗ GEMINI_API_KEY not set")
        print("  Set with: export GEMINI_API_KEY='your_key'")

    if kimi_key:
        print(f"✓ KIMI_API_KEY_v3 set ({kimi_key[:20]}...)")
    else:
        print("✗ KIMI_API_KEY_v3 not set")
        print("  Set with: export KIMI_API_KEY_v3='your_key'")

    return bool(gemini_key or kimi_key)


def test_agent_definitions():
    """Check that agent definition files exist."""
    print("\nChecking agent definitions...")

    base = Path(__file__).parent.parent / "agents"

    gemini_agents = list((base / "gemini").glob("*.md"))
    kimi_agents = list((base / "kimi").glob("*.md"))

    print(f"✓ Found {len(gemini_agents)} Gemini agents")
    for agent in sorted(gemini_agents):
        print(f"  - {agent.name}")

    print(f"✓ Found {len(kimi_agents)} Kimi agents")
    for agent in sorted(kimi_agents):
        print(f"  - {agent.name}")

    return len(gemini_agents) > 0 and len(kimi_agents) > 0


def test_registry():
    """Test agent registry."""
    print("\nTesting agent registry...")

    try:
        from lib.agent_registry import get_registry

        registry = get_registry()
        tools = registry.list_tools()

        print(f"✓ Registry initialized with {len(tools)} tools")
        print("\nRegistered tools:")
        for tool in sorted(tools):
            print(f"  - {tool}")

        return True

    except Exception as e:
        print(f"✗ Registry test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Gemini/Kimi Agent Integration - Setup Test")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("API Keys", test_api_keys),
        ("Agent Definitions", test_agent_definitions),
        ("Agent Registry", test_registry),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ Setup complete! All tests passed.")
        print("\nNext steps:")
        print("1. Set API keys if not already set")
        print("2. Test agents: python experiments/gemini_variations/test_multimodal.py")
        print("3. View docs: cat docs/GEMINI_KIMI_INTEGRATION.md")
    else:
        print("\n⚠️  Some tests failed. Review errors above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
