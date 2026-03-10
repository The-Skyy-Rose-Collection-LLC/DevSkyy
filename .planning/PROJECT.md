# Production Armor & WordPress Build Autonomy

## What This Is

A multi-layered defense system that prevents autonomous AI agents from breaking the live SkyyRose ecommerce site. Four layers of protection (git hooks, CI, PR gates, deploy verification) catch bad code at every stage, while a WordPress build pipeline automates minification, PHP testing, and WP-CLI deployments — enabling zero-touch, agent-driven releases.

## Core Value

No agent-written code can reach production without passing automated quality gates at every layer — local, CI, PR, and post-deploy.

## Requirements

### Validated

- ✓ GitHub Actions CI pipeline with lint + test stages — existing
- ✓ Jest test framework configured for Next.js frontend — existing
- ✓ Python testing with pytest — existing
- ✓ ESLint + Ruff + Black formatting tools — existing
- ✓ TypeScript type checking — existing
- ✓ Security scanning workflows (DAST, security-gate) — existing
- ✓ Concurrency control on CI runs — existing
- ✓ Local git hooks (lint, type-check, tests, PHP syntax) on every commit — v1.0
- ✓ CI pipeline enforces hard failures — no soft warnings, no skippable checks — v1.0
- ✓ PR branch protection — merge blocked unless all CI checks pass — v1.0
- ✓ Post-deploy verification validates live site content (not just HTTP 200) — v1.0
- ✓ WordPress CSS/JS minification pipeline (local npm build + CI validation) — v1.0
- ✓ PHP linting and testing for WordPress theme files — v1.0
- ✓ WP-CLI automated deployment via SSH with maintenance mode safety — v1.0
- ✓ Single command deploys theme from commit to live site — v1.0

### Active

(None — next milestone requirements defined via `/gsd:new-milestone`)

### Out of Scope

- Human code review requirement — agents operate autonomously, CI is the reviewer
- Coverage threshold gates — focus on hard pass/fail, not percentage targets
- Rollback automation — manual rollback acceptable for v1
- Staging environment — deploy directly to production with verification
- Mobile app CI — deferred until native app exists

## Context

- **Monorepo structure**: Root (Python/JS platform) + `frontend/` (Next.js 16) + `wordpress-theme/skyyrose-flagship/` (PHP theme)
- **CI**: 9 GitHub Actions workflows, zero continue-on-error, 5 required status checks on main
- **Git hooks**: Husky v9 + lint-staged routing Python/JS/TS/PHP through 6 tools + conditional mypy/pytest
- **WordPress build**: webpack (43 JS) + clean-css (56 CSS) + source maps (99 .map files)
- **Deploy pipeline**: `deploy-pipeline.sh` → npm build → rsync/lftp with maintenance mode → 6-page content verification
- **Agent context**: Ralph Wiggum loop and Claude Code agents autonomously write and commit code
- **Known tech debt**: 20+ mypy error codes disabled (2094 pre-existing type errors), VALIDATION.md frontmatter not updated
- **Deploy targets**: Vercel (frontend), WordPress host via SSH/WP-CLI (theme)

## Constraints

- **Tech stack**: GitHub Actions for CI, Husky for git hooks, npm scripts for build
- **Compatibility**: Must work with existing `ci.yml` pipeline — extend, don't replace
- **Performance**: Git hooks must complete in <30 seconds to not block agent iteration speed
- **SSH**: WordPress deploys use SSH + WP-CLI (no FTP, no git-based deploy)
- **Node**: v22.x (per `.nvmrc`)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| All CI checks must pass for merge | Agent autonomy requires automated quality gates, not human review | ✓ Good — 5 required checks enforced |
| WP-CLI over SFTP for deploys | WP-CLI enables cache flushing, maintenance mode, plugin management | ✓ Good — maintenance mode + cache flush integrated |
| Local + CI minification | Local build for fast dev feedback, CI validates output matches source | ✓ Good — drift detection catches stale .min files |
| Husky for git hooks | Industry standard, npm-native, works with existing package.json | ✓ Good — 6 tools routing via lint-staged |
| Extend existing CI, don't replace | 9 workflows already exist with security scanning | ✓ Good — wordpress-theme job added, no disruption |
| Separate verify script from deploy | Independently testable, reusable outside pipeline | ✓ Good — 6-page deep content verification |
| Build runs even in dry-run | Catches build errors before live deploy (local-only) | ✓ Good — no false-positive dry-runs |
| 20+ mypy error codes disabled | 2094 pre-existing type errors, Phase 1 scope was CI fix not debt | ⚠️ Revisit — incrementally re-enable |

---
*Last updated: 2026-03-10 after v1.0 milestone*
