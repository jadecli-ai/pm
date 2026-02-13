---
name: neon-dashboard
description: Generate and serve a Vercel-inspired local dashboard for Neon PostgreSQL insights, project architecture visualization, and branch impact analysis from conventional commits. Use when preparing PRs, reviewing branch changes, analyzing database state, or visualizing how conventional commits affect project architecture. Triggers on PR creation, commit to existing PR, architecture review, or database inspection.
---

# Neon Dashboard Skill

Generate a local Vercel-style dashboard showing Neon DB insights, architecture, and branch impact.

## Quick Start

```bash
cd $PM && make l0-dashboard    # Generate DASHBOARD.json + open DASHBOARD.html
```

## Components

### Data Generator (`scripts/dashboard/generate.py`)

Collects from 6 sources into `DASHBOARD.json`:

| Source | Data | Method |
|--------|------|--------|
| Neon DB | documents, chunks, queue stats | `python3 -m lib.neon_docs status` |
| Git log | conventional commits, types, scopes | `git log --format origin/main..HEAD` |
| Merkle tree | root hash, file count, agents | `.index/merkle-tree.json` |
| Git diff | files changed, insertions, deletions | `git diff --stat origin/main..HEAD` |
| GitHub PR | number, title, URL, state | `gh pr list --json` |
| Phase map | completion status per phase | Commit message analysis |

### Dashboard (`DASHBOARD.html`)

4-tab Vercel-dark interface:

1. **Database** — Neon stats cards (docs, chunks, queue), health indicator
2. **Architecture** — Merkle hash, agent grid, layer distribution bars
3. **Branch Impact** — Commit type/scope charts, file change tree, diff summary
4. **PR Release** — Phase checklist, commit timeline, PR link

### Triggers

**On PR creation or commit to existing PR:**

```bash
# Makefile target
make l0-dashboard

# Or via GitHub Actions (.github/workflows/dashboard.yml)
# Runs on: push to feat/* branches, pull_request events
```

**Manual:**

```bash
# Generate data only
cd $PM && python3 scripts/dashboard/generate.py

# Serve locally (optional)
cd $PM && python3 -m http.server 8080
# Open http://localhost:8080/DASHBOARD.html
```

## Integration with neon-release

The neon-dashboard skill complements `neon-release`:

| neon-release (backend) | neon-dashboard (frontend) |
|------------------------|--------------------------|
| Creates PR with conventional commits | Visualizes commit impact |
| Sets up MLflow tracing | Shows trace experiment link |
| Maps commits to plan tasks | Shows phase completion |
| Pushes branch | Generates PR diff analysis |

**Workflow:**

```
1. Work on feature branch (conventional commits)
2. make l0-dashboard          ← Generate dashboard
3. Review DASHBOARD.html      ← Visual verification
4. make l2-pr-open            ← Create/update PR
5. Dashboard auto-regenerates ← CI trigger
```

## Conventional Commit → Architecture Mapping

The dashboard analyzes how commits change the architecture:

| Commit Type | Architecture Impact |
|-------------|-------------------|
| `feat(neon)` | New backend components |
| `feat(agents)` | New middleware components |
| `test(neon)` | Test coverage changes |
| `ci:` | Infrastructure layer |
| `docs(plans)` | Frontend/docs layer |
| `chore(index)` | Data layer (merkle tree) |

## Data Flow

```
git log + git diff + neon CLI + merkle-tree.json + gh pr
    ↓
scripts/dashboard/generate.py
    ↓
DASHBOARD.json (embedded or fetched)
    ↓
DASHBOARD.html (renders 4 tabs)
```

## Makefile Targets

```makefile
l0-dashboard    # Generate DASHBOARD.json
l1-dashboard    # Generate + open in browser
l2-pr-dashboard # Generate + commit + push (for PR updates)
```
