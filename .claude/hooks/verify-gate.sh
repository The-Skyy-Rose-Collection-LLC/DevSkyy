#!/bin/bash
# verify-gate.sh — Stop-hook gate
# Exits 2 (block) unless one of:
#   - no uncommitted source changes this turn (nothing to verify)
#   - tasks/.last-verify-passed is fresh (updated within 10 min AND newer than last commit)
# Exit 0 allows the turn to end; exit 2 blocks.
set -u

repo=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
if [ -z "$repo" ]; then
  # Not in a repo — don't block.
  exit 0
fi

marker="$repo/tasks/.last-verify-passed"
failmarker="$repo/tasks/.last-verify-failed"

# If there are no uncommitted working-tree changes AND no staged changes, nothing to verify.
dirty=$(git -C "$repo" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$dirty" = "0" ]; then
  exit 0
fi

# Source-file detection — bash, php, js/ts/tsx, py, css trigger verification.
# Docs-only (md, txt, json unless in scripts/) are treated as skippable at the gate,
# but user can still run /go manually.
src_changed=$(git -C "$repo" status --porcelain 2>/dev/null \
  | awk '{print $2}' \
  | grep -E '\.(py|php|ts|tsx|js|jsx|css|scss|sh|sql)$' \
  | head -1)

if [ -z "$src_changed" ]; then
  # No source changes — allow end even without marker.
  exit 0
fi

# Source changes present — demand a fresh pass marker.
if [ -f "$marker" ]; then
  now=$(date +%s)
  marker_ts=$(stat -c %Y "$marker" 2>/dev/null || stat -f %m "$marker" 2>/dev/null || echo 0)
  age=$((now - marker_ts))

  if [ "$age" -lt 600 ]; then
    exit 0
  fi
  echo "[verify-gate] tasks/.last-verify-passed is ${age}s old (limit: 600s) — run /go again" >&2
else
  echo "[verify-gate] tasks/.last-verify-passed missing" >&2
fi

echo "[verify-gate] BLOCKED: source changes detected but /go has not passed this turn" >&2
echo "[verify-gate] Run /go before ending. For pure docs/config edits: touch tasks/.last-verify-passed" >&2
if [ -f "$failmarker" ]; then
  echo "[verify-gate] last failure details:" >&2
  tail -20 "$failmarker" >&2
fi
exit 2
