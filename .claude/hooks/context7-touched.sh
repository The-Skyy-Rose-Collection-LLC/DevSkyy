#!/usr/bin/env bash
# PostToolUse companion to context7-prefetch.sh (and legacy context7-gate.sh).
#
# Fires after mcp__*Context7*query-docs and stamps two markers:
#   1. Per-library cache: ${TMPDIR}/claude/ctx7-cache/<canonical>
#      — read by context7-prefetch.sh with a 24h TTL so freshly-queried libs
#        don't re-trigger nudges on every subsequent prompt.
#   2. Per-session sentinel: ${TMPDIR}/claude/ctx7-${SESSION_ID}.touched
#      — kept for backward compatibility with the (now-disabled) blocking
#        gate, in case it gets re-enabled.

set -euo pipefail

payload=$(cat)
tool_name=$(printf '%s' "$payload" | jq -r '.tool_name // ""')

case "$tool_name" in
    *Context7*query-docs|*context7*query-docs) ;;
    *) exit 0 ;;
esac

cache_dir="${TMPDIR:-/tmp}/claude/ctx7-cache"
mkdir -p "$cache_dir"

# Extract libraryId (e.g., "/anthropics/claude-agent-sdk-python") and
# normalize to a canonical cache name. Strip leading /, strip org prefix,
# strip language suffix.
lib_id=$(printf '%s' "$payload" | jq -r '.tool_input.libraryId // .tool_input.libraryName // ""')

if [[ -n "$lib_id" ]]; then
    canonical=$(printf '%s' "$lib_id" \
        | sed 's|^/||; s|.*/||; s|-python$||; s|-js$||; s|-ts$||; s|-node$||; s|-docs$||' \
        | tr '[:upper:]' '[:lower:]' \
        | tr -c 'a-z0-9.-' '-' \
        | sed 's|^-*||; s|-*$||')
    if [[ -n "$canonical" ]]; then
        touch "$cache_dir/$canonical"
    fi
fi

# Legacy per-session sentinel for the blocking gate (still useful if anyone
# re-enables it via settings.json).
session_id="${CLAUDE_CODE_SESSION_ID:-default}"
mkdir -p "${TMPDIR:-/tmp}/claude"
touch "${TMPDIR:-/tmp}/claude/ctx7-${session_id}.touched"

exit 0
