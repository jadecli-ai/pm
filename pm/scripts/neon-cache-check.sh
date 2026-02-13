#!/usr/bin/env bash
# pm/scripts/neon-cache-check.sh
# PreToolUse hook for WebFetch — checks Neon cache before fetching
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(dirname "$SCRIPT_DIR")"

# Extract URL from hook input (TOOL_INPUT env var contains JSON)
URL=$(echo "${TOOL_INPUT:-{}}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('url', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")

if [ -z "$URL" ]; then
    exit 0  # No URL, let WebFetch proceed
fi

# Check cache (suppress errors — hook must not block agent)
RESULT=$(cd "$PM_DIR" && PYTHONPATH="$PM_DIR" python3 -m lib.neon_docs check-url "$URL" 2>/dev/null) || RESULT="CACHE_MISS"

if [ "$RESULT" != "CACHE_MISS" ] && [ -n "$RESULT" ]; then
    echo "[neon-cache] HIT: $URL" >&2
    echo "$RESULT"
else
    echo "[neon-cache] MISS: $URL" >&2
fi

exit 0
