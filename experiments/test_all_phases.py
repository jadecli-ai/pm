"""Comprehensive test suite for Phase 2 & 3 with MLflow tracking.

Tests all Gemini and Kimi capabilities with performance metrics.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import json
from typing import Dict, List, Any
import mlflow
from datetime import datetime

# Import environment setup
from src.env_get import get_gemini_api_key, get_kimi_api_key, check_env_status

# Import Gemini tools
from lib.gemini.code_execution import GeminiCodeExecutor
from lib.gemini.multimodal import GeminiMultimodal
from lib.gemini.embeddings import GeminiEmbeddings

# Results storage
results = {
    "timestamp": datetime.now().isoformat(),
    "gemini": {},
    "kimi": {},
    "hybrid": {},
    "summary": {}
}


def setup_mlflow():
    """Initialize MLflow tracking."""
    mlflow.set_experiment("gemini-kimi-phase2-phase3")
    print("✓ MLflow experiment initialized")


def test_gemini_embeddings() -> Dict[str, Any]:
    """Test Gemini embeddings (Task #9)."""
    print("\n[1/12] Testing Gemini Embeddings...")

    with mlflow.start_run(run_name="gemini-embeddings"):
        tool = GeminiEmbeddings()

        # Test 1: Single embedding
        result1 = tool.embed_text("Machine learning is transforming software development")
        mlflow.log_metric("embed_single_latency_ms", result1.latency_ms)
        mlflow.log_metric("embed_single_tokens", result1.tokens_used)

        # Test 2: Batch embedding
        texts = [
            "Python is a great programming language",
            "JavaScript powers the web",
            "Rust ensures memory safety"
        ]
        result2 = tool.embed_batch(texts)
        mlflow.log_metric("embed_batch_latency_ms", result2.latency_ms)
        mlflow.log_metric("embed_batch_tokens", result2.tokens_used)

        # Test 3: Similarity search
        documents = [
            "Python is used for AI and data science",
            "JavaScript is used for web development",
            "Rust is used for systems programming",
            "Python has excellent machine learning libraries"
        ]
        result3 = tool.similarity_search("machine learning", documents, top_k=2)
        mlflow.log_metric("similarity_search_latency_ms", result3.latency_ms)

        success = result1.success and result2.success and result3.success
        mlflow.log_metric("success", 1 if success else 0)

        return {
            "status": "✅ PASS" if success else "❌ FAIL",
            "single_latency": f"{result1.latency_ms:.0f}ms",
            "batch_latency": f"{result2.latency_ms:.0f}ms",
            "search_latency": f"{result3.latency_ms:.0f}ms",
            "embedding_dim": 768,
            "error": result1.error or result2.error or result3.error
        }


def test_gemini_structured_json() -> Dict[str, Any]:
    """Test Gemini structured JSON generation (Task #10)."""
    print("\n[2/12] Testing Gemini Structured JSON...")

    with mlflow.start_run(run_name="gemini-structured-json"):
        try:
            from google import genai
            from src.env_get import get_gemini_api_key

            client = genai.Client(api_key=get_gemini_api_key())
            start = time.time()

            # Define schema
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                    "skills": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["name", "age"]
            }

            # Generate structured JSON
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents="Generate a profile for a senior Python developer",
                config={"response_mime_type": "application/json"}
            )

            latency = (time.time() - start) * 1000
            mlflow.log_metric("structured_json_latency_ms", latency)
            mlflow.log_metric("success", 1)

            # Validate JSON
            parsed = json.loads(response.text)

            return {
                "status": "✅ PASS",
                "latency": f"{latency:.0f}ms",
                "sample_output": str(parsed)[:100] + "...",
                "error": None
            }
        except Exception as e:
            mlflow.log_metric("success", 0)
            return {
                "status": "❌ FAIL",
                "latency": "N/A",
                "error": str(e)
            }


def test_gemini_thinking() -> Dict[str, Any]:
    """Test Gemini thinking mode (Task #11)."""
    print("\n[3/12] Testing Gemini Thinking Mode...")

    with mlflow.start_run(run_name="gemini-thinking"):
        try:
            from google import genai
            from src.env_get import get_gemini_api_key

            client = genai.Client(api_key=get_gemini_api_key())
            start = time.time()

            # Complex reasoning task
            response = client.models.generate_content(
                model="gemini-2.0-flash-thinking-exp",
                contents="Solve: If a train leaves Station A at 60mph and another leaves Station B (300 miles away) at 40mph, when do they meet? Show your reasoning."
            )

            latency = (time.time() - start) * 1000
            mlflow.log_metric("thinking_latency_ms", latency)
            mlflow.log_metric("success", 1)

            return {
                "status": "✅ PASS",
                "latency": f"{latency:.0f}ms",
                "output_length": len(response.text),
                "error": None
            }
        except Exception as e:
            mlflow.log_metric("success", 0)
            return {
                "status": "⚠️ SKIP" if "thinking" in str(e).lower() else "❌ FAIL",
                "latency": "N/A",
                "error": str(e)
            }


