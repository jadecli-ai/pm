"""YAML frontmatter parsing utilities.

Shared across:
- .index/generate-merkle.py
- tests/validate-entity.sh (via Python)
- scripts/architecture/generate.py
"""

import re
from pathlib import Path
from typing import Any


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Extract YAML frontmatter from markdown content.

    Args:
        content: Full markdown file content

    Returns:
        Dict of frontmatter fields, empty if no frontmatter

    Raises:
        ValueError: If frontmatter is malformed
    """
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    frontmatter = {}
    current_key = None
    current_list = None

    for line in match.group(1).split("\n"):
        line = line.rstrip()

        # Skip empty lines
        if not line:
            continue

        # List item
        if line.startswith("  - "):
            if current_list is not None:
                current_list.append(line[4:].strip().strip('"').strip("'"))
            continue

        # New key
        if ":" in line:
            # Save previous list if any
            if current_key and current_list is not None:
                frontmatter[current_key] = current_list
                current_list = None

            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            # Check if starting a list
            if value == "" or value == "[]":
                current_key = key
                current_list = []
            else:
                # Scalar value
                value = value.strip('"').strip("'")
                frontmatter[key] = value
                current_key = key

    # Save final list if any
    if current_key and current_list is not None:
        frontmatter[current_key] = current_list

    return frontmatter


def parse_file(path: Path) -> dict[str, Any]:
    """Parse frontmatter from a file path.

    Args:
        path: Path to markdown file

    Returns:
        Dict of frontmatter fields

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If frontmatter is malformed
    """
    content = path.read_text(encoding="utf-8", errors="ignore")
    return parse_frontmatter(content)


def extract_dependencies(frontmatter: dict[str, Any]) -> dict[str, list[str]]:
    """Extract all dependency fields from frontmatter.

    Returns:
        Dict with keys: dependsOn, dependedBy, blocks, blockedBy
    """
    return {
        "dependsOn": frontmatter.get("dependsOn", []),
        "dependedBy": frontmatter.get("dependedBy", []),
        "blocks": frontmatter.get("blocks", []),
        "blockedBy": frontmatter.get("blockedBy", []),
    }


def get_body(content: str) -> str:
    """Extract markdown body (everything after frontmatter).

    Args:
        content: Full markdown file content

    Returns:
        Body content without frontmatter
    """
    match = re.match(r"^---\n.*?\n---\n?", content, re.DOTALL)
    if match:
        return content[match.end():]
    return content
