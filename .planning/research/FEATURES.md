# Features Research: Production Armor & WordPress Build Autonomy

**Research Date:** 2026-03-08
**Dimension:** Features
**Confidence:** HIGH

## Table Stakes (Must Have)

### Git Hooks (Local Protection)

| Feature | Complexity | Dependencies |
|---------|-----------|--------------|
| Pre-commit lint (ESLint, Ruff, Black, isort) | Low | Husky, lint-staged |
| Pre-commit type checking (tsc, mypy) | Low | Existing tools |
| Pre-commit PHP syntax check (php -l) | Low | php-parallel-lint |
| Pre-commit fast unit tests (changed files only) | Medium | jest --changedSince, pytest |
| Hook bypass protection (warn on --no-verify) | Low | CI detection |

### CI Hard Failures

| Feature | Complexity | Dependencies |
|---------|-----------|--------------|
| Remove all `continue-on-error: true` (17 instances) | Low | None — just delete lines |
| All lint steps fail the build on error | Low | Remove continue-on-error |
| All type-check steps fail the build on error | Low | Remove continue-on-error |
| PHP syntax validation in CI | Low | php -l step |
| WordPress theme build validation (minified output matches source) | Medium | npm build in CI |

### PR Protection

| Feature | Complexity | Dependencies |
|---------|-----------|--------------|
| Required status checks on main branch | Low | GitHub settings |
| Block direct pushes to main | Low | GitHub settings |
| Block force pushes to main | Low | GitHub settings |
| Require branches to be up-to-date before merge | Low | GitHub settings |

### WordPress Minification

| Feature | Complexity | Dependencies |
|---------|-----------|--------------|
| All 24 JS files built through webpack | Medium | webpack config extension |
| All 31 CSS files built through clean-css | Medium | npm script extension |
| Source maps for development | Low | webpack config |
| Build verification (CI checks .min files are current) | Medium | npm build + git diff |

### Deploy Automation

| Feature | Complexity | Dependencies |
|---------|-----------|--------------|
| rsync theme files to server via SSH | Medium | SSH keys, rsync |
| WP-CLI maintenance mode on/off during deploy | Low | WP-CLI, SSH |
| WP-CLI cache flush after deploy | Low | WP-CLI, SSH |
| Post-deploy health check (curl health endpoints) | Low | Health endpoints exist |
| Single-command deploy (npm run deploy or similar) | Medium | Script orchestration |

## Differentiators (Competitive Advantage for Agent Autonomy)

| Feature | Complexity | Dependencies |
|---------|-----------|--------------|
| Agent-aware hook messaging (clear error output for AI parsing) | Low | Hook scripts |
| Minification drift detection (CI fails if .min files are stale) | Medium | Build + git diff |
| Deploy dry-run mode (validate without actually deploying) | Medium | Deploy script flag |
| Health endpoint deep check (not just 200, validate page content) | Medium | curl + grep |
| Automatic theme version bump on deploy | Low | WP-CLI + sed |

## Anti-Features (Deliberately NOT Building)

| Feature | Reason |
|---------|--------|
| Human code review requirement | Agents operate autonomously — CI is the reviewer |
| Coverage threshold gates | Adds complexity without clear value for agent workflows |
| Auto-rollback on failed health check | Too risky for v1 — manual rollback is safer |
| Staging environment | Deploy directly to production with verification |
| Docker-based CI | Adds complexity — native runners sufficient for this stack |
| PHPCS/WordPress coding standards enforcement | Would generate hundreds of warnings on existing theme code |

## Feature Dependencies

```
Git Hooks ──────────────── (independent, build first)
     │
CI Hard Failures ───────── (independent, build alongside hooks)
     │
     ├── PR Protection ──── (depends on CI checks existing)
     │
WP Minification ────────── (independent)
     │
     ├── Deploy Automation ─ (depends on minification pipeline)
     │
     └── Deploy Verification (depends on deploy automation)
```

## MVP Priority Order

1. **Remove `continue-on-error`** — zero effort, maximum impact (17 silent failures → hard failures)
2. **Branch protection rules** — zero code, prevents direct pushes to main
3. **Husky v9 + lint-staged** — fast local feedback loop
4. **Extend minification coverage** — 24 JS + 31 CSS files fully built
5. **PHP linting** — catch syntax errors in theme files
6. **Deploy script** — rsync + WP-CLI orchestration
7. **Post-deploy verification** — health checks confirm live site works

---
*Research completed: 2026-03-08*
