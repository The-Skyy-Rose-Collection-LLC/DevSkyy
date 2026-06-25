#!/usr/bin/env bash
# Regenerate .wolf/anatomy.md scoped to git main and origin/main.
#
# Pipeline:
#   1. openwolf scan  -- walks working tree, generates descriptions + token estimates
#   2. anatomy_filter_main.py  -- drops entries not present on main ∪ origin/main
#
# Idempotent. Safe to run any number of times. Output is deterministic given
# the same git state.
#
# Exit code 0 on success, non-zero if openwolf or filter fails.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if ! command -v openwolf >/dev/null 2>&1; then
  echo "openwolf CLI not found on PATH" >&2
  exit 1
fi

openwolf scan >/dev/null
python3 scripts/anatomy_filter_main.py

# `openwolf scan` always rewrites the `Last scanned: <ISO>` header line,
# even when nothing else changed. That timestamp-only drift used to drive
# an infinite "post-commit: anatomy ... were regenerated" → commit → drift
# loop. If the timestamp is the only diff vs HEAD, revert the file so the
# working tree stays clean.
ANATOMY_TIMESTAMP_RE='^> Auto-maintained by OpenWolf\. Last scanned:'
if git diff --quiet -I "$ANATOMY_TIMESTAMP_RE" -- .wolf/anatomy.md 2>/dev/null; then
  git checkout -- .wolf/anatomy.md 2>/dev/null || true
fi
