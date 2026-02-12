"""File assignment algorithm for conflict-free parallel implementation.

Assigns files to agents based on domain ownership and detects conflicts
that require serialized execution.

schema: task
depends_on:
  - pm/lib/frontmatter.py
  - pm/lib/review_generator.py
depended_by:
  - pm/agents/assignment-manager.md
semver: minor
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .frontmatter import parse_frontmatter, get_body


# Domain to agent mapping
DOMAIN_AGENT_MAP: dict[str, str] = {
    "auth": "staff-engineer-1",
    "api": "staff-engineer-2",
    "db": "staff-engineer-3",
    "data": "staff-engineer-3",
    "frontend": "staff-engineer-4",
    "tests": "tester-1",
    "testing": "tester-1",
    "infrastructure": "infra-engineer",
    "infra": "infra-engineer",
    "backend": "staff-engineer-1",  # Default fallback
}

# Path patterns for domain classification
DOMAIN_PATTERNS: list[tuple[str, str]] = [
    (r"src/auth/|src/middleware/auth", "auth"),
    (r"src/api/|src/routes/", "api"),
    (r"src/db/|migrations/|src/repositories/", "data"),
    (r"app/|src/components/|src/pages/|src/views/", "frontend"),
    (r"tests/|__tests__/|\.test\.|_test\.", "testing"),
    (r"\.github/|scripts/|infra/|docker/|k8s/", "infrastructure"),
    (r"src/utils/|src/lib/|src/shared/", "shared"),  # Conflict zone
]


@dataclass
class TaskFiles:
    """Files associated with a task."""

    task_id: str
    priority: str
    files: list[str] = field(default_factory=list)
    domain: str = ""


@dataclass
class Assignment:
    """Assignment of files to an agent."""

    agent: str
    domain: str
    files: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)
    estimated_hours: float = 0.0


@dataclass
class Conflict:
    """A conflict where multiple tasks touch the same file."""

    file: str
    tasks: list[str] = field(default_factory=list)
    resolution: str = ""
    blocked_by_added: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class AssignmentResult:
    """Complete assignment result."""

    branch: str
    assignments: dict[str, Assignment] = field(default_factory=dict)
    serialized: dict[str, dict[str, Any]] = field(default_factory=dict)
    conflicts: list[Conflict] = field(default_factory=list)
    parallel_groups: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Convert to JSON string for assignments.json."""
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "branch": self.branch,
            "generated": datetime.now(timezone.utc).isoformat(),
            "assignments": {
                agent: {
                    "domain": a.domain,
                    "files": a.files,
                    "tasks": a.tasks,
                    "estimated_hours": a.estimated_hours,
                }
                for agent, a in self.assignments.items()
            },
            "serialized": self.serialized,
            "conflicts": [
                {
                    "file": c.file,
                    "tasks": c.tasks,
                    "resolution": c.resolution,
                }
                for c in self.conflicts
            ],
            "parallel_groups": self.parallel_groups,
            "stats": self.stats,
        }


def classify_domain(file_path: str) -> str:
    """Classify file into a domain based on path patterns.

    Args:
        file_path: Path to the file

    Returns:
        Domain name (auth, api, data, frontend, testing, infrastructure, shared, backend)
    """
    path = file_path.lower()

    for pattern, domain in DOMAIN_PATTERNS:
        if re.search(pattern, path):
            return domain

    return "backend"  # Default


