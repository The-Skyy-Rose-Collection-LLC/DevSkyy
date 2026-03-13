---
phase: 07-deploy-core
plan: 01
subsystem: infra
tags: [bash, rsync, lftp, ssh, wp-cli, deploy, maintenance-mode, shellcheck, pytest]

# Dependency graph
requires:
  - phase: 05-wordpress-build-pipeline
    provides: "npm run build producing minified JS/CSS assets for deployment"
provides:
  - "deploy-theme.sh: production deploy script with rsync/lftp, maintenance mode, cache flush, trap safety"
  - "tests/scripts/test_deploy_theme.py: 26 subprocess-based tests for deploy script behavior"
affects: [08-deploy-verification-orchestration]

# Tech tracking
tech-stack:
  added: [sshpass, rsync, lftp, shellcheck]
  patterns: [trap-cleanup-on-exit, wp-cli-over-ssh, rsync-with-lftp-fallback, dry-run-preview-mode]

key-files:
  created:
    - scripts/deploy-theme.sh
    - tests/scripts/test_deploy_theme.py
    - tests/scripts/__init__.py
  modified: []

key-decisions:
  - "27 rsync exclude patterns prevent dev artifacts from reaching production"
  - "trap cleanup EXIT INT TERM with MAINTENANCE_ACTIVE flag guarantees maintenance mode deactivation on any failure"
  - "rsync as primary transfer with lftp SFTP mirror as fallback for environments without rsync"
  - "ENV_FILE override via environment variable enables isolated test execution"

patterns-established:
  - "Deploy script pattern: preflight -> maintenance activate -> transfer -> deactivate -> cache flush"
  - "WP-CLI remote execution via sshpass+ssh with dry-run passthrough"
  - "Subprocess-based bash script testing via pytest"

requirements-completed: [DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-07]

# Metrics
duration: 8min
completed: 2026-03-09
---

# Phase 7 Plan 01: Deploy Core Summary

**Production deploy script with rsync/lftp transfer, WP-CLI maintenance mode, trap-based safety cleanup, and 26 pytest subprocess tests**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-09T23:47:00Z
- **Completed:** 2026-03-09T23:55:49Z
- **Tasks:** 2
- **Files created:** 3

## Accomplishments
- Created `scripts/deploy-theme.sh` with full deploy lifecycle: preflight, maintenance mode, rsync transfer (lftp fallback), cache flush, trap cleanup
- 27 rsync exclude patterns prevent dev files (node_modules, .git, .env*, *.map, tests, scripts/) from reaching production
- Trap-based cleanup guarantees maintenance mode deactivation even on mid-transfer failure
- 26 pytest tests verify dry-run output, help flag, missing credentials, command ordering, exclude patterns, and shellcheck compliance
- Human-verified dry-run output confirming correct ordering and safety mechanisms

## Task Commits

Each task was committed atomically:

1. **Task 1: Create deploy-theme.sh with maintenance mode, rsync/lftp transfer, and trap safety** - `4f209583` (test) + `19d5c703` (feat)
2. **Task 2: Verify deploy script dry-run and review safety mechanisms** - checkpoint:human-verify (APPROVED, no commit needed)

## Files Created/Modified
- `scripts/deploy-theme.sh` - Production deploy script with maintenance mode, rsync/lftp transfer, cache flush, and trap safety
- `tests/scripts/test_deploy_theme.py` - 26 subprocess-based tests for deploy script behavior
- `tests/scripts/__init__.py` - Package init for tests/scripts/

## Decisions Made
- 27 rsync exclude patterns covering all dev artifacts (node_modules, .git, .env*, *.map, tests, scripts/, package.json, composer files, config files, build tooling)
- trap cleanup EXIT INT TERM with MAINTENANCE_ACTIVE boolean flag -- checks state before calling wp_remote to avoid false deactivation
- rsync as primary transfer method with lftp SFTP mirror as automatic fallback
- ENV_FILE overridable via environment variable for controlled test execution without real credentials
- sshpass + ssh for WP-CLI remote execution (matches proven wp-deploy-theme.sh pattern)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Credentials are sourced from `.env.wordpress` which already exists.

## Next Phase Readiness
- Deploy script is ready for production use (human-approved)
- Phase 8 can add health verification endpoints and single-command pipeline orchestration on top of this deploy core
- The deploy script's `--dry-run` mode provides the foundation for Phase 8's dry-run orchestration requirement (DEPLOY-06)

---
*Phase: 07-deploy-core*
*Completed: 2026-03-09*
