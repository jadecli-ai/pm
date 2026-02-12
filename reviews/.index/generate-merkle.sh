#!/bin/bash
# Generate Merkle tree index for Reviews system
# Outputs JSON structure for agent pre-indexing

set -e

REVIEWS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INDEX_DIR="$REVIEWS_DIR/.index"
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

for f in $(find "$REVIEWS_DIR" -type f \( -name "*.md" -o -name "*.json" -o -name "*.sh" \) ! -path "*/.index/*" | sort); do
  REL_PATH="${f#$REVIEWS_DIR/}"
  HASH=$(hash_file "$f")
  LINES=$(line_count "$f")
  FILE_HASHES["$REL_PATH"]="$HASH"

  # Extract metadata for .md files
  TYPE=""
  PURPOSE=""

  if [[ "$f" == *.md ]]; then
    if [[ "$REL_PATH" == review.schema.md ]]; then
      TYPE="schema"
      PURPOSE="schema:review"
    elif [[ "$REL_PATH" == */REVIEW-*.md ]]; then
      TYPE="review"
      REVIEW_TYPE=$(get_frontmatter_field "$f" "review_type")
      BRANCH=$(get_frontmatter_field "$f" "branch")
      PURPOSE="review:$REVIEW_TYPE:$BRANCH"
    else
      TYPE="doc"
      PURPOSE="doc:$(basename "$f" .md)"
    fi
  elif [[ "$f" == *.json ]]; then
    if [[ "$REL_PATH" == */summary.json ]]; then
      TYPE="summary"
      PURPOSE="summary:$(dirname "$REL_PATH")"
    elif [[ "$REL_PATH" == */assignments.json ]]; then
      TYPE="assignments"
      PURPOSE="assignments:$(dirname "$REL_PATH")"
    else
      TYPE="data"
      PURPOSE="data:$(basename "$f" .json)"
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
for dir in $(find "$REVIEWS_DIR" -type d ! -path "*/.index*" ! -path "*/.git*" | sort); do
  REL_DIR="${dir#$REVIEWS_DIR/}"
  [[ "$REL_DIR" == "$REVIEWS_DIR" ]] && REL_DIR="."
  [[ -z "$REL_DIR" ]] && REL_DIR="."

  # Collect hashes of all files in this directory (non-recursive)
  DIR_CONTENT=""
  for f in "$dir"/*.md "$dir"/*.json "$dir"/*.sh 2>/dev/null; do
    [[ -f "$f" ]] || continue
    REL_F="${f#$REVIEWS_DIR/}"
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
  FILE_COUNT=$(find "$dir" -maxdepth 1 -type f \( -name "*.md" -o -name "*.json" -o -name "*.sh" \) 2>/dev/null | wc -l | tr -d ' ')
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

# Add semantic index for reviews
echo '  "semanticIndex": {' >> "$OUTPUT"
cat >> "$OUTPUT" << 'EOF'
    "entryPoints": ["review.schema.md"],
    "reviewTypes": {
      "test": {"agent": "test-reviewer", "model": "opus", "focus": "coverage"},
      "value": {"agent": "value-reviewer", "model": "opus", "focus": "architecture"},
      "mlflow": {"agent": "mlflow-analyzer", "model": "opus", "focus": "performance"}
    },
    "priorities": ["P0", "P1", "P2", "P3"],
    "confidenceThreshold": 80,
    "taskGenerationRules": {
      "eligible": ["P0", "P1"],
      "minConfidence": 80
    }
  }
EOF

echo "}" >> "$OUTPUT"

echo "Generated: $OUTPUT"
echo "Root hash: $ROOT_HASH"
