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

SHA="" DESC=""
if [ "$MODE" = "pr" ]; then
  # Merge preview first — the commit GitHub CI actually validates.
  if git fetch --quiet origin "pull/${TARGET}/merge" 2>/dev/null; then
    SHA=$(git rev-parse FETCH_HEAD)
    DESC="PR #${TARGET} (merge preview)"
  elif git fetch --quiet origin "pull/${TARGET}/head" 2>/dev/null; then
    SHA=$(git rev-parse FETCH_HEAD)
    DESC="PR #${TARGET} (HEAD — no merge ref; PR likely conflicts with main)"
    echo "ci-sim: WARNING: no merge preview for PR #${TARGET}; gating its head instead" >&2
  else
    echo "ci-sim: cannot fetch PR #${TARGET} (neither merge nor head ref)" >&2
    exit 2
  fi
else
  git fetch --quiet origin 2>/dev/null || true
  SHA=$(git rev-parse --verify "${TARGET}^{commit}" 2>/dev/null) || {
    echo "ci-sim: cannot resolve ref '${TARGET}'" >&2; exit 2; }
  DESC="ref ${TARGET}"
fi

WT="${ROOT}/.claude/worktrees/ci-sim-${MODE}-${TARGET//\//-}"
cleanup() {
  if [ "${KEEP:-0}" = "1" ]; then
    echo "ci-sim: KEEP=1 — worktree left at ${WT}"
  else
    git worktree remove --force "$WT" 2>/dev/null || true
  fi
}
trap cleanup EXIT
git worktree remove --force "$WT" 2>/dev/null || true
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
