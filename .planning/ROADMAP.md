# Roadmap: Production Armor & WordPress Build Autonomy

## Overview

This roadmap delivers a 4-layer defense system (hooks, CI, PR gates, deploy verification) that prevents autonomous AI agents from shipping broken code to the live SkyyRose ecommerce site. The work progresses from hardening the existing CI pipeline, through local git hooks, PR gates, WordPress build automation, and finally deploy automation with health verification. Each phase delivers a complete, verifiable capability. The two main chains -- "armor" (Phases 1-4) and "build & ship" (Phases 5-8) -- converge at the end into a fully automated, zero-touch pipeline.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: CI Failure Triage & Fix** - Remove 17 continue-on-error directives and fix the underlying failures they mask
- [x] **Phase 2: Husky Foundation** - Replace broken Husky v4 config with working v9 setup at monorepo root
- [x] **Phase 3: Pre-commit Hook Checks** - Wire up lint, type-check, PHP syntax, and fast tests on staged files
- [x] **Phase 4: PR Branch Protection** - Block merges to main unless all CI checks pass
- [x] **Phase 5: WordPress Build Pipeline** - Full minification of all JS and CSS theme files via single build command
- [x] **Phase 6: WordPress CI Integration** - CI validates PHP syntax, build output, and minification drift for theme files
- [ ] **Phase 7: Deploy Core** - Transfer built theme to production via rsync/SSH with maintenance mode safety
- [ ] **Phase 8: Deploy Verification & Orchestration** - Health checks, single-command pipeline, and dry-run mode

## Phase Details

### Phase 1: CI Failure Triage & Fix
**Goal**: The CI pipeline produces hard failures on real problems -- no check is silently swallowed
**Depends on**: Nothing (first phase)
**Requirements**: CI-01, CI-02
**Success Criteria** (what must be TRUE):
  1. Running the CI pipeline on main with a deliberately broken lint rule causes the workflow to fail (red status), not warn
  2. All existing CI workflow runs on main pass green without any continue-on-error directives present
  3. A commit with a Python type error (mypy) or a JS lint error (ESLint) fails CI within the appropriate job
**Plans:** 2 plans

Plans:
- [x] 01-01-PLAN.md -- Fix underlying lint/format/type/test failures (black, isort, ruff, mypy, ESLint, tsc)
- [x] 01-02-PLAN.md -- Remove all 17 continue-on-error directives from ci.yml, security-gate.yml, dast-scan.yml

### Phase 2: Husky Foundation
**Goal**: Git hooks infrastructure is installed and functional at the monorepo root
**Depends on**: Nothing (independent of Phase 1)
**Requirements**: HOOK-07
**Success Criteria** (what must be TRUE):
  1. Running `git commit` on a staged file triggers a pre-commit hook (observable via hook output in terminal)
  2. The broken Husky v4 `husky.hooks` block is removed from package.json
  3. A `.husky/pre-commit` file exists and is executable
**Plans:** 1 plan

Plans:
- [x] 02-01-PLAN.md -- Initialize Husky v9, create hooks and verification script, clean up WordPress theme

### Phase 3: Pre-commit Hook Checks
**Goal**: Every commit is checked for lint, type, syntax, and test errors on staged files before it reaches the remote
**Depends on**: Phase 2 (Husky must be installed)
**Requirements**: HOOK-01, HOOK-02, HOOK-03, HOOK-04, HOOK-05, HOOK-06, HOOK-08
**Success Criteria** (what must be TRUE):
  1. Committing a staged JS file with an ESLint error blocks the commit with a clear error message
  2. Committing a staged Python file with a Ruff/Black/isort violation blocks the commit
  3. Committing a staged PHP file with a syntax error (`php -l`) blocks the commit
  4. Committing a staged TypeScript file with a type error blocks the commit (tsc or mypy for Python)
  5. All pre-commit checks complete in under 30 seconds on a typical commit touching 5 files
**Plans:** 2 plans

Plans:
- [x] 03-01-PLAN.md -- Create lint-staged config, PHP lint wrapper, and wire pre-commit hook with real checks
- [x] 03-02-PLAN.md -- Create verification scripts and validate all HOOK requirements end-to-end

