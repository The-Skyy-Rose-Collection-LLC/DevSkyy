#!/usr/bin/env bash
# Ship gate — composite pre-push gate. Fail-fast: cheap stages first.
# Order: lint → security → tests  (hard, stop at first failure)
#        then clean-tree + changelog (advisory; --strict makes them hard)
# Usage:
#   ship.sh                # gate this branch vs main (or working changes on main)
#   ship.sh --base <b>     # override base branch (default: main)
#   ship.sh --strict       # clean-tree + changelog become hard failures
#
# Exit 0 = ready to ship. Exit 1 = a gate failed (message says which).

set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
DW="$ROOT/scripts/devworkflows"
cd "$ROOT"

BASE="main"
STRICT=0
while [[ $# -gt 0 ]]; do
  case $1 in
    --base)   BASE="$2"; shift 2 ;;
    --strict) STRICT=1; shift ;;
    *) shift ;;
  esac
done

BRANCH="$(git rev-parse --abbrev-ref HEAD)"

# Review/security scope: branch diff when on a feature branch, else working tree.
REVIEW_ARGS=()
[[ "$BRANCH" != "$BASE" ]] && REVIEW_ARGS=(--base "$BASE")

# ── Helpers ───────────────────────────────────────────────────────────────────
_commit_range() {
  if [[ "$BRANCH" != "$BASE" ]]; then
    local mb
    mb="$(git merge-base HEAD "$BASE" 2>/dev/null || echo "")"
    [[ -n "$mb" ]] && echo "$mb..HEAD"
  else
    git rev-list "origin/$BASE..HEAD" >/dev/null 2>&1 && echo "origin/$BASE..HEAD"
  fi
}

_clean_tree() { [[ -z "$(git status --porcelain)" ]]; }

_changelog_touched() {
  local range
  range="$(_commit_range)"
  if [[ -n "$range" ]] && git diff --name-only "$range" 2>/dev/null | grep -qx "CHANGELOG.md"; then
    return 0
  fi
  git status --porcelain | grep -q ' CHANGELOG.md$'
}

# Anything to ship at all?
HAS_DIFF=0
[[ -n "$(git status --porcelain)" ]] && HAS_DIFF=1
[[ -n "$(_commit_range)" ]] && [[ -n "$(git rev-list "$(_commit_range)" 2>/dev/null || echo "")" ]] && HAS_DIFF=1

if [[ $HAS_DIFF -eq 0 ]]; then
  echo "ship: nothing to ship (no diff vs $BASE, clean tree). exit: 0"
  exit 0
fi

echo ""
echo "╔════════════════════════════════════════╗"
echo "║          DEVWORKFLOW SHIP              ║"
echo "╚════════════════════════════════════════╝"
echo "branch: $BRANCH   base: $BASE   strict: $STRICT"
echo ""

# Hard stage: run it; on failure print the block reason and exit immediately.
hard_stage() {
  local name="$1"; shift
  echo "── $name ───────────────────────────────"
  if bash "$@"; then
    echo "✔ $name PASS"
    echo ""
    return 0
  fi
  echo ""
  echo "✘ $name FAILED — ship blocked here."
  echo "  Fix the findings above, then re-run: bash scripts/devworkflows/ship.sh"
  echo "════════════════════════════════════════"
  echo "BLOCKED at: $name"
  echo "exit: 1"
  exit 1
}

# 1. lint
if [[ ${#REVIEW_ARGS[@]} -gt 0 ]]; then
  hard_stage "lint" "$DW/review.sh" "${REVIEW_ARGS[@]}"
else
  hard_stage "lint" "$DW/review.sh"
fi

# 2. security
if [[ ${#REVIEW_ARGS[@]} -gt 0 ]]; then
  hard_stage "security" "$DW/security.sh" "${REVIEW_ARGS[@]}"
else
  hard_stage "security" "$DW/security.sh"
fi

# 3. tests (slowest — only reached if lint + security are clean)
hard_stage "tests" "$DW/tdd.sh"

# ── Advisory checks (only reached when all hard gates pass) ──────────────────
WARN=0
soft_check() {
  local name="$1"; shift
  if "$@"; then
    echo "✔ $name"
  elif [[ $STRICT -eq 1 ]]; then
    echo "✘ $name (strict) — ship blocked"
    echo "════════════════════════════════════════"
    echo "BLOCKED at: $name"
    echo "exit: 1"
    exit 1
  else
    echo "⚠ $name — advisory (enforce with --strict)"
    WARN=1
  fi
}

echo "── advisory ────────────────────────────"
soft_check "clean-tree (all changes committed)" _clean_tree
soft_check "changelog touched"                  _changelog_touched
echo ""

echo "════════════════════════════════════════"
[[ $WARN -eq 1 ]] && echo "READY TO SHIP — with advisories above"
[[ $WARN -eq 0 ]] && echo "READY TO SHIP — all gates green"
echo "exit: 0"
exit 0
