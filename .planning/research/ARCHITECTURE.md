# Architecture Research: Production Armor & WordPress Build Autonomy

**Research Date:** 2026-03-08
**Dimension:** Architecture
**Confidence:** HIGH

## System Architecture

### Overview

The 4-layer protection model forms a pipeline where each layer catches what the previous missed:

```
Agent writes code
       │
       ▼
┌─────────────────┐
│  Layer 1: Hooks  │  Local — seconds — catches syntax, lint, types
│  (pre-commit)    │
└────────┬────────┘
         │ git push
         ▼
┌─────────────────┐
│  Layer 2: CI     │  Remote — minutes — full test suite, build validation
│  (GitHub Actions)│
└────────┬────────┘
         │ PR created
         ▼
┌─────────────────┐
│  Layer 3: PR     │  Policy — blocks merge until CI green
│  (Branch Rules)  │
└────────┬────────┘
         │ merge to main
         ▼
┌─────────────────┐
│  Layer 4: Deploy │  Production — validates live site after deploy
│  (Verification)  │
└─────────────────┘
```

### Component Boundaries

#### Git Hooks Subsystem
- **Location:** `.husky/` (root) + `lint-staged.config.js` or package.json config
- **Scope:** Runs on developer/agent machine before commit
- **Boundary:** Only checks staged files. Cannot run full test suite (too slow).
- **Languages:** Shell scripts (`.husky/pre-commit`), Node.js (lint-staged)
- **Monorepo concern:** Must detect which part of repo changed (Python, JS/TS, PHP) and run appropriate checks

#### CI Pipeline Subsystem
- **Location:** `.github/workflows/ci.yml` (primary) + supporting workflows
- **Scope:** Full validation on remote runners after push
- **Boundary:** Runs everything — lint, types, tests, builds. No shortcuts.
- **Monorepo concern:** Use path filters to only run relevant jobs (Python changes → Python tests, WP changes → PHP checks + build)

#### PR Protection Subsystem
- **Location:** GitHub repository settings (not code — API/UI configuration)
- **Scope:** Policy enforcement at merge time
- **Boundary:** Pure configuration — references CI job names as required checks
- **Setup:** GitHub CLI (`gh api`) or repository settings UI

#### WordPress Build Pipeline
- **Location:** `wordpress-theme/skyyrose-flagship/` (package.json, webpack.config.js)
- **Scope:** Minification of all CSS/JS files, theme packaging
- **Boundary:** Local build produces `.min` files. CI validates build output matches.
- **Current gap:** webpack covers ~6/24 JS files, clean-css covers 3/31 CSS files

#### Deploy Pipeline
- **Location:** Deploy script (new) + GitHub Actions workflow (new or extended)
- **Scope:** Transfer built theme to production server, activate, verify
- **Boundary:** SSH → rsync files → WP-CLI commands → health check
- **Components:**
  1. **rsync:** Efficient file transfer (only changed files)
  2. **WP-CLI:** `wp maintenance-mode activate`, `wp theme activate`, `wp cache flush`
  3. **Health check:** curl against `/health`, `/health/ready`, `/health/live`

### Data Flow

```
Staged files → lint-staged → ESLint/Ruff/Black/isort/php-l/tsc/mypy
                                    │
                              Pass? ─┤─ No → Block commit
                                    │
                              Yes ──→ git commit succeeds
                                    │
                              git push → GitHub Actions triggered
                                    │
                              CI jobs run (parallel):
                              ├── Python lint + tests
                              ├── Frontend lint + type-check + tests
                              ├── WordPress PHP lint + build validation
                              └── Security scanning
                                    │
                              All green? ─┤─ No → PR blocked
                                          │
                                    Yes ──→ PR mergeable
                                          │
                                    Merge to main
                                          │
                                    Deploy workflow:
                                    ├── npm run build (WP theme)
                                    ├── rsync to server
                                    ├── WP-CLI maintenance mode
                                    ├── WP-CLI activate + cache flush
                                    └── Health check verification
```

### Monorepo Path Mapping

| Path | Hooks Check | CI Job |
|------|------------|--------|
| `*.py`, `tests/` | ruff, black, isort, mypy, pytest | python-tests |
| `frontend/**/*.ts(x)` | eslint, tsc | frontend-tests |
| `wordpress-theme/**/*.php` | php -l | wp-php-lint |
| `wordpress-theme/**/*.js` | eslint | wp-build-validation |
| `wordpress-theme/**/*.css` | (none — auto-built) | wp-build-validation |

### Suggested Build Order

1. **CI hardening** (remove `continue-on-error`) — no new code, immediate impact
2. **Husky + lint-staged setup** — local protection layer
3. **WordPress build pipeline extension** — cover all CSS/JS files
4. **PHP linting** — add to hooks and CI
5. **PR branch protection** — configure via GitHub API
6. **Deploy automation** — rsync + WP-CLI script
7. **Deploy verification** — health check integration
8. **Minification drift detection** — CI validates .min files are current

The order follows dependency chains: CI must have real checks before branch protection references them. Build pipeline must exist before deploy can ship built assets.

---
*Research completed: 2026-03-08*
