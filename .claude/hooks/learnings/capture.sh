#!/bin/bash
# capture.sh — Stop hook: detect lesson-worthy signals in the session transcript
# and append candidates to tasks/learnings-staging.jsonl.
#
# Reads the hook payload (JSON) on stdin. The Claude Code hook protocol passes
# session metadata; transcript access varies by version. We stay defensive: if
# the transcript isn't available, we still capture git-based signals (red-green
# fix via working-tree diff) so the pipeline is useful even without transcript.
#
# Never blocks the turn — always exits 0.
set -u

repo=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
if [ -z "$repo" ]; then exit 0; fi

staging="$repo/tasks/learnings-staging.jsonl"
mkdir -p "$(dirname "$staging")"

# Read hook payload from stdin (may be empty on some platforms).
payload=""
if [ ! -t 0 ]; then
  payload=$(cat || true)
fi

# Extract transcript_path if provided — the hook protocol may include it.
transcript=""
if [ -n "$payload" ] && command -v jq >/dev/null 2>&1; then
  transcript=$(echo "$payload" | jq -r '.transcript_path // .transcript // empty' 2>/dev/null || true)
fi

session_id=""
if [ -n "$payload" ] && command -v jq >/dev/null 2>&1; then
  session_id=$(echo "$payload" | jq -r '.session_id // empty' 2>/dev/null || true)
fi
[ -z "$session_id" ] && session_id="unknown"

ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Classify touched files into a category
classify_category() {
  local files="$1"
  if echo "$files" | grep -qE '^wordpress-theme/.*/deploy|scripts/deploy-theme\.sh'; then
    echo "WordPress Deploy"; return
  fi
  if echo "$files" | grep -qE '^wordpress-theme/'; then echo "WordPress"; return; fi
  if echo "$files" | grep -qE '^frontend/'; then echo "Frontend"; return; fi
  if echo "$files" | grep -qE '^agents/|^llm/|^orchestration/'; then echo "Architecture"; return; fi
  if echo "$files" | grep -qE '^security/|auth|jwt|csrf'; then echo "Security"; return; fi
  if echo "$files" | grep -qE '^\.claude/hooks/'; then echo "Hooks"; return; fi
  if echo "$files" | grep -qE '^api/'; then echo "Architecture"; return; fi
  echo "General"
}

# Compute a stable context hash for dedup
hash_context() {
  printf '%s|%s' "$1" "$2" | sha256sum 2>/dev/null | awk '{print "sha256:"$1}' \
    || printf '%s|%s' "$1" "$2" | shasum -a 256 | awk '{print "sha256:"$1}'
}

emit_candidate() {
  # $1=pattern, $2=category, $3=severity, $4=lesson, $5=evidence
  local pattern="$1" category="$2" severity="$3" lesson="$4" evidence="$5"
  local ctx_hash
  ctx_hash=$(hash_context "$pattern" "$evidence")

  # Skip if this context_hash already in staging (turn-level dedup)
  if [ -f "$staging" ] && grep -Fq "\"context_hash\":\"$ctx_hash\"" "$staging" 2>/dev/null; then
    return
  fi

  # Escape JSON strings minimally (replace " and \)
  local j_lesson j_evidence j_cat j_session
  j_lesson=$(printf '%s' "$lesson" | sed 's/\\/\\\\/g; s/"/\\"/g')
  j_evidence=$(printf '%s' "$evidence" | sed 's/\\/\\\\/g; s/"/\\"/g')
  j_cat=$(printf '%s' "$category" | sed 's/"/\\"/g')
  j_session=$(printf '%s' "$session_id" | sed 's/"/\\"/g')

  printf '{"ts":"%s","category":"%s","severity":"%s","context_hash":"%s","lesson":"%s","evidence":"%s","session_id":"%s","pattern":"%s"}\n' \
    "$ts" "$j_cat" "$severity" "$ctx_hash" "$j_lesson" "$j_evidence" "$j_session" "$pattern" \
    >> "$staging"
}

