---
phase: 04-pr-branch-protection
plan: 01
subsystem: infra
tags: [github, branch-protection, ci-gates, auto-merge, gh-api]

# Dependency graph
requires:
  - phase: 01-ci-failure-triage-fix
    provides: "Reliable CI checks that can be required as merge gates"
provides:
  - "GitHub branch protection on main requiring all 4 CI checks"
  - "Idempotent setup/verify script at scripts/setup-branch-protection.sh"
  - "Repository auto-merge enabled for agent workflows"
affects: [05-wordpress-build-pipeline, 06-wordpress-ci-integration, 07-deploy-core, 08-deploy-verification]

# Tech tracking
tech-stack:
  added: []
  patterns: [idempotent-config-script, gh-api-branch-protection, verify-flag-pattern]

key-files:
  created:
    - scripts/setup-branch-protection.sh
  modified: []

key-decisions:
  - "Used temp file for JSON payload instead of heredoc stdin to guarantee UTF-8 emoji encoding"
  - "Set app_id: -1 (any source) for required checks, matching GitHub Actions app correctly"
  - "enforce_admins: true -- even repo owner must use PR workflow"

patterns-established:
  - "Idempotent config script: apply + verify in one pass, --verify for read-only mode"
  - "gh api over curl for GitHub REST operations (handles auth, pagination, error formatting)"

requirements-completed: [PR-01, PR-02]

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 4 Plan 01: PR Branch Protection Summary

**GitHub branch protection on main requiring 4 CI checks (lint, tests, security, frontend) with strict up-to-date, enforce_admins, and auto-merge for agent workflows**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T08:20:43Z
- **Completed:** 2026-03-09T08:22:33Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Branch protection live on main: 4 required status checks, strict mode, enforce_admins, force pushes blocked
- Auto-merge enabled so Ralph and Claude Code can use `gh pr merge --auto --squash`
- Idempotent script with `--verify` flag for read-only checks (5 PASS/FAIL verifications)
- All success criteria verified against live GitHub API

## Task Commits

Each task was committed atomically:

1. **Task 1: Create idempotent branch protection setup script** - `b95d8876` (feat)
2. **Task 2: Apply branch protection and verify all settings** - No file changes (API configuration applied to live GitHub repo; verified via script)

## Files Created/Modified
- `scripts/setup-branch-protection.sh` - Idempotent script that configures and verifies GitHub branch protection via `gh api`

## Decisions Made
- Used temp file for JSON payload instead of piping heredoc to stdin, to guarantee emoji characters in check-run names survive encoding (addressed Open Question 1 from RESEARCH.md)
- Set `app_id: -1` (accept from any source) for all 4 required checks, which correctly matches GitHub Actions
- Set `enforce_admins: true` so even the repo owner cannot bypass protection rules

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Armor chain (Phases 1-4) is complete: local hooks + CI checks + PR gates all enforced
- All future code changes to main must go through a PR with passing CI
- Ready for Phase 5 (WordPress Build Pipeline) -- independent of armor chain

## Self-Check: PASSED

- FOUND: scripts/setup-branch-protection.sh (executable)
- FOUND: commit b95d8876
- FOUND: 04-01-SUMMARY.md

---
*Phase: 04-pr-branch-protection*
*Completed: 2026-03-09*
