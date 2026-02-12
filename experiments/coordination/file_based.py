#!/usr/bin/env python3
"""File-based agent coordination pattern.

This pattern uses JSON files in a shared directory for async communication.

Pros:
- Simple, no external dependencies
- Debuggable (can inspect files)
- Good for async workflows

Cons:
- Slower than Redis
- No real-time updates
- File system race conditions possible
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.agent_registry import get_registry
from lib.mlflow_tracing import trace_agent_call


class FileBasedCoordinator:
    """Coordinate agents via shared file system."""

    def __init__(self, work_dir: Path = None):
        self.work_dir = work_dir or Path("/tmp/agent_coordination")
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir = self.work_dir / "tasks"
        self.results_dir = self.work_dir / "results"
        self.tasks_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)

    def create_task(self, task_id: str, agent_type: str, tool_name: str, params: dict) -> Path:
        """Create a task file for an agent to pick up.

        Args:
            task_id: Unique task identifier
            agent_type: Type of agent (gemini, kimi)
            tool_name: Tool to execute
            params: Tool parameters

        Returns:
            Path to task file
        """
        task = {
            "id": task_id,
            "agent_type": agent_type,
            "tool": tool_name,
            "params": params,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

        task_file = self.tasks_dir / f"{task_id}.json"
        task_file.write_text(json.dumps(task, indent=2))

        print(f"✓ Created task: {task_file}")
        return task_file

    def execute_task(self, task_id: str) -> dict:
        """Execute a task by reading its file.

        Args:
            task_id: Task identifier

        Returns:
            Result dict
        """
        task_file = self.tasks_dir / f"{task_id}.json"

        if not task_file.exists():
            return {"success": False, "error": f"Task not found: {task_id}"}

        # Read task
        task = json.loads(task_file.read_text())

        print(f"→ Executing task {task_id}: {task['tool']}")

        # Update status to running
        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat()
        task_file.write_text(json.dumps(task, indent=2))

        # Execute via registry
        registry = get_registry()

        with trace_agent_call(task["agent_type"], task["tool"], task_id=task_id):
            result = registry.execute_tool(task["tool"], **task["params"])

        # Write result
        result_data = {
            "task_id": task_id,
            "result": result,
            "completed_at": datetime.now().isoformat()
        }

        result_file = self.results_dir / f"{task_id}_result.json"
        result_file.write_text(json.dumps(result_data, indent=2))

        # Update task status
        task["status"] = "completed" if result.get("success") else "failed"
        task["completed_at"] = datetime.now().isoformat()
        task_file.write_text(json.dumps(task, indent=2))

        print(f"✓ Task {task_id} completed: {task['status']}")

        return result

    def wait_for_result(self, task_id: str, timeout: int = 30) -> dict:
        """Wait for a task result to be written.

        Args:
            task_id: Task identifier
            timeout: Max seconds to wait

        Returns:
            Result dict
        """
        result_file = self.results_dir / f"{task_id}_result.json"

        start = time.time()
        while (time.time() - start) < timeout:
            if result_file.exists():
                return json.loads(result_file.read_text())
            time.sleep(0.5)

        return {"success": False, "error": f"Timeout waiting for {task_id}"}

    def fan_out_parallel(self, tasks: list[dict]) -> list[dict]:
        """Execute multiple tasks in parallel (simulated async).

        Args:
            tasks: List of task dicts with: agent_type, tool, params

        Returns:
            List of results
        """
        print(f"\n=== Fan-Out: {len(tasks)} tasks ===")

        # Create all tasks
        task_ids = []
        for i, task in enumerate(tasks):
            task_id = f"task_{int(time.time())}_{i}"
            self.create_task(
                task_id,
                task["agent_type"],
                task["tool"],
                task["params"]
            )
            task_ids.append(task_id)

        # Execute all (in real parallel scenario, spawn threads/processes)
        results = []
        for task_id in task_ids:
            result = self.execute_task(task_id)
            results.append(result)

        print(f"✓ Fan-Out complete: {len(results)} results\n")
        return results


def demo_file_coordination():
    """Demonstrate file-based coordination."""
    print("=" * 60)
    print("File-Based Agent Coordination Demo")
    print("=" * 60)

    coordinator = FileBasedCoordinator()

    # Example 1: Single task
    print("\n### Example 1: Single Task Execution ###\n")

    task_id = coordinator.create_task(
        "analyze_code",
        "kimi",
        "kimi_load_codebase",
        {
            "files": ["lib/gemini/multimodal.py"],
            "query": "Summarize this code"
        }
    )

    result = coordinator.execute_task("analyze_code")
    print(f"Result: {result['success']}")
    if result['success']:
        print(f"Output: {result['output'][:100]}...")

    # Example 2: Fan-out parallel
    print("\n### Example 2: Fan-Out Parallel Execution ###\n")

    tasks = [
        {
            "agent_type": "kimi",
            "tool": "kimi_load_codebase",
            "params": {"files": ["lib/gemini/multimodal.py"], "query": "Count functions"}
        },
        {
            "agent_type": "kimi",
            "tool": "kimi_load_codebase",
            "params": {"files": ["lib/kimi/long_context.py"], "query": "Count functions"}
        }
    ]

    results = coordinator.fan_out_parallel(tasks)

    print("\n### Results Summary ###")
    for i, result in enumerate(results):
        status = "✓" if result.get("success") else "✗"
        print(f"{status} Task {i+1}: {result.get('success', False)}")

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print(f"\nTask files: {coordinator.tasks_dir}")
    print(f"Result files: {coordinator.results_dir}")


if __name__ == "__main__":
    demo_file_coordination()
