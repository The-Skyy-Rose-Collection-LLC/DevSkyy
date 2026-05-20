#!/usr/bin/env bash
# Parallel lint review of changed files — ruff | tsc | phpcs
# Usage:
#   review.sh                    # all changes vs last commit
#   review.sh --staged           # staged files only
#   review.sh --base <branch>    # branch diff (e.g. --base main)
#   review.sh --files a.py b.ts  # explicit file list

set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

STAGED=0
BASE=""
EXPLICIT_FILES=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --staged) STAGED=1; shift ;;
    --base)   BASE="$2"; shift 2 ;;
    --files)  shift; while [[ $# -gt 0 && "$1" != --* ]]; do EXPLICIT_FILES+=("$1"); shift; done ;;
    *) shift ;;
  esac
done

# ── Collect changed files (bash 3 compat — no mapfile) ────────────────────────
ALL_FILES=()

_read_lines_into_all() {
  local line
  while IFS= read -r line; do
    [[ -n "$line" ]] && ALL_FILES+=("$line")
  done
}

if [[ ${#EXPLICIT_FILES[@]} -gt 0 ]]; then
  ALL_FILES=("${EXPLICIT_FILES[@]}")
elif [[ $STAGED -eq 1 ]]; then
  _read_lines_into_all < <(git diff --cached --name-only --diff-filter=ACMR)
elif [[ -n "$BASE" ]]; then
  _read_lines_into_all < <(git diff --name-only --diff-filter=ACMR "$(git merge-base HEAD "$BASE")" HEAD)
else
  _read_lines_into_all < <({ git diff --cached --name-only --diff-filter=ACMR; git diff --name-only --diff-filter=ACMR HEAD; } | sort -u)
fi

if [[ ${#ALL_FILES[@]} -eq 0 ]]; then
  echo "review: no changed files detected"
  exit 0
fi

# ── Bucket by type ────────────────────────────────────────────────────────────
PY_FILES=()
TS_FILES=()
PHP_FILES=()

for f in "${ALL_FILES[@]}"; do
  # Support both absolute paths and repo-relative paths
  case "$f" in
    /*) abs="$f" ;;
    *)  abs="$ROOT/$f" ;;
  esac
  [[ ! -f "$abs" ]] && continue
  case "$abs" in
    *.py)       PY_FILES+=("$abs") ;;
    *.ts|*.tsx) TS_FILES+=("$abs") ;;
    *.php)      PHP_FILES+=("$abs") ;;
  esac
done

RUFF_BIN="$(command -v ruff 2>/dev/null || echo "")"
PHP_BIN="/opt/homebrew/bin/php"
PHPCS_BIN="$ROOT/wordpress-theme/skyyrose-flagship/vendor/bin/phpcs"
PHPCS_CFG="$ROOT/wordpress-theme/skyyrose-flagship/.phpcs.xml"

PIDS=()
AUTOFIX=0
[[ "${FIX:-0}" == "1" ]] && AUTOFIX=1

# ── Python: ruff ─────────────────────────────────────────────────────────────
if [[ ${#PY_FILES[@]} -gt 0 && -n "$RUFF_BIN" ]]; then
  {
    echo "[py:ruff]"
    if [[ $AUTOFIX -eq 1 ]]; then
      "$RUFF_BIN" check --fix "${PY_FILES[@]}" --output-format=concise 2>&1 \
        | grep -v "^All checks passed" | grep -v "^Found [0-9]" || true
    else
      "$RUFF_BIN" check "${PY_FILES[@]}" --output-format=concise 2>&1 \
        | grep -v "^All checks passed" | grep -v "^Found [0-9]" || true
    fi
  } > "$TMP/ruff.txt" &
  PIDS+=($!)
fi

# ── TypeScript: tsc ───────────────────────────────────────────────────────────
if [[ ${#TS_FILES[@]} -gt 0 && -d "$ROOT/frontend" ]]; then
  {
    echo "[ts:tsc]"
    cd "$ROOT/frontend"
    npx --yes tsc --noEmit 2>&1 | grep -E "error TS[0-9]" | head -40 || true
  } > "$TMP/tsc.txt" &
  PIDS+=($!)
fi

# ── PHP: syntax + phpcs ───────────────────────────────────────────────────────
if [[ ${#PHP_FILES[@]} -gt 0 ]]; then
  {
    echo "[php:syntax]"
    for fp in "${PHP_FILES[@]}"; do
      "$PHP_BIN" -l "$fp" 2>&1 | grep -v "^No syntax errors" || true
    done

    if [[ -x "$PHPCS_BIN" && -f "$PHPCS_CFG" ]]; then
      echo "[php:phpcs]"
      "$PHPCS_BIN" --standard="$PHPCS_CFG" --report=emacs "${PHP_FILES[@]}" 2>&1 || true
    fi
  } > "$TMP/php.txt" &
  PIDS+=($!)
fi

# Wait for all parallel linters (bash 3 safe — empty array guard)
[[ ${#PIDS[@]} -gt 0 ]] && for pid in "${PIDS[@]}"; do wait "$pid" 2>/dev/null || true; done

# ── Aggregate & report ────────────────────────────────────────────────────────
TOTAL=0

print_section() {
  local file="$1"
  [[ ! -s "$file" ]] && return 0
  # Count only non-header, non-empty lines (actual findings)
  local lines
  lines=$(grep -vc '^\[' "$file" | tr -d '[:space:]' || echo 0)
  [[ "$lines" -eq 0 ]] && return 0  # only had header, skip
  TOTAL=$((TOTAL + lines))
  cat "$file"
  echo ""
}

echo ""
echo "┌────────────────────────────────────────┐"
echo "│          DEVWORKFLOW REVIEW            │"
echo "└────────────────────────────────────────┘"
echo ""
echo "Changed: ${#ALL_FILES[@]} file(s)"
echo ""

print_section "$TMP/ruff.txt"
print_section "$TMP/tsc.txt"
print_section "$TMP/php.txt"

echo "────────────────────────────────────────"
echo "Findings: $TOTAL"

[[ $TOTAL -gt 0 ]] && exit 1 || exit 0
