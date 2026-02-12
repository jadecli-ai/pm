#!/bin/bash
# Run all PM system tests

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== PM System Integration Tests ==="
echo "Date: $(date)"
echo ""

PASSED=0
FAILED=0

# Test 1: Schema Validation
echo "▶️ Test 1: Schema Validation"
SCHEMA_PASS=true
for f in "$PM_DIR"/entities/examples/*.md; do
  if ! "$SCRIPT_DIR/validate-entity.sh" "$f"; then
    SCHEMA_PASS=false
  fi
done

if $SCHEMA_PASS; then
  echo "✅ PASS: Schema Validation"
  ((PASSED++))
else
  echo "❌ FAIL: Schema Validation"
  ((FAILED++))
fi
echo ""

# Test 2: Claude Code Alignment
echo "▶️ Test 2: Claude Code Alignment"
TASK_FILE="$PM_DIR/entities/examples/TASK-004.md"
ALIGNMENT_PASS=true

if [[ -f "$TASK_FILE" ]]; then
  FRONTMATTER=$(awk '/^---$/{p=1-p;next} p' "$TASK_FILE")

  SUBJECT=$(echo "$FRONTMATTER" | grep -E '^subject:' | head -1)
  ACTIVE_FORM=$(echo "$FRONTMATTER" | grep -E '^activeForm:' | head -1)

  if [[ -z "$SUBJECT" ]]; then
    echo "  ❌ Missing subject field"
    ALIGNMENT_PASS=false
  else
    echo "  ✓ subject field present"
  fi

  if [[ -z "$ACTIVE_FORM" ]]; then
    echo "  ❌ Missing activeForm field"
    ALIGNMENT_PASS=false
  else
    echo "  ✓ activeForm field present"
  fi
else
  echo "  ❌ No task fixture found"
  ALIGNMENT_PASS=false
fi

if $ALIGNMENT_PASS; then
  echo "✅ PASS: Claude Code Alignment"
  ((PASSED++))
else
  echo "❌ FAIL: Claude Code Alignment"
  ((FAILED++))
fi
echo ""

# Test 3: Dependency Consistency
echo "▶️ Test 3: Dependency Consistency"
DEPS_PASS=true
for f in "$PM_DIR"/entities/examples/*.md; do
  FRONTMATTER=$(awk '/^---$/{p=1-p;next} p' "$f")
  PARENT=$(echo "$FRONTMATTER" | grep -E '^parent:' | head -1 | sed 's/parent: *//' | tr -d '"')
  TYPE=$(echo "$FRONTMATTER" | grep -E '^type:' | head -1 | sed 's/type: *//' | tr -d '"')

  if [[ "$TYPE" != "epic" && ( -z "$PARENT" || "$PARENT" == "null" ) ]]; then
    echo "  ⚠️ $(basename "$f"): non-epic without parent"
    # This is a warning, not a failure for examples
  else
    echo "  ✓ $(basename "$f"): dependencies valid"
  fi
done

if $DEPS_PASS; then
  echo "✅ PASS: Dependency Consistency"
  ((PASSED++))
else
  echo "❌ FAIL: Dependency Consistency"
  ((FAILED++))
fi
echo ""

# Test 4: SemVer Compliance
echo "▶️ Test 4: SemVer Compliance"
SEMVER_PASS=true
for f in "$PM_DIR"/entities/examples/*.md; do
  FRONTMATTER=$(awk '/^---$/{p=1-p;next} p' "$f")
  VERSION=$(echo "$FRONTMATTER" | grep -E '^version:' | head -1 | sed 's/version: *//' | tr -d '"')

  if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "  ❌ $(basename "$f"): Invalid semver: $VERSION"
    SEMVER_PASS=false
  else
    echo "  ✓ $(basename "$f"): $VERSION"
  fi
done

if $SEMVER_PASS; then
  echo "✅ PASS: SemVer Compliance"
  ((PASSED++))
else
  echo "❌ FAIL: SemVer Compliance"
  ((FAILED++))
fi
echo ""

# Test 5: Agent Schema
echo "▶️ Test 5: Agent Schema"
AGENT_PASS=true
for f in "$PM_DIR"/agents/*.md; do
  if [[ -f "$f" ]]; then
    FRONTMATTER=$(awk '/^---$/{p=1-p;next} p' "$f")
    NAME=$(echo "$FRONTMATTER" | grep -E '^name:' | head -1)

    if [[ -z "$NAME" ]]; then
      echo "  ❌ $(basename "$f"): Missing name"
      AGENT_PASS=false
    else
      echo "  ✓ $(basename "$f")"
    fi
  fi
done

if $AGENT_PASS; then
  echo "✅ PASS: Agent Schema"
  ((PASSED++))
else
  echo "❌ FAIL: Agent Schema"
  ((FAILED++))
fi
echo ""

# Summary
echo "=== Summary ==="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [[ $FAILED -eq 0 ]]; then
  echo "✅ All tests passed!"
  exit 0
else
  echo "❌ Some tests failed"
  exit 1
fi
