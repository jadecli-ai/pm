"""Review finding to Task entity conversion.

Converts structured findings from review agents into Task entities
that align with Claude Code's TaskCreate system.

schema: task
depends_on:
  - pm/lib/frontmatter.py
depended_by:
  - pm/agents/review-synthesizer.md
semver: minor
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .frontmatter import parse_frontmatter, get_body


@dataclass
class Finding:
    """A single review finding."""

    id: str
    priority: str  # P0, P1, P2, P3
    confidence: int  # 0-100
    category: str
    file: str
    lines: list[int] = field(default_factory=list)
    title: str = ""
    description: str = ""
    suggestion: str = ""
    source_review: str = ""
    generated_task: str | None = None

    @property
    def is_task_eligible(self) -> bool:
        """Check if finding qualifies for automatic task generation."""
        return (
            self.priority in ("P0", "P1")
            and self.confidence >= 80
            and bool(self.suggestion)
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any], source_review: str) -> "Finding":
        """Create Finding from parsed JSON dict."""
        return cls(
            id=data.get("id", ""),
            priority=data.get("priority", "P2"),
            confidence=data.get("confidence", 0),
            category=data.get("category", "unknown"),
            file=data.get("file", ""),
            lines=data.get("lines", []),
            title=data.get("title", ""),
            description=data.get("description", ""),
            suggestion=data.get("suggestion", ""),
            source_review=source_review,
            generated_task=data.get("generated_task"),
        )


@dataclass
class Review:
    """A review entity with its findings."""

    id: str
    review_type: str  # test, value, mlflow
    branch: str
    commit: str
    findings: list[Finding] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: Path) -> "Review":
        """Parse Review from markdown file."""
        content = path.read_text(encoding="utf-8", errors="ignore")
        frontmatter = parse_frontmatter(content)
        body = get_body(content)

        review = cls(
            id=frontmatter.get("id", path.stem),
            review_type=frontmatter.get("review_type", "unknown"),
            branch=frontmatter.get("branch", ""),
            commit=frontmatter.get("commit", ""),
        )

        # Extract findings JSON from body
        findings_json = extract_findings_json(body)
        if findings_json:
            for f_data in findings_json.get("findings", []):
                review.findings.append(Finding.from_dict(f_data, review.id))
            review.metrics = findings_json.get("metrics", {})

        return review


@dataclass
class TaskEntity:
    """A Task entity compatible with pm/entities/task.schema.md."""

    id: str
    subject: str
    description: str
    active_form: str
    priority: str
    domain: str
    size: str = "XS"
    agent_hours: float = 0.5
    source_review: str = ""
    source_finding: str = ""
    tags: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Generate markdown file content for the task entity."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        tags_yaml = "\n".join(f'  - "{tag}"' for tag in self.tags) if self.tags else ""

        return f'''---
id: "{self.id}"
version: "1.0.0"
type: task
status: pending
created: {now}
updated: {now}

parent: null
children: []

dependsOn: []
blocks: []
blockedBy: []

owner: null
domain: "{self.domain}"

priority: "{self.priority}"
iteration: null
size: "{self.size}"
agentHours: {self.agent_hours}

source_review: "{self.source_review}"
source_finding: "{self.source_finding}"

subject: "{self.subject}"
activeForm: "{self.active_form}"

tags:
{tags_yaml}
---

# {self.subject}

## Objective

{self.description}

## Source

- Review: `{self.source_review}`
- Finding: `{self.source_finding}`

## Files

<!-- Files to modify based on finding -->

## Test Requirements

<!-- Tests to add/modify -->
'''


def extract_findings_json(body: str) -> dict[str, Any] | None:
    """Extract JSON block containing findings from review body.

    Looks for fenced JSON blocks with findings array.
    """
    # Match ```json ... ``` blocks
    json_blocks = re.findall(r"```json\n(.*?)\n```", body, re.DOTALL)

    for block in json_blocks:
        try:
            data = json.loads(block)
            if "findings" in data:
                return data
        except json.JSONDecodeError:
            continue

    return None


def infer_domain(file_path: str) -> str:
    """Infer domain from file path.

    Maps file paths to domains for task assignment.
    """
    path = file_path.lower()

    domain_patterns = [
        (r"src/auth/|src/middleware/auth", "auth"),
        (r"src/api/|src/routes/", "api"),
        (r"src/db/|migrations/", "data"),
        (r"app/|src/components/|src/pages/", "frontend"),
        (r"tests/", "testing"),
        (r"\.github/|scripts/|infra/", "infrastructure"),
    ]

    for pattern, domain in domain_patterns:
        if re.search(pattern, path):
            return domain

    return "backend"  # Default


def generate_task_id(existing_ids: set[str]) -> str:
    """Generate next available TASK-XXX id.

    Args:
        existing_ids: Set of existing task IDs

    Returns:
        Next available ID like "TASK-101"
    """
    max_num = 100  # Start from TASK-101
    for task_id in existing_ids:
        match = re.match(r"TASK-(\d+)", task_id)
        if match:
            max_num = max(max_num, int(match.group(1)))

    return f"TASK-{max_num + 1}"


def generate_task_from_finding(
    finding: Finding,
    existing_task_ids: set[str],
) -> TaskEntity:
    """Create TaskEntity from a review finding.

    Args:
        finding: The finding to convert
        existing_task_ids: Set of existing task IDs to avoid collisions

    Returns:
        TaskEntity ready to write to file
    """
    task_id = generate_task_id(existing_task_ids)

    # Determine sizing based on priority
    if finding.priority == "P0":
        size = "S"
        agent_hours = 1.0
    else:  # P1
        size = "XS"
        agent_hours = 0.5

    # Build description
    description_parts = []
    if finding.description:
        description_parts.append(finding.description)
    if finding.suggestion:
        description_parts.append(f"\n**Suggestion**: {finding.suggestion}")

    return TaskEntity(
        id=task_id,
        subject=f"Fix {finding.category}: {finding.title}",
        description="\n".join(description_parts),
        active_form=f"Fixing {finding.category} in {finding.file}",
        priority=finding.priority,
        domain=infer_domain(finding.file),
        size=size,
        agent_hours=agent_hours,
        source_review=finding.source_review,
        source_finding=finding.id,
        tags=["review-fix", finding.category, finding.priority.lower()],
    )


def process_reviews(
    review_dir: Path,
    output_dir: Path,
    existing_task_ids: set[str] | None = None,
) -> list[TaskEntity]:
    """Process all reviews in a directory and generate tasks.

    Args:
        review_dir: Directory containing REVIEW-*.md files
        output_dir: Directory to write generated TASK-*.md files
        existing_task_ids: Optional set of existing task IDs

    Returns:
        List of generated TaskEntity objects
    """
    if existing_task_ids is None:
        existing_task_ids = set()

    # Collect all findings
    all_findings: list[Finding] = []

    for review_file in review_dir.glob("REVIEW-*.md"):
        review = Review.from_file(review_file)
        all_findings.extend(review.findings)

    # Filter eligible findings
    eligible = [f for f in all_findings if f.is_task_eligible]

    # Sort by priority (P0 first) then confidence (highest first)
    eligible.sort(
        key=lambda f: (0 if f.priority == "P0" else 1, -f.confidence)
    )

    # Generate tasks (max 10)
    generated_tasks: list[TaskEntity] = []
    current_ids = existing_task_ids.copy()

    for finding in eligible[:10]:
        task = generate_task_from_finding(finding, current_ids)
        current_ids.add(task.id)

        # Write task file
        task_path = output_dir / f"{task.id}.md"
        task_path.write_text(task.to_markdown(), encoding="utf-8")

        # Update finding with generated task ID
        finding.generated_task = task.id
        generated_tasks.append(task)

    return generated_tasks


def deduplicate_findings(findings: list[Finding]) -> list[Finding]:
    """Deduplicate overlapping findings.

    Merge findings that reference the same file and have similar issues.

    Args:
        findings: List of findings from multiple reviews

    Returns:
        Deduplicated list with merged findings
    """
    # Group by (file, category)
    groups: dict[tuple[str, str], list[Finding]] = {}

    for finding in findings:
        key = (finding.file, finding.category)
        if key not in groups:
            groups[key] = []
        groups[key].append(finding)

    # Merge groups
    unique: list[Finding] = []

    for key, group in groups.items():
        if len(group) == 1:
            unique.append(group[0])
        else:
            # Merge: keep highest confidence, combine descriptions
            merged = merge_findings(group)
            unique.append(merged)

    return unique


def merge_findings(findings: list[Finding]) -> Finding:
    """Merge multiple findings into one.

    Uses highest confidence and priority, combines descriptions.
    """
    # Sort by priority then confidence
    findings.sort(key=lambda f: (0 if f.priority == "P0" else 1, -f.confidence))
    primary = findings[0]

    # Combine descriptions
    descriptions = [f.description for f in findings if f.description]
    combined_desc = "\n\n".join(descriptions) if descriptions else primary.description

    # Combine suggestions
    suggestions = [f.suggestion for f in findings if f.suggestion]
    combined_suggestion = "\n".join(suggestions) if suggestions else primary.suggestion

    # Combine source reviews
    sources = list(set(f.source_review for f in findings))
    source_ref = ", ".join(sources)

    return Finding(
        id=primary.id,
        priority=primary.priority,
        confidence=max(f.confidence for f in findings),
        category=primary.category,
        file=primary.file,
        lines=primary.lines,
        title=primary.title,
        description=f"{combined_desc}\n\n(Merged from: {source_ref})",
        suggestion=combined_suggestion,
        source_review=sources[0],  # Primary source
    )
