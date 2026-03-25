---
phase: 01-ci-failure-triage-fix
plan: 02
subsystem: infra
tags: [ci, continue-on-error, security-scanning, gitleaks, trufflehog, pip-licenses, dast, workflow]

# Dependency graph
requires:
  - phase: 01-ci-failure-triage-fix/01
    provides: "All Python and frontend tools pass clean (black, isort, ruff, mypy, eslint, tsc, three.js)"
provides:
  - "CI workflow (ci.yml) with zero continue-on-error directives"
  - "Security gate (security-gate.yml) with zero continue-on-error and hard failure on secrets detection"
  - "DAST workflow (dast-scan.yml) with early-exit guards instead of continue-on-error"
  - "License compliance via explicit allowlist instead of suppression"
affects: [01-ci-failure-triage-fix]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Security tool steps use proper exit codes with no || true suppression"
    - "Secrets scanners (Gitleaks, TruffleHog) are hard failures -- no suppression allowed"
    - "DAST steps use early-exit guards (if [ ! -f ]) for missing scripts instead of continue-on-error"
    - "Deploy tag uses if: success() gate and informational || echo on push (not || true on tag creation)"
    - "License check uses explicit --fail-on and --allow-only lists for precise license control"

key-files:
  created: []
  modified:
    - .github/workflows/ci.yml
    - .github/workflows/security-gate.yml
    - .github/workflows/dast-scan.yml

key-decisions:
  - "Deploy tag restructured with if: success() and || echo on push (tag creation itself hard-fails, push failure is informational)"
  - "Gitleaks and TruffleHog are hard failures -- secrets in code must never be silently swallowed"
  - "License allowlist includes LGPL (permissive for library usage) but blocks GPL-3.0 and AGPL-3.0 (full copyleft)"
  - "DAST early-exit guards use ::notice:: annotations (not ::warning::) since missing scripts are expected during provisioning"

patterns-established:
  - "Security scanners: hard failure, no suppression, no continue-on-error"
  - "Optional steps (Codecov upload, Slack webhook, pip install fallback): || true is acceptable"
  - "Missing-script guards: if [ ! -f ] with ::notice:: and exit 0"

requirements-completed: [CI-01]

# Metrics
duration: 3min
completed: 2026-03-08
---

# Phase 1 Plan 2: Remove All continue-on-error Directives Summary

**Removed all 17 continue-on-error: true directives across 3 CI workflows; secrets scanners are hard failures, DAST uses early-exit guards, license check uses explicit allowlist**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-08T22:32:17Z
- **Completed:** 2026-03-08T22:35:18Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- All 17 continue-on-error: true directives removed across ci.yml (12), security-gate.yml (3), and dast-scan.yml (2)
- Security tool commands in ci.yml have no || true suppression (pip-audit, bandit, semgrep all use proper exit codes)
- Gitleaks and TruffleHog are now hard failures -- detected secrets will fail the security gate
- pip-licenses uses explicit --fail-on (GPL-3.0, AGPL-3.0) and --allow-only (MIT, BSD, Apache, etc.) instead of blanket suppression
- DAST scan and baseline comparison use early-exit guards for missing scripts (graceful skip, not silent swallowing)
- Deploy tag restructured as post-deploy step gated by if: success(), with SHA suffix in tag name
- Preserved all intentional || true patterns: Codecov upload, pip install fallback, Slack webhook, pip install in requirements

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove continue-on-error from ci.yml and restructure security/deploy steps** - `928507bf` (fix)
2. **Task 2: Remove continue-on-error from security-gate.yml and dast-scan.yml** - `3991fbb7` (fix)

## Files Created/Modified
- `.github/workflows/ci.yml` - Removed 12 continue-on-error directives; cleaned || true from pip-audit, bandit, semgrep; restructured deploy tag
- `.github/workflows/security-gate.yml` - Removed 3 continue-on-error directives; hardened Gitleaks/TruffleHog; added license allowlist
- `.github/workflows/dast-scan.yml` - Removed 2 continue-on-error directives; added early-exit guards for missing scripts

## Decisions Made

1. **Deploy tag restructured with if: success() gate:** The tag step now only runs after a successful deploy. Tag creation itself is a hard operation (no || true), but `git push origin "$TAG"` uses `|| echo "::warning::"` because tag push failure is informational -- the deploy already succeeded. The tag also includes the commit SHA suffix for traceability.

2. **Gitleaks/TruffleHog as hard failures:** Both `|| true` and `continue-on-error` removed from secrets scanners. Per user decision, any detected secret must fail the pipeline immediately -- silent pass-through would defeat the purpose of secrets scanning.

3. **License allowlist includes LGPL:** LGPL-2.1 and LGPL-3.0 are included in the allow-only list because LGPL is permissive for library usage (dynamically linked). Only full GPL-3.0 and AGPL-3.0 are blocked via --fail-on, since those would require source distribution of the entire project.

4. **DAST guards use ::notice:: level:** Missing DAST scripts are expected during the provisioning phase. Using `::notice::` (not `::warning::`) avoids false alarm fatigue while still being visible in the Actions log.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None - all 17 directives were removed cleanly and all fix strategies from the plan worked as specified.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 1 (CI Failure Triage & Fix) is now complete: all underlying failures fixed (Plan 01) and all suppression directives removed (Plan 02)
- CI pipeline will now produce hard failures on real problems -- nothing is silently swallowed
- GitHub Actions billing/quota issue still blocks CI validation via GitHub runners (identified in research phase)
- Ready to proceed to Phase 2 per roadmap

## Self-Check: PASSED

- All 3 workflow files exist on disk
- Both task commits (928507bf, 3991fbb7) verified in git log
- Zero continue-on-error: true across all 3 workflow files confirmed

---
*Phase: 01-ci-failure-triage-fix*
*Completed: 2026-03-08*
