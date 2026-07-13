#!/bin/bash
# Stop Hook — Summarize CLAUDE.md staleness at session end
#
# Reads the daily tracker, groups changes by CLAUDE.md file, emits a
# formatted summary to stderr, and persists to .claude/claude-md-staleness.log
# for next-session carry-over.
#
# Does NOT delete the /tmp tracker (decision 6A — avoids race with concurrent sessions).

set -euo pipefail

TRACKER="${TRACKER:-/tmp/claude-md-tracker-$(date +%Y%m%d)}"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "/Users/theceo/DevSkyy")
STALENESS_LOG="${STALENESS_LOG:-$REPO_ROOT/.claude/claude-md-staleness.log}"

# Exit if no tracker or tracker is empty
if [ ! -s "$TRACKER" ]; then
  exit 0
fi

# --- Group by CLAUDE.md path, count changes, collect unique types ---
# Output format: "  COUNT changes → CLAUDE_MD (type1,type2)"
summary=$(awk -F'|' '
{
  claude_md = $1
  change_type = $2
  counts[claude_md]++
  if (!seen[claude_md, change_type]++) {
    if (types[claude_md] == "")
      types[claude_md] = change_type
    else
      types[claude_md] = types[claude_md] "," change_type
  }
}
END {
  for (cm in counts) {
    printf "  %d changes -> %s (%s)\n", counts[cm], cm, types[cm]
  }
}
' "$TRACKER" | sort -rn)

# Exit if summary is empty (shouldn't happen if tracker has content, but defensive)
[ -z "$summary" ] && exit 0

# --- Emit formatted summary to stderr ---
{
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "[CLAUDE.md] Session Staleness Report"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "$summary" | sed 's/->/→/'
  echo ""
  echo "Run /revise-claude-md to update stale files"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
} >&2

# --- Persist to staleness log for next-session carry-over ---
mkdir -p "$(dirname "$STALENESS_LOG")"
{
  echo "# CLAUDE.md Staleness Report — $(date '+%Y-%m-%d %H:%M')"
  echo "$summary" | sed 's/->/→/'
} > "$STALENESS_LOG"
