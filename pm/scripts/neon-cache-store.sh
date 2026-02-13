#!/usr/bin/env bash
# pm/scripts/neon-cache-store.sh
# PostToolUse hook for WebFetch — stores fetched content in Neon cache
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(dirname "$SCRIPT_DIR")"

# Extract URL from hook input
URL=$(echo "${TOOL_INPUT:-{}}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('url', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")

if [ -z "$URL" ]; then
    exit 0
fi

# Store in background (don't block the agent)
(cd "$PM_DIR" && PYTHONPATH="$PM_DIR" python3 -m lib.neon_docs store --url "$URL" >/dev/null 2>&1) &

echo "[neon-cache] STORE: $URL (background)" >&2
exit 0
