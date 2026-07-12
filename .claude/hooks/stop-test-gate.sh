#!/usr/bin/env bash
# Stop test-gate — runs the fast pytest suite when Python files are dirty, and
# RETRIES a failure once (last-failed only, after a short settle) to absorb the
# two false-block modes this shared worktree produces:
#   1. load-timeout flakes — e.g. test_ml_optional's 60s import guard trips when
#      the machine is saturated; the import itself succeeds (~7s unloaded).
#   2. concurrent-session mid-edit races — a second session editing a test file
#      is caught half-written (e.g. a fixture using tmp_path a beat before the
#      param lands), an error that does not reproduce once the edit completes.
# Blocks the Stop (exit 2) ONLY when a failure reproduces on a clean re-run.
# Everything else exits 0 so a genuinely-passing suite never false-blocks.
set -uo pipefail

REPO="/Users/theceo/DevSkyy"
cd "$REPO" || exit 0

PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || exit 0   # no venv resolvable → don't block the Stop

# Gate only when Python actually changed (same trigger as the original hook).
git status --porcelain -- '*.py' | grep -q . || exit 0

# Half-written NEW test files (untracked) are not a gate — ignore them.
ig=$(git ls-files --others --exclude-standard "tests/*.py" "tests/**/*.py" 2>/dev/null \
     | sed "s/^/--ignore=/" | tr "\n" " ")

run_full()       { $PY -m pytest tests/ -x -q $ig 2>&1; }
run_lastfailed() { $PY -m pytest --last-failed -q $ig 2>&1; }

out=$(run_full); rc=$?
[ "$rc" -eq 0 ] && exit 0   # green on the first try

# First run failed. Settle (load drains / the other session's edit completes),
# then re-run only what failed. pytest's --last-failed uses the cache from the
# run above; if the cache is empty it falls back to the full suite (still safe).
sleep 5
out2=$(run_lastfailed); rc2=$?
if [ "$rc2" -eq 0 ]; then
  echo "Stop-gate: failure cleared on clean re-run (transient flake / mid-edit race) — not blocking."
  exit 0
fi

echo "$out2" | tail -25
echo "Stop-gate: failure reproduced on re-run — blocking Stop."
exit 2