### Phase 4: PR Branch Protection
**Goal**: No code reaches the main branch without passing all CI checks via a pull request
**Depends on**: Phase 1 (CI checks must be reliable before they can be required)
**Requirements**: PR-01, PR-02
**Success Criteria** (what must be TRUE):
  1. A PR with a failing CI check cannot be merged (merge button is disabled or gh merge fails)
  2. A PR whose branch is behind main cannot be merged until it is updated
  3. Agents (Ralph, Claude Code) can still create PRs and merge them when CI passes -- no human review required
**Plans:** 1 plan

Plans:
- [x] 04-01-PLAN.md -- Configure GitHub branch protection, required status checks, and auto-merge via idempotent shell script

### Phase 5: WordPress Build Pipeline
**Goal**: All WordPress theme assets are minified from source via a single build command
**Depends on**: Nothing (independent of armor chain, but placed here for logical ordering)
**Requirements**: BUILD-01, BUILD-02, BUILD-03, BUILD-04
**Success Criteria** (what must be TRUE):
  1. Running `npm run build` in the WordPress theme directory produces .min.js files for all 43 JS source files
  2. Running `npm run build` produces .min.css files for all 55+ CSS source files (including subdirectories)
  3. Source maps (.map files) are generated alongside minified output for debugging
  4. A single `npm run build` command produces all minified output -- no manual steps required
**Plans:** 1 plan

Plans:
- [x] 05-01-PLAN.md -- Rewrite webpack config with dynamic JS entry discovery, create CSS build script, and build verification

### Phase 6: WordPress CI Integration
**Goal**: CI catches PHP errors and stale minified files in the WordPress theme before they can be merged
**Depends on**: Phase 1 (hard-failure CI), Phase 5 (build pipeline must exist for drift detection)
**Requirements**: CI-03, CI-04, CI-05
**Success Criteria** (what must be TRUE):
  1. A PHP syntax error in any theme file causes CI to fail
  2. CI runs `npm run build` for the WordPress theme and the build step passes
  3. If a developer edits a source CSS/JS file without rebuilding, CI fails with a minification drift error
**Plans:** 1 plan

Plans:
- [x] 06-01-PLAN.md -- Add wordpress-theme CI job (PHP lint, build + verify, drift detection) and update branch protection to 5 checks

### Phase 7: Deploy Core
**Goal**: Built theme files can be transferred to the production WordPress server safely
**Depends on**: Phase 5 (must have built assets to deploy)
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-07
**Success Criteria** (what must be TRUE):
  1. The deploy script transfers theme files to the production server via rsync over SSH
  2. The live site enters WP-CLI maintenance mode before file transfer begins
  3. Maintenance mode is disabled and cache is flushed after transfer completes
  4. If the deploy script fails mid-transfer, maintenance mode is still disabled (try/finally safety)
**Plans**: TBD

Plans:
- [ ] 07-01: TBD
- [ ] 07-02: TBD

### Phase 8: Deploy Verification & Orchestration
**Goal**: Deploys are verified against the live site and can be triggered with a single command (including dry-run)
**Depends on**: Phase 7 (core deploy must work before adding verification and orchestration)
**Requirements**: DEPLOY-04, DEPLOY-05, DEPLOY-06
**Success Criteria** (what must be TRUE):
  1. After deploy, the script hits health endpoints (/health, /health/ready, /health/live) and verifies page content -- not just HTTP 200
  2. A single command runs the full pipeline: build, transfer, verify -- no manual intermediate steps
  3. Running the deploy in dry-run mode shows what would be transferred without actually deploying to production
**Plans**: TBD

Plans:
- [ ] 08-01: TBD
- [ ] 08-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. CI Failure Triage & Fix | 2/2 | Complete | 2026-03-08 |
| 2. Husky Foundation | 1/1 | Complete | 2026-03-09 |
| 3. Pre-commit Hook Checks | 2/2 | Complete | 2026-03-09 |
| 4. PR Branch Protection | 1/1 | Complete | 2026-03-09 |
| 5. WordPress Build Pipeline | 1/1 | Complete | 2026-03-09 |
| 6. WordPress CI Integration | 1/1 | Complete | 2026-03-09 |
| 7. Deploy Core | 0/2 | Not started | - |
| 8. Deploy Verification & Orchestration | 0/2 | Not started | - |
