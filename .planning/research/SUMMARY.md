# Project Research Summary

**Project:** Production Armor & WordPress Build Autonomy
**Domain:** CI/CD Pipeline Hardening + WordPress Build Automation
**Researched:** 2026-03-08
**Confidence:** HIGH

## Executive Summary

This project is a defense-in-depth system for autonomous AI agents operating on a production ecommerce codebase. The core problem is straightforward: agents (Ralph Wiggum, Claude Code) write and commit code autonomously, but the existing CI pipeline has 17 `continue-on-error: true` directives that silently swallow failures, no git hooks exist despite Husky being in dependencies, no branch protection prevents direct pushes to main, and only a fraction of WordPress theme assets pass through the build pipeline. The result is that broken code can reach production unchecked.

The recommended approach is a 4-layer pipeline — local hooks, CI enforcement, PR gates, deploy verification — built almost entirely with tools already in the repo. The critical insight from research is that this is not a greenfield tooling project. The tools exist (Husky, ESLint, Ruff, webpack, clean-css, pytest, GitHub Actions). The work is removing soft failures, fixing broken configurations, extending partial coverage to full coverage, and wiring up deployment automation. Roughly 70% of the effort is configuration and integration, not new code.

The top risks are: (1) removing `continue-on-error` will immediately break CI because those checks currently fail — the failures must be fixed first or the pipeline becomes unusable; (2) the Husky v4 config format in package.json will silently not work with Husky v9 — it must be deleted and replaced, not upgraded; (3) minification drift is already happening — only 6/24 JS and 3/31 CSS files go through the build pipeline, meaning most `.min` files are stale. All three risks are confirmed present in the current codebase, not hypothetical.

## Key Findings

### Recommended Stack

The stack is almost entirely existing tools that need proper configuration. No major new dependencies are required. The only additions are php-parallel-lint for PHP syntax checking and potentially PHPStan for static analysis.

**Core technologies:**
- **Husky v9** + **lint-staged v15**: Local git hooks that check only staged files in <30s — replacing the broken v4 config already in package.json
- **GitHub Actions** (existing): CI enforcement by removing 17 `continue-on-error` directives — zero new tools
- **webpack 5** + **clean-css-cli** (existing): WordPress asset minification — needs config extension from partial to full coverage
- **WP-CLI** + **rsync**: Deploy pipeline over SSH — maintenance mode, cache flush, file transfer, health verification
- **PHPStan**: Optional PHP static analysis at level 5 for the WordPress theme
- **GitHub Branch Protection / Rulesets**: PR gates that block merge until CI passes — native GitHub features, no tools needed

**Rejected alternatives:** pre-commit (Python-based, wrong ecosystem), PHPCS (too noisy for existing codebase), Psalm (overkill for WP theme), Docker-based CI (unnecessary complexity), lefthook (less npm ecosystem support).

### Expected Features

**Must have (table stakes):**
- Remove all `continue-on-error: true` from CI (17 instances) — zero effort, maximum safety impact
- Pre-commit hooks: lint, type-check, PHP syntax for staged files
- Branch protection: block direct pushes and force pushes to main
- Full minification: all 24 JS + 31 CSS files through the build pipeline
- Deploy automation: single-command rsync + WP-CLI deploy with health verification

**Should have (differentiators for agent autonomy):**
- Agent-aware hook messaging — clear, parseable error output for AI agents
- Minification drift detection — CI fails if `.min` files are stale vs source
- Deploy dry-run mode — validate without actually deploying
- Deep health checks — verify page content, not just HTTP 200

**Defer (v2+):**
- Auto-rollback on failed health check — manual rollback safer for v1
- Coverage threshold gates — adds complexity without clear agent workflow value
- Staging environment — direct-to-production with verification is acceptable for v1
- PHPCS/WordPress coding standards — too many existing violations to gate on

### Architecture Approach

The architecture is a linear 4-layer pipeline where each layer catches what the previous missed: hooks (seconds, local), CI (minutes, remote), PR gates (policy, merge-time), deploy verification (production, post-ship). The monorepo structure requires path-aware routing — Python changes trigger Python checks, WordPress changes trigger PHP checks and build validation, frontend changes trigger TypeScript checks. Components have clean boundaries: hooks live in `.husky/`, CI in `.github/workflows/`, build pipeline in `wordpress-theme/skyyrose-flagship/package.json`, deploy script as a new top-level script.

