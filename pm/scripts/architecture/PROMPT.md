---
id: "PROMPT-001"
version: "1.0.0"
type: doc
status: active
created: 2026-02-11
updated: 2026-02-11
dependsOn:
  - "lib/architecture.py"
  - "lib/frontmatter.py"
dependedBy: []
---

# Architecture Generation Prompt

> Use this prompt with Claude Code to generate/update architecture documentation

## Quick Generation

```
Generate architecture documentation for this project:
1. Run: python scripts/architecture/generate.py
2. Review ARCHITECTURE.md and ARCHITECTURE.html
3. Commit if changes look correct
```

## Full Interactive Prompt

Copy this prompt to generate comprehensive architecture:

---

**PROMPT START**

Analyze this codebase and generate an interactive HTML architecture visualization.

## Requirements

1. **Scan all files** with YAML frontmatter to identify components
2. **Classify into layers**:
   - Frontend: docs/, UI, user-facing
   - Middleware: agents/, orchestration, coordination
   - Backend: lib/, scripts/, tests/, business logic
   - Data: entities/, .index/, storage

3. **Extract relationships** from frontmatter:
   - `dependsOn`: What this component needs
   - `dependedBy`: What needs this component
   - `blocks`/`blockedBy`: Execution dependencies

4. **Generate outputs**:
   - `ARCHITECTURE.md`: Mermaid diagram + component tables
   - `ARCHITECTURE.html`: Interactive dark-themed visualization
   - `architecture.json`: Machine-readable for CI/CD

5. **HTML must include**:
   - Layer filter buttons (All/Frontend/Middleware/Backend/Data)
   - Click component for details panel
   - Status indicators (colored dots)
   - Mermaid dependency graph
   - Organization badge (jadecli-ai)
   - Dark theme (#0d1117 background)

## Organization Context

```
jadecli-ai/                    # GitHub Organization
├── pm/                        # This repo - PM System
│   ├── agents/                # AI agent definitions
│   │   ├── vp-product.md      # Opus - strategic
│   │   ├── sdm.md             # Sonnet - tactical
│   │   ├── staff-engineer.md  # Sonnet - implementation
│   │   └── sprint-master.md   # Haiku - ceremonies
│   ├── entities/              # Work item hierarchy
│   │   ├── epic.schema.md
│   │   ├── story.schema.md
│   │   ├── task.schema.md     # Claude Code aligned
│   │   └── subtask.schema.md
│   ├── lib/                   # Shared code (single source)
│   ├── .index/                # Merkle tree index
│   └── tests/                 # Integration tests
└── (future repos)             # Will share lib/ patterns
```

## Execution

```bash
python scripts/architecture/generate.py
```

**PROMPT END**

---

## Automation

Architecture auto-updates on:
- PR merge to main
- Push to main
- Manual workflow dispatch

See `.github/workflows/architecture.yml`

## Extending

To add new layers or component types:

1. Edit `lib/architecture.py`:
   - Add to `classify_layer()` function
   - Update `generate_html()` styles

2. Regenerate:
   ```bash
   python scripts/architecture/generate.py
   ```

## Troubleshooting

**Components not appearing?**
- Ensure file has YAML frontmatter with `id` and `type`

**Wrong layer assignment?**
- Add explicit `layer: frontend|middleware|backend|data` to frontmatter

**Dependencies not showing?**
- Check `dependsOn` is a list in frontmatter
- External deps should prefix: `npm:`, `pip:`
