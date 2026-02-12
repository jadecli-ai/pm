#!/usr/bin/env python3
"""Generate architecture documentation.

Outputs:
- ARCHITECTURE.md (Mermaid diagram)
- ARCHITECTURE.html (Interactive visualization)
- architecture.json (Machine-readable)

Usage:
    python scripts/architecture/generate.py
"""

import json
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.architecture import scan_architecture, generate_mermaid, generate_html


def main():
    root = Path(__file__).parent.parent.parent
    output_dir = root

    print("Scanning architecture...")
    arch = scan_architecture(root)
    print(f"Found {len(arch.components)} components")

    # Generate ARCHITECTURE.md
    md_content = f"""---
id: "ARCH-001"
version: "{arch.version}"
type: doc
status: active
created: 2026-02-11
updated: 2026-02-11
dependsOn: []
dependedBy: []
---

# {arch.name} Architecture

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
| **Frontend** | Documentation, UI | {len([c for c in arch.components if c.layer == 'frontend'])} |
| **Middleware** | Agents, orchestration | {len([c for c in arch.components if c.layer == 'middleware'])} |
| **Backend** | Scripts, tests, lib | {len([c for c in arch.components if c.layer == 'backend'])} |
| **Data** | Entities, index | {len([c for c in arch.components if c.layer == 'data'])} |

## Component Diagram

{generate_mermaid(arch)}

## Components by Layer

### Frontend ({len([c for c in arch.components if c.layer == 'frontend'])})

| Component | Type | Version | Status |
|-----------|------|---------|--------|
"""

    for c in arch.components:
        if c.layer == "frontend":
            md_content += f"| {c.name} | {c.type} | {c.version} | {c.status} |\n"

    md_content += f"""
### Middleware ({len([c for c in arch.components if c.layer == 'middleware'])})

| Component | Type | Version | Status |
|-----------|------|---------|--------|
"""

    for c in arch.components:
        if c.layer == "middleware":
            md_content += f"| {c.name} | {c.type} | {c.version} | {c.status} |\n"

    md_content += f"""
### Backend ({len([c for c in arch.components if c.layer == 'backend'])})

| Component | Type | Version | Status |
|-----------|------|---------|--------|
"""

    for c in arch.components:
        if c.layer == "backend":
            md_content += f"| {c.name} | {c.type} | {c.version} | {c.status} |\n"

    md_content += f"""
### Data ({len([c for c in arch.components if c.layer == 'data'])})

| Component | Type | Version | Status |
|-----------|------|---------|--------|
"""

    for c in arch.components:
        if c.layer == "data":
            md_content += f"| {c.name} | {c.type} | {c.version} | {c.status} |\n"

    md_content += """
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
"""

    # Write outputs
    (output_dir / "ARCHITECTURE.md").write_text(md_content)
    print(f"Generated: ARCHITECTURE.md")

    html_content = generate_html(arch)
    (output_dir / "ARCHITECTURE.html").write_text(html_content)
    print(f"Generated: ARCHITECTURE.html")

    json_content = json.dumps(arch.to_dict(), indent=2)
    (output_dir / "architecture.json").write_text(json_content)
    print(f"Generated: architecture.json")

    print("Done!")


if __name__ == "__main__":
    main()