**Major components:**
1. **Git Hooks Subsystem** (`.husky/` + lint-staged) — seconds-fast local protection on staged files only
2. **CI Pipeline** (`.github/workflows/ci.yml`) — full validation with hard failures, path-filtered parallel jobs
3. **PR Protection** (GitHub API/settings) — policy enforcement referencing CI job names as required checks
4. **WordPress Build Pipeline** (`wordpress-theme/` webpack + clean-css) — minification of all theme assets
5. **Deploy Pipeline** (new script) — rsync + WP-CLI + health check orchestration

### Critical Pitfalls

1. **`continue-on-error` removal will break CI immediately** — those 17 directives mask real failures. Fix underlying lint/type errors first, then remove the directives. Consider phased removal: critical checks (ruff, tsc) first, then formatting, then type-checking.
2. **Husky v4 config is silently broken** — the `husky.hooks` block in package.json does nothing with Husky v8/v9. Delete it entirely, install Husky v9 at the monorepo root, create `.husky/pre-commit` shell scripts. Verify with an empty test commit.
3. **Minification drift is confirmed present** — only 9 of 55 theme asset files go through the build pipeline. The rest have stale `.min` files. Extend webpack and clean-css configs to cover everything, then add CI drift detection (`npm run build && git diff --exit-code`).
4. **WP-CLI maintenance mode can get stuck** — if deploy fails after enabling maintenance mode, the live site stays down. Wrap deploy in try/finally, add timeout, verify maintenance mode is OFF in health check.
5. **Branch protection can lock out agents** — do NOT require human reviews. Map exact CI job names to required status checks. Test with a real PR before enabling enforcement.

## Implications for Roadmap

Based on research, the project decomposes into 5 phases following a strict dependency chain.

### Phase 1: CI Hardening
**Rationale:** Highest impact, lowest effort. The CI pipeline already exists with real checks — they just don't fail the build. This must come first because branch protection (Phase 3) depends on having reliable CI checks to reference.
**Delivers:** A CI pipeline where failures actually block merges. All lint, type-check, and test steps produce hard failures.
**Addresses:** Remove `continue-on-error` (17 instances), fix underlying lint/type failures that the directives were masking, add PHP syntax validation step.
**Avoids:** Pitfall #3 (CI breaking) — fix failures before removing soft-fail directives. Phased approach: remove for critical checks first, less critical later.

### Phase 2: Local Git Hooks
**Rationale:** Provides fast feedback before code ever reaches CI. Independent of Phase 1 technically, but building after CI hardening means hook failures align with what CI enforces — no surprises.
**Delivers:** Pre-commit hooks via Husky v9 + lint-staged that check staged files in <30 seconds. Monorepo-aware: detects which language changed and runs appropriate checks.
**Addresses:** Husky v9 setup (replace broken v4 config), lint-staged for ESLint/Ruff/Black/isort/php-l/tsc/mypy, fast unit tests on changed files.
**Avoids:** Pitfall #1 (Husky version mismatch) — delete old config, fresh v9 install at root. Pitfall #2 (wrong directory) — test with deliberately broken files. Pitfall #7 (performance) — type checking as pre-push if too slow.

### Phase 3: PR Branch Protection
**Rationale:** Depends on Phase 1 (CI checks must exist and be reliable before they can be required). Pure configuration, no code. Closes the gap where agents push directly to main.
**Delivers:** Branch protection rules that block direct pushes, force pushes, and merges without passing CI. Agents must use PRs.
**Addresses:** Required status checks on main, block direct/force pushes, require branches up-to-date.
**Avoids:** Pitfall #8 (locking out agents) — no human review requirement, exact CI job name mapping, test with real PR before enforcement.

### Phase 4: WordPress Build Pipeline
**Rationale:** Independent of Phases 1-3 technically, but placed here because deploy automation (Phase 5) needs a complete build pipeline to ship. Extends existing partial webpack/clean-css configs.
**Delivers:** All 24 JS files through webpack, all 31 CSS files through clean-css, source maps for dev, CI drift detection that fails if `.min` files are stale.
**Addresses:** Full minification coverage, build verification in CI, source map generation.
**Avoids:** Pitfall #4 (minification drift) — CI step runs `npm run build && git diff --exit-code` to catch stale outputs.

