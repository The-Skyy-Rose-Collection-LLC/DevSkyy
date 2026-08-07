#!/usr/bin/env bash
# UserPromptSubmit hook — auto-nudge Context7 docs lookup when the user's
# prompt mentions an external library / framework whose docs aren't in the
# session's 24h cache.
#
# Strategy:
#   1. Scan the user's prompt for known library keywords (case-insensitive).
#   2. For each match, check ${TMPDIR}/claude/ctx7-cache/<canonical>.
#      - File exists AND mtime < 24h ago     → considered fresh, no nudge.
#      - File missing or older than 24h      → stale, nudge.
#   3. If any libraries are stale, emit a UserPromptSubmit additionalContext
#      payload that tells Claude exactly which libs to Context7-verify
#      BEFORE generating code.
#
# This replaces the prior PreToolUse blocking gate (context7-gate.sh). It is
# structural rather than punitive: Claude sees the directive on every prompt
# that references an external lib, and can't write code that touches that lib
# without seeing it. The companion PostToolUse hook stamps the cache the
# moment Claude calls mcp__*Context7*query-docs.
#
# Disable for this shell:
#   export CONTEXT7_PREFETCH_DISABLE=1

set -euo pipefail

if [[ "${CONTEXT7_PREFETCH_DISABLE:-0}" == "1" ]]; then
    exit 0
fi

payload=$(cat)
prompt=$(printf '%s' "$payload" | jq -r '.prompt // ""')

if [[ -z "$prompt" ]]; then
    exit 0
fi

# Library detection table: parallel arrays. Each LIB_PATTERNS[i] is a
# case-insensitive ERE; LIB_NAMES[i] is the canonical cache name.
# (Bash associative arrays with regex keys break on `[`, `?`, `*` chars
# because bash tries to evaluate them as parameter expansions. Parallel
# arrays sidestep the parsing entirely.)
LIB_PATTERNS=()
LIB_NAMES=()
add_lib() { LIB_PATTERNS+=("$1"); LIB_NAMES+=("$2"); }

add_lib 'claude[._ -]?agent[._ -]?sdk'                       'claude-agent-sdk'
add_lib '@anthropic-ai/sdk|anthropic[._ -]?sdk|anthropic api|anthropic\.com' 'anthropic'
add_lib 'google[._ -]?genai|gemini[._ -]?api'                'google-genai'
add_lib 'openai[._ -]?sdk|@openai|openai api'                'openai'
add_lib 'mistralai|mistral api'                              'mistralai'
add_lib 'langchain'                                          'langchain'
add_lib 'langgraph'                                          'langgraph'
add_lib 'crewai'                                             'crewai'
add_lib 'llama[._ -]?index'                                  'llama-index'
add_lib 'fastapi'                                            'fastapi'
add_lib 'pydantic'                                           'pydantic'
add_lib 'sqlalchemy'                                         'sqlalchemy'
add_lib 'alembic migration|alembic\.ini'                     'alembic'
add_lib 'strawberry[._ -]?graphql'                           'strawberry-graphql'
add_lib 'next\.?js|nextjs|next 1[5-9]'                       'nextjs'
add_lib 'three\.?js|@react-three|react-three-fiber'          'threejs'
add_lib 'gsap|greensock'                                     'gsap'
add_lib 'framer[._ -]?motion'                                'framer-motion'
add_lib 'tailwind ?css|tailwindcss'                          'tailwindcss'
add_lib 'shadcn[/-]?ui'                                      'shadcn-ui'
add_lib 'woocommerce'                                        'woocommerce'
add_lib 'wordpress (theme|plugin|rest)'                      'wordpress'
add_lib 'elementor'                                          'elementor'
add_lib 'playwright'                                         'playwright'
add_lib 'chromadb'                                           'chromadb'
add_lib 'mcp server|mcp client|model context protocol'       'mcp'
add_lib 'stripe (api|sdk|payment)'                           'stripe'
add_lib 'voyageai|voyage embeddings'                         'voyageai'
add_lib 'meshy api|meshy\.ai'                                'meshy'
add_lib 'tripo[._ -]?(3d|ai)?'                               'tripo'
add_lib 'fashn (api|tryon)'                                  'fashn'
add_lib 'vercel (deploy|api)'                                'vercel'

cache_dir="${TMPDIR:-/tmp}/claude/ctx7-cache"
mkdir -p "$cache_dir"
ttl_seconds=$((24 * 3600))
now=$(date +%s)

stale_libs=()
for i in "${!LIB_PATTERNS[@]}"; do
    pattern="${LIB_PATTERNS[$i]}"
    canonical="${LIB_NAMES[$i]}"
    if printf '%s' "$prompt" | grep -qiE -- "$pattern"; then
        marker="$cache_dir/$canonical"
        if [[ -f "$marker" ]]; then
            mtime=$(stat -f %m "$marker" 2>/dev/null || stat -c %Y "$marker" 2>/dev/null || echo 0)
            age=$(( now - mtime ))
            if (( age < ttl_seconds )); then
                continue
            fi
        fi
        stale_libs+=("$canonical")
    fi
done

if (( ${#stale_libs[@]} == 0 )); then
    exit 0
fi

libs_csv=$(IFS=,; echo "${stale_libs[*]}")

# Emit UserPromptSubmit additionalContext — Claude sees this prepended to
# the conversation BEFORE deciding how to respond to the user's prompt.
jq -n --arg libs "$libs_csv" --arg cache_dir "$cache_dir" '
{
    hookSpecificOutput: {
        hookEventName: "UserPromptSubmit",
        additionalContext: (
            "[context7-prefetch] DevSkyy auto-detection: the user prompt mentions external library / framework: " + $libs + ".\n" +
            "No Context7 docs cached for these (or cache > 24h stale).\n\n" +
            "DevSkyy CLAUDE.md MANDATE: before generating code that touches any of the libraries above, you MUST:\n" +
            "  1. Call mcp__claude_ai_Context7__resolve-library-id (one call per library).\n" +
            "  2. Call mcp__claude_ai_Context7__query-docs with the resolved /org/repo id.\n" +
            "  3. Verify signatures against the docs.\n" +
            "  4. THEN write code.\n\n" +
            "If this prompt is conversational / planning / explanatory only (no code will be written touching these libs), you may proceed without lookup — explicitly state in your response that no Context7 call is needed because no code is being generated.\n\n" +
            "The companion PostToolUse hook will stamp the cache the moment you call query-docs; subsequent prompts in the next 24h that mention the same lib will not trigger this directive."
        )
    }
}'

exit 0
