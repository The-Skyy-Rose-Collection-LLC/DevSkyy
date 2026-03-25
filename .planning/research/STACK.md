# Stack Research: Production Armor & WordPress Build Autonomy

**Research Date:** 2026-03-08
**Dimension:** Stack
**Confidence:** HIGH

## Recommended Stack

### Layer 1: Local Git Hooks

| Tool | Version | Role | Confidence |
|------|---------|------|------------|
| **Husky** | v9.x | Git hooks manager (npm-native) | HIGH |
| **lint-staged** | v15.x | Run linters only on staged files | HIGH |
| **php-parallel-lint** | v1.4.x (composer) | PHP syntax validation (`php -l` wrapper) | HIGH |

**Rationale:** Husky v9 uses a simpler `.husky/` directory structure (no more `husky.hooks` in package.json — that's the v4 format currently in the WP theme). lint-staged ensures hooks run fast (<30s) by only checking changed files. php-parallel-lint runs `php -l` in parallel across all changed PHP files.

**Do NOT use:**
- pre-commit (Python-based) — adds a Python dependency to a primarily JS/PHP project
- Husky v4 format (`husky.hooks` in package.json) — deprecated, already broken in this repo
- lefthook — less ecosystem support than Husky for npm projects

### Layer 2: CI Hard Failures (GitHub Actions)

| Tool | Version | Role | Confidence |
|------|---------|------|------------|
| **GitHub Actions** | existing | CI/CD platform | HIGH |
| **Ruff** | 0.8.x+ | Python linter (already in use) | HIGH |
| **Black** | 24.x+ | Python formatter (already in use) | HIGH |
| **mypy** | 1.x+ | Python type checker (already in use) | HIGH |
| **ESLint** | v9.x | JS linter (upgrade from v8) | MEDIUM |
| **tsc** | 5.x | TypeScript type checker | HIGH |
| **PHPStan** | 1.12.x | PHP static analysis (level 5 for theme) | MEDIUM |

**Rationale:** All Python tools already exist but run with `continue-on-error: true` (17 instances!). The primary work is removing soft failures, not adding new tools. PHPStan adds static analysis beyond `php -l` syntax checking.

**Do NOT use:**
- PHPCS (PHP_CodeSniffer) — too opinionated for an existing theme, would generate hundreds of warnings
- Psalm — overkill for a WordPress theme; PHPStan is simpler
- prettier for PHP — no established PHP prettier plugin worth using

### Layer 3: PR Protection

| Tool | Version | Role | Confidence |
|------|---------|------|------------|
| **GitHub Branch Protection Rules** | native | Enforce required checks | HIGH |
| **GitHub Rulesets** | native | More granular than branch protection | HIGH |
| **CODEOWNERS** | native | Optional — define review ownership | MEDIUM |

**Rationale:** GitHub native features — no external tools needed. Rulesets (2024+) are more flexible than classic branch protection and support tag/branch patterns.

### Layer 4: Deploy Verification

| Tool | Version | Role | Confidence |
|------|---------|------|------------|
| **curl + health endpoints** | native | Post-deploy smoke tests | HIGH |
| **WP-CLI** | 2.10.x | WordPress management via SSH | HIGH |
| **rsync** | native | File transfer over SSH | HIGH |

**Rationale:** WP-CLI handles maintenance mode, cache flushing, plugin/theme activation. rsync handles efficient file transfer (only changed files). curl validates health endpoints post-deploy.

### WordPress Build Pipeline

| Tool | Version | Role | Confidence |
|------|---------|------|------------|
| **webpack** | 5.x (existing) | JS bundling + minification | HIGH |
| **clean-css-cli** | 5.x (existing) | CSS minification | HIGH |
| **terser-webpack-plugin** | 5.x (existing) | JS minification within webpack | HIGH |
| **npm scripts** | native | Build orchestration | HIGH |

**Rationale:** All build tools already exist in the WP theme `package.json`. The gap is coverage — webpack handles ~6/24 JS files, clean-css covers 3/31 CSS files. Need to extend configs to cover all theme assets.

## Existing State (What's Already There)

- **ci.yml**: Full pipeline with lint, Python tests, frontend tests, security scanning — but 14 `continue-on-error: true` directives
- **security-gate.yml**: 3 more `continue-on-error: true`
- **dast-scan.yml**: 2 more `continue-on-error: true`
- **WordPress package.json**: Husky v8 in devDeps, v4 config format (never initialized), webpack + clean-css partially configured
- **No `.husky/` directory**: Hooks never set up despite being in dependencies
- **No branch protection**: Agents can push directly to main

## Build Order Implications

1. Remove `continue-on-error` from CI (zero new tools needed)
2. Set up Husky v9 + lint-staged (replace broken v4 config)
3. Extend webpack/clean-css to cover all theme files
4. Add PHP linting (php-parallel-lint + optional PHPStan)
5. Build deploy script (rsync + WP-CLI)
6. Configure branch protection rules
7. Add post-deploy verification

---
*Research completed: 2026-03-08*
