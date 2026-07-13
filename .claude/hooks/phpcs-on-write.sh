#!/usr/bin/env bash
# PostToolUse hook — runs PHPCS WordPress standard on a single PHP file
# immediately after Edit/Write/MultiEdit. Non-blocking warning (exit 2 surfaces
# findings to Claude but does not undo the write).
#
# Catches violations at write time so debt does not compound between deploys.
# Memory log shows: 156 errors → 0 across 3 sessions, phpcbf run 6+ times.
# Per-file scan at write time prevents that cycle.
#
# Skip rules:
#   - Path must end in .php
#   - Path must be under wordpress-theme/skyyrose-flagship/
#   - Path must NOT be under vendor/, tests/coverage/, node_modules/, or assets/js/lib/
#
# Bypass: export PHPCS_ON_WRITE_DISABLE=1

set -euo pipefail

if [[ "${PHPCS_ON_WRITE_DISABLE:-0}" == "1" ]]; then
    exit 0
fi

# Fail-open on missing jq — this is a style linter, not a safety gate.
# Blocking writes because a lint helper can't parse the payload would punish
# users for a missing dev tool. paid-api-stopgate.sh fails closed because
# money is at stake; PHPCS findings are not money.
if ! command -v jq >/dev/null 2>&1; then
    echo "[phpcs-on-write] jq missing from PATH — skipping (warning, not blocking)." >&2
    exit 0
fi

payload=$(cat)
file_path=$(printf '%s' "$payload" | jq -r '.tool_input.file_path // ""')

# Skip if no file path in payload
[[ -z "$file_path" ]] && exit 0

# Skip if not PHP
[[ "$file_path" == *.php ]] || exit 0

# Derive theme path from script location so the hook works on every clone,
# worktree, and the secondary machine (coreyfoster). Hardcoded absolute path
# silently disabled the hook anywhere outside /Users/theceo/DevSkyy/.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEME_DIR="$(cd "$SCRIPT_DIR/../../wordpress-theme/skyyrose-flagship" 2>/dev/null && pwd)" || {
    echo "[phpcs-on-write] theme dir not found relative to script — skipping." >&2
    exit 0
}
[[ "$file_path" == "$THEME_DIR"/* ]] || exit 0

# Skip excluded subdirectories (mirrors .phpcs.xml exclude-pattern exactly).
# tests/* must be skipped wholesale — phpcs honors exclude-pattern only
# when sniffing directories, not when given an explicit file path.
case "$file_path" in
    "$THEME_DIR"/vendor/*)        exit 0 ;;
    "$THEME_DIR"/node_modules/*)  exit 0 ;;
    "$THEME_DIR"/tests/*)         exit 0 ;;
    "$THEME_DIR"/assets/js/lib/*) exit 0 ;;
esac

# File must exist on disk (Write may have just created it, Edit modified it)
[[ -f "$file_path" ]] || exit 0

# PHPCS binary must exist (composer install required)
PHPCS_BIN="$THEME_DIR/vendor/bin/phpcs"
if [[ ! -x "$PHPCS_BIN" ]]; then
    echo "[phpcs-on-write] vendor/bin/phpcs missing — run: cd $THEME_DIR && composer install" >&2
    exit 0
fi

# Run phpcs with theme root as cwd so the .phpcs.xml resolves relative paths
cd "$THEME_DIR"
result=$("$PHPCS_BIN" --standard=.phpcs.xml -s --report=full "$file_path" 2>&1) || rc=$?
rc=${rc:-0}

# PHPCS exit codes: 0=clean, 1=errors found, 2=warnings only, 3=errors+warnings.
# Any non-zero means findings worth surfacing.
if [[ "$rc" -eq 0 ]]; then
    exit 0
fi

# Surface findings to Claude via stderr (exit 2 = warning visible, non-blocking).
# `|| true` on head prevents SIGPIPE from killing the hook under set -o pipefail
# when phpcs output is shorter than the head limit.
echo "[phpcs-on-write] PHPCS findings in $(basename "$file_path"):" >&2
echo "" >&2
echo "$result" | head -50 >&2 || true
echo "" >&2
echo "[phpcs-on-write] Fix with: cd $THEME_DIR && vendor/bin/phpcbf --standard=.phpcs.xml '$file_path'" >&2
exit 2
