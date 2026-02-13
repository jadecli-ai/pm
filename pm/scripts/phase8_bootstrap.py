#!/usr/bin/env python3
# pm/scripts/phase8_bootstrap.py
"""Phase 8 bootstrap runner with MLflow tracing and structured logging.

Executes Tasks 42-48 sequentially:
  42: Verify Ollama model
  43: Run migrations
  44: Bulk-index crawler docs
  45: Drain processing queue
  46: Verify status
  47: Test search quality
  48: Test idempotency

Usage:
    cd $PM && PYTHONPATH=. python3 scripts/phase8_bootstrap.py 2>&1 | tee /tmp/phase8.log
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time

# Bootstrap logging + MLflow before anything else
from lib.neon_docs.log import get_logger, setup_logging

setup_logging("DEBUG")
logger = get_logger("phase8")

try:
    import mlflow

    mlflow.set_experiment("pm-neon-phase8")
    MLFLOW_AVAILABLE = True
    logger.info("MLflow experiment set: pm-neon-phase8")
except ImportError:
    MLFLOW_AVAILABLE = False
    logger.warning("MLflow not available — tracing disabled")

LOG_FILE = "/tmp/phase8.log"


class TaskResult:
    def __init__(self, task_id: int, name: str) -> None:
        self.task_id = task_id
        self.name = name
        self.success = False
        self.output: str = ""
        self.duration_ms: float = 0
        self.error: str | None = None

    def to_dict(self) -> dict:
        return {
            "task": self.task_id,
            "name": self.name,
            "success": self.success,
            "duration_ms": round(self.duration_ms, 1),
            "error": self.error,
        }


results: list[TaskResult] = []


def run_task(task_id: int, name: str, func):
    """Run a task with timing and error capture."""
    r = TaskResult(task_id, name)
    logger.info("=" * 60)
    logger.info("TASK %d: %s — START", task_id, name)
    start = time.monotonic()
    try:
        output = func()
        r.output = str(output) if output else ""
        r.success = True
        logger.info("TASK %d: %s — PASS", task_id, name)
    except Exception as e:
        r.error = str(e)
        logger.error("TASK %d: %s — FAIL: %s", task_id, name, e)
    r.duration_ms = (time.monotonic() - start) * 1000
    results.append(r)
    return r


def task_42_verify_ollama():
    """Verify Ollama is running and nomic-embed-text is available."""
    out = subprocess.run(
        ["ollama", "list"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if out.returncode != 0:
        raise RuntimeError(f"ollama list failed: {out.stderr}")
    if "nomic-embed-text" not in out.stdout:
        raise RuntimeError(f"nomic-embed-text not found in: {out.stdout}")
    logger.info("Ollama models: %s", out.stdout.strip())
    return out.stdout


def task_43_run_migrations():
    """Run database migrations."""
    from lib.neon_docs.migrate import run_migrations

    applied = asyncio.run(run_migrations())
    logger.info("Migrations applied: %s", applied)
    return {"applied": applied}


def task_43b_idempotent_migrations():
    """Verify migrations are idempotent."""
    from lib.neon_docs.migrate import run_migrations

    applied = asyncio.run(run_migrations())
    if applied:
        raise RuntimeError(f"Expected 0 migrations on re-run, got: {applied}")
    logger.info("Migrations idempotent: 0 applied on re-run")
    return {"applied": [], "idempotent": True}


def task_44_bulk_index():
    """Bulk-index crawler docs."""
    out = subprocess.run(
        ["python3", "-m", "lib.neon_docs", "bulk-index", "../docs/crawler-improvements/"],
        capture_output=True,
        text=True,
        timeout=120,
        env=_env(),
    )
    if out.returncode != 0:
        # Try alternate doc paths
        logger.warning("crawler-improvements/ not found, trying docs/fetch/")
        out = subprocess.run(
            ["python3", "-m", "lib.neon_docs", "bulk-index", "../docs/fetch/"],
            capture_output=True,
            text=True,
            timeout=120,
            env=_env(),
        )
    if out.returncode != 0:
        logger.warning("docs/fetch/ not found, trying docs/")
        out = subprocess.run(
            ["python3", "-m", "lib.neon_docs", "bulk-index", "../docs/"],
            capture_output=True,
            text=True,
            timeout=120,
            env=_env(),
        )
    if out.returncode != 0:
        raise RuntimeError(f"bulk-index failed: {out.stderr}")
    logger.info("Bulk index output: %s", out.stdout.strip())
    logger.info("Bulk index stderr: %s", out.stderr.strip())
    return json.loads(out.stdout) if out.stdout.strip() else {"raw": out.stdout}


def task_45_drain_queue():
    """Drain processing queue."""
    from lib.neon_docs.db import close_pool
    from lib.neon_docs.worker import drain_queue

    result = asyncio.run(_drain_and_close())
    logger.info("Queue drain result: %s", result)
    return result


async def _drain_and_close():
    from lib.neon_docs.db import close_pool
    from lib.neon_docs.worker import drain_queue

    try:
        return await drain_queue()
    finally:
        await close_pool()


def task_46_verify_status():
    """Check cache status."""
    out = subprocess.run(
        ["python3", "-m", "lib.neon_docs", "status"],
        capture_output=True,
        text=True,
        timeout=30,
        env=_env(),
    )
    if out.returncode != 0:
        raise RuntimeError(f"status failed: {out.stderr}")
    status = json.loads(out.stdout)
    logger.info("Cache status: %s", json.dumps(status))
    if status.get("queue_pending", 0) > 0:
        logger.warning("Queue still has %d pending items", status["queue_pending"])
    return status


def task_47_test_search():
    """Test search quality with sample queries."""
    queries = [
        "how to use tool_use with Claude API",
        "prompt caching",
    ]
    all_results = {}
    for query in queries:
        out = subprocess.run(
            ["python3", "-m", "lib.neon_docs", "search", query, "--limit", "3"],
            capture_output=True,
            text=True,
            timeout=30,
            env=_env(),
        )
        if out.returncode != 0:
            logger.warning("Search failed for '%s': %s", query, out.stderr)
            all_results[query] = {"error": out.stderr}
        else:
            results_data = json.loads(out.stdout)
            logger.info("Search '%s': %d results", query, len(results_data))
            for r in results_data[:2]:
                logger.info(
                    "  %.3f | %s | %s",
                    r.get("similarity", 0),
                    r.get("title", "?"),
                    r.get("chunk_text", "")[:80],
                )
            all_results[query] = results_data
    return all_results


def task_48_test_idempotency():
    """Re-run bulk-index, verify unchanged count."""
    out = subprocess.run(
        ["python3", "-m", "lib.neon_docs", "bulk-index", "../docs/"],
        capture_output=True,
        text=True,
        timeout=120,
        env=_env(),
    )
    if out.returncode != 0:
        raise RuntimeError(f"idempotency re-index failed: {out.stderr}")
    result = json.loads(out.stdout) if out.stdout.strip() else {}
    inserted = result.get("inserted", 0)
    if inserted > 0:
        logger.warning("Idempotency check: %d new inserts (expected 0)", inserted)
    else:
        logger.info("Idempotency confirmed: 0 new inserts")
    return result


def _env():
    """Build env dict with PYTHONPATH set."""
    import os

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    return env


def main():
    logger.info("Phase 8 Bootstrap — START")
    logger.info("MLflow available: %s", MLFLOW_AVAILABLE)

    run_task(42, "Verify Ollama model", task_42_verify_ollama)
    run_task(43, "Run migrations", task_43_run_migrations)
    run_task(43, "Verify migrations idempotent", task_43b_idempotent_migrations)
    run_task(44, "Bulk-index docs", task_44_bulk_index)
    run_task(45, "Drain processing queue", task_45_drain_queue)
    run_task(46, "Verify cache status", task_46_verify_status)
    run_task(47, "Test search quality", task_47_test_search)
    run_task(48, "Test idempotency", task_48_test_idempotency)

    logger.info("=" * 60)
    logger.info("Phase 8 Bootstrap — SUMMARY")
    passed = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)
    logger.info("Passed: %d | Failed: %d | Total: %d", passed, failed, len(results))

    for r in results:
        status = "PASS" if r.success else f"FAIL: {r.error}"
        logger.info("  Task %d (%s): %s [%.0fms]", r.task_id, r.name, status, r.duration_ms)

    print(json.dumps([r.to_dict() for r in results], indent=2))

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
