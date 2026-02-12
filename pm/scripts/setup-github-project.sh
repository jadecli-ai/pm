#!/bin/bash
# Setup GitHub Project for Iterative Development
# Usage: setup-github-project.sh <owner> <project-name>

set -e

OWNER="${1:-}"
PROJECT_NAME="${2:-jadecli-iterations}"

if [[ -z "$OWNER" ]]; then
  echo "Usage: $0 <github-owner> [project-name]"
  echo "Example: $0 alexzh-august jadecli-iterations"
  exit 1
fi

echo "=== Setting up GitHub Project: $PROJECT_NAME ==="

# Check gh CLI
if ! command -v gh &> /dev/null; then
  echo "Error: gh CLI not found. Install from https://cli.github.com/"
  exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
  echo "Error: Not authenticated. Run 'gh auth login'"
  exit 1
fi

# Create project (user project)
echo "Creating project..."
PROJECT_ID=$(gh api graphql -f query='
  mutation($owner: String!, $title: String!) {
    createProjectV2(input: {ownerId: $owner, title: $title}) {
      projectV2 { id number }
    }
  }
' -f owner="$OWNER" -f title="$PROJECT_NAME" --jq '.data.createProjectV2.projectV2.id' 2>/dev/null || echo "")

if [[ -z "$PROJECT_ID" ]]; then
  echo "Note: Project may already exist or use web UI to create"
  echo "Visit: https://github.com/users/$OWNER/projects/new"
  echo ""
  echo "Select: Iterative Development template"
  echo ""
  echo "Add these custom fields manually:"
fi

# Output field configuration
cat << 'EOF'

## Required Custom Fields

1. **Priority** (Single select)
   - P0-critical (Red)
   - P1-high (Orange)
   - P2-medium (Yellow)
   - P3-low (Green)
   - P4-someday (Gray)

2. **Size** (Single select)
   - XS (0.5-1 hrs)
   - S (1-2 hrs)
   - M (2-4 hrs)
   - L (4-8 hrs)
   - XL (8-16 hrs)

3. **Domain** (Single select)
   - Frontend
   - Backend
   - Infrastructure
   - Data

4. **Agent-Hours** (Number)
   - Estimated agent execution time

5. **Blocked-By** (Text)
   - Dependencies on other items

## Columns/Views

### Board View
1. Backlog
2. Iteration (current)
3. In Progress
4. In Review
5. Done

### Table View
- Group by: Domain
- Sort by: Priority, then Size

### Roadmap View
- Iterations on timeline

## Automations (via Project Settings)

1. Item added → Set status to "Backlog"
2. Item closed → Set status to "Done"
3. PR merged → Close linked issue

## Labels to Create in Repos

```bash
# Run in each repo
gh label create "P0-critical" --color "B60205" --description "Drop everything"
gh label create "P1-high" --color "D93F0B" --description "This iteration"
gh label create "P2-medium" --color "FBCA04" --description "Next iteration"
gh label create "P3-low" --color "0E8A16" --description "Backlog"
gh label create "P4-someday" --color "C2E0C6" --description "Ideas"
gh label create "size:XS" --color "EDEDED" --description "0.5-1 agent-hours"
gh label create "size:S" --color "EDEDED" --description "1-2 agent-hours"
gh label create "size:M" --color "EDEDED" --description "2-4 agent-hours"
gh label create "size:L" --color "EDEDED" --description "4-8 agent-hours"
gh label create "size:XL" --color "EDEDED" --description "8-16 agent-hours"
gh label create "domain:frontend" --color "1D76DB"
gh label create "domain:backend" --color "5319E7"
gh label create "domain:infra" --color "006B75"
gh label create "domain:data" --color "BFD4F2"
gh label create "agent-blocked" --color "B60205" --description "Agent cannot proceed"
gh label create "needs-human" --color "FBCA04" --description "Requires human decision"
```

EOF

echo ""
echo "=== Setup instructions complete ==="
echo "Create project at: https://github.com/users/$OWNER/projects/new"
