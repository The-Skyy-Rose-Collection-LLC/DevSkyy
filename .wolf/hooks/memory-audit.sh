#!/usr/bin/env bash
# .wolf/hooks/memory-audit.sh
#
# Thin wrapper around memory-audit.py. Callable directly (manual run) or wired
# into Claude Code SessionStart hooks via ~/.claude/settings.json:
#
#   {
#     "type": "command",
#     "command": "bash /Users/theceo/DevSkyy/.wolf/hooks/memory-audit.sh",
#     "timeout": 5
#   }
#
# Exits 0 on success (including when decay is detected — decay is informational,
# not a failure). Exits non-zero only if the Python script crashes.
#
# Override repo root with SKYYROSE_REPO_ROOT env var if needed.

set -euo pipefail

REPO_ROOT="${SKYYROSE_REPO_ROOT:-/Users/theceo/DevSkyy}"
AUDIT_PY="${REPO_ROOT}/.wolf/hooks/memory-audit.py"

if [[ ! -f "$AUDIT_PY" ]]; then
  echo "[memory-audit] $AUDIT_PY not found" >&2
  exit 0   # non-blocking — a missing audit script shouldn't kill the session
fi

exec python3 "$AUDIT_PY" "$@"
