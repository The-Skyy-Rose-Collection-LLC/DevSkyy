#!/usr/bin/env bash
# DEPRECATED 2026-05-13. Replaced by context7-prefetch.sh (UserPromptSubmit
# auto-nudge with 24h per-library cache). This blocking gate is kept on
# disk for revival emergencies — to re-enable, restore the PreToolUse
# matcher block in .claude/settings.json and (optionally) disable the
# prefetch hook. See cerebrum.md "Context7 auto-prefetch" entry for the
# senior-engineering rationale (alarm fatigue vs structural enforcement).
#
# Original purpose follows.
# =========================
# PreToolUse hook — enforce DevSkyy CLAUDE.md Context7-first protocol.
#
# Blocks Write/Edit/MultiEdit on .py/.ts/.tsx/.js/.jsx files that touch an
# external library unless Context7 docs were already queried this session.
#
# Allow-list: edits to files without external-lib imports are unaffected.
# Bypass:    touch the sentinel manually if you've already verified out-of-band:
#              touch "${TMPDIR:-/tmp}/ctx7-${CLAUDE_CODE_SESSION_ID:-default}.touched"
#
# Companion hook context7-touched.sh creates the sentinel on Context7 use.

set -euo pipefail

# Disable gate entirely:  export CONTEXT7_GATE_DISABLE=1
if [[ "${CONTEXT7_GATE_DISABLE:-0}" == "1" ]]; then
    exit 0
fi

payload=$(cat)

tool_name=$(printf '%s' "$payload" | jq -r '.tool_name // ""')
case "$tool_name" in
    Write|Edit|MultiEdit) ;;
    *) exit 0 ;;
esac

file_path=$(printf '%s' "$payload" | jq -r '.tool_input.file_path // ""')
case "$file_path" in
    *.py|*.ts|*.tsx|*.js|*.jsx|*.mjs|*.cjs) ;;
    *) exit 0 ;;
esac

# Coding file detected — Context7 lookup required this session, period.
# Per DevSkyy CLAUDE.md "Context7 first — non-negotiable on every task."
# No external-lib filter: ANY coding file edit gates on Context7.

# Sentinel: Context7 already queried this session?
session_id="${CLAUDE_CODE_SESSION_ID:-default}"
sentinel_dir="${TMPDIR:-/tmp}/claude"
sentinel="${sentinel_dir}/ctx7-${session_id}.touched"

if [[ -f "$sentinel" ]]; then
    exit 0
fi

# Block — emit reason on stderr per Claude Code PreToolUse spec.
cat >&2 <<EOF
[context7-gate] BLOCKED: $tool_name on $file_path

DevSkyy CLAUDE.md MANDATES Context7 documentation lookup BEFORE writing or
editing any coding file (.py, .ts, .tsx, .js, .jsx, .mjs, .cjs). No
external-lib filter: every coding-file edit requires Context7 verification
of the libraries / APIs / patterns you'll use, even for refactors and
internal-only files (you may still touch types, signatures, framework APIs).

Required steps in THIS session before the edit is allowed:
  1. Call  mcp__claude_ai_Context7__resolve-library-id  for the relevant lib
  2. Call  mcp__claude_ai_Context7__query-docs          for the resolved id
  3. Verify the exact signatures / patterns you're about to use
  4. THEN retry this Write/Edit/MultiEdit

If the edit truly involves zero library / framework / pattern surface (e.g.,
a one-line comment, a typo fix, a string-literal change), bypass the gate
explicitly:
  touch "${sentinel}"

Permanently disable for this shell (not recommended):
  export CONTEXT7_GATE_DISABLE=1
EOF

exit 2
