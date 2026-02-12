#!/bin/bash
# Post-edit hook to suggest running tests
# Runs after file edits in src/ or lib/ directories

set -e

# Read hook input from stdin
input=$(cat)

# Extract file path from tool input
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Only process source files
if [[ ! "$file_path" =~ ^(src|lib)/ ]]; then
  echo '{}'
  exit 0
fi

# Determine test framework based on project files
if [[ -f "pyproject.toml" ]] || [[ -f "pytest.ini" ]]; then
  echo "Reminder: Run 'pytest' to verify changes" >&2
elif [[ -f "package.json" ]]; then
  echo "Reminder: Run 'npm test' to verify changes" >&2
elif [[ -f "Cargo.toml" ]]; then
  echo "Reminder: Run 'cargo test' to verify changes" >&2
fi

echo '{}'
