#!/usr/bin/env bash
# Parallel security gate on changed files — bandit | secret scan | npm audit
# Usage:
#   security.sh                    # changed files vs HEAD
#   security.sh --staged           # staged files only
#   security.sh --base <branch>    # branch diff (e.g. --base main)
#   security.sh --files a.py b.ts  # explicit file list
#   security.sh --deps             # ALSO run pip-audit (slow, network)
#
# Exit 0 = clean. Exit 1 = HIGH/CRITICAL finding or hardcoded secret.
#
# Suppress a false positive:
#   inline       add  devflow:allow-secret  on the same line
#   whole file   put  devflow:allow-secrets-file  in the first 5 lines

set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

STAGED=0
BASE=""
DEPS=0
EXPLICIT_FILES=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --staged) STAGED=1; shift ;;
    --base)   BASE="$2"; shift 2 ;;
    --deps)   DEPS=1; shift ;;
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

if [[ ${#ALL_FILES[@]} -eq 0 && $DEPS -eq 0 ]]; then
  echo "security: no changed files detected"
  exit 0
fi

# ── Secret-scan exclusions (false-positive killers) ──────────────────────────
_excluded() {
  case "$1" in
    *node_modules/*|*/vendor/*|*.venv*|*__pycache__*|.wolf/*|*/.wolf/*) return 0 ;;
    tests/*|*/tests/*|docs/*|*/docs/*) return 0 ;;
    *.example|*.sample|*.md|*.min.*|*-lock.json|package-lock.json|*.lock|*.map) return 0 ;;
  esac
  return 1
}

# ── Bucket by type ────────────────────────────────────────────────────────────
PY_FILES=()
JS_FILES=()
SCAN_FILES=()
PKG_CHANGED=0

for f in "${ALL_FILES[@]}"; do
  case "$f" in
    /*) abs="$f"; rel="${f#"$ROOT"/}" ;;
    *)  abs="$ROOT/$f"; rel="$f" ;;
  esac
  [[ ! -f "$abs" ]] && continue
  case "$rel" in
    package.json|*/package.json|package-lock.json|*/package-lock.json) PKG_CHANGED=1 ;;
  esac
  case "$abs" in
    *.py)                              PY_FILES+=("$abs") ;;
    *.ts|*.tsx|*.js|*.jsx|*.mjs|*.cjs) JS_FILES+=("$abs") ;;
  esac
  _excluded "$rel" || SCAN_FILES+=("$abs")
done

# ── Secret patterns (literal file — no bash quote hell, POSIX ERE) ───────────
cat > "$TMP/secret_patterns.txt" <<'PATTERNS'
-----BEGIN ([A-Z]+ )?PRIVATE KEY-----
AKIA[0-9A-Z]{16}
sk-ant-[a-zA-Z0-9_-]{20,}
sk-[a-zA-Z0-9]{32,}
ghp_[0-9A-Za-z]{36}
gho_[0-9A-Za-z]{36}
glpat-[0-9A-Za-z_-]{20,}
xox[baprs]-[0-9A-Za-z-]{10,}
AIza[0-9A-Za-z_-]{35}
(api[_-]?key|secret|token|passwd|password|client[_-]?secret|access[_-]?key)["']?[[:space:]]*[:=][[:space:]]*["'][^"']{12,}["']
PATTERNS

PIDS=()

# ── Python: bandit (HIGH severity, MEDIUM+ confidence) ───────────────────────
if [[ ${#PY_FILES[@]} -gt 0 ]] && command -v python3 >/dev/null 2>&1; then
  {
    echo "[py:bandit]"
    python3 -m bandit --severity-level high --confidence-level medium \
      -f custom --msg-template "{abspath}:{line}: {test_id} {severity}: {msg}" \
      "${PY_FILES[@]}" 2>/dev/null | grep -E ': B[0-9]+ ' || true
  } > "$TMP/bandit.txt" &
  PIDS+=($!)
fi

# ── Secret scan (grep — zero tool dependency) ────────────────────────────────
if [[ ${#SCAN_FILES[@]} -gt 0 ]]; then
  {
    echo "[secrets]"
    for fp in "${SCAN_FILES[@]}"; do
      if [[ -f "$fp" && ! -L "$fp" ]] && head -n 5 "$fp" 2>/dev/null | grep -q 'devflow:allow-secrets-file'; then
        continue
      fi
      grep -nE -f "$TMP/secret_patterns.txt" "$fp" 2>/dev/null \
        | grep -v 'devflow:allow-secret' \
        | awk -v F="$fp" '{ print F ":" $0 }' || true
    done
  } > "$TMP/secrets.txt" &
  PIDS+=($!)
fi

# ── npm audit (only if JS changed or package manifest touched) ───────────────
if [[ ( ${#JS_FILES[@]} -gt 0 || $PKG_CHANGED -eq 1 ) && -f "$ROOT/frontend/package.json" ]]; then
  {
    echo "[npm:audit]"
    cd "$ROOT/frontend"
    npm audit --audit-level=high --json 2>/dev/null | python3 - <<'PY' || true
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
vulns = data.get("metadata", {}).get("vulnerabilities", {})
high = vulns.get("high", 0)
crit = vulns.get("critical", 0)
if high or crit:
    print(f"frontend/package.json:0: NPM-AUDIT: {crit} critical + {high} high vulnerable deps (run: cd frontend && npm audit)")
PY
  } > "$TMP/npm.txt" &
  PIDS+=($!)
fi

# ── pip-audit (opt-in: slow, network-bound) ──────────────────────────────────
if [[ $DEPS -eq 1 ]] && command -v python3 >/dev/null 2>&1; then
  {
    echo "[py:pip-audit]"
    cd "$ROOT"
    python3 -m pip_audit . --progress-spinner=off 2>/dev/null \
      | grep -E '^[A-Za-z0-9_.-]+ ' | grep -viE '^name|^---|no known vuln' || true
  } > "$TMP/pipaudit.txt" &
  PIDS+=($!)
fi

# Wait for all parallel scans (bash 3 safe — empty array guard)
[[ ${#PIDS[@]} -gt 0 ]] && for pid in "${PIDS[@]}"; do wait "$pid" 2>/dev/null || true; done

# ── Aggregate & report ────────────────────────────────────────────────────────
TOTAL=0

print_section() {
  local file="$1"
  [[ ! -s "$file" ]] && return 0
  local lines
  lines=$(grep -vc '^\[' "$file" | tr -d '[:space:]' || echo 0)
  [[ "$lines" -eq 0 ]] && return 0
  TOTAL=$((TOTAL + lines))
  cat "$file"
  echo ""
}

echo ""
echo "┌────────────────────────────────────────┐"
echo "│         DEVWORKFLOW SECURITY           │"
echo "└────────────────────────────────────────┘"
echo ""
echo "Scanned: ${#ALL_FILES[@]} file(s)"
echo ""

print_section "$TMP/bandit.txt"
print_section "$TMP/secrets.txt"
print_section "$TMP/npm.txt"
print_section "$TMP/pipaudit.txt"

echo "────────────────────────────────────────"
echo "Findings: $TOTAL"

[[ $TOTAL -gt 0 ]] && exit 1 || exit 0
