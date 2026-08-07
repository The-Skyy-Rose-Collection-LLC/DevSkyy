#!/bin/bash
# Test harness for CLAUDE.md staleness tracking hooks
# Runs 21 test cases covering all codepaths from the plan review.
#
# Usage: bash .claude/hooks/claude-md-tracker/test-hooks.sh
#
# Each test feeds mock JSON to track-changes.sh and verifies whether a
# tracker line was appended (or not). Uses a temp directory with mock
# CLAUDE.md files to simulate the repo structure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TRACK_SCRIPT="$SCRIPT_DIR/track-changes.sh"
SUMMARY_SCRIPT="$SCRIPT_DIR/session-summary.sh"
SESSION_START_SCRIPT="$(dirname "$SCRIPT_DIR")/memory-persistence/session-start.sh"

PASS=0
FAIL=0
TOTAL=0

# --- Setup temp repo ---
TMPDIR_BASE=$(mktemp -d)
REPO="$TMPDIR_BASE/test-repo"
mkdir -p "$REPO"
cd "$REPO"
git init -q
git config user.email "test@test.com"
git config user.name "Test"

# Create mock directory structure with CLAUDE.md files
mkdir -p core/cqrs scripts wordpress-theme/skyyrose-flagship/inc .claude/worktrees/fix
echo "# Core" > core/CLAUDE.md
echo "# Scripts" > scripts/CLAUDE.md
echo "# WP Theme" > wordpress-theme/CLAUDE.md
echo "# Root" > CLAUDE.md
# Create an existing tracked file
echo "existing content" > core/existing.py
git add -A && git commit -q -m "init"

# Override TRACKER and STALENESS_LOG to use test-specific files
export TRACKER="$TMPDIR_BASE/test-tracker"
export STALENESS_LOG="$TMPDIR_BASE/test-staleness.log"

# --- Helpers ---
run_test() {
  local test_num="$1"
  local test_name="$2"
  local json_input="$3"
  local expect_line="$4"  # "yes" or "no" — should a tracker line be added?

  TOTAL=$((TOTAL + 1))

  # Clear tracker for each test
  rm -f "$TRACKER"

  # Run the script (override REPO_ROOT detection via git)
  local output
  output=$(echo "$json_input" | bash "$TRACK_SCRIPT" 2>&1) || true

  local has_line="no"
  if [ -f "$TRACKER" ] && [ -s "$TRACKER" ]; then
    has_line="yes"
  fi

  if [ "$has_line" = "$expect_line" ]; then
    PASS=$((PASS + 1))
    echo "  PASS  T${test_num}: ${test_name}"
  else
    FAIL=$((FAIL + 1))
    echo "  FAIL  T${test_num}: ${test_name} (expected=${expect_line}, got=${has_line})"
    if [ -f "$TRACKER" ]; then
      echo "        tracker: $(cat "$TRACKER")"
    fi
    if [ -n "$output" ]; then
      echo "        output: $output"
    fi
  fi
}

run_threshold_test() {
  local test_num="$1"
  local test_name="$2"
  local expect_alert="$3"  # "yes" or "no" — should stderr contain alert?

  TOTAL=$((TOTAL + 1))

  local stderr_output
  stderr_output=$(echo '{"tool":"Write","tool_input":{"file_path":"'"$REPO"'/core/threshold_file_'"$RANDOM"'.py"}}' | bash "$TRACK_SCRIPT" 2>&1 1>/dev/null) || true

  local has_alert="no"
  if echo "$stderr_output" | grep -q '\[CLAUDE.md\]'; then
    has_alert="yes"
  fi

  if [ "$has_alert" = "$expect_alert" ]; then
    PASS=$((PASS + 1))
    echo "  PASS  T${test_num}: ${test_name}"
  else
    FAIL=$((FAIL + 1))
    echo "  FAIL  T${test_num}: ${test_name} (expected alert=${expect_alert}, got=${has_alert})"
    if [ -n "$stderr_output" ]; then
      echo "        stderr: $stderr_output"
    fi
  fi
}

echo ""
echo "=== CLAUDE.md Staleness Tracker — Test Suite ==="
echo ""

# ============================================================
# Write tool tests
# ============================================================
echo "--- Write tool ---"

# T1: Write → new file (untracked by git) → should track
run_test 1 "Write new file (untracked)" \
  '{"tool":"Write","tool_input":{"file_path":"'"$REPO"'/core/new_module.py"}}' \
  "yes"

