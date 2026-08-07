#!/usr/bin/env bash
# PostToolUse companion to learning-reminder.sh.
#
# Watches Bash tool calls + Edit tool calls for fingerprints of bug fixes,
# test runs that produce failures, build errors, and corrections. When a
# tripwire fires, appends a one-line reason to the session-scoped trigger
# file. At Stop time, learning-reminder.sh reads that file and emits the
# reminder.

set -euo pipefail

# shellcheck source=lib/common.sh
source "$(dirname "$0")/lib/common.sh"

payload=$(cat)
tool_name=$(read_field "$payload" '.tool_name')

trigger_file=$(session_sentinel "learning-trigger")
log_reason() {
    printf '  - %s\n' "$1" >> "$trigger_file"
}

case "$tool_name" in
    Bash)
        cmd=$(read_field "$payload" '.tool_input.command')
        output=$(read_field "$payload" '.tool_response.stdout // .tool_response.output // ""')
        # Test failure / build error fingerprints
        if printf '%s' "$output" | grep -qiE 'FAILED|ERROR|Traceback|fatal:|exit code: [1-9]|build failed'; then
            log_reason "Test / build failure detected in Bash output"
        fi
        # Bug-fix commit pattern
        if printf '%s' "$cmd" | grep -qE 'git commit.*-m.*(fix|hotfix|bugfix|patch|repair)'; then
            log_reason "Bug-fix commit: $(printf '%s' "$cmd" | head -c 100)"
        fi
        ;;
    Edit|MultiEdit)
        new_str=$(read_field "$payload" '.tool_input.new_string')
        if printf '%s' "$new_str" | grep -qiE 'FIXME|TODO|XXX|HACK|known bug|workaround'; then
            log_reason "New FIXME/TODO/HACK comment added"
        fi
        ;;
esac

exit 0
