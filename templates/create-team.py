#!/usr/bin/env python3
"""Team Generator - Creates new team subpackages from templates.

schema: N/A (script)
depends_on:
  - templates/team/
depended_by:
  - teams/
semver: minor
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("Error: jinja2 not installed. Run: pip install jinja2")
    sys.exit(1)


# Model configurations
MODELS = {
    "opus": {
        "id": "claude-opus-4-5-20251101",
        "turns": 25,
        "token_budget": 160000,
    },
    "sonnet": {
        "id": "claude-sonnet-4-5-20250929",
        "turns": 15,
        "token_budget": 160000,
    },
    "haiku": {
        "id": "claude-haiku-3-5-20241022",
        "turns": 10,
        "token_budget": 160000,
    },
}


def slugify(name: str) -> str:
    """Convert team name to slug format."""
    return name.lower().replace(" ", "-").replace("_", "-")


def create_team(
    name: str,
    description: str,
    output_dir: Path,
    lead_model: str = "opus",
    engineer_model: str = "sonnet",
    tester_model: str = "haiku",
    wrap_up_threshold: float = 0.80,
    as_repo: bool = False,
) -> Path:
    """Create a new team subpackage from templates."""

    # Setup paths
    template_dir = Path(__file__).parent / "team"
    team_slug = slugify(name)
    team_dir = output_dir / team_slug

    if team_dir.exists():
        print(f"Error: Team directory already exists: {team_dir}")
        sys.exit(1)

    # Get model configs
    lead_config = MODELS.get(lead_model, MODELS["opus"])
    engineer_config = MODELS.get(engineer_model, MODELS["sonnet"])
    tester_config = MODELS.get(tester_model, MODELS["haiku"])

    # Template context
    context = {
        "team_name": name,
        "team_slug": team_slug,
        "description": description,
        "lead_model": lead_config["id"],
        "lead_turns": lead_config["turns"],
        "engineer_model": engineer_config["id"],
        "engineer_turns": engineer_config["turns"],
        "tester_model": tester_config["id"],
        "tester_turns": tester_config["turns"],
        "token_budget": lead_config["token_budget"],
        "wrap_up_threshold": wrap_up_threshold,
    }

    # Setup Jinja environment
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        keep_trailing_newline=True,
    )

    # Create directory structure
    dirs = [
        team_dir,
        team_dir / "agents",
        team_dir / "entities" / "examples",
        team_dir / "lib",
        team_dir / "docs",
        team_dir / "tests",
        team_dir / ".index",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {d}")

    # Process templates
    templates = [
        ("CLAUDE.md.j2", team_dir / "CLAUDE.md"),
        ("package.json.j2", team_dir / "package.json"),
        ("agents/team-lead.md.j2", team_dir / "agents" / f"{team_slug}-lead.md"),
        ("agents/team-engineer.md.j2", team_dir / "agents" / f"{team_slug}-engineer.md"),
        ("agents/team-tester.md.j2", team_dir / "agents" / f"{team_slug}-tester.md"),
    ]

    for template_path, output_path in templates:
        try:
            template = env.get_template(template_path)
            content = template.render(**context)
            output_path.write_text(content)
            print(f"  Created: {output_path}")
        except Exception as e:
            print(f"  Error processing {template_path}: {e}")

    # Copy static files
    static_files = [
        ("entities/README.md", team_dir / "entities" / "README.md"),
        ("lib/__init__.py", team_dir / "lib" / "__init__.py"),
    ]

    for src_rel, dst_path in static_files:
        src_path = template_dir / src_rel
        if src_path.exists():
            # Simple template rendering for static files with {{ team_name }}
            content = src_path.read_text()
            content = content.replace("{{ team_name }}", name)
            dst_path.write_text(content)
            print(f"  Created: {dst_path}")

    # Create empty index files
    index_files = [
        (team_dir / ".index" / "AGENT-INDEX.md", f"# {name} Team Agent Index\n\nGenerate with: `python3 .index/generate-merkle.py`\n"),
        (team_dir / ".index" / "merkle-tree.json", "{}"),
        (team_dir / "tests" / "README.md", f"# {name} Team Tests\n\nRun with: `./run-tests.sh`\n"),
    ]

    for path, content in index_files:
        path.write_text(content)
        print(f"  Created: {path}")

    print(f"\n✅ Team '{name}' created at: {team_dir}")

    if as_repo:
        print(f"\n📦 To push as separate repo:")
        print(f"   cd {team_dir}")
        print(f"   git init")
        print(f"   git add .")
        print(f"   git commit -m 'feat: initialize {team_slug} team'")
        print(f"   gh repo create jadecli-ai/{team_slug} --public --source=.")

    return team_dir


def main():
    parser = argparse.ArgumentParser(
        description="Create a new team subpackage from templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --name "Backend Engineering" --description "Backend services and APIs"
  %(prog)s --name "Frontend Engineering" --lead-model sonnet
  %(prog)s --name "Data Science" --as-repo
        """,
    )

    parser.add_argument(
        "--name",
        required=True,
        help="Team name (e.g., 'Backend Engineering')",
    )
    parser.add_argument(
        "--description",
        default="",
        help="Team description",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: ../teams/)",
    )
    parser.add_argument(
        "--lead-model",
        choices=["opus", "sonnet", "haiku"],
        default="opus",
        help="Model for team lead (default: opus)",
    )
    parser.add_argument(
        "--engineer-model",
        choices=["opus", "sonnet", "haiku"],
        default="sonnet",
        help="Model for engineers (default: sonnet)",
    )
    parser.add_argument(
        "--tester-model",
        choices=["opus", "sonnet", "haiku"],
        default="haiku",
        help="Model for tester (default: haiku)",
    )
    parser.add_argument(
        "--wrap-up-threshold",
        type=float,
        default=0.80,
        help="Budget wrap-up threshold (default: 0.80)",
    )
    parser.add_argument(
        "--as-repo",
        action="store_true",
        help="Print instructions for creating as separate repo",
    )

    args = parser.parse_args()

    # Default output directory
    if args.output_dir is None:
        args.output_dir = Path(__file__).parent.parent / "teams"

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Set default description
    if not args.description:
        args.description = f"{args.name} Agent Team"

    print(f"🔧 Creating team: {args.name}")
    print(f"   Output: {args.output_dir}")
    print(f"   Lead model: {args.lead_model}")
    print(f"   Engineer model: {args.engineer_model}")
    print(f"   Tester model: {args.tester_model}")
    print()

    create_team(
        name=args.name,
        description=args.description,
        output_dir=args.output_dir,
        lead_model=args.lead_model,
        engineer_model=args.engineer_model,
        tester_model=args.tester_model,
        wrap_up_threshold=args.wrap_up_threshold,
        as_repo=args.as_repo,
    )


if __name__ == "__main__":
    main()
