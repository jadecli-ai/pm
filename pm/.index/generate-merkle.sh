#!/bin/bash
# Generate Merkle tree index for PM system
# Outputs JSON structure for agent pre-indexing

set -e

PM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INDEX_DIR="$PM_DIR/.index"
OUTPUT="$INDEX_DIR/merkle-tree.json"

# Hash a file's content
hash_file() {
  sha256sum "$1" 2>/dev/null | cut -d' ' -f1
}

# Hash a string
hash_string() {
  echo -n "$1" | sha256sum | cut -d' ' -f1
}

# Extract frontmatter field
get_frontmatter_field() {
  local file="$1"
  local field="$2"
  awk '/^---$/{p=1-p;next} p' "$file" | grep -E "^${field}:" | head -1 | sed "s/${field}: *//" | tr -d '"'
}

# Get file line count
line_count() {
  wc -l < "$1" | tr -d ' '
}

# Start JSON output
echo "{" > "$OUTPUT"
echo '  "version": "1.0.0",' >> "$OUTPUT"
echo "  \"generated\": \"$(date -Iseconds)\"," >> "$OUTPUT"
echo '  "root": null,' >> "$OUTPUT"
echo '  "files": {' >> "$OUTPUT"

# Collect all file hashes
declare -A FILE_HASHES
declare -A DIR_HASHES
FIRST_FILE=true

for f in $(find "$PM_DIR" -type f \( -name "*.md" -o -name "*.sh" \) ! -path "*/.index/*" | sort); do
  REL_PATH="${f#$PM_DIR/}"
  HASH=$(hash_file "$f")
  LINES=$(line_count "$f")
  FILE_HASHES["$REL_PATH"]="$HASH"

  # Extract metadata for .md files
  TYPE=""
  PURPOSE=""
  EXPORTS=""

  if [[ "$f" == *.md ]]; then
    # Check if it's an entity, agent, or doc
    if [[ "$REL_PATH" == entities/examples/* ]]; then
      TYPE=$(get_frontmatter_field "$f" "type")
      ID=$(get_frontmatter_field "$f" "id")
      PURPOSE="entity:$TYPE:$ID"
    elif [[ "$REL_PATH" == entities/*.schema.md ]]; then
      TYPE="schema"
      PURPOSE="schema:$(basename "$f" .schema.md)"
    elif [[ "$REL_PATH" == agents/* ]]; then
      TYPE="agent"
      NAME=$(get_frontmatter_field "$f" "name")
      MODEL=$(get_frontmatter_field "$f" "model")
      PURPOSE="agent:$NAME:$MODEL"
    elif [[ "$REL_PATH" == tests/* ]]; then
      TYPE="test"
      PURPOSE="test:$(basename "$f" .md)"
    else
      TYPE="doc"
      PURPOSE="doc:$(basename "$f" .md)"
    fi
  elif [[ "$f" == *.sh ]]; then
    TYPE="script"
    PURPOSE="script:$(basename "$f" .sh)"
  fi

  if ! $FIRST_FILE; then
    echo "," >> "$OUTPUT"
  fi
  FIRST_FILE=false

  cat >> "$OUTPUT" << EOF
    "$REL_PATH": {
      "hash": "$HASH",
      "lines": $LINES,
      "type": "$TYPE",
      "purpose": "$PURPOSE"
    }
EOF
done

echo "" >> "$OUTPUT"
echo "  }," >> "$OUTPUT"

# Build directory tree with Merkle hashes
echo '  "directories": {' >> "$OUTPUT"

FIRST_DIR=true
for dir in $(find "$PM_DIR" -type d ! -path "*/.index*" ! -path "*/.git*" | sort); do
  REL_DIR="${dir#$PM_DIR/}"
  [[ "$REL_DIR" == "$PM_DIR" ]] && REL_DIR="."
  [[ -z "$REL_DIR" ]] && REL_DIR="."

  # Collect hashes of all files in this directory (non-recursive)
  DIR_CONTENT=""
  for f in "$dir"/*.md "$dir"/*.sh 2>/dev/null; do
    [[ -f "$f" ]] || continue
    REL_F="${f#$PM_DIR/}"
    if [[ -n "${FILE_HASHES[$REL_F]}" ]]; then
      DIR_CONTENT+="${FILE_HASHES[$REL_F]}"
    fi
  done

  # Hash the concatenated file hashes
  if [[ -n "$DIR_CONTENT" ]]; then
    DIR_HASH=$(hash_string "$DIR_CONTENT")
  else
    DIR_HASH="empty"
  fi

  DIR_HASHES["$REL_DIR"]="$DIR_HASH"

  if ! $FIRST_DIR; then
    echo "," >> "$OUTPUT"
  fi
  FIRST_DIR=false

  # Count children
  FILE_COUNT=$(find "$dir" -maxdepth 1 -type f \( -name "*.md" -o -name "*.sh" \) 2>/dev/null | wc -l | tr -d ' ')
  DIR_COUNT=$(find "$dir" -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
  ((DIR_COUNT--)) || true  # Subtract self

  echo -n "    \"$REL_DIR\": {\"hash\": \"$DIR_HASH\", \"files\": $FILE_COUNT, \"dirs\": $DIR_COUNT}" >> "$OUTPUT"
done

echo "" >> "$OUTPUT"
echo "  }," >> "$OUTPUT"

# Compute root hash from top-level directory hashes
ROOT_CONTENT=""
for key in "${!DIR_HASHES[@]}"; do
  ROOT_CONTENT+="${DIR_HASHES[$key]}"
done
ROOT_HASH=$(hash_string "$ROOT_CONTENT")

# Update root hash
sed -i "s/\"root\": null/\"root\": \"$ROOT_HASH\"/" "$OUTPUT"

# Add semantic index for agents
echo '  "semanticIndex": {' >> "$OUTPUT"
cat >> "$OUTPUT" << 'EOF'
    "entryPoints": ["ENTRYPOINT.md", "README.md"],
    "agents": {
      "vp-product": {"model": "opus", "owns": ["epics"]},
      "sdm": {"model": "sonnet", "owns": ["stories", "tasks"]},
      "staff-engineer": {"model": "sonnet", "owns": ["tasks", "subtasks"]},
      "sprint-master": {"model": "haiku", "owns": ["ceremonies"]}
    },
    "entityHierarchy": ["epic", "story", "task", "subtask"],
    "schemas": {
      "epic": "entities/epic.schema.md",
      "story": "entities/story.schema.md",
      "task": "entities/task.schema.md",
      "subtask": "entities/subtask.schema.md"
    },
    "claudeCodeAlignment": {
      "taskFields": ["subject", "activeForm", "status", "blockedBy", "blocks"],
      "tools": ["TaskCreate", "TaskUpdate", "TaskGet", "TaskList"]
    }
  }
EOF

echo "}" >> "$OUTPUT"

echo "Generated: $OUTPUT"
echo "Root hash: $ROOT_HASH"
