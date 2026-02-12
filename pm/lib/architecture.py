"""Architecture diagram generation utilities.

Generates:
- Mermaid diagrams for documentation
- Interactive HTML visualization
- Dependency graphs
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .frontmatter import parse_file, extract_dependencies


@dataclass
class Component:
    """A component in the architecture."""
    id: str
    name: str
    type: str
    layer: str  # backend, frontend, middleware, data
    file_path: str
    version: str
    status: str
    depends_on: list[str] = field(default_factory=list)
    depended_by: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class Architecture:
    """Full system architecture."""
    name: str
    version: str
    components: list[Component] = field(default_factory=list)
    org: str = "jadecli-ai"
    repo: str = "pm"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "org": self.org,
            "repo": self.repo,
            "layers": {
                "backend": [c.__dict__ for c in self.components if c.layer == "backend"],
                "middleware": [c.__dict__ for c in self.components if c.layer == "middleware"],
                "frontend": [c.__dict__ for c in self.components if c.layer == "frontend"],
                "data": [c.__dict__ for c in self.components if c.layer == "data"],
            },
            "all_components": [c.__dict__ for c in self.components],
        }


def classify_layer(file_path: str, frontmatter: dict) -> str:
    """Classify a file into architecture layer."""
    path = file_path.lower()

    # Explicit layer in frontmatter
    if "layer" in frontmatter:
        return frontmatter["layer"]

    # Infer from path/type
    if "agents/" in path:
        return "middleware"
    if "entities/" in path:
        return "data"
    if "tests/" in path:
        return "backend"
    if ".index/" in path:
        return "data"
    if "lib/" in path:
        return "backend"
    if "scripts/" in path:
        return "backend"
    if "docs/" in path:
        return "frontend"  # Documentation layer

    return "middleware"  # Default


def scan_architecture(root: Path) -> Architecture:
    """Scan project and build architecture model.

    Args:
        root: Project root directory

    Returns:
        Architecture object with all components
    """
    arch = Architecture(
        name="PM System",
        version="1.0.0",
    )

    # Scan all markdown files
    for md_file in root.rglob("*.md"):
        # Skip hidden and docs
        rel_path = str(md_file.relative_to(root))
        if rel_path.startswith(".git"):
            continue

        try:
            frontmatter = parse_file(md_file)
        except Exception:
            continue

        if not frontmatter:
            continue

        deps = extract_dependencies(frontmatter)

        component = Component(
            id=frontmatter.get("id", rel_path),
            name=frontmatter.get("name", md_file.stem),
            type=frontmatter.get("type", "doc"),
            layer=classify_layer(rel_path, frontmatter),
            file_path=rel_path,
            version=frontmatter.get("version", "0.0.0"),
            status=frontmatter.get("status", "unknown"),
            depends_on=deps["dependsOn"],
            depended_by=deps["dependedBy"],
            description=frontmatter.get("description", ""),
        )
        arch.components.append(component)

    return arch


def generate_mermaid(arch: Architecture) -> str:
    """Generate Mermaid diagram from architecture.

    Uses flowchart with swimlanes per layer.
    """
    lines = [
        "```mermaid",
        "flowchart TB",
        "",
        "    subgraph Frontend[\"Frontend Layer\"]",
    ]

    # Frontend components
    for c in arch.components:
        if c.layer == "frontend":
            lines.append(f"        {c.id.replace('-', '_')}[\"{c.name}\"]")

    lines.extend([
        "    end",
        "",
        "    subgraph Middleware[\"Middleware Layer\"]",
    ])

    # Middleware components
    for c in arch.components:
        if c.layer == "middleware":
            lines.append(f"        {c.id.replace('-', '_')}[\"{c.name}\"]")

    lines.extend([
        "    end",
        "",
        "    subgraph Backend[\"Backend Layer\"]",
    ])

    # Backend components
    for c in arch.components:
        if c.layer == "backend":
            lines.append(f"        {c.id.replace('-', '_')}[\"{c.name}\"]")

    lines.extend([
        "    end",
        "",
        "    subgraph Data[\"Data Layer\"]",
    ])

    # Data components
    for c in arch.components:
        if c.layer == "data":
            lines.append(f"        {c.id.replace('-', '_')}[\"{c.name}\"]")

    lines.extend([
        "    end",
        "",
        "    %% Dependencies",
    ])

    # Add dependency arrows
    for c in arch.components:
        for dep in c.depends_on:
            if dep.startswith(("npm:", "pip:")):
                continue
            dep_id = dep.replace("-", "_").replace("/", "_").replace(".", "_")
            c_id = c.id.replace("-", "_")
            lines.append(f"    {c_id} --> {dep_id}")

    lines.append("```")

    return "\n".join(lines)


def generate_html(arch: Architecture) -> str:
    """Generate interactive HTML architecture visualization."""

    arch_json = json.dumps(arch.to_dict(), indent=2)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{arch.name} - Architecture</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        :root {{
            --bg: #0d1117;
            --surface: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --text-muted: #8b949e;
            --accent: #58a6ff;
            --success: #3fb950;
            --warning: #d29922;
            --error: #f85149;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 2rem; }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }}
        h1 {{ font-size: 1.5rem; font-weight: 600; }}
        .meta {{ color: var(--text-muted); font-size: 0.875rem; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        .layer {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
        }}
        .layer-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border);
        }}
        .layer-title {{ font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; }}
        .layer-count {{ background: var(--border); padding: 0.125rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }}
        .component {{
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: var(--bg);
            border-radius: 6px;
            cursor: pointer;
            transition: border-color 0.2s;
            border: 1px solid transparent;
        }}
        .component:hover {{ border-color: var(--accent); }}
        .component.selected {{ border-color: var(--accent); background: rgba(88, 166, 255, 0.1); }}
        .component-name {{ font-weight: 500; margin-bottom: 0.25rem; }}
        .component-meta {{ font-size: 0.75rem; color: var(--text-muted); }}
        .status {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 0.5rem; }}
        .status.completed {{ background: var(--success); }}
        .status.in_progress {{ background: var(--warning); }}
        .status.pending {{ background: var(--text-muted); }}
        .status.active {{ background: var(--success); }}
        .details {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            margin-top: 2rem;
        }}
        .details h2 {{ margin-bottom: 1rem; font-size: 1.125rem; }}
        .details-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; }}
        .detail-item {{ margin-bottom: 0.5rem; }}
        .detail-label {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }}
        .detail-value {{ font-family: monospace; }}
        .deps {{ margin-top: 1rem; }}
        .dep-list {{ list-style: none; }}
        .dep-list li {{ padding: 0.25rem 0; font-family: monospace; font-size: 0.875rem; }}
        .dep-list li::before {{ content: "→ "; color: var(--accent); }}
        .diagram {{ margin-top: 2rem; background: var(--surface); border-radius: 8px; padding: 1rem; }}
        .org-badge {{
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
        }}
        .filter-bar {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }}
        .filter-btn {{
            padding: 0.5rem 1rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text);
            cursor: pointer;
            font-size: 0.875rem;
        }}
        .filter-btn.active {{ background: var(--accent); border-color: var(--accent); color: #000; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>{arch.name}</h1>
                <div class="meta">v{arch.version} • {arch.org}/{arch.repo}</div>
            </div>
            <span class="org-badge">{arch.org}</span>
        </header>

        <div class="filter-bar">
            <button class="filter-btn active" onclick="filterLayer('all')">All</button>
            <button class="filter-btn" onclick="filterLayer('frontend')">Frontend</button>
            <button class="filter-btn" onclick="filterLayer('middleware')">Middleware</button>
            <button class="filter-btn" onclick="filterLayer('backend')">Backend</button>
            <button class="filter-btn" onclick="filterLayer('data')">Data</button>
        </div>

        <div class="grid" id="layers"></div>

        <div class="details" id="details" style="display: none;">
            <h2 id="detail-title">Component Details</h2>
            <div class="details-grid" id="detail-content"></div>
        </div>

        <div class="diagram">
            <h2 style="margin-bottom: 1rem;">Dependency Graph</h2>
            <div id="mermaid-diagram"></div>
        </div>
    </div>

    <script>
        const architecture = {arch_json};

        function renderLayers(filter = 'all') {{
            const container = document.getElementById('layers');
            container.innerHTML = '';

            const layers = ['frontend', 'middleware', 'backend', 'data'];

            layers.forEach(layer => {{
                if (filter !== 'all' && filter !== layer) return;

                const components = architecture.layers[layer] || [];
                const layerEl = document.createElement('div');
                layerEl.className = 'layer';
                layerEl.innerHTML = `
                    <div class="layer-header">
                        <span class="layer-title">${{layer}}</span>
                        <span class="layer-count">${{components.length}}</span>
                    </div>
                `;

                components.forEach(c => {{
                    const compEl = document.createElement('div');
                    compEl.className = 'component';
                    compEl.onclick = () => showDetails(c);
                    compEl.innerHTML = `
                        <div class="component-name">
                            <span class="status ${{c.status}}"></span>
                            ${{c.name}}
                        </div>
                        <div class="component-meta">${{c.type}} • v${{c.version}}</div>
                    `;
                    layerEl.appendChild(compEl);
                }});

                container.appendChild(layerEl);
            }});
        }}

        function showDetails(component) {{
            document.querySelectorAll('.component').forEach(el => el.classList.remove('selected'));
            event.currentTarget.classList.add('selected');

            const details = document.getElementById('details');
            const title = document.getElementById('detail-title');
            const content = document.getElementById('detail-content');

            details.style.display = 'block';
            title.textContent = component.name;

            content.innerHTML = `
                <div class="detail-item">
                    <div class="detail-label">ID</div>
                    <div class="detail-value">${{component.id}}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Type</div>
                    <div class="detail-value">${{component.type}}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Version</div>
                    <div class="detail-value">${{component.version}}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Status</div>
                    <div class="detail-value">${{component.status}}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">File</div>
                    <div class="detail-value">${{component.file_path}}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Layer</div>
                    <div class="detail-value">${{component.layer}}</div>
                </div>
                <div class="deps" style="grid-column: span 2;">
                    <div class="detail-label">Dependencies</div>
                    <ul class="dep-list">
                        ${{component.depends_on.map(d => `<li>${{d}}</li>`).join('') || '<li style="color: var(--text-muted)">None</li>'}}
                    </ul>
                </div>
            `;
        }}

        function filterLayer(layer) {{
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.currentTarget.classList.add('active');
            renderLayers(layer);
        }}

        // Initialize
        renderLayers();

        // Render Mermaid diagram
        const mermaidCode = `flowchart LR
            subgraph Frontend
                ${{architecture.layers.frontend.map(c => c.id.replace(/-/g, '_') + '["' + c.name + '"]').join('\\n                ')}}
            end
            subgraph Middleware
                ${{architecture.layers.middleware.map(c => c.id.replace(/-/g, '_') + '["' + c.name + '"]').join('\\n                ')}}
            end
            subgraph Backend
                ${{architecture.layers.backend.map(c => c.id.replace(/-/g, '_') + '["' + c.name + '"]').join('\\n                ')}}
            end
            subgraph Data
                ${{architecture.layers.data.map(c => c.id.replace(/-/g, '_') + '["' + c.name + '"]').join('\\n                ')}}
            end
        `;

        document.getElementById('mermaid-diagram').innerHTML = '<pre class="mermaid">' + mermaidCode + '</pre>';
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    </script>
</body>
</html>
'''
