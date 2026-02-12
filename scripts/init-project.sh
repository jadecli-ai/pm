#!/bin/bash
# Initialize a new project with jadecli org settings
# Usage: init-project.sh <project-name>

set -e

PROJECT_NAME="${1:-}"
ORG_DIR="$HOME/projects/.claude-org"
PROJECTS_DIR="$HOME/projects"

if [[ -z "$PROJECT_NAME" ]]; then
  echo "Usage: $0 <project-name>"
  exit 1
fi

PROJECT_DIR="$PROJECTS_DIR/$PROJECT_NAME"

echo "=== Initializing jadecli project: $PROJECT_NAME ==="

# Create project directory
mkdir -p "$PROJECT_DIR/.claude/agents"
mkdir -p "$PROJECT_DIR/src"
mkdir -p "$PROJECT_DIR/tests"
mkdir -p "$PROJECT_DIR/docs"
mkdir -p "$PROJECT_DIR/scripts"

# Create project settings from template
sed "s/PROJECT_NAME/$PROJECT_NAME/g" "$ORG_DIR/templates/project-settings.json" \
  > "$PROJECT_DIR/.claude/settings.json"

# Create project CLAUDE.md from template
sed "s/PROJECT_NAME/$PROJECT_NAME/g" "$ORG_DIR/templates/project-CLAUDE.md" \
  > "$PROJECT_DIR/CLAUDE.md"

# Link org agents (optional - projects can override)
echo "Org agents available at: $ORG_DIR/agents/"

# Create .gitignore
cat > "$PROJECT_DIR/.gitignore" << 'EOF'
# Dependencies
node_modules/
__pycache__/
*.pyc
.venv/
venv/
target/

# Environment
.env
.env.*
!.env.example

# IDE
.idea/
.vscode/
*.swp
*.swo

# Build
dist/
build/
*.egg-info/

# Claude Code local settings
.claude/settings.local.json
.claude/tasks/

# OS
.DS_Store
Thumbs.db
EOF

# Create .env.example
cat > "$PROJECT_DIR/.env.example" << 'EOF'
# Copy to .env and fill in values
# DO NOT commit .env files

# Example environment variables
# API_KEY=your_api_key_here
# DATABASE_URL=postgresql://localhost/dbname
EOF

# Initialize git if not already
if [[ ! -d "$PROJECT_DIR/.git" ]]; then
  cd "$PROJECT_DIR" && git init
  echo "Initialized git repository"
fi

echo ""
echo "=== Project initialized: $PROJECT_DIR ==="
echo ""
echo "Next steps:"
echo "  1. cd $PROJECT_DIR"
echo "  2. Edit CLAUDE.md with project details"
echo "  3. Copy .env.example to .env"
echo "  4. Start coding!"
echo ""
echo "Org settings inherited from: $ORG_DIR/settings.json"