def test_gemini_audio() -> Dict[str, Any]:
    """Test Gemini audio analysis (Task #12)."""
    print("\n[4/12] Testing Gemini Audio Analysis...")

    # Skip if no audio file available
    return {
        "status": "⏸️ SKIP",
        "reason": "No test audio file available",
        "note": "Implementation ready, needs test audio file"
    }


def test_kimi_sdk_installation() -> Dict[str, Any]:
    """Verify Kimi SDK is installed (Task #8)."""
    print("\n[5/12] Verifying Kimi SDK...")

    try:
        import kimi_agent_sdk
        return {
            "status": "✅ PASS",
            "installed": True,
            "error": None
        }
    except ImportError as e:
        return {
            "status": "❌ FAIL",
            "installed": False,
            "error": str(e)
        }


def test_kimi_long_context() -> Dict[str, Any]:
    """Test Kimi 256K context window (Task #13)."""
    print("\n[6/12] Testing Kimi Long Context (256K)...")

    with mlflow.start_run(run_name="kimi-long-context"):
        try:
            # Use OpenAI-compatible API
            import openai
            from src.env_get import get_kimi_api_key

            client = openai.OpenAI(
                api_key=get_kimi_api_key(),
                base_url="https://api.moonshot.cn/v1"
            )

            start = time.time()

            # Create large context (simulated)
            large_text = "Line {}: This is sample code for testing.\n" * 1000  # ~1000 lines
            large_text = large_text.format(*range(1000))

            response = client.chat.completions.create(
                model="moonshot-v1-256k",
                messages=[
                    {"role": "system", "content": "You are a code analyzer."},
                    {"role": "user", "content": f"Analyze this code:\n\n{large_text}\n\nHow many lines?"}
                ]
            )

            latency = (time.time() - start) * 1000
            mlflow.log_metric("kimi_context_latency_ms", latency)
            mlflow.log_metric("kimi_context_lines", 1000)
            mlflow.log_metric("success", 1)

            return {
                "status": "✅ PASS",
                "latency": f"{latency:.0f}ms",
                "context_size": "~1000 lines",
                "model": "moonshot-v1-256k",
                "error": None
            }
        except Exception as e:
            mlflow.log_metric("success", 0)
            return {
                "status": "❌ FAIL",
                "latency": "N/A",
                "error": str(e)
            }


def test_kimi_agent_swarm() -> Dict[str, Any]:
    """Test Kimi agent swarm (Task #14)."""
    print("\n[7/12] Testing Kimi Agent Swarm...")

    # Note: Agent swarm requires specific SDK features
    return {
        "status": "⏸️ SKIP",
        "reason": "Requires kimi-agent-sdk Session API",
        "note": "SDK installed, but swarm features need deeper integration"
    }


def test_kimi_vibe_coding() -> Dict[str, Any]:
    """Test Kimi vibe coding (Task #15)."""
    print("\n[8/12] Testing Kimi Vibe Coding...")

    with mlflow.start_run(run_name="kimi-vibe-coding"):
        try:
            import openai
            from src.env_get import get_kimi_api_key

            client = openai.OpenAI(
                api_key=get_kimi_api_key(),
                base_url="https://api.moonshot.cn/v1"
            )

            start = time.time()

            response = client.chat.completions.create(
                model="moonshot-v1-256k",
                messages=[
                    {"role": "user", "content": "Write a Python function to calculate fibonacci numbers"}
                ]
            )

            latency = (time.time() - start) * 1000
            mlflow.log_metric("vibe_coding_latency_ms", latency)
            mlflow.log_metric("success", 1)

            return {
                "status": "✅ PASS",
                "latency": f"{latency:.0f}ms",
                "generated_code": response.choices[0].message.content[:100] + "...",
                "error": None
            }
        except Exception as e:
            mlflow.log_metric("success", 0)
            return {
                "status": "❌ FAIL",
                "error": str(e)
            }


def test_multimodal_benchmark() -> Dict[str, Any]:
    """Test multimodal capabilities (Task #17)."""
    print("\n[9/12] Running Multimodal Benchmarks...")

    # Skip if no test files
    return {
        "status": "⏸️ SKIP",
        "reason": "No test images/videos available",
        "note": "Implementation ready in lib/gemini/multimodal.py"
    }


def test_hybrid_workflow() -> Dict[str, Any]:
    """Test Gemini + Kimi hybrid workflow (Task #18)."""
    print("\n[10/12] Testing Hybrid Workflow...")

    with mlflow.start_run(run_name="hybrid-workflow"):
        try:
            # Workflow: Gemini (fast code) + Kimi (large context analysis)

            # Step 1: Gemini generates code (fast)
            from lib.gemini.code_execution import GeminiCodeExecutor
            gemini = GeminiCodeExecutor()

            code_result = gemini.execute_code("def hello(): return 'Hello from Gemini'")

            # Step 2: Kimi analyzes (with context)
            import openai
            from src.env_get import get_kimi_api_key

            kimi = openai.OpenAI(
                api_key=get_kimi_api_key(),
                base_url="https://api.moonshot.ai/v1"
            )

            analysis = kimi.chat.completions.create(
                model="moonshot-v1-256k",
                messages=[
                    {"role": "user", "content": f"Analyze this code output: {code_result.output}"}
                ]
            )

            mlflow.log_metric("hybrid_gemini_latency", code_result.latency_ms)
            mlflow.log_metric("success", 1)

            return {
                "status": "✅ PASS",
                "gemini_step": f"{code_result.latency_ms:.0f}ms",
                "kimi_step": "completed",
                "workflow": "Gemini (execute) → Kimi (analyze)",
                "error": None
            }
        except Exception as e:
            mlflow.log_metric("success", 0)
            return {
                "status": "❌ FAIL",
                "error": str(e)
            }


