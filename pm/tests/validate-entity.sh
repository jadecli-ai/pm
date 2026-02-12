#!/bin/bash
# Validate a PM entity file against its schema
# Usage: validate-entity.sh <entity-file>

set -e

ENTITY_FILE="${1:-}"

if [[ -z "$ENTITY_FILE" ]]; then
  echo "Usage: $0 <entity-file.md>"
  echo "Example: $0 pm/entities/examples/TASK-004.md"
  exit 1
fi

if [[ ! -f "$ENTITY_FILE" ]]; then
  echo "Error: File not found: $ENTITY_FILE"
  exit 1
fi

echo "=== Validating: $ENTITY_FILE ==="

# Extract frontmatter (between first two --- lines)
FRONTMATTER=$(awk '/^---$/{p=1-p;next} p' "$ENTITY_FILE")

if [[ -z "$FRONTMATTER" ]]; then
  echo "❌ Error: No YAML frontmatter found"
  exit 1
fi

# Parse required fields
ID=$(echo "$FRONTMATTER" | grep -E "^id:" | head -1 | sed 's/id: *//' | tr -d '"')
VERSION=$(echo "$FRONTMATTER" | grep -E "^version:" | head -1 | sed 's/version: *//' | tr -d '"')
TYPE=$(echo "$FRONTMATTER" | grep -E "^type:" | head -1 | sed 's/type: *//' | tr -d '"')
STATUS=$(echo "$FRONTMATTER" | grep -E "^status:" | head -1 | sed 's/status: *//' | tr -d '"')

ERRORS=0

# Validate ID
if [[ -z "$ID" ]]; then
  echo "❌ Missing: id"
  ((ERRORS++))
else
  # Check ID format based on type
  case "$TYPE" in
    epic) [[ "$ID" =~ ^EPIC-[0-9]+$ ]] || { echo "❌ Invalid ID format: $ID (expected EPIC-XXX)"; ((ERRORS++)); } ;;
    story) [[ "$ID" =~ ^STORY-[0-9]+$ ]] || { echo "❌ Invalid ID format: $ID (expected STORY-XXX)"; ((ERRORS++)); } ;;
    task) [[ "$ID" =~ ^TASK-[0-9]+$ ]] || { echo "❌ Invalid ID format: $ID (expected TASK-XXX)"; ((ERRORS++)); } ;;
    subtask) [[ "$ID" =~ ^SUBTASK-[0-9]+$ ]] || { echo "❌ Invalid ID format: $ID (expected SUBTASK-XXX)"; ((ERRORS++)); } ;;
  esac
  echo "✓ id: $ID"
fi

# Validate version (semver)
if [[ -z "$VERSION" ]]; then
  echo "❌ Missing: version"
  ((ERRORS++))
elif [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "❌ Invalid version format: $VERSION (expected X.Y.Z)"
  ((ERRORS++))
else
  echo "✓ version: $VERSION"
fi

# Validate type
if [[ -z "$TYPE" ]]; then
  echo "❌ Missing: type"
  ((ERRORS++))
elif [[ ! "$TYPE" =~ ^(epic|story|task|subtask)$ ]]; then
  echo "❌ Invalid type: $TYPE (expected epic|story|task|subtask)"
  ((ERRORS++))
else
  echo "✓ type: $TYPE"
fi

# Validate status
if [[ -z "$STATUS" ]]; then
  echo "❌ Missing: status"
  ((ERRORS++))
elif [[ ! "$STATUS" =~ ^(pending|in_progress|completed|blocked)$ ]]; then
  echo "❌ Invalid status: $STATUS (expected pending|in_progress|completed|blocked)"
  ((ERRORS++))
else
  echo "✓ status: $STATUS"
fi

# Type-specific validations
case "$TYPE" in
  task|subtask)
    # Tasks must have subject and activeForm
    SUBJECT=$(echo "$FRONTMATTER" | grep -E "^subject:" | head -1 | sed 's/subject: *//' | tr -d '"')
    ACTIVE_FORM=$(echo "$FRONTMATTER" | grep -E "^activeForm:" | head -1 | sed 's/activeForm: *//' | tr -d '"')

    if [[ -z "$SUBJECT" ]]; then
      echo "❌ Missing: subject (required for $TYPE)"
      ((ERRORS++))
    else
      # Check imperative form
      if [[ "$SUBJECT" =~ ^(Implementing|Creating|Adding|Fixing) ]]; then
        echo "⚠️ Warning: subject should be imperative ('Implement' not 'Implementing')"
      fi
      echo "✓ subject: $SUBJECT"
    fi

    if [[ -z "$ACTIVE_FORM" ]]; then
      echo "❌ Missing: activeForm (required for $TYPE)"
      ((ERRORS++))
    else
      echo "✓ activeForm: $ACTIVE_FORM"
    fi
    ;;

  epic)
    # Epics should have owner = vp-product
    OWNER=$(echo "$FRONTMATTER" | grep -E "^owner:" | head -1 | sed 's/owner: *//' | tr -d '"')
    if [[ "$OWNER" != "vp-product" ]]; then
      echo "⚠️ Warning: Epic owner should be 'vp-product', got '$OWNER'"
    fi
    ;;
esac

# Check for parent (required for non-epics)
if [[ "$TYPE" != "epic" ]]; then
  PARENT=$(echo "$FRONTMATTER" | grep -E "^parent:" | head -1 | sed 's/parent: *//' | tr -d '"')
  if [[ -z "$PARENT" || "$PARENT" == "null" ]]; then
    echo "❌ Missing: parent (required for $TYPE)"
    ((ERRORS++))
  else
    echo "✓ parent: $PARENT"
  fi
fi

# Summary
echo ""
if [[ $ERRORS -eq 0 ]]; then
  echo "✅ Validation passed"
  exit 0
else
  echo "❌ Validation failed with $ERRORS error(s)"
  exit 1
fi
