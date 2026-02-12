# PM System Index (Pre-computed)

## Quick Reference

```
pm/
├── ENTRYPOINT.md          # Start here - agent team launch guide
├── README.md              # System overview
├── agents/                # Agent definitions
│   ├── vp-product.md      # Opus - owns Epics
│   ├── sdm.md             # Sonnet - owns Stories/Tasks
│   ├── staff-engineer.md  # Sonnet - owns Tasks/Subtasks
│   └── sprint-master.md   # Haiku - ceremonies
├── entities/              # Work item schemas
│   ├── epic.schema.md     # Strategic initiatives
│   ├── story.schema.md    # User features
│   ├── task.schema.md     # Implementation units (Claude Code aligned)
│   ├── subtask.schema.md  # Atomic work
│   └── examples/          # Live entity instances
└── tests/                 # Integration tests
    └── run-tests.sh       # Validates all entities
```

## Entity → Claude Code Mapping

| Entity Field | TaskCreate | TaskUpdate |
|--------------|------------|------------|
| subject | subject | subject |
| description | description | description |
| activeForm | activeForm | activeForm |
| status | - | status |
| blockedBy | - | addBlockedBy |
| blocks | - | addBlocks |

## Frontmatter Template (Task)

```yaml
---
id: "TASK-XXX"
version: "1.0.0"
type: task
status: pending
parent: "STORY-XXX"
dependsOn: []
blockedBy: []
blocks: []
owner: null
size: M
agentHours: 3
subject: "Implement feature X"
activeForm: "Implementing feature X"
---
```

## Version Bumps

- PATCH (+0.0.1): status change, typo fix
- MINOR (+0.1.0): completion, new dependency
- MAJOR (+1.0.0): scope change, breaking AC

## Workflow

1. VP Product creates Epic → `entities/examples/EPIC-XXX.md`
2. SDM breaks into Stories → creates Task entities
3. Staff Engineer: `TaskCreate(subject, description, activeForm)`
4. Work → `TaskUpdate(status="in_progress")`
5. Done → `TaskUpdate(status="completed")` + entity version bump