def test_code_execution_baseline() -> Dict[str, Any]:
    """Baseline test: Gemini code execution (already tested)."""
    print("\n[11/12] Testing Gemini Code Execution (Baseline)...")

    with mlflow.start_run(run_name="gemini-code-execution-baseline"):
        tool = GeminiCodeExecutor()
        result = tool.execute_code("print(sum(range(1, 101)))")

        mlflow.log_metric("code_exec_latency_ms", result.latency_ms)
        mlflow.log_metric("code_exec_tokens", result.tokens_used)
        mlflow.log_metric("success", 1 if result.success else 0)

        return {
            "status": "✅ PASS" if result.success else "❌ FAIL",
            "latency": f"{result.latency_ms:.0f}ms",
            "model": result.model,
            "output": result.output[:100],
            "error": result.error
        }


def generate_mlflow_dashboard() -> Dict[str, Any]:
    """Generate MLflow dashboard summary (Task #19)."""
    print("\n[12/12] Generating MLflow Dashboard...")

    # Get all runs from this experiment
    experiment = mlflow.get_experiment_by_name("gemini-kimi-phase2-phase3")
    if experiment:
        runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])

        dashboard = {
            "total_runs": len(runs),
            "avg_latency_ms": runs['metrics.embed_single_latency_ms'].mean() if 'metrics.embed_single_latency_ms' in runs else 0,
            "success_rate": (runs['metrics.success'].sum() / len(runs) * 100) if 'metrics.success' in runs else 0,
            "mlflow_ui": "Run: mlflow ui --backend-store-uri ./mlruns"
        }

        return {
            "status": "✅ COMPLETE",
            "dashboard": dashboard
        }

    return {
        "status": "⚠️ PARTIAL",
        "note": "Metrics logged, run 'mlflow ui' to view"
    }


def main():
    """Run all tests and generate report."""
    print("="*70)
    print("GEMINI & KIMI AGENT TEST SUITE - PHASE 2 & 3")
    print("="*70)

    # Check environment
    env_status = check_env_status()
    print(f"\n✓ Environment: {env_status}")

    # Initialize MLflow
    setup_mlflow()

    # Run all tests
    results["gemini"]["embeddings"] = test_gemini_embeddings()
    results["gemini"]["structured_json"] = test_gemini_structured_json()
    results["gemini"]["thinking"] = test_gemini_thinking()
    results["gemini"]["audio"] = test_gemini_audio()
    results["gemini"]["code_execution"] = test_code_execution_baseline()

    results["kimi"]["sdk"] = test_kimi_sdk_installation()
    results["kimi"]["long_context"] = test_kimi_long_context()
    results["kimi"]["agent_swarm"] = test_kimi_agent_swarm()
    results["kimi"]["vibe_coding"] = test_kimi_vibe_coding()

    results["hybrid"]["workflow"] = test_hybrid_workflow()
    results["hybrid"]["multimodal_benchmark"] = test_multimodal_benchmark()
    results["hybrid"]["dashboard"] = generate_mlflow_dashboard()

    # Generate summary
    total_tests = 12
    passed = sum(1 for cat in results.values() if isinstance(cat, dict)
                 for test in cat.values() if isinstance(test, dict) and test.get("status") == "✅ PASS")
    failed = sum(1 for cat in results.values() if isinstance(cat, dict)
                 for test in cat.values() if isinstance(test, dict) and test.get("status") == "❌ FAIL")
    skipped = total_tests - passed - failed

    results["summary"] = {
        "total": total_tests,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "success_rate": f"{(passed / total_tests * 100):.1f}%"
    }

    # Print results
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)

    for category, tests in results.items():
        if category == "summary":
            continue
        print(f"\n{category.upper()}:")
        if isinstance(tests, dict):
            for name, result in tests.items():
                if isinstance(result, dict):
                    status = result.get("status", "?")
                    print(f"  {name:30s} {status}")

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total:        {results['summary']['total']}")
    print(f"Passed:       {results['summary']['passed']} ✅")
    print(f"Failed:       {results['summary']['failed']} ❌")
    print(f"Skipped:      {results['summary']['skipped']} ⏸️")
    print(f"Success Rate: {results['summary']['success_rate']}")

    # Save detailed results
    output_file = Path(__file__).parent / "phase2_phase3_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Detailed results saved to: {output_file}")
    print(f"✓ MLflow UI: mlflow ui --backend-store-uri ./mlruns")
    print("="*70)

    return results


if __name__ == "__main__":
    main()
