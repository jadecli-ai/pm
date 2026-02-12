---
id: "LIB-001"
version: "1.0.0"
type: library
status: active
created: 2026-02-11
updated: 2026-02-11
dependsOn: []
dependedBy:
  - "tests/run-tests.sh"
  - "tests/validate-entity.sh"
  - ".index/generate-merkle.py"
  - "scripts/architecture/generate.py"
---

# Shared Library (`lib/`)

> Reusable code objects - single source of truth per Anthropic patterns

## Philosophy

Per [Anthropic Engineering](https://www.anthropic.com/engineering):
- **Single Definition**: Each concept defined once, imported everywhere
- **Explicit Dependencies**: Frontmatter tracks what uses what
- **Fail Fast Validation**: Shared validators crash early

## Structure

```
lib/
├── frontmatter.py       # YAML frontmatter parser
├── validators.py        # Entity validation functions
├── merkle.py            # Merkle tree utilities
├── architecture.py      # Architecture diagram generation
└── constants.py         # Shared constants and enums
```

## Usage

```python
from lib.frontmatter import parse_frontmatter, extract_dependencies
from lib.validators import validate_entity, validate_semver
from lib.merkle import hash_file, hash_directory
from lib.architecture import generate_mermaid, generate_html
```

## Import Convention

All scripts MUST import from `lib/` rather than duplicating logic:

```python
# ✓ Good
from lib.validators import validate_entity

# ✗ Bad - duplicating validation logic inline
def validate_entity(path):  # Don't do this
    ...
```