# T2: Write → existing file (tracked by git) → should NOT track
run_test 2 "Write existing file (tracked)" \
  '{"tool":"Write","tool_input":{"file_path":"'"$REPO"'/core/existing.py"}}' \
  "no"

# T3: Write → image file (.webp) → should NOT track
run_test 3 "Write image file (.webp)" \
  '{"tool":"Write","tool_input":{"file_path":"'"$REPO"'/core/photo.webp"}}' \
  "no"

# T4: Write → CLAUDE.md itself → should NOT track
run_test 4 "Write CLAUDE.md file" \
  '{"tool":"Write","tool_input":{"file_path":"'"$REPO"'/core/CLAUDE.md"}}' \
  "no"

# T5: Write → file inside .claude/worktrees/ → should NOT track
run_test 5 "Write inside .claude/worktrees/" \
  '{"tool":"Write","tool_input":{"file_path":"'"$REPO"'/.claude/worktrees/fix/new.py"}}' \
  "no"

# ============================================================
# Edit tool tests
# ============================================================
echo "--- Edit tool ---"

# T6: Edit → __init__.py → should track as config_edit
run_test 6 "Edit __init__.py (config_edit)" \
  '{"tool":"Edit","tool_input":{"file_path":"'"$REPO"'/core/__init__.py"}}' \
  "yes"

# T7: Edit → regular .py file → should NOT track
run_test 7 "Edit regular .py file" \
  '{"tool":"Edit","tool_input":{"file_path":"'"$REPO"'/core/existing.py"}}' \
  "no"

# T8: Edit → package.json → should track as config_edit
run_test 8 "Edit package.json (config_edit)" \
  '{"tool":"Edit","tool_input":{"file_path":"'"$REPO"'/scripts/package.json"}}' \
  "yes"

# ============================================================
# Bash tool tests
# ============================================================
echo "--- Bash tool ---"

# T9: Bash → rm core/old.py → should track as del_file
run_test 9 "Bash rm file" \
  '{"tool":"Bash","tool_input":{"command":"rm '"$REPO"'/core/old.py"}}' \
  "yes"

# T10: Bash → cd core && rm old.py → should track (broad match, decision 7B)
run_test 10 "Bash cd && rm (broad match)" \
  '{"tool":"Bash","tool_input":{"command":"cd '"$REPO"'/core && rm old.py"}}' \
  "yes"

# T11: Bash → mkdir core/new_module → should track as new_dir
run_test 11 "Bash mkdir" \
  '{"tool":"Bash","tool_input":{"command":"mkdir '"$REPO"'/core/new_module"}}' \
  "yes"

# T12: Bash → mv core/old.py core/new.py → should track as rename
run_test 12 "Bash mv (rename)" \
  '{"tool":"Bash","tool_input":{"command":"mv '"$REPO"'/core/old.py '"$REPO"'/core/new.py"}}' \
  "yes"

# T13: Bash → npm install (no structural command) → should NOT track
run_test 13 "Bash npm install (not structural)" \
  '{"tool":"Bash","tool_input":{"command":"npm install"}}' \
  "no"

# ============================================================
# Walk-up tests
# ============================================================
echo "--- Walk-up ---"

# T14: File in nested dir → should map to nearest CLAUDE.md (core/CLAUDE.md)
run_test 14 "Walk-up finds nearest CLAUDE.md" \
  '{"tool":"Write","tool_input":{"file_path":"'"$REPO"'/core/cqrs/new_handler.py"}}' \
  "yes"

# T15: File in dir with no CLAUDE.md ancestors (create one without)
mkdir -p "$REPO/orphan_dir"
run_test 15 "Walk-up finds no CLAUDE.md" \
  '{"tool":"Bash","tool_input":{"command":"mkdir '"$REPO"'/orphan_dir/sub"}}' \
  "yes"
# Note: orphan_dir has no CLAUDE.md, but repo root does — so it maps to root CLAUDE.md

# ============================================================
# Edge case tests (from code review)
# ============================================================
echo "--- Edge cases ---"

# T22: Bash rm with only flags (no file) → flag rejected as target
run_test 22 "Bash rm -rf (flag as target, rejected)" \
  '{"tool":"Bash","tool_input":{"command":"rm -rf"}}' \
  "no"

