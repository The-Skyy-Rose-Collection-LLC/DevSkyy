#!/bin/bash
# PostToolUse Hook — Track structural changes for CLAUDE.md staleness detection
#
# Fires on Write/Edit/Bash tool calls. Detects structural changes (new files,
# deletions, renames, new directories, config edits) and tracks which CLAUDE.md
# files may be stale as a result.
#
# Design: filter-first — parse JSON, check exclusions, exit early. Only ~10%
# of calls that represent structural changes do any real work.
#
# Data flow:
#   stdin JSON → classify → filter → walk-up to nearest CLAUDE.md → append tracker → threshold alert
#
# Tracker file: /tmp/claude-md-tracker-YYYYMMDD (daily, accumulates across sessions)

set -euo pipefail

# --- Parse stdin JSON ---
input=$(cat)
tool=$(echo "$input" | jq -r '.tool // ""')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')
command=$(echo "$input" | jq -r '.tool_input.command // ""')

# --- Config ---
TRACKER="${TRACKER:-/tmp/claude-md-tracker-$(date +%Y%m%d)}"
THRESHOLD=3

# --- Classify change type and extract target path(s) ---
change_type=""
target_path=""

case "$tool" in
  Write)
    target_path="$file_path"
    # Will check git ls-files later (after filters) to determine if new
    change_type="pending_write"
    ;;
  Edit)
    target_path="$file_path"
    # Only structural if editing a config file
    basename_file=$(basename "$file_path" 2>/dev/null || echo "")
    case "$basename_file" in
      __init__.py|functions.php|package.json)
        change_type="config_edit"
        ;;
      *)
        # Regular edit — not a structural change
        exit 0
        ;;
    esac
    ;;
  Bash)
    # Look for rm/mkdir/mv anywhere in the command (decision 7B)
    if echo "$command" | grep -qE '\brm\b'; then
      # Extract the last argument that looks like a path
      target_path=$(echo "$command" | grep -oE '[^ ]+$' | head -1)
      change_type="del_file"
    elif echo "$command" | grep -qE '\bmkdir\b'; then
      target_path=$(echo "$command" | grep -oE '[^ ]+$' | head -1)
      change_type="new_dir"
    elif echo "$command" | grep -qE '\bmv\b'; then
      # For mv, track the destination (last arg)
      target_path=$(echo "$command" | grep -oE '[^ ]+$' | head -1)
      change_type="rename"
    else
      # No structural command detected
      exit 0
    fi
    ;;
  *)
    # Unknown tool — not tracked
    exit 0
    ;;
esac

# --- FILTER GATE (fast exits before any expensive operations) ---

# No target path extracted
[ -z "$target_path" ] && exit 0

# Reject flag-like targets (e.g., "rm -rf" → "-rf" extracted as last word)
case "$target_path" in
  -*) exit 0 ;;
esac

# Reject paths with embedded newlines (jq -r decodes JSON \n sequences)
case "$target_path" in
  *$'\n'*) exit 0 ;;
esac

# --- Determine repo root from the target path (not file_path, which is empty for Bash) ---
# For absolute paths, use the target's directory. For relative paths, use CWD.
if [[ "$target_path" == /* ]]; then
  _resolve_dir=$(dirname "$target_path")
else
  _resolve_dir="."
fi
REPO_ROOT=$(git -C "$_resolve_dir" rev-parse --show-toplevel 2>/dev/null || git rev-parse --show-toplevel 2>/dev/null || echo "")
[ -z "$REPO_ROOT" ] && exit 0

# Resolve to absolute path if relative
if [[ "$target_path" != /* ]]; then
  target_path="$REPO_ROOT/$target_path"
fi

# Canonicalize path to resolve symlinks (macOS: /tmp → /private/tmp)
# git rev-parse resolves symlinks in REPO_ROOT, so target_path must match
target_dir=$(cd "$(dirname "$target_path")" 2>/dev/null && pwd -P) || target_dir=$(dirname "$target_path")
target_path="$target_dir/$(basename "$target_path")"

# Skip image/asset files
case "$target_path" in
  *.webp|*.jpg|*.jpeg|*.png|*.svg|*.gif|*.mp4|*.mp3|*.wav|*.ico|*.woff|*.woff2|*.ttf|*.eot)
    exit 0
    ;;
esac

# Skip CLAUDE.md files themselves
if [[ "$(basename "$target_path")" == "CLAUDE.md" ]]; then
  exit 0
fi

# Skip paths outside repo root
if [[ "$target_path" != "$REPO_ROOT"/* ]]; then
  exit 0
fi

# Skip paths inside .claude/worktrees/
if [[ "$target_path" == *"/.claude/worktrees/"* ]]; then
  exit 0
fi

# --- Write-specific: check if file is new (untracked by git) ---
if [ "$change_type" = "pending_write" ]; then
  if git -C "$REPO_ROOT" ls-files --error-unmatch "$target_path" >/dev/null 2>&1; then
    # File is tracked — this is an overwrite, not a structural change
    exit 0
  fi
  change_type="new_file"
fi

# --- Walk UP to nearest CLAUDE.md ---
dir=$(dirname "$target_path")
claude_md=""

while [ "$dir" != "/" ] && [[ "$dir" == "$REPO_ROOT"* ]]; do
  if [ -f "$dir/CLAUDE.md" ]; then
    claude_md="$dir/CLAUDE.md"
    break
  fi
  dir=$(dirname "$dir")
done

# No CLAUDE.md found in any ancestor — skip
[ -z "$claude_md" ] && exit 0

# Make path relative to repo root
relative_claude_md="${claude_md#$REPO_ROOT/}"
relative_target="${target_path#$REPO_ROOT/}"

# --- Append to daily tracker ---
echo "${relative_claude_md}|${change_type}|${relative_target}" >> "$TRACKER"

# --- Threshold alert ---
count=$(grep -c "^${relative_claude_md}|" "$TRACKER" 2>/dev/null || echo "0")

if [ "$count" -eq "$THRESHOLD" ]; then
  echo "[CLAUDE.md] ${relative_claude_md} may be stale (${count} structural changes)" >&2
  echo "[CLAUDE.md] Run /revise-claude-md when ready" >&2
elif [ "$count" -gt "$THRESHOLD" ] && [ $((count % 5)) -eq 0 ]; then
  echo "[CLAUDE.md] ${relative_claude_md} — ${count} structural changes and counting" >&2
fi
