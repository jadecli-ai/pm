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
│   ├── sprint-master.md   # Haiku - ceremonies
│   ├── test-reviewer.md   # Opus - test coverage review
│   ├── value-reviewer.md  # Opus - business value review
│   ├── mlflow-analyzer.md # Opus - trace analysis
│   ├── review-synthesizer.md # Sonnet - merge findings
│   └── assignment-manager.md # Haiku - file assignment
├── entities/              # Work item schemas
│   ├── epic.schema.md     # Strategic initiatives
│   ├── story.schema.md    # User features
│   ├── task.schema.md     # Implementation units (Claude Code aligned)
│   ├── subtask.schema.md  # Atomic work
│   └── examples/          # Live entity instances
├── lib/                   # Shared Python libraries
│   ├── review_generator.py    # Findings → Task conversion
│   └── assignment_algorithm.py # File → Agent mapping
└── tests/                 # Integration tests
    └── run-tests.sh       # Validates all entities

reviews/                   # Automated review output
├── review.schema.md       # Review entity schema
├── .index/
│   └── merkle-tree.json   # Change detection
└── {branch}/              # Per-branch review results
    ├── REVIEW-test-*.md   # Test reviewer findings
    ├── REVIEW-value-*.md  # Value reviewer findings
    ├── REVIEW-mlflow-*.md # MLflow analyzer findings
    ├── summary.json       # Aggregated findings
    └── assignments.json   # File → Agent mapping
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

## Review Agents

Automated review pipeline for quality assurance:

| Agent | Model | Focus | Output |
|-------|-------|-------|--------|
| test-reviewer | Opus | Coverage, test quality | REVIEW-test-*.md |
| value-reviewer | Opus | Architecture, security | REVIEW-value-*.md |
| mlflow-analyzer | Opus | Cost, latency, errors | REVIEW-mlflow-*.md |
| review-synthesizer | Sonnet | Merge findings, generate tasks | summary.json |
| assignment-manager | Haiku | File → agent mapping | assignments.json |

### Review Pipeline Levels

| Level | Command | Description |
|-------|---------|-------------|
| L0 | `/review l0-{type}` | Single reviewer |
| L1 | `/review l1-parallel` | All 3 reviewers in parallel |
| L2 | `/review l2-full` | + synthesis + task generation |
| L3 | `/review l3-implement` | + parallel implementation |

### Task Generation Rules

Tasks auto-generated when:
- Priority: P0 or P1
- Confidence: >= 80%
- Has concrete suggestion

Generated tasks include `source_review` and `source_finding` for traceability.