# T23: Multiple structural commands — rm first match, extracts last word of full command
run_test 23 "Bash rm && mkdir (last word extracted)" \
  '{"tool":"Bash","tool_input":{"command":"rm '"$REPO"'/core/a.py && mkdir '"$REPO"'/core/b"}}' \
  "yes"

# ============================================================
# Threshold tests
# ============================================================
echo "--- Threshold ---"

# T16: After 3 entries for same CLAUDE.md, should emit alert
# We need to use a persistent tracker for this test
rm -f "$TRACKER"
# Write 2 entries manually, then the 3rd triggers alert
echo "core/CLAUDE.md|new_file|core/a.py" >> "$TRACKER"
echo "core/CLAUDE.md|new_file|core/b.py" >> "$TRACKER"
run_threshold_test 16 "Threshold alert at count==3" "yes"

# ============================================================
# Session summary tests
# ============================================================
echo "--- Session summary ---"

# T17: session-summary.sh with tracker data → should produce output
TOTAL=$((TOTAL + 1))
rm -f "$TRACKER"
echo "core/CLAUDE.md|new_file|core/a.py" >> "$TRACKER"
echo "core/CLAUDE.md|config_edit|core/__init__.py" >> "$TRACKER"
echo "scripts/CLAUDE.md|new_file|scripts/tool.py" >> "$TRACKER"

summary_output=$(bash "$SUMMARY_SCRIPT" 2>&1) || true
if echo "$summary_output" | grep -q "Staleness Report"; then
  PASS=$((PASS + 1))
  echo "  PASS  T17: Session summary with data"
else
  FAIL=$((FAIL + 1))
  echo "  FAIL  T17: Session summary with data"
  echo "        output: $summary_output"
fi

# T18: session-summary.sh with no tracker → should exit cleanly
TOTAL=$((TOTAL + 1))
rm -f "$TRACKER"
summary_output=$(bash "$SUMMARY_SCRIPT" 2>&1) || true
if [ -z "$summary_output" ]; then
  PASS=$((PASS + 1))
  echo "  PASS  T18: Session summary with no tracker"
else
  FAIL=$((FAIL + 1))
  echo "  FAIL  T18: Session summary with no tracker (expected no output)"
  echo "        output: $summary_output"
fi

# ============================================================
# Session start tests
# ============================================================
echo "--- Session start ---"

STALENESS_LOG="$REPO/.claude/claude-md-staleness.log"
mkdir -p "$REPO/.claude"

# T19: session-start.sh with fresh staleness log → should emit reminder
TOTAL=$((TOTAL + 1))
echo "  2 changes → core/CLAUDE.md (new_file,config_edit)" > "$STALENESS_LOG"
start_output=$(bash "$SESSION_START_SCRIPT" 2>&1) || true
if echo "$start_output" | grep -q "staleness"; then
  PASS=$((PASS + 1))
  echo "  PASS  T19: Session start with fresh staleness log"
else
  FAIL=$((FAIL + 1))
  echo "  FAIL  T19: Session start with fresh staleness log"
  echo "        output: $start_output"
fi

# T20: session-start.sh with stale log (>3 days) → should delete
TOTAL=$((TOTAL + 1))
echo "old data" > "$STALENESS_LOG"
touch -t 202601010000 "$STALENESS_LOG"  # Set to Jan 1 2026 (well over 3 days old)
start_output=$(bash "$SESSION_START_SCRIPT" 2>&1) || true
if [ ! -f "$STALENESS_LOG" ]; then
  PASS=$((PASS + 1))
  echo "  PASS  T20: Session start deletes stale log (>3 days)"
else
  FAIL=$((FAIL + 1))
  echo "  FAIL  T20: Session start deletes stale log (expected deletion)"
fi

# T21: session-start.sh with no log → should not error
TOTAL=$((TOTAL + 1))
rm -f "$STALENESS_LOG"
start_output=$(bash "$SESSION_START_SCRIPT" 2>&1) || true
# Should not contain any error
if ! echo "$start_output" | grep -qi "error\|no such file"; then
  PASS=$((PASS + 1))
  echo "  PASS  T21: Session start with no staleness log"
else
  FAIL=$((FAIL + 1))
  echo "  FAIL  T21: Session start with no staleness log"
  echo "        output: $start_output"
fi

# ============================================================
# Results
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Results: ${PASS}/${TOTAL} passed, ${FAIL} failed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Cleanup
rm -rf "$TMPDIR_BASE"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
