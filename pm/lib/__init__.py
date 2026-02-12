"""PM System shared library - reusable code objects."""

__version__ = "1.1.0"

# Review pipeline exports
from .review_generator import (
    Finding,
    Review,
    TaskEntity,
    generate_task_from_finding,
    process_reviews,
    deduplicate_findings,
)

from .assignment_algorithm import (
    assign_files_to_agents,
    TaskFiles,
    Assignment,
    AssignmentResult,
    classify_domain,
    process_assignments,
)