### Phase 5: Deploy Automation and Verification
**Rationale:** Depends on Phase 4 (must have complete build output to deploy). The final layer that connects the pipeline to production.
**Delivers:** Single-command deploy script (rsync + WP-CLI), maintenance mode handling, cache flush, post-deploy health checks against `/health`, `/health/ready`, `/health/live`.
**Addresses:** rsync file transfer, WP-CLI orchestration, health endpoint validation, deploy dry-run mode.
**Avoids:** Pitfall #5 (SSH key management) — dedicated deploy key in GitHub Secrets. Pitfall #6 (maintenance mode stuck) — try/finally wrapper with timeout, health check verifies mode is OFF.

### Phase Ordering Rationale

- **Phases 1-3 form the "armor" chain:** CI must be reliable before branch protection can reference it, and hooks provide local fast-feedback that mirrors CI enforcement.
- **Phases 4-5 form the "build and ship" chain:** Full build pipeline must exist before deploy can ship built assets.
- **The two chains are mostly independent** but Phase 3 should precede Phase 5 — you want PR gates in place before automated deploys exist, so agents cannot deploy unchecked code.
- **This order maximizes safety at each step:** After Phase 1, bad code is caught in CI. After Phase 3, it cannot reach main. After Phase 5, it is deployed and verified automatically.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1 (CI Hardening):** Needs investigation of the 17 specific `continue-on-error` instances to determine which underlying failures are quick fixes vs substantial work. A triage step is required before removal.
- **Phase 5 (Deploy Automation):** SSH access patterns, server environment (PHP version, WP-CLI version), and hosting provider constraints need validation. Health endpoint behavior under maintenance mode should be tested.

Phases with standard patterns (skip research-phase):
- **Phase 2 (Git Hooks):** Husky v9 + lint-staged is extremely well-documented. The only nuance is monorepo path handling, which lint-staged docs cover.
- **Phase 3 (Branch Protection):** Pure GitHub configuration with extensive documentation. Can be done via `gh api` in minutes.
- **Phase 4 (WP Build Pipeline):** webpack and clean-css are mature tools already partially configured. Extension is mechanical — add entry points, not new patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Nearly all tools already exist in the repo. Versions and configs verified against package.json and workflow files. |
| Features | HIGH | Feature list derived from confirmed gaps in the current codebase (17 soft failures, missing hooks, partial build coverage). |
| Architecture | HIGH | 4-layer pipeline is a standard CI/CD pattern. Monorepo path routing is well-documented. |
| Pitfalls | HIGH | Top 3 pitfalls (continue-on-error masking failures, Husky version mismatch, minification drift) are confirmed present, not speculative. |

**Overall confidence:** HIGH

This is not a novel architecture problem. It is a configuration and integration project using mature, well-documented tools that are largely already present in the repo. The research confidence is high because findings are grounded in the actual codebase state, not hypothetical patterns.

### Gaps to Address

- **Specific CI failure triage:** The 17 `continue-on-error` instances mask real failures. Before removing them, each must be triaged: is the fix trivial (formatting) or substantial (type errors across hundreds of files)? This determines Phase 1 scope.
- **WordPress server environment:** PHP version, WP-CLI version, hosting provider restrictions, and SSH access patterns need confirmation before Phase 5 planning. The research assumes SSH + WP-CLI are available (stated in PROJECT.md) but specifics are unknown.
- **Agent workflow integration:** How exactly do Ralph Wiggum and Claude Code interact with PRs today? Do they push directly to main? Do they create branches? This affects Phase 3 configuration — branch protection rules must match the agent workflow, not break it.
- **Existing `.min` file provenance:** Are the 46 unbuilt `.min` files hand-minified, copy-pasted, or generated by a now-removed tool? This affects the Phase 4 approach — extending the build pipeline may produce different output than existing `.min` files, causing a large diff.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `.github/workflows/ci.yml`, `wordpress-theme/skyyrose-flagship/package.json`, `wordpress-theme/skyyrose-flagship/webpack.config.js`
- `.planning/PROJECT.md` — project definition with validated requirements and constraints
- Husky v9 migration guide — `.husky/` directory structure, removal of package.json config format
- GitHub Actions documentation — `continue-on-error` behavior, required status checks

### Secondary (MEDIUM confidence)
- lint-staged monorepo patterns — community conventions for path-aware linting
- PHPStan WordPress extension — level 5 analysis for theme code
- WP-CLI deployment patterns — maintenance mode + cache flush orchestration

---
*Research completed: 2026-03-08*
*Ready for roadmap: yes*
