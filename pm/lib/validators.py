"""Entity validation utilities.

Shared across:
- tests/run-tests.sh
- tests/validate-entity.sh
- Pre-commit hooks
"""

import re
from pathlib import Path
from typing import Any

from .frontmatter import parse_file


# Valid entity types
ENTITY_TYPES = {"epic", "story", "task", "subtask", "library", "agent", "schema", "doc"}

# Valid statuses
STATUSES = {"pending", "in_progress", "completed", "blocked", "active"}

# ID patterns per type
ID_PATTERNS = {
    "epic": r"^EPIC-\d+$",
    "story": r"^STORY-\d+$",
    "task": r"^TASK-\d+$",
    "subtask": r"^SUBTASK-\d+$",
    "library": r"^LIB-\d+$",
}

# SemVer pattern
SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_semver(version: str) -> bool:
    """Validate SemVer format.

    Args:
        version: Version string to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If invalid
    """
    if not re.match(SEMVER_PATTERN, version):
        raise ValidationError(f"Invalid SemVer: {version} (expected X.Y.Z)")
    return True


def validate_id(id_value: str, entity_type: str) -> bool:
    """Validate entity ID format.

    Args:
        id_value: ID string to validate
        entity_type: Type of entity

    Returns:
        True if valid

    Raises:
        ValidationError: If invalid
    """
    pattern = ID_PATTERNS.get(entity_type)
    if pattern and not re.match(pattern, id_value):
        raise ValidationError(
            f"Invalid ID format: {id_value} (expected {entity_type.upper()}-XXX)"
        )
    return True


def validate_entity(path: Path) -> dict[str, Any]:
    """Validate an entity file.

    Args:
        path: Path to entity file

    Returns:
        Parsed frontmatter if valid

    Raises:
        ValidationError: If validation fails
        FileNotFoundError: If file doesn't exist
    """
    if not path.exists():
        raise FileNotFoundError(f"Entity not found: {path}")

    frontmatter = parse_file(path)

    if not frontmatter:
        raise ValidationError(f"No frontmatter in {path}")

    # Required fields
    required = ["id", "version", "type"]
    for field in required:
        if field not in frontmatter:
            raise ValidationError(f"Missing required field: {field}")

    # Validate type
    entity_type = frontmatter["type"]
    if entity_type not in ENTITY_TYPES:
        raise ValidationError(f"Invalid type: {entity_type}")

    # Validate version
    validate_semver(frontmatter["version"])

    # Validate ID format
    validate_id(frontmatter["id"], entity_type)

    # Validate status if present
    if "status" in frontmatter and frontmatter["status"] not in STATUSES:
        raise ValidationError(f"Invalid status: {frontmatter['status']}")

    # Task-specific validation
    if entity_type in ("task", "subtask"):
        if "subject" not in frontmatter:
            raise ValidationError(f"Tasks require 'subject' field")
        if "activeForm" not in frontmatter:
            raise ValidationError(f"Tasks require 'activeForm' field")

    # Non-epic entities need parent
    if entity_type not in ("epic", "library", "agent", "schema", "doc"):
        parent = frontmatter.get("parent")
        if not parent or parent == "null":
            raise ValidationError(f"Non-epic entities require 'parent' field")

    return frontmatter


def validate_dependencies(frontmatter: dict[str, Any], all_ids: set[str]) -> bool:
    """Validate that dependencies reference existing entities.

    Args:
        frontmatter: Parsed frontmatter
        all_ids: Set of all valid entity IDs

    Returns:
        True if valid

    Raises:
        ValidationError: If dependency references non-existent entity
    """
    for dep in frontmatter.get("blockedBy", []):
        if dep.startswith(("npm:", "pip:", "agents/")):
            continue  # External dependencies
        if dep not in all_ids:
            raise ValidationError(f"blockedBy references unknown entity: {dep}")

    for dep in frontmatter.get("blocks", []):
        if dep not in all_ids:
            raise ValidationError(f"blocks references unknown entity: {dep}")

    return True
