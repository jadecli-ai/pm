# Entity Hierarchy

> Work item entities with frontmatter for dependency tracking and semver

## Hierarchy

```
Epic (strategic initiative)
  └── Story (user-facing feature)
        └── Task (implementation unit - aligns with Claude Code TaskCreate)
              └── Subtask (atomic work item)
```

## Alignment with Claude Code

The **Task** entity is specifically designed to map 1:1 with Claude Code's built-in task system:

| Entity Field | Claude Code TaskCreate | Purpose |
|--------------|------------------------|---------|
| `subject` | `subject` | Brief title (imperative) |
| `description` | `description` | Detailed requirements |
| `activeForm` | `activeForm` | Present continuous for spinner |
| `status` | `status` | pending/in_progress/completed |
| `blockedBy` | `blockedBy` | Dependency IDs |
| `blocks` | `blocks` | What this blocks |

## Frontmatter Schema

All entities use YAML frontmatter with:

```yaml
---
id: "EPIC-001"           # Unique identifier
version: "1.0.0"         # SemVer for tracking changes
type: epic               # epic|story|task|subtask
status: pending          # pending|in_progress|completed|blocked
created: 2025-02-11
updated: 2025-02-11

# Hierarchy
parent: null             # Parent entity ID
children: []             # Child entity IDs

# Dependencies
dependsOn: []            # IDs this depends on (external)
blocks: []               # IDs this blocks
blockedBy: []            # IDs blocking this (internal hierarchy)

# Ownership
owner: null              # Agent or human owner
domain: null             # frontend|backend|infra|data

# Sizing (for tasks/subtasks)
size: null               # XS|S|M|L|XL
agentHours: null         # Estimated agent execution time

# Metadata
tags: []
priority: null           # P0-P4
iteration: null          # Iteration milestone
---
```

## SemVer Rules

Version bumps indicate:
- **MAJOR (X.0.0)**: Breaking change to acceptance criteria or scope
- **MINOR (0.X.0)**: Added requirements, new subtasks
- **PATCH (0.0.X)**: Clarifications, typo fixes, estimate adjustments

## Dependency Tracking

### `dependsOn` vs `blockedBy`

- **dependsOn**: External dependencies (libraries, APIs, other epics)
- **blockedBy**: Internal hierarchy (parent task, sibling tasks)

### Example

```yaml
---
id: "TASK-005"
dependsOn:
  - "npm:zod@3.22"        # Code dependency
  - "EPIC-002"            # Another epic must complete first
blockedBy:
  - "TASK-004"            # Sibling task in same story
blocks:
  - "TASK-006"            # What this unblocks when done
---
```

## Files

| File | Purpose |
|------|---------|
| `epic.schema.md` | Epic entity schema |
| `story.schema.md` | Story entity schema |
| `task.schema.md` | Task entity schema (Claude Code aligned) |
| `subtask.schema.md` | Subtask entity schema |
| `examples/` | Example entities |
