#!/usr/bin/env bash
set -euo pipefail

################################################################################
# setup-branch-protection.sh
#
# Idempotent script to configure GitHub branch protection on main.
# Requires: gh CLI authenticated with repo scope.
#
# Usage:
#   bash scripts/setup-branch-protection.sh           # Apply + verify
#   bash scripts/setup-branch-protection.sh --verify   # Verify only (read-only)
################################################################################

OWNER="The-Skyy-Rose-Collection-LLC"
REPO="DevSkyy"
BRANCH="main"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
pass() { echo "  PASS: $1"; }
fail() { echo "  FAIL: $1"; FAILURES=$((FAILURES + 1)); }

# ---------------------------------------------------------------------------
# Step 1: Enable auto-merge on the repository
# ---------------------------------------------------------------------------
enable_auto_merge() {
  echo "==> Step 1: Enabling auto-merge on repository..."
  gh api --method PATCH "repos/$OWNER/$REPO" \
    -f allow_auto_merge=true \
    --silent
  echo "    Auto-merge enabled."
}

# ---------------------------------------------------------------------------
# Step 2: Set branch protection rules via PUT
# ---------------------------------------------------------------------------
apply_protection() {
  echo "==> Step 2: Setting branch protection rules on $BRANCH..."

  # Write JSON payload to a temp file to guarantee UTF-8 encoding of emoji
  local payload_file
  payload_file=$(mktemp)
  trap 'rm -f "$payload_file"' EXIT

  cat > "$payload_file" <<'PAYLOAD'
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      {"context": "🔍 Lint & Static Analysis", "app_id": -1},
      {"context": "🐍 Python Tests", "app_id": -1},
      {"context": "🔐 Security Scan", "app_id": -1},
      {"context": "⚛️ Frontend Tests", "app_id": -1},
      {"context": "🏗️ WordPress Theme", "app_id": -1}
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
PAYLOAD

  gh api --method PUT "repos/$OWNER/$REPO/branches/$BRANCH/protection" \
    --input "$payload_file" \
    --silent

  rm -f "$payload_file"
  trap - EXIT

  echo "    Branch protection applied."
}

# ---------------------------------------------------------------------------
# Step 3: Verify all settings
# ---------------------------------------------------------------------------
verify() {
  echo "==> Step 3: Verifying branch protection settings..."
  echo ""

  FAILURES=0

  # Check 1: Required status checks count equals 5
  local check_count
  check_count=$(gh api "repos/$OWNER/$REPO/branches/$BRANCH/protection" \
    --jq '.required_status_checks.checks | length' 2>/dev/null || echo "0")
  if [ "$check_count" = "5" ]; then
    pass "Required status checks: $check_count/5 configured"
  else
    fail "Required status checks: $check_count/5 configured (expected 5)"
  fi

  # Check 2: Strict mode (branch must be up-to-date)
  local strict
  strict=$(gh api "repos/$OWNER/$REPO/branches/$BRANCH/protection" \
    --jq '.required_status_checks.strict' 2>/dev/null || echo "false")
  if [ "$strict" = "true" ]; then
    pass "Strict mode (up-to-date required): $strict"
  else
    fail "Strict mode (up-to-date required): $strict (expected true)"
  fi

  # Check 3: Enforce admins (block direct pushes)
  local enforce_admins
  enforce_admins=$(gh api "repos/$OWNER/$REPO/branches/$BRANCH/protection" \
    --jq '.enforce_admins.enabled' 2>/dev/null || echo "false")
  if [ "$enforce_admins" = "true" ]; then
    pass "Enforce admins (direct push blocked): $enforce_admins"
  else
    fail "Enforce admins (direct push blocked): $enforce_admins (expected true)"
  fi

  # Check 4: Force pushes blocked
  local force_pushes
  force_pushes=$(gh api "repos/$OWNER/$REPO/branches/$BRANCH/protection" \
    --jq '.allow_force_pushes.enabled' 2>/dev/null || echo "true")
  if [ "$force_pushes" = "false" ]; then
    pass "Force pushes blocked: allow_force_pushes=$force_pushes"
  else
    fail "Force pushes blocked: allow_force_pushes=$force_pushes (expected false)"
  fi

  # Check 5: Auto-merge enabled on repository
  local auto_merge
  auto_merge=$(gh api "repos/$OWNER/$REPO" \
    --jq '.allow_auto_merge' 2>/dev/null || echo "false")
  if [ "$auto_merge" = "true" ]; then
    pass "Auto-merge enabled: $auto_merge"
  else
    fail "Auto-merge enabled: $auto_merge (expected true)"
  fi

  echo ""
  if [ "$FAILURES" -eq 0 ]; then
    echo "All 5 checks PASSED. Branch protection is correctly configured."
    exit 0
  else
    echo "$FAILURES check(s) FAILED. Branch protection is NOT correctly configured."
    exit 1
  fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  echo "GitHub Branch Protection Setup"
  echo "Repo: $OWNER/$REPO  Branch: $BRANCH"
  echo "----------------------------------------"

  if [ "${1:-}" = "--verify" ]; then
    echo "Mode: VERIFY ONLY (read-only)"
    echo ""
    verify
  else
    echo "Mode: APPLY + VERIFY"
    echo ""
    enable_auto_merge
    echo ""
    apply_protection
    echo ""
    verify
  fi
}

main "$@"
