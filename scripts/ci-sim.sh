#!/usr/bin/env bash
# =============================================================================
# ci-sim.sh — simulated CI clone: run the offline gate against a PR or ref
# =============================================================================
# GitHub Actions is disabled repo-level (since 2026-06-29), so nothing gates
# the PR queue. This wrapper reproduces what the Actions runner would do:
#
#   1. Resolve the commit CI would test:
#        --pr N   → refs/pull/N/merge (GitHub's merge preview — the exact
#                   commit a pull_request run validates), falling back to
#                   pull/N/head when no merge ref exists (conflicting PR)
#        --ref R  → any local/remote ref or SHA
#   2. Check it out into a clean disposable worktree (clone-equivalent:
#        tracked files only, no dirty local state, no gitignored riders)
#   3. Run scripts/ci-local.sh there — the offline mirror of ci.yml's six
#      gating jobs (lint · python-tests · security · frontend-tests ·
#      threejs-tests · wordpress-theme, aggregated upstream as the
#      "Pipeline Summary" check)
#   4. Tear the worktree down and report a single PASS/FAIL verdict
#
# The canonical ci-local.sh from THIS checkout is used (CI_LOCAL_ROOT
# override, same pattern as the pre-push hook), so PRs whose branches
# predate the gate script are still checkable.
#
# Usage:
#   scripts/ci-sim.sh --pr 788                      # full gate on PR #788
#   scripts/ci-sim.sh --pr 788 lint python-tests    # subset of jobs
#   scripts/ci-sim.sh --ref origin/main             # gate a branch/SHA
#   FAST=1 scripts/ci-sim.sh --pr 788               # skip heavy installs
#   KEEP=1 scripts/ci-sim.sh --pr 788               # keep worktree for debug
#
# SECURITY / trust boundary: --pr checks out an arbitrary PR ref and RUNS it
#   (pytest collection imports every conftest/test module; `npm install`/`npm
#   ci` run package.json lifecycle scripts) using this machine's interpreter,
#   npm, and filesystem — NOT a sandbox. This repo is public, so any PR is
#   untrusted. This is the same exposure as a manual `gh pr checkout N &&
#   pytest`, made one command. Only gate PRs you are actively reviewing; for
#   unknown/untrusted authors, run inside a container or throwaway VM.
#
# Exit code: ci-local.sh's (0 = every non-skipped check passed).
# =============================================================================
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 2

MODE="" TARGET=""
case "${1:-}" in
  --pr)  MODE="pr";  TARGET="${2:?usage: ci-sim.sh --pr N [jobs...]}";  shift 2 ;;
  --ref) MODE="ref"; TARGET="${2:?usage: ci-sim.sh --ref REF [jobs...]}"; shift 2 ;;
  *) echo "usage: ci-sim.sh (--pr N | --ref REF) [jobs...]" >&2; exit 2 ;;
esac

# Unified teardown, armed BEFORE any resource is created so every early-exit
# path cleans up: the private fetch ref, the stderr temp, and the worktree.
TMPREF="refs/ci-sim/tmp-$$"
FETCH_ERR="$(mktemp "${TMPDIR:-/tmp}/ci-sim-fetch-XXXXXX")"
WT=""
# shellcheck disable=SC2329  # invoked indirectly via `trap cleanup EXIT`
cleanup() {
  git update-ref -d "$TMPREF" 2>/dev/null || true
  rm -f "$FETCH_ERR"
  [ -n "$WT" ] || return 0
  if [ "${KEEP:-0}" = "1" ]; then
    echo "ci-sim: KEEP=1 — worktree left at ${WT}"
  else
    git worktree remove --force "$WT" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# Resolve the commit to gate WITHOUT reading the shared FETCH_HEAD. FETCH_HEAD
# is a single file in the common git dir; a concurrent `git fetch` (a second
# ci-sim run, a manual fetch in another terminal) can overwrite it between our
# fetch and rev-parse, silently gating the WRONG commit. Fetch the PR ref into
# a private per-process ref and read that instead — no shared state, no race.
SHA="" DESC=""
if [ "$MODE" = "pr" ]; then
  # Merge preview first — the commit GitHub CI actually validates.
  if git fetch --quiet origin "+pull/${TARGET}/merge:${TMPREF}" 2>"$FETCH_ERR"; then
    SHA=$(git rev-parse --verify "${TMPREF}")
    DESC="PR #${TARGET} (merge preview)"
  elif git fetch --quiet origin "+pull/${TARGET}/head:${TMPREF}" 2>"$FETCH_ERR"; then
    SHA=$(git rev-parse --verify "${TMPREF}")
    DESC="PR #${TARGET} (HEAD — no merge ref; PR likely conflicts with main)"
    echo "ci-sim: WARNING: no merge preview for PR #${TARGET}; gating its head instead" >&2
  else
    echo "ci-sim: cannot fetch PR #${TARGET} (neither merge nor head ref):" >&2
    sed 's/^/  /' "$FETCH_ERR" >&2
    exit 2
  fi
  # SECURITY: --pr checks out and RUNS unreviewed PR code (pytest collection,
  # npm lifecycle scripts) with this machine's interpreter and filesystem, and
  # this repo is public — so any PR is untrusted. Same trust boundary as a
  # manual `gh pr checkout N && pytest`; only gate PRs you are reviewing, and
  # for unknown authors prefer a sandbox/container (see the header note).
  echo "ci-sim: NOTE: running unreviewed PR code locally — treat PR #${TARGET} as untrusted" >&2
else
  # Ref mode resolves TARGET directly (not via FETCH_HEAD), so no shared-ref
  # race — refresh remote-tracking refs so origin/* targets resolve fresh.
  git fetch --quiet origin 2>"$FETCH_ERR" || true
  SHA=$(git rev-parse --verify "${TARGET}^{commit}" 2>/dev/null) || {
    echo "ci-sim: cannot resolve ref '${TARGET}':" >&2
    sed 's/^/  /' "$FETCH_ERR" >&2
    exit 2; }
  DESC="ref ${TARGET}"
fi

# Per-process worktree path: a purely target-derived path would let a second
# run for the same PR/ref force-remove this run's worktree mid-job. $$ makes it
# unique; prune reaps registrations left by any crashed prior run.
git worktree prune 2>/dev/null || true
WT="${ROOT}/.claude/worktrees/ci-sim-${MODE}-${TARGET//\//-}-$$"
git worktree add --detach --quiet "$WT" "$SHA" || {
  echo "ci-sim: worktree add failed for ${SHA}" >&2; exit 2; }

# Gate tooling: prefer the isolated CI toolchain, fall back to the project venv.
if [ -f "${ROOT}/ci-env/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  . "${ROOT}/ci-env/.venv/bin/activate"
elif [ -f "${ROOT}/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  . "${ROOT}/.venv/bin/activate"
fi

echo "ci-sim: gating ${DESC} @ ${SHA:0:12}"
echo "ci-sim: clean worktree ${WT}"

CI_LOCAL_ROOT="$WT" bash "${ROOT}/scripts/ci-local.sh" "$@"
rc=$?

if [ "$rc" -eq 0 ]; then
  echo "ci-sim: VERDICT ${DESC} @ ${SHA:0:8} — PASS"
else
  echo "ci-sim: VERDICT ${DESC} @ ${SHA:0:8} — FAIL (rc=${rc})"
fi
exit "$rc"
