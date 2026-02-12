#!/bin/bash
# Pre-commit hook for Claude Code
# Validates code before allowing commits

set -e

# Read hook input from stdin
input=$(cat)

# Extract tool input
tool_input=$(echo "$input" | jq -r '.tool_input // empty')
command=$(echo "$tool_input" | jq -r '.command // empty')

# Only process git commit commands
if [[ ! "$command" =~ ^git\ commit ]]; then
  echo '{}'
  exit 0
fi

# Check for secrets patterns in staged files
secrets_found=false
staged_files=$(git diff --cached --name-only 2>/dev/null || true)

for file in $staged_files; do
  if [[ -f "$file" ]]; then
    # Check for common secret patterns
    if grep -qE '(api[_-]?key|secret[_-]?key|password|credential|private[_-]?key)\s*[:=]' "$file" 2>/dev/null; then
      echo "Warning: Potential secret found in $file" >&2
      secrets_found=true
    fi

    # Check for AWS keys
    if grep -qE 'AKIA[0-9A-Z]{16}' "$file" 2>/dev/null; then
      echo "Warning: Potential AWS key found in $file" >&2
      secrets_found=true
    fi
  fi
done

if [[ "$secrets_found" == "true" ]]; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","decision":"reject","reason":"Potential secrets detected in staged files"}}'
else
  echo '{}'
fi
