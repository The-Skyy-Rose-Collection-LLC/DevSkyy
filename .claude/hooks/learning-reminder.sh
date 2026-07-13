#!/usr/bin/env bash
# Stop hook — structural reminder to update cerebrum / buglog / memory.md
# when the just-ended session contained corrections, bug fixes, or new
# learnings.
#
# Per OPENWOLF.md: "BEFORE fixing any bug: read .wolf/buglog.json. AFTER
# fixing: ALWAYS log to .wolf/buglog.json." Also: "After receiving a user
# correction, update .wolf/cerebrum.md immediately."
#
# This hook fires when Claude finishes its turn (Stop event). It does NOT
# block — it injects a final message that nudges Claude to check whether
# the session warrants a cerebrum/buglog/memory update before ending.
#
# Tracking: any Bash tool call this session matching common bug-fix or
# error-resolution patterns drops a marker. If markers exist at Stop, the
# hook injects the reminder.

set -euo pipefail

# shellcheck source=lib/common.sh
source "$(dirname "$0")/lib/common.sh"

if [[ "${LEARNING_REMINDER_DISABLE:-0}" == "1" ]]; then
    exit 0
fi

session_marker=$(session_sentinel "learning-trigger")

# At Stop time, check if any learning-worthy markers exist for THIS session.
if [[ ! -f "$session_marker" ]]; then
    exit 0
fi

# Read the marker (it lists the trigger reasons).
reasons=$(cat "$session_marker" 2>/dev/null || echo "unspecified")

# Stop hook does NOT accept hookSpecificOutput.additionalContext (that schema is
# UserPromptSubmit/PostToolUse only). The Stop event has no "next turn" to
# inject context into — Claude has already finished. Emit a human-readable
# advisory to stderr (visible in the terminal) and exit cleanly. No stdout
# JSON, so the schema validator stays happy.
{
    printf '\n[learning-reminder] Session contained learning-worthy events:\n'
    printf '%s\n' "$reasons"
    printf '\nBefore closing, consider updating:\n'
    printf '  1. .wolf/cerebrum.md  — Key Learning / Do-Not-Repeat entry\n'
    printf '  2. .wolf/buglog.json  — bug fix / error resolution row\n'
    printf '  3. .wolf/memory.md    — one-row session summary\n'
    printf '  4. .wolf/anatomy.md   — file create/delete/rename updates\n\n'
} >&2

# Clear the marker so the reminder fires once per learning-worthy session.
rm -f "$session_marker"
exit 0
