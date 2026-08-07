#!/usr/bin/env bash
set -euo pipefail

# Lightweight, failure-safe image hook.
# This hook is intentionally conservative and non-destructive:
# - Reads tool input from stdin (if present)
# - Locates candidate image paths only
# - Skips gracefully when tools/inputs are unavailable

input="$(cat || true)"
file_path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)"
command_path="$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"

is_image_file() {
  [[ "$1" =~ \.(jpg|jpeg|png|webp|gif|svg)$ ]] || return 1
}

process_file() {
  local target="$1"
  [ -f "$target" ] || return 0
  is_image_file "$target" || return 0
  echo "[Image Hook] Skipped optimization for: $target" >&2
}

if [ -n "$file_path" ]; then
  process_file "$file_path"
elif [ -n "$command_path" ]; then
  # Best-effort extraction from command string for copy/move/fetch workflows
  while IFS= read -r token; do
    process_file "$token"
  done < <(printf '%s' "$command_path" | tr ' ' '\n' | sed -n '2,$p')
fi

printf '%s\n' "$input"
exit 0
