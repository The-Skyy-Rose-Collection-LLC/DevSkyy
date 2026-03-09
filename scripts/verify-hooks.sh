#!/usr/bin/env bash
set -uo pipefail

# Permanent verification script for Husky v9 hook infrastructure.
# Runs 4 checks and exits 0 (all pass) or 1 (any fail).

PASS=0
FAIL=0
TEMP_BRANCH=""
TEMP_FILE=""
ORIG_BRANCH=""

cleanup() {
  if [[ -n "$TEMP_FILE" && -f "$TEMP_FILE" ]]; then
    rm -f "$TEMP_FILE" 2>/dev/null || true
  fi
  if [[ -n "$TEMP_BRANCH" ]]; then
    git reset HEAD~1 --quiet 2>/dev/null || true
    git checkout "$ORIG_BRANCH" --quiet 2>/dev/null || true
    git branch -D "$TEMP_BRANCH" --quiet 2>/dev/null || true
  fi
}
trap cleanup EXIT

check_pass() {
  echo "  PASS: $1"
  PASS=$((PASS + 1))
}

check_fail() {
  echo "  FAIL: $1"
  FAIL=$((FAIL + 1))
}

echo "=== Husky Hook Verification ==="
echo ""

# Check 1: .husky/pre-commit exists
echo "Check 1: .husky/pre-commit exists"
if test -f .husky/pre-commit; then
  check_pass ".husky/pre-commit exists"
else
  check_fail ".husky/pre-commit does not exist"
fi

# Check 2: .husky/pre-commit is executable
echo "Check 2: .husky/pre-commit is executable"
if test -x .husky/pre-commit; then
  check_pass ".husky/pre-commit is executable"
else
  check_fail ".husky/pre-commit is not executable"
fi

# Check 3: core.hooksPath is set to .husky/_
echo "Check 3: core.hooksPath is .husky/_"
HOOKS_PATH=$(git config core.hooksPath 2>/dev/null || echo "")
if [[ "$HOOKS_PATH" == ".husky/_" ]]; then
  check_pass "core.hooksPath = .husky/_"
else
  check_fail "core.hooksPath = '$HOOKS_PATH' (expected .husky/_)"
fi

# Check 4: Hook fires on commit
echo "Check 4: Pre-commit hook fires on test commit"
ORIG_BRANCH=$(git branch --show-current 2>/dev/null || git rev-parse --short HEAD)
TEMP_BRANCH="verify-hooks-test-$$"
TEMP_FILE="$(git rev-parse --show-toplevel)/.verify-hooks-temp-$$"

if git checkout -b "$TEMP_BRANCH" --quiet 2>/dev/null; then
  echo "test" > "$TEMP_FILE"
  git add "$TEMP_FILE" 2>/dev/null || true

  # Capture commit output; ignore exit code (post-commit LFS hook may return non-zero)
  COMMIT_OUTPUT=$(git commit -m "hook test" 2>&1) || true

  if echo "$COMMIT_OUTPUT" | grep -q "pre-commit hook active"; then
    check_pass "pre-commit hook fired (output contains 'pre-commit hook active')"
  else
    check_fail "pre-commit hook did not fire (expected 'pre-commit hook active' in output)"
  fi

  # Clean up the test commit
  git reset HEAD~1 --quiet 2>/dev/null || true
  rm -f "$TEMP_FILE" 2>/dev/null || true
  git checkout "$ORIG_BRANCH" --quiet 2>/dev/null || true
  git branch -D "$TEMP_BRANCH" --quiet 2>/dev/null || true
  # Clear trap targets since we cleaned up manually
  TEMP_BRANCH=""
  TEMP_FILE=""
else
  check_fail "Could not create test branch"
  TEMP_BRANCH=""
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
exit 0