# --- Signal 1: red → green via transcript (if available) ---
# Look for a Bash call that exited non-zero followed by the same command exiting zero.
if [ -n "$transcript" ] && [ -f "$transcript" ] && command -v jq >/dev/null 2>&1; then
  # Transcript is JSONL of messages. Extract Bash tool_use/tool_result pairs.
  # This is best-effort; schema varies. Guard every step.
  tmp=$(mktemp)
  jq -r 'select(.type=="tool_use" or .type=="tool_result") | @json' "$transcript" 2>/dev/null > "$tmp" || true

  # Detect pytest / test failure followed by success
  if grep -q '"name":"Bash"' "$tmp" 2>/dev/null; then
    if grep -qE '(pytest|npm (run )?test|vitest|jest).*(FAIL|Error|fail)' "$tmp" 2>/dev/null \
       && grep -qE '(passed|PASS|ok.*ran|✓.*passed)' "$tmp" 2>/dev/null; then
      files=$(git -C "$repo" diff --name-only HEAD 2>/dev/null | head -5 | tr '\n' ',' | sed 's/,$//')
      category=$(classify_category "$files")
      lesson="Test suite went red→green — candidate for a behavioral learning"
      emit_candidate "red_green_fix" "$category" "low" "$lesson" "$files"
    fi
  fi

  # Detect code-reviewer agent flagging CRITICAL/HIGH
  if grep -qE '"(code-reviewer|security-reviewer)"' "$tmp" 2>/dev/null \
     && grep -qE '(CRITICAL|HIGH|SEVERITY_HIGH)' "$tmp" 2>/dev/null; then
    files=$(git -C "$repo" diff --name-only HEAD 2>/dev/null | head -5 | tr '\n' ',' | sed 's/,$//')
    category=$(classify_category "$files")
    lesson="Reviewer flagged CRITICAL/HIGH during session — codify the fix as a learning"
    emit_candidate "reviewer_flag" "$category" "high" "$lesson" "$files"
  fi

  rm -f "$tmp"
fi

# --- Signal 2: verify-gate previously blocked, now we're passing ---
# If a recent .last-verify-failed exists and was followed by a successful verify,
# that's a pattern worth capturing.
failmarker="$repo/tasks/.last-verify-failed"
passmarker="$repo/tasks/.last-verify-passed"
if [ -f "$failmarker" ] && [ -f "$passmarker" ]; then
  fail_ts=$(stat -c %Y "$failmarker" 2>/dev/null || stat -f %m "$failmarker" 2>/dev/null || echo 0)
  pass_ts=$(stat -c %Y "$passmarker" 2>/dev/null || stat -f %m "$passmarker" 2>/dev/null || echo 0)
  if [ "$pass_ts" -gt "$fail_ts" ] && [ $((pass_ts - fail_ts)) -lt 3600 ]; then
    files=$(git -C "$repo" diff --name-only HEAD 2>/dev/null | head -5 | tr '\n' ',' | sed 's/,$//')
    category=$(classify_category "$files")
    fail_first_line=$(head -1 "$failmarker" 2>/dev/null | cut -c1-160)
    lesson="verify-gate blocked turn then passed — root cause: ${fail_first_line:-see last-verify-failed}"
    emit_candidate "hook_block_resolution" "$category" "medium" "$lesson" "$files"
  fi
fi

# --- Signal 3: phpcs ran clean after earlier failure (WP workflow) ---
if [ -n "$transcript" ] && [ -f "$transcript" ] && command -v jq >/dev/null 2>&1; then
  if grep -qE 'phpcs.*(ERROR|FOUND.*ERROR)' "$transcript" 2>/dev/null \
     && grep -qE '(phpcbf|No errors found|0 errors)' "$transcript" 2>/dev/null; then
    lesson="PHPCS surfaced WPCS violations — record the cause to avoid recurring"
    emit_candidate "phpcs_violation_fixed" "WordPress" "low" "$lesson" "wordpress-theme/skyyrose-flagship/"
  fi
fi

exit 0
