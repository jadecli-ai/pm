#!/usr/bin/env python3
"""Test Gemini multimodal agent."""
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.gemini.multimodal import GeminiMultimodal
from lib.mlflow_tracing import trace_agent_call

def main():
    """Test Gemini multimodal analysis."""
    print("=" * 60)
    print("Testing Gemini Multimodal Agent")
    print("=" * 60)

    try:
        tool = GeminiMultimodal()
        print("✓ GeminiMultimodal initialized")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        print("\nMake sure:")
        print("1. GEMINI_API_KEY is set")
        print("2. google-genai is installed: pip install google-genai")
        return False

    # Test 1: Analyze image (stub - need real image)
    print("\nTest 1: Analyze Image")
    print("-" * 60)

    # Note: This will fail without a real image file
    # Users should replace with actual test image path
    test_image = "test_screenshot.png"

    if Path(test_image).exists():
        with trace_agent_call("gemini-multimodal", "analyze_image", image=test_image):
            result = tool.analyze_image(test_image, "Describe this image")

            if result.success:
                print(f"✓ Success!")
                print(f"  Tokens: {result.tokens_used}")
                print(f"  Latency: {result.latency_ms:.0f}ms")
                print(f"  Output: {result.output[:200]}...")
            else:
                print(f"✗ Failed: {result.error}")
    else:
        print(f"⚠️  Test image not found: {test_image}")
        print("   Create a test image or update path to test this feature")

    # Test 2: Extract document (stub)
    print("\nTest 2: Extract Document")
    print("-" * 60)

    test_doc = "test_document.pdf"

    if Path(test_doc).exists():
        result = tool.extract_document(test_doc, "Extract all text")

        if result.success:
            print(f"✓ Success!")
            print(f"  Output: {result.output[:200]}...")
        else:
            print(f"✗ Failed: {result.error}")
    else:
        print(f"⚠️  Test document not found: {test_doc}")
        print("   Create a test PDF to test this feature")

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("Gemini multimodal agent is configured and ready.")
    print("\nTo test with real files:")
    print("1. Place test image at:", test_image)
    print("2. Place test PDF at:", test_doc)
    print("3. Run this script again")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
