---
id: "ARCH-001"
version: "1.0.0"
type: doc
status: active
created: 2026-02-11
updated: 2026-02-11
dependsOn: []
dependedBy: []
---

# PM System Architecture

> Auto-generated - DO NOT EDIT MANUALLY
>
> Regenerate with: `python scripts/architecture/generate.py`

## Organization Context

```
jadecli-ai/
├── pm/              ← This repository
│   ├── agents/      # AI agent definitions
│   ├── entities/    # Work item hierarchy
│   ├── lib/         # Shared code
│   └── ...
└── (future repos)
```

## System Layers

| Layer | Purpose | Components |
|-------|---------|------------|
| **Frontend** | Documentation, UI | 0 |
| **Middleware** | Agents, orchestration | 4 |
| **Backend** | Scripts, tests, lib | 2 |
| **Data** | Entities, index | 2 |

## Component Diagram

```mermaid
flowchart TB

    subgraph Frontend["Frontend Layer"]
    end

    subgraph Middleware["Middleware Layer"]
        agents/staff_engineer.md["staff-engineer"]
        agents/sprint_master.md["sprint-master"]
        agents/vp_product.md["vp-product"]
        agents/sdm.md["sdm"]
    end

    subgraph Backend["Backend Layer"]
        LIB_001["README"]
        PROMPT_001["PROMPT"]
    end

    subgraph Data["Data Layer"]
        EPIC_001["EPIC-001"]
        TASK_004["TASK-004"]
    end

    %% Dependencies
    TASK_004 --> TASK_003
    PROMPT_001 --> lib_architecture_py
    PROMPT_001 --> lib_frontmatter_py
```

## Components by Layer

### Frontend (0)

| Component | Type | Version | Status |
|-----------|------|---------|--------|

### Middleware (4)

| Component | Type | Version | Status |
|-----------|------|---------|--------|
| staff-engineer | doc | 0.0.0 | unknown |
| sprint-master | doc | 0.0.0 | unknown |
| vp-product | doc | 0.0.0 | unknown |
| sdm | doc | 0.0.0 | unknown |

### Backend (2)

| Component | Type | Version | Status |
|-----------|------|---------|--------|
| README | library | 1.0.0 | active |
| PROMPT | doc | 1.0.0 | active |

### Data (2)

| Component | Type | Version | Status |
|-----------|------|---------|--------|
| EPIC-001 | epic | 1.2.0 | in_progress |
| TASK-004 | task | 1.0.1 | in_progress |

## Dependency Flow

```
Entities (Data) → Agents (Middleware) → Tests/Scripts (Backend) → Docs (Frontend)
```

## Interactive Visualization

Open `ARCHITECTURE.html` in a browser for interactive exploration.

## Updating

This file is auto-generated on every PR merge via GitHub Actions.

Manual regeneration:
```bash
python scripts/architecture/generate.py
```
