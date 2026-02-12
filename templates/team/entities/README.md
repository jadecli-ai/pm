# Entities

Work items for the {{ team_name }} team.

## Entity Types

| Type | Purpose |
|------|---------|
| task | Individual work item |
| subtask | Part of a task |

## Creating Entities

Each entity must have frontmatter:

```yaml
---
id: "TASK-XXX"
version: "1.0.0"
type: task
status: pending
created: YYYY-MM-DD
updated: YYYY-MM-DD

# Claude Code Alignment
subject: "Short task title"
description: "Full description"
activeForm: "Present participle form (e.g., 'Implementing feature')"

# Hierarchy
parent: "STORY-XXX"

# Dependencies
dependsOn: []
blockedBy: []
blocks: []
---
```

## Examples

See `examples/` for sample entities.
