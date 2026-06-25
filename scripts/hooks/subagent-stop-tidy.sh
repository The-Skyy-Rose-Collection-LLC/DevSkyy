#!/usr/bin/env bash
# L5 dirty-file reducer — fires after subagent stops.
# OBSERVE mode (default): logs proposed actions to .claude/tidy-log.jsonl, no fs changes.
# ACTIVE mode (TIDY_MODE=active): also reverts/deletes whitelisted noise.
#
# Whitelist (confidence 1.0 — provably safe):
#   - Files whose only added content is an empty <claude-mem-context></claude-mem-context> block
#   - OS artifacts: .DS_Store, *.pyc, *.swp, *.swo
#
# Safety properties:
#   - Never auto-commits
#   - Never touches files outside the whitelist
#   - Skips read-only subagent types (Explore, investigator, mapper, classifier, search)
#   - Skips in CI environments

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "$ROOT" ]] && exit 0
cd "$ROOT"

MODE="${TIDY_MODE:-observe}"
LOG=".claude/tidy-log.jsonl"
SUBAGENT_TYPE="${1:-${CLAUDE_SUBAGENT_TYPE:-unknown}}"

[[ -n "${CI:-}" ]] && exit 0

case "$SUBAGENT_TYPE" in
  Explore|*investigator*|*mapper*|*classifier*|*search*|*explore*|gsd-codebase-mapper|gsd-doc-classifier)
    exit 0
    ;;
esac

mkdir -p "$(dirname "$LOG")"
ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

emit() {
  local file="$1" action="$2" pattern="$3"
  jq -nc \
    --arg ts "$ts" \
    --arg subagent "$SUBAGENT_TYPE" \
    --arg mode "$MODE" \
    --arg file "$file" \
    --arg action "$action" \
    --arg pattern "$pattern" \
    '{ts:$ts, subagent:$subagent, mode:$mode, file:$file, action:$action, pattern:$pattern, confidence:1.0}' \
    >> "$LOG"
}

is_empty_stub_diff() {
  local file="$1"
  local diff
  diff="$(git diff -- "$file" 2>/dev/null)" || return 1
  [[ -z "$diff" ]] && return 1
  echo "$diff" | grep -qE '^\+<claude-mem-context>$' || return 1
  echo "$diff" | grep -qE '^\+</claude-mem-context>$' || return 1
  if echo "$diff" | grep -E '^\+' \
      | grep -vqE '^\+\+\+|^\+$|^\+[[:space:]]*$|^\+<claude-mem-context>$|^\+</claude-mem-context>$'; then
    return 1
  fi
  return 0
}

is_empty_stub_file() {
  local file="$1"
  [[ ! -f "$file" ]] && return 1
  local content
  content="$(tr -d '[:space:]' < "$file")"
  [[ "$content" == "<claude-mem-context></claude-mem-context>" ]]
}

while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  if is_empty_stub_diff "$file"; then
    emit "$file" "revert" "empty-claude-mem-context-stub"
    if [[ "$MODE" == "active" ]]; then
      git checkout -- "$file" 2>/dev/null || true
    fi
  fi
done < <(git diff --name-only --diff-filter=M 2>/dev/null | grep -E '(^|/)CLAUDE\.md$' || true)

while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  if is_empty_stub_file "$file"; then
    emit "$file" "delete" "empty-claude-mem-context-stub"
    if [[ "$MODE" == "active" ]]; then
      rm -f "$file"
    fi
  fi
done < <(git ls-files --others --exclude-standard 2>/dev/null | grep -E '(^|/)CLAUDE\.md$' || true)

while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  emit "$file" "delete" "os-noise"
  if [[ "$MODE" == "active" ]]; then
    rm -f "$file"
  fi
done < <(git status --porcelain 2>/dev/null | awk '{print $NF}' | grep -E '(\.DS_Store|\.pyc|\.swp|\.swo)$' || true)

exit 0
