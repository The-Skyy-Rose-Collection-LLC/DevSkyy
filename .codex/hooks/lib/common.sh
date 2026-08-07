#!/usr/bin/env bash
# Shared helpers for DevSkyy structural-enforcement hooks.
#
# Design: structural enforcement (pre-emit context the model needs) instead
# of punitive blocking. Used by:
#   - context7-prefetch.sh      (library doc lookup)
#   - canon-prefetch.sh         (catalog / brand / cerebrum source-of-truth)
#   - learning-reminder.sh      (cerebrum / buglog update nudge)
#
# Blocking gates only appear where the action is irreversible / costs money
# (e.g., paid-api-stopgate.sh enforces CLAUDE.md STOP-AND-SHOW protocol).

set -euo pipefail

# Standard cache root. All structural hooks share this layout:
#   $CACHE_ROOT/<topic>/<canonical-name>     ← TTL'd cache files (touch-only)
#   $CACHE_ROOT/sessions/<session-id>.*      ← per-session sentinels
DEVSKYY_CACHE_ROOT="${DEVSKYY_CACHE_ROOT:-${TMPDIR:-/tmp}/claude}"

# Init a topic subdir.  Usage:  topic_dir=$(ensure_cache_topic "ctx7-cache")
ensure_cache_topic() {
    local topic="$1"
    local d="$DEVSKYY_CACHE_ROOT/$topic"
    mkdir -p "$d"
    printf '%s' "$d"
}

# Read JSON payload from stdin into a global variable.  Usage:
#   payload=$(cat); read_field "$payload" '.prompt'
read_field() {
    local payload="$1" path="$2"
    printf '%s' "$payload" | jq -r "$path // \"\""
}

# Check whether a cache marker is fresh.
# Args: <marker-path> <ttl-seconds>
# Returns: 0 (fresh) | 1 (stale or missing)
is_fresh() {
    local marker="$1" ttl="$2"
    [[ -f "$marker" ]] || return 1
    local mtime now age
    mtime=$(stat -f %m "$marker" 2>/dev/null || stat -c %Y "$marker" 2>/dev/null || echo 0)
    now=$(date +%s)
    age=$(( now - mtime ))
    (( age < ttl ))
}

# Emit UserPromptSubmit additionalContext JSON.
# Args: <multi-line context string>
emit_user_prompt_context() {
    local ctx="$1"
    jq -n --arg ctx "$ctx" '{
        hookSpecificOutput: {
            hookEventName: "UserPromptSubmit",
            additionalContext: $ctx
        }
    }'
}

# Scan a prompt against a list of pattern|name pairs (one per line, pipe-
# separated). Returns a sorted-unique list of matched canonical names on
# stdout (newline-separated).
#
# Usage:
#   matches=$(scan_patterns "$prompt" <<'EOF'
#   catalog|product[._ -]?catalog|skyyrose-catalog|catalog
#   brand|skyyrose brand|brand canon|brand voice|brand-canon
#   EOF
#   )
scan_patterns() {
    local prompt="$1"
    awk -v prompt="$prompt" '
        BEGIN { IGNORECASE = 1 }
        /^[[:space:]]*$/ || /^[[:space:]]*#/ { next }
        {
            n = index($0, "|")
            if (n == 0) next
            name = substr($0, 1, n-1)
            pat  = substr($0, n+1)
            if (match(tolower(prompt), tolower(pat))) print name
        }
    ' | sort -u
}

# Per-session sentinel path. Usage: sentinel=$(session_sentinel "ctx7")
session_sentinel() {
    local topic="$1"
    local session_id="${CLAUDE_CODE_SESSION_ID:-default}"
    ensure_cache_topic "sessions" >/dev/null
    printf '%s/sessions/%s.%s' "$DEVSKYY_CACHE_ROOT" "$session_id" "$topic"
}
