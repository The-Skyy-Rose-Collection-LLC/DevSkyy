#!/usr/bin/env bash
# PostToolUse hook — formats a single Python file immediately after
# Edit/Write/MultiEdit with the project's canonical chain (isort -> ruff
# check --fix -> black, matching `make format`), then surfaces any remaining
# unfixable lint. Non-blocking: it formats in place and never undoes the write.
#
# The Python sibling of phpcs-on-write.sh — PHP already auto-formats on write;
# this closes the asymmetry so .py debt does not compound between commits.
#
# Skip rules:
#   - Path must end in .py
#   - Path must be under the repo root
#   - Path must NOT be under .venv*/, node_modules/, .claude/worktrees/, build/, dist/, .next/
#
# Bypass: export PY_FORMAT_ON_WRITE_DISABLE=1

set -euo pipefail

if [[ "${PY_FORMAT_ON_WRITE_DISABLE:-0}" == "1" ]]; then
    exit 0
fi

# Fail-open on missing jq — this is a formatter, not a safety gate.
if ! command -v jq >/dev/null 2>&1; then
    echo "[py-format-on-write] jq missing from PATH — skipping (warning, not blocking)." >&2
    exit 0
fi

file_path=$(cat | jq -r '.tool_input.file_path // ""')

[[ -z "$file_path" ]] && exit 0
[[ "$file_path" == *.py ]] || exit 0

# Derive repo root from script location so the hook works on every clone/worktree.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." 2>/dev/null && pwd)" || exit 0
[[ "$file_path" == "$REPO_ROOT"/* ]] || exit 0

case "$file_path" in
    "$REPO_ROOT"/.venv*/*) exit 0 ;;
    *"/node_modules/"*) exit 0 ;;
    "$REPO_ROOT"/.claude/worktrees/*) exit 0 ;;
    */build/* | */dist/* | */.next/*) exit 0 ;;
esac

[[ -f "$file_path" ]] || exit 0

# Resolve each tool from the venv first, then PATH; no-op if absent.
VENV_BIN="$REPO_ROOT/.venv/bin"
run_tool() {
    local bin="$1"
    shift
    if [[ -x "$VENV_BIN/$bin" ]]; then
        "$VENV_BIN/$bin" "$@"
    elif command -v "$bin" >/dev/null 2>&1; then
        "$bin" "$@"
    fi
}

# Canonical format chain (mirrors `make format`), scoped to one file, best-effort.
run_tool isort "$file_path" >/dev/null 2>&1 || true
run_tool ruff check --fix --quiet "$file_path" >/dev/null 2>&1 || true
run_tool black --quiet "$file_path" >/dev/null 2>&1 || true

# Surface remaining (unfixable) lint as a non-blocking warning (exit 2 = visible).
lint=$(run_tool ruff check --quiet "$file_path" 2>&1) || true
if [[ -n "$lint" ]]; then
    echo "[py-format-on-write] formatted $(basename "$file_path"); remaining lint:" >&2
    echo "" >&2
    echo "$lint" | head -30 >&2 || true
    exit 2
fi

exit 0