def extract_files_from_task(task_path: Path) -> list[str]:
    """Extract file paths from a task entity's body.

    Parses the Files section looking for patterns like:
    - `path/to/file.ts` - Create
    - `path/to/file.ts` - Modify

    Args:
        task_path: Path to TASK-XXX.md file

    Returns:
        List of file paths mentioned in the task
    """
    content = task_path.read_text(encoding="utf-8", errors="ignore")
    body = get_body(content)

    files: list[str] = []

    # Pattern: - `path/to/file` - Action
    file_list_pattern = r"-\s*`([^`]+)`\s*-\s*\w+"
    files.extend(re.findall(file_list_pattern, body))

    # Pattern: **File**: `path/to/file:lines`
    file_ref_pattern = r"\*\*File\*\*:\s*`([^`:]+)"
    files.extend(re.findall(file_ref_pattern, body))

    # Pattern: in finding references like "in {file}"
    inline_pattern = r"in\s+`([^`]+\.[a-z]+)`"
    files.extend(re.findall(inline_pattern, body, re.IGNORECASE))

    # Deduplicate while preserving order
    seen = set()
    unique_files = []
    for f in files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)

    return unique_files


def find_conflicts(task_files: dict[str, list[str]]) -> dict[str, list[str]]:
    """Find files that appear in multiple tasks.

    Args:
        task_files: Mapping of task_id -> list of files

    Returns:
        Mapping of file -> list of task_ids that reference it
    """
    file_to_tasks: dict[str, list[str]] = defaultdict(list)

    for task_id, files in task_files.items():
        for file in files:
            file_to_tasks[file].append(task_id)

    # Only return files with multiple tasks
    return {f: tasks for f, tasks in file_to_tasks.items() if len(tasks) > 1}


def sort_tasks_by_priority(
    task_ids: list[str],
    task_priorities: dict[str, str],
) -> list[str]:
    """Sort task IDs by priority (P0 first) then by ID.

    Args:
        task_ids: List of task IDs to sort
        task_priorities: Mapping of task_id -> priority

    Returns:
        Sorted list of task IDs
    """
    def priority_key(task_id: str) -> tuple[int, str]:
        priority = task_priorities.get(task_id, "P2")
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        return (priority_order.get(priority, 2), task_id)

    return sorted(task_ids, key=priority_key)


def form_parallel_groups(
    task_ids: list[str],
    blocked_by: dict[str, set[str]],
) -> list[list[str]]:
    """Form groups of tasks that can execute in parallel.

    Uses topological sorting to group tasks with no dependencies
    in the same group.

    Args:
        task_ids: All task IDs
        blocked_by: Mapping of task_id -> set of blocking task_ids

    Returns:
        List of groups, each group can run in parallel
    """
    groups: list[list[str]] = []
    remaining = set(task_ids)
    completed: set[str] = set()

    while remaining:
        # Find tasks with no blockers in remaining set
        ready = {
            t for t in remaining
            if not (blocked_by.get(t, set()) - completed)
        }

        if not ready:
            # Circular dependency - shouldn't happen, but break to avoid infinite loop
            groups.append(sorted(remaining))
            break

        groups.append(sorted(ready))
        completed.update(ready)
        remaining -= ready

    return groups


