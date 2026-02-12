#!/usr/bin/env python3
"""Redis-based agent coordination pattern.

This pattern uses Redis for real-time, stateful coordination.

Pros:
- Real-time updates
- Pub/sub for notifications
- Atomic operations
- Shared state

Cons:
- Requires Redis server
- More complex setup
- Network dependency
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisCoordinator:
    """Coordinate agents via Redis."""

    def __init__(self, host: str = "localhost", port: int = 6379):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis not installed. Run: pip install redis")

        self.client = redis.Redis(host=host, port=port, decode_responses=True)
        self.task_hash = "agent_tasks"
        self.result_hash = "agent_results"
        self.queue_key = "task_queue"

    def create_task(self, task_id: str, agent_type: str, tool_name: str, params: dict):
        """Create task in Redis.

        Args:
            task_id: Unique task identifier
            agent_type: Type of agent
            tool_name: Tool to execute
            params: Tool parameters
        """
        task = {
            "id": task_id,
            "agent_type": agent_type,
            "tool": tool_name,
            "params": params,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

        # Store task
        self.client.hset(self.task_hash, task_id, json.dumps(task))

        # Add to queue
        self.client.lpush(self.queue_key, task_id)

        print(f"✓ Created task in Redis: {task_id}")

    def get_next_task(self) -> Optional[dict]:
        """Get next task from queue (blocking).

        Returns:
            Task dict or None
        """
        # Pop from queue (non-blocking for demo)
        task_id = self.client.rpop(self.queue_key)

        if not task_id:
            return None

        # Get task details
        task_json = self.client.hget(self.task_hash, task_id)
        if not task_json:
            return None

        return json.loads(task_json)

    def execute_task(self, task_id: str) -> dict:
        """Execute a task from Redis.

        Args:
            task_id: Task identifier

        Returns:
            Result dict
        """
        from lib.agent_registry import get_registry
        from lib.mlflow_tracing import trace_agent_call

        # Get task
        task_json = self.client.hget(self.task_hash, task_id)
        if not task_json:
            return {"success": False, "error": f"Task not found: {task_id}"}

        task = json.loads(task_json)

        print(f"→ Executing Redis task {task_id}: {task['tool']}")

        # Update status
        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat()
        self.client.hset(self.task_hash, task_id, json.dumps(task))

        # Execute
        registry = get_registry()

        with trace_agent_call(task["agent_type"], task["tool"], task_id=task_id):
            result = registry.execute_tool(task["tool"], **task["params"])

        # Store result
        result_data = {
            "task_id": task_id,
            "result": result,
            "completed_at": datetime.now().isoformat()
        }

        self.client.hset(self.result_hash, task_id, json.dumps(result_data))

        # Update task
        task["status"] = "completed" if result.get("success") else "failed"
        task["completed_at"] = datetime.now().isoformat()
        self.client.hset(self.task_hash, task_id, json.dumps(task))

        print(f"✓ Redis task {task_id} completed: {task['status']}")

        return result

    def get_result(self, task_id: str) -> Optional[dict]:
        """Get result for a task.

        Args:
            task_id: Task identifier

        Returns:
            Result dict or None
        """
        result_json = self.client.hget(self.result_hash, task_id)
        if not result_json:
            return None

        return json.loads(result_json)

    def get_task_status(self, task_id: str) -> str:
        """Get task status.

        Args:
            task_id: Task identifier

        Returns:
            Status string
        """
        task_json = self.client.hget(self.task_hash, task_id)
        if not task_json:
            return "not_found"

        task = json.loads(task_json)
        return task.get("status", "unknown")


def demo_redis_coordination():
    """Demonstrate Redis-based coordination."""
    print("=" * 60)
    print("Redis-Based Agent Coordination Demo")
    print("=" * 60)

    try:
        coordinator = RedisCoordinator()
    except Exception as e:
        print(f"\n✗ Redis not available: {e}")
        print("\nTo use Redis coordination:")
        print("1. Install Redis: pip install redis")
        print("2. Start Redis server: redis-server")
        print("3. Run this script again")
        return

    # Test connection
    try:
        coordinator.client.ping()
        print("\n✓ Redis connection successful\n")
    except Exception as e:
        print(f"\n✗ Redis connection failed: {e}")
        return

    # Example 1: Create and execute task
    print("### Example 1: Single Task ###\n")

    coordinator.create_task(
        "redis_task_1",
        "kimi",
        "kimi_load_codebase",
        {
            "files": ["lib/agent_registry.py"],
            "query": "Summarize this module"
        }
    )

    result = coordinator.execute_task("redis_task_1")
    print(f"Result: {result['success']}")

    # Example 2: Multiple tasks
    print("\n### Example 2: Multiple Tasks ###\n")

    for i in range(3):
        coordinator.create_task(
            f"redis_task_{i+2}",
            "kimi",
            "kimi_load_codebase",
            {
                "files": [f"lib/gemini/multimodal.py"],
                "query": f"Analysis {i+1}"
            }
        )

    # Process queue
    print("\nProcessing task queue...")
    while True:
        task = coordinator.get_next_task()
        if not task:
            break

        coordinator.execute_task(task["id"])

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo_redis_coordination()
