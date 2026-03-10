# SkyyRose WordPress — Quality & Accessibility

## What This Is

The SkyyRose luxury streetwear ecommerce site (skyyrose.co) built on WordPress/WooCommerce with a custom flagship theme. Three collections (Black Rose, Love Hurts, Signature) with immersive 3D experiences, pre-order gateways, and a luxury shopping experience. Protected by a 4-layer production armor chain (git hooks → CI → PR gates → deploy verification) with automated build and deploy pipelines.

## Core Value

skyyrose.co works flawlessly on every device, passes WCAG AA accessibility, and shows the right products in the right collections — a professional luxury shopping experience with zero embarrassing bugs.

## Current Milestone: v1.1 WordPress Quality & Accessibility

**Goal:** Fix all accessibility errors, optimize responsive design, fix product placement, and polish the luxury cursor — making the live site flawless.

**Target features:**
- Zero Ally plugin errors (currently 100+ per page)
- WCAG AA compliant color contrast and ARIA
- Responsive typography and layout across all devices
- Luxury cursor working correctly on popups/modals
- Correct hero banners and product-to-collection assignments
- Pre-order products properly separated from live collections

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

(Defined in `.planning/REQUIREMENTS.md` for v1.1)

### Out of Scope

- Human code review requirement — agents operate autonomously, CI is the reviewer
- Coverage threshold gates — focus on hard pass/fail, not percentage targets
- Rollback automation — manual rollback acceptable for v1
- Staging environment — deploy directly to production with verification
- Mobile app CI — deferred until native app exists
- WCAG AAA compliance — targeting AA level
- New feature development — this milestone is polish and fixes only

## Context

- **Monorepo structure**: Root (Python/JS platform) + `frontend/` (Next.js 16) + `wordpress-theme/skyyrose-flagship/` (PHP theme)
- **CI**: 9 GitHub Actions workflows, zero continue-on-error, 5 required status checks on main
- **Git hooks**: Husky v9 + lint-staged routing Python/JS/TS/PHP through 6 tools + conditional mypy/pytest
- **WordPress build**: webpack (43 JS) + clean-css (56 CSS) + source maps (99 .map files)
- **Deploy pipeline**: `deploy-pipeline.sh` → npm build → rsync/lftp with maintenance mode → 6-page content verification
- **Agent context**: Ralph Wiggum loop and Claude Code agents autonomously write and commit code
- **Known tech debt**: 20+ mypy error codes disabled (2094 pre-existing type errors), VALIDATION.md frontmatter not updated
- **Deploy targets**: Vercel (frontend), WordPress host via SSH/WP-CLI (theme)
- **Ally plugin**: Installed on live site, finds 100+ errors per page (HTML validation, ARIA, contrast)
- **Accessibility fix plugin**: `skyyrose-accessibility-fix.php` exists as bandaid — fixes should be in theme code directly
- **Theme audit findings**: Duplicate stylesheet handles, cursor z-index conflicts with modals, small text contrast issues, hero image missing loading="eager"

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