def assign_files_to_agents(
    tasks: list[TaskFiles],
    branch: str,
) -> AssignmentResult:
    """Main assignment algorithm.

    Assigns files to agents by domain, detects conflicts,
    and creates serialization order for shared files.

    Args:
        tasks: List of TaskFiles with their file lists
        branch: Branch name for the result

    Returns:
        AssignmentResult with assignments and conflict info
    """
    result = AssignmentResult(branch=branch)

    # Build task -> files mapping
    task_files: dict[str, list[str]] = {t.task_id: t.files for t in tasks}
    task_priorities: dict[str, str] = {t.task_id: t.priority for t in tasks}

    # Get all unique files
    all_files: set[str] = set()
    for files in task_files.values():
        all_files.update(files)

    # Classify files by domain
    file_domains: dict[str, str] = {f: classify_domain(f) for f in all_files}

    # Initial assignment by domain
    agent_files: dict[str, set[str]] = defaultdict(set)
    agent_domains: dict[str, str] = {}

    for file, domain in file_domains.items():
        agent = DOMAIN_AGENT_MAP.get(domain, "staff-engineer-1")

        # Handle shared domain - assign to first task's domain agent
        if domain == "shared":
            for task in tasks:
                if file in task.files:
                    task_domain = task.domain or "backend"
                    agent = DOMAIN_AGENT_MAP.get(task_domain, "staff-engineer-1")
                    break

        agent_files[agent].add(file)
        if agent not in agent_domains:
            agent_domains[agent] = domain

    # Find conflicts
    conflicts = find_conflicts(task_files)
    blocked_by: dict[str, set[str]] = defaultdict(set)

    for file, conflicting_tasks in conflicts.items():
        # Sort by priority
        ordered = sort_tasks_by_priority(conflicting_tasks, task_priorities)

        # Create serialization: later tasks blocked by earlier ones
        for i, task_id in enumerate(ordered[1:], 1):
            blocked_by[task_id].add(ordered[i - 1])

        conflict = Conflict(
            file=file,
            tasks=conflicting_tasks,
            resolution=f"Serialize: {' then '.join(ordered)}",
            blocked_by_added={
                ordered[i]: [ordered[i - 1]]
                for i in range(1, len(ordered))
            },
        )
        result.conflicts.append(conflict)

        # Record in serialized
        result.serialized[file] = {
            "tasks": ordered,
            "order": ordered,
            "reason": "Shared file requires sequential execution",
            "blockedBy_added": conflict.blocked_by_added,
        }

    # Build assignments
    for agent, files in agent_files.items():
        # Find tasks that touch these files
        agent_tasks = []
        for task in tasks:
            if any(f in files for f in task.files):
                if task.task_id not in agent_tasks:
                    agent_tasks.append(task.task_id)

        # Estimate hours (0.5 per task)
        hours = len(agent_tasks) * 0.5

        result.assignments[agent] = Assignment(
            agent=agent,
            domain=agent_domains.get(agent, "backend"),
            files=sorted(files),
            tasks=agent_tasks,
            estimated_hours=hours,
        )

    # Form parallel groups
    all_task_ids = [t.task_id for t in tasks]
    groups = form_parallel_groups(all_task_ids, blocked_by)

    for i, group in enumerate(groups, 1):
        result.parallel_groups.append({
            "group": i,
            "tasks": group,
            "can_start_immediately": i == 1,
        })

    # Stats
    result.stats = {
        "total_files": len(all_files),
        "total_tasks": len(tasks),
        "agents_needed": len(result.assignments),
        "conflicts_found": len(conflicts),
        "max_parallelism": max(len(g) for g in groups) if groups else 0,
    }

    return result


def load_tasks_from_directory(task_dir: Path) -> list[TaskFiles]:
    """Load TaskFiles from a directory of TASK-*.md files.

    Args:
        task_dir: Directory containing task entity files

    Returns:
        List of TaskFiles with extracted file lists
    """
    tasks: list[TaskFiles] = []

    for task_path in task_dir.glob("TASK-*.md"):
        content = task_path.read_text(encoding="utf-8", errors="ignore")
        frontmatter = parse_frontmatter(content)

        task_id = frontmatter.get("id", task_path.stem)
        priority = frontmatter.get("priority", "P2")
        domain = frontmatter.get("domain", "")

        files = extract_files_from_task(task_path)

        tasks.append(TaskFiles(
            task_id=task_id,
            priority=priority,
            files=files,
            domain=domain,
        ))

    return tasks


def process_assignments(
    task_dir: Path,
    output_path: Path,
    branch: str,
) -> AssignmentResult:
    """Full pipeline: load tasks, assign, write output.

    Args:
        task_dir: Directory containing TASK-*.md files
        output_path: Path to write assignments.json
        branch: Branch name

    Returns:
        AssignmentResult
    """
    tasks = load_tasks_from_directory(task_dir)
    result = assign_files_to_agents(tasks, branch)

    output_path.write_text(result.to_json(), encoding="utf-8")

    return result
