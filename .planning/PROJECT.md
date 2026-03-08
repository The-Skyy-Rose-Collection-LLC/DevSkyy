# Production Armor & WordPress Build Autonomy

## What This Is

A multi-layered defense system that prevents autonomous AI agents from breaking the live SkyyRose ecommerce site. Four layers of protection (git hooks, CI, PR gates, deploy verification) catch bad code at every stage, while a WordPress build pipeline automates minification, PHP testing, and WP-CLI deployments — enabling zero-touch, agent-driven releases.

## Core Value

No agent-written code can reach production without passing automated quality gates at every layer — local, CI, PR, and post-deploy.

## Requirements

### Validated

<!-- Existing capabilities inferred from codebase -->

- ✓ GitHub Actions CI pipeline with lint + test stages — existing (`ci.yml`)
- ✓ Jest test framework configured for Next.js frontend — existing
- ✓ Python testing with pytest — existing
- ✓ ESLint + Ruff + Black formatting tools — existing
- ✓ TypeScript type checking — existing
- ✓ Security scanning workflows (DAST, security-gate) — existing
- ✓ Concurrency control on CI runs — existing

### Active

<!-- Current scope. Building toward these. -->

- [ ] Local git hooks that run lint, type-check, fast tests, and PHP syntax on every commit
- [ ] CI pipeline enforces hard failures — no soft warnings, no skippable checks
- [ ] PR branch protection rules — merge blocked unless all CI checks pass
- [ ] Post-deploy verification hits health endpoints and validates live site
- [ ] WordPress CSS/JS minification pipeline (local npm build + CI validation)
- [ ] PHP linting and testing for WordPress theme files
- [ ] WP-CLI automated deployment via SSH
- [ ] Single command deploys theme from commit to live site

### Out of Scope

- Human code review requirement — agents operate autonomously, CI is the reviewer
- Coverage threshold gates — focus on hard pass/fail, not percentage targets
- Security vulnerability scanning gates — existing DAST/security-gate workflows sufficient for now
- Rollback automation — manual rollback acceptable for v1
- Staging environment — deploy directly to production with verification
- Mobile app (native) — future milestone, not current scope
- Mobile app CI — deferred until native app exists

## Context

- **Monorepo structure**: Root (Python/JS platform) + `frontend/` (Next.js 16) + `wordpress-theme/skyyrose-flagship/` (PHP theme)
- **Existing CI**: 9 GitHub Actions workflows exist but lack enforcement rigor; `ci.yml` has lint + test stages
- **No git hooks**: No `.husky/` or pre-commit configuration exists
- **WordPress theme**: 31 CSS files, 24 JS files, 19 PHP modules — all have `.min` counterparts already
- **WordPress server**: SSH access confirmed, WP-CLI available
- **Agent context**: Ralph Wiggum loop and Claude Code agents autonomously write and commit code
- **Known concerns**: 232 console statements in production, 33 `any` type usages, incomplete error handling
- **Deploy targets**: Vercel (frontend), WordPress host via WP-CLI (theme)

## Constraints

- **Tech stack**: GitHub Actions for CI (existing), Husky for git hooks, npm scripts for build
- **Compatibility**: Must work with existing `ci.yml` pipeline — extend, don't replace
- **Performance**: Git hooks must complete in <30 seconds to not block agent iteration speed
- **SSH**: WordPress deploys use SSH + WP-CLI (no FTP, no git-based deploy)
- **Node**: v22.x (per `.nvmrc`)
- **PHP**: Must validate against whatever PHP version runs on the WordPress server

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| All CI checks must pass for merge | Agent autonomy requires automated quality gates, not human review | — Pending |
| WP-CLI over SFTP for deploys | WP-CLI enables cache flushing, maintenance mode, plugin management alongside file transfer | — Pending |
| Local + CI minification | Local build for fast dev feedback, CI validates minified output matches source | — Pending |
| Husky for git hooks | Industry standard, npm-native, works with existing package.json | — Pending |
| Extend existing CI, don't replace | 9 workflows already exist with security scanning — preserve that investment | — Pending |

---
*Last updated: 2026-03-08 after initialization*
