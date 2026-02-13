#!/usr/bin/env bash
# pm/tests/neon_docs/test_hooks.sh
# Test hook scripts are syntactically valid and handle edge cases
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "=== Hook Script Tests ==="

# Test 1: cache-check handles empty TOOL_INPUT
echo "▶ Test 1: cache-check with empty input"
TOOL_INPUT="" bash "$PM_DIR/scripts/neon-cache-check.sh" > /dev/null 2>&1
echo "✅ PASS: cache-check handles empty input"

# Test 2: cache-check handles malformed JSON
echo "▶ Test 2: cache-check with malformed JSON"
TOOL_INPUT="not json" bash "$PM_DIR/scripts/neon-cache-check.sh" > /dev/null 2>&1
echo "✅ PASS: cache-check handles malformed JSON"

# Test 3: cache-store handles empty TOOL_INPUT
echo "▶ Test 3: cache-store with empty input"
TOOL_INPUT="" bash "$PM_DIR/scripts/neon-cache-store.sh" > /dev/null 2>&1
echo "✅ PASS: cache-store handles empty input"

echo ""
echo "=== All hook tests passed ==="
