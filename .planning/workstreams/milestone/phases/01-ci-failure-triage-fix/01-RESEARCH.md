# Phase 1: CI Failure Triage & Fix - Research

**Researched:** 2026-03-08
**Domain:** GitHub Actions CI/CD, Python linting/formatting, TypeScript/ESLint, security scanning
**Confidence:** HIGH

## Summary

Phase 1 targets removing all 17 `continue-on-error: true` directives from three workflow files (ci.yml, security-gate.yml, dast-scan.yml) and fixing the underlying failures they mask. The codebase is in better shape than expected -- most failures are auto-fixable formatting issues (13 black files, 70 ruff import-sorting errors) or broken tooling (Next.js 16 removed `next lint`). The security scanning steps use a dual-suppression pattern (`|| true` at command level AND `continue-on-error` at step level) that needs careful unwinding.

A critical finding: GitHub Actions runners are currently not executing (billing/quota issue -- all recent runs show 0 steps, runner_id 0, completing in 2 seconds). This means CI fixes cannot be validated via GitHub Actions until the billing issue is resolved. Local validation of each tool is the only verification path available now.

**Primary recommendation:** Auto-fix formatting first (`black .`, `isort .`, `ruff check --fix .`), fix the one mypy error, migrate frontend ESLint from `next lint` to direct `eslint` CLI, then remove `continue-on-error` directives in a structured order (lint -> security -> frontend -> DAST -> deploy tag).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Remove `continue-on-error` from all security steps in ci.yml and security-gate.yml
- Many security commands already use `|| true` at command level -- refactor these to use proper exit codes
- Keep the existing gate pattern: individual tools report findings, "Fail on critical vulnerabilities" step enforces on HIGH+HIGH confidence
- For gitleaks/trufflehog in security-gate.yml: remove `continue-on-error` AND `|| true` -- secrets in code should be a hard failure
- For pip-licenses: remove `continue-on-error`, add an allowlist for known acceptable licenses
- Auto-fix codebase FIRST: run `black .`, `isort .` to format all Python code
- Then remove `continue-on-error` from black and isort steps -- they should pass clean
- For mypy: add targeted `# type: ignore` comments or configure `mypy.ini` to exclude known problematic modules -- don't suppress the entire check
- For ESLint: fix real errors in frontend code, then remove `continue-on-error`
- For tsc (TypeScript): fix type errors in frontend, then remove `continue-on-error`
- DAST workflow (dast-scan.yml): Remove the 2 `continue-on-error` directives; add a clear early-exit guard so it fails fast with an informative message rather than silently swallowing errors
- Three.js tests: Verify whether `npm run test:collections` actually works; if tests exist and pass, remove `continue-on-error`; if they don't exist or are fundamentally broken, remove the entire job
- Remove `continue-on-error` from git tag step
- Make tag creation robust: use timestamp-based tags that won't conflict, or check-before-create
- Tag failure should not block the deploy -- restructure so tagging is a post-deploy step

### Claude's Discretion
- Exact mypy configuration (which modules to exclude vs fix)
- Whether to split ci.yml security steps into a separate job or keep in current structure
- Order of fixes (lint first vs security first)
- Whether to auto-fix ESLint issues with `--fix` or fix manually

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CI-01 | All 17 `continue-on-error: true` directives removed from ci.yml, security-gate.yml, dast-scan.yml | Full inventory of all 17 directives completed with line numbers, underlying failures triaged, fix strategies identified for each |
| CI-02 | Underlying lint/type/format failures fixed so CI passes without soft failures | Local validation shows: 13 black files (auto-fix), 70 ruff errors (auto-fix), 0 isort errors (clean), 1 mypy error (fixable), 0 TypeScript errors (clean), ESLint needs migration from broken `next lint` to direct `eslint` CLI, Three.js tests pass (408/408), security tools need `|| true` removal |
</phase_requirements>

## Full Inventory: 17 `continue-on-error` Directives

### ci.yml (12 directives)

| # | Line | Step Name | Underlying Issue | Fix Strategy |
|---|------|-----------|------------------|--------------|
| 1 | 89 | Check black formatting | 13 files need reformatting | Auto-fix: `black .`, then remove directive |
| 2 | 93 | Check isort imports | Currently clean (0 errors) | Remove directive directly |
| 3 | 105 | Run mypy type checking | 1 error: duplicate module name (`test_connection.py`) | Exclude paths in mypy config, then remove directive |
| 4 | 216 | Run pip-audit | `|| true` at command level too; tool may find real vulnerabilities | Remove both `|| true` and directive; let gate step handle severity |
| 5 | 228 | Run bandit | `|| true` at command level too; dual suppression | Remove both; gate step already handles HIGH+HIGH |
| 6 | 233 | Run safety check | Advisory nature -- may find issues | Remove directive; let gate step handle |
| 7 | 239 | Run semgrep | `|| true` at command level too; dual suppression | Remove both; let gate step handle |
| 8 | 250 | Run custom security audit | Script exists but may fail in CI (missing deps) | Remove directive; guard with `if [ -f ... ]` (already done) |
| 9 | 327 | Run ESLint | `next lint` removed in Next.js 16 -- always fails | Migrate to direct `eslint` CLI; add ESLint as frontend devDependency |
| 10 | 331 | Run TypeScript type check | Currently clean (0 errors locally) | Remove directive directly |
| 11 | 368 | Run Three.js collection tests | Tests exist and pass (408/408) | Remove directive directly |
| 12 | 680 | Create deployment tag | Tag may already exist | Make tag name unique (timestamp already used), add `|| echo` with warning |

### security-gate.yml (3 directives)

| # | Line | Step Name | Underlying Issue | Fix Strategy |
|---|------|-----------|------------------|--------------|
| 13 | 44 | Run Gitleaks | `|| true` at command level too | Remove BOTH -- secrets are hard failures per user decision |
| 14 | 52 | Run TruffleHog | `|| true` at command level too | Remove BOTH -- secrets are hard failures per user decision |
| 15 | 135 | Check Python licenses | `|| true` in install, `|| echo` in check | Remove directive; add license allowlist for known acceptable licenses |

### dast-scan.yml (2 directives)

| # | Line | Step Name | Underlying Issue | Fix Strategy |
|---|------|-----------|------------------|--------------|
| 16 | 57 | Run DAST scan | `staging/run_dast_scan.sh` does not exist | Add early-exit guard that checks for script existence |
| 17 | 105 | Compare with baseline | `staging/compare_baseline.py` does not exist | Add early-exit guard that checks for script existence |

## `|| true` Patterns (Companion Issues)

These command-level suppressions compound with `continue-on-error` and need parallel removal:

| File | Line | Command | Action |
|------|------|---------|--------|
| ci.yml | 176 | Codecov upload `\|\| true` | KEEP -- Codecov is optional, not a quality gate |
| ci.yml | 214 | pip-audit JSON output `\|\| true` | REMOVE -- let gate step handle |
| ci.yml | 224 | bandit `\|\| true` | REMOVE -- let gate step handle |
| ci.yml | 237 | semgrep `\|\| true` | REMOVE -- let gate step handle |
| security-gate.yml | 43 | gitleaks `\|\| true` | REMOVE -- hard failure per user decision |
| security-gate.yml | 51 | trufflehog `\|\| true` | REMOVE -- hard failure per user decision |
| security-gate.yml | 129 | pip install `\|\| true` | KEEP -- defensive install fallback |
| dast-scan.yml | 30 | pip install requirements `\|\| true` | KEEP -- requirements.txt may not exist |
| dast-scan.yml | 212 | Slack webhook `\|\| true` | KEEP -- notification failure should not break scan |

## Standard Stack

### Core (already in use)
| Tool | Version | Purpose | Status in CI |
|------|---------|---------|--------------|
| ruff | >=0.1 | Fast Python linter | Hard failure (no continue-on-error) -- 70 fixable errors |
| black | >=24.1 | Python formatter | Soft failure -- 13 files need reformatting |
| isort | >=5.13 | Import sorter | Soft failure -- currently clean |
| mypy | >=1.8 | Python type checker | Soft failure -- 1 error (duplicate module) |
| ESLint | 9.x | JS/TS linter | BROKEN -- `next lint` removed in Next.js 16 |
| TypeScript | ^5.9.3 | Type checker | Soft failure -- currently clean |
| Jest | ^30.2.0 | Three.js/Node tests | Soft failure -- 408 tests pass |
| pip-audit | (CI-installed) | Dependency vulnerabilities | Dual-suppressed |
| bandit | (CI-installed) | Code security analysis | Dual-suppressed |
| semgrep | (CI-installed) | SAST scanning | Dual-suppressed |
| safety | (CI-installed) | Dependency safety check | Suppressed |
| gitleaks | v8.18.4 | Secrets detection | Dual-suppressed |
| trufflehog | latest | Secrets detection | Dual-suppressed |
| pip-licenses | (CI-installed) | License compliance | Suppressed |

### Required Additions
| Tool | Version | Purpose | Why Needed |
|------|---------|---------|------------|
| eslint | ^9.39 | Frontend linting | Must be added as frontend devDependency since `next lint` is removed |

## Architecture Patterns

### Security Scanning: Gate Pattern (PRESERVE)
The existing ci.yml security architecture uses a gate pattern that should be preserved:
1. Individual security tools run and produce reports (pip-audit, bandit, semgrep, safety)
2. Tools save JSON output as artifacts
3. Final "Fail on critical vulnerabilities" step reads bandit JSON and fails on HIGH severity + HIGH confidence
4. This gate step runs ONLY on `refs/heads/main`

**After removing `continue-on-error`:** The individual tool steps will become hard failures. This means if pip-audit, bandit, or semgrep finds ANY issue, the job fails -- not just HIGH+HIGH. The gate step becomes redundant for the tools that are now hard failures.

**Recommended approach:** For security tools (pip-audit, bandit, semgrep, safety), the right pattern is:
```yaml
- name: Run bandit (code security)
  run: |
    bandit -r . \
      -x ./tests,./venv,./.venv,./node_modules \
      -f json -o bandit-results.json \
      -ll
    # Report saved for artifacts; exit code determines pass/fail
```
Remove BOTH `|| true` and `continue-on-error`. If any tool finds issues at the configured severity level, that is a real failure that should stop the pipeline.

For the "Fail on critical vulnerabilities" gate step: KEEP it as a defense-in-depth measure, but understand that individual tool failures will now also block.

### DAST Workflow: Early Exit Guard Pattern
```yaml
- name: Run DAST scan
  run: |
    if [ ! -f "staging/run_dast_scan.sh" ]; then
      echo "::warning::DAST scan script not found. Skipping."
      echo "Create staging/run_dast_scan.sh to enable DAST scanning."
      exit 0
    fi
    chmod +x staging/run_dast_scan.sh
    ./staging/run_dast_scan.sh
```

### Deploy Tag: Robust Tagging Pattern
```yaml
- name: Create deployment tag
  run: |
    TAG_NAME="deploy-$(date +%Y%m%d-%H%M%S)-${GITHUB_SHA::7}"
    git tag -a "$TAG_NAME" -m "Production deployment" || {
      echo "::warning::Failed to create tag $TAG_NAME"
    }
    git push origin "$TAG_NAME" 2>/dev/null || {
      echo "::warning::Failed to push tag $TAG_NAME"
    }
```
Note: Per user decision, tag failure should NOT block deploy. Restructure as post-deploy step or use `if: always()`.

### ESLint Migration Pattern (Next.js 16)
Since `next lint` was removed in Next.js 16, the frontend `npm run lint` script must be updated:

```json
{
  "scripts": {
    "lint": "eslint ."
  },
  "devDependencies": {
    "eslint": "^9.39.0",
    "@eslint/eslintrc": "^3.3.3"
  }
}
```

The existing `eslint.config.mjs` is already in flat config format with `FlatCompat` for legacy Next.js extends. This should work with direct ESLint CLI.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| License allowlist | Custom license parsing | pip-licenses `--allow-classifiers` or `--fail-on` with exclusions | pip-licenses has built-in allowlist/denylist support |
| Security severity filtering | Custom JSON parsing scripts | bandit's `-ll` (low and above) or `-ii` (high confidence only) | bandit has built-in severity/confidence filters |
| ESLint for Next.js | Custom lint wrapper | Direct `eslint` CLI + `@next/eslint-plugin-next` | Standard approach after Next.js 16 migration |

## Common Pitfalls

### Pitfall 1: Removing `continue-on-error` Without Fixing Underlying Issues
**What goes wrong:** CI immediately breaks and blocks all development
**Why it happens:** Removing the suppression exposes failures that were always there
**How to avoid:** Fix every underlying issue BEFORE removing its `continue-on-error`
**Warning signs:** Running the tool locally shows errors

### Pitfall 2: Security Tool Exit Codes Are Not Uniform
**What goes wrong:** Some tools exit non-zero for ANY finding, others only for HIGH severity
**Why it happens:** Each tool has its own exit code semantics
**How to avoid:** Understand each tool's exit code behavior:
- `pip-audit --strict`: exits 1 on ANY vulnerability
- `bandit -ll`: exits 1 on LOW or above (use `-lll` for HIGH only, or `-ii` for HIGH confidence)
- `semgrep`: exits 1 on any finding at configured severity
- `gitleaks detect`: exits 1 on any detected secret
- `trufflehog`: exits 1 on any verified secret
**Warning signs:** CI fails on known, accepted low-severity issues

### Pitfall 3: Dual mypy Configuration
**What goes wrong:** Different behavior locally vs CI because two configs exist
**Why it happens:** `mypy.ini` (lenient, `disallow_untyped_defs = False`) takes precedence over `pyproject.toml` (strict, `strict = true`)
**How to avoid:** Consolidate into ONE config. Since CI uses `mypy . --ignore-missing-imports`, and `mypy.ini` is the primary config, keep `mypy.ini` and remove the `[tool.mypy]` section from `pyproject.toml` -- OR delete `mypy.ini` and let `pyproject.toml` be the single source. The lenient `mypy.ini` is the safer choice to avoid hundreds of new errors.
**Warning signs:** mypy passes locally but fails in CI (or vice versa)

### Pitfall 4: Node Version Mismatch
**What goes wrong:** Tests pass locally but fail in CI due to API differences
**Why it happens:** CI uses `NODE_VERSION: "20"` but `.nvmrc` says 22 and `package.json` requires `>=22`
**How to avoid:** Update ci.yml `NODE_VERSION` to `"22"` to match `.nvmrc`
**Warning signs:** ESM module errors, missing Node APIs

### Pitfall 5: `@eslint/eslintrc` + ajv Compatibility Crash
**What goes wrong:** ESLint crashes with `Cannot set properties of undefined (setting 'defaultMeta')`
**Why it happens:** Version mismatch between `@eslint/eslintrc` v3.x and `ajv` when using `FlatCompat`
**How to avoid:** Either pin compatible versions or migrate away from `FlatCompat` to native flat config
**Warning signs:** Running `npx eslint .` locally crashes with the above error

### Pitfall 6: GitHub Actions Billing/Quota
**What goes wrong:** All CI jobs fail with 0 steps and runner_id 0
**Why it happens:** GitHub Actions minutes exhausted or billing issue
**How to avoid:** Verify billing status before expecting CI to validate changes
**Warning signs:** All jobs complete in <3 seconds with no step data

## Code Examples

### Fix 1: Auto-fix Python Formatting (run locally)
```bash
# Source: CLAUDE.md project instructions
cd /Users/theceo/DevSkyy
isort .                    # Sort imports (already clean but ensures consistency)
ruff check --fix .         # Auto-fix 70 import sorting errors
black .                    # Auto-fix 13 files with formatting issues
```

### Fix 2: Fix mypy Duplicate Module Error
```ini
# In mypy.ini, add to exclude:
[mypy]
# ... existing config ...
exclude = (?x)(
    hf-spaces/.*
    | legacy/.*
    | \.venv/.*
    | build/.*
    | dist/.*
    | gemini/clients/.*
    | anthropic/clients/.*
  )
```

### Fix 3: Migrate Frontend ESLint
```bash
# In frontend directory:
cd frontend
npm install --save-dev eslint @eslint/eslintrc
```
Then update `package.json`:
```json
{
  "scripts": {
    "lint": "eslint ."
  }
}
```

### Fix 4: DAST Early Exit Guard
```yaml
- name: Run DAST scan
  id: dast_scan
  run: |
    if [ ! -f "staging/run_dast_scan.sh" ]; then
      echo "::notice::DAST scan infrastructure not yet provisioned. Skipping."
      exit 0
    fi
    chmod +x staging/run_dast_scan.sh
    ./staging/run_dast_scan.sh
```

### Fix 5: Robust Deployment Tag
```yaml
- name: Create deployment tag
  if: success()
  run: |
    TAG="deploy-$(date +%Y%m%d-%H%M%S)-${GITHUB_SHA::7}"
    git tag -a "$TAG" -m "Production deployment ${GITHUB_SHA::7}"
    git push origin "$TAG" || echo "::warning::Could not push tag $TAG"
```

### Fix 6: pip-licenses with Allowlist
```yaml
- name: Check Python licenses
  run: |
    pip-licenses --format=markdown --with-urls > licenses.md
    pip-licenses --fail-on="GPL-3.0-only;AGPL-3.0-only;GPL-3.0-or-later;AGPL-3.0-or-later" \
      --allow-only="MIT;BSD-2-Clause;BSD-3-Clause;Apache-2.0;ISC;PSF-2.0;Python-2.0;MPL-2.0;Unlicense;Public Domain"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `next lint` (built-in) | `eslint .` (direct CLI) | Next.js 16 (2025) | Must add ESLint as devDependency and update npm scripts |
| `.eslintrc.json` (legacy) | `eslint.config.mjs` (flat) | ESLint 9+ (2024) | Frontend already uses flat config via FlatCompat |
| ruff + isort separate | ruff handles isort (I rules) | ruff 0.1+ | ruff already checks `I001`; standalone isort may conflict |

**Note on ruff + isort overlap:** ruff's `I` rule set (currently enabled in pyproject.toml) handles import sorting. Running both `ruff check --fix` and `isort .` may produce different results. In CI, ruff runs first (hard failure) and isort runs second (soft failure). Since ruff's I rules match isort's "black" profile, running `ruff check --fix .` should make both pass. Verify this before removing isort's `continue-on-error`.

## Critical Discovery: CI Infrastructure Down

All GitHub Actions runs since at least 2026-03-08T01:47:55Z are failing at the infrastructure level:
- **runner_id: 0** (no runner assigned)
- **0 steps executed** (jobs never start)
- **2-second completion** (instant failure)

This is almost certainly a GitHub Actions billing/quota exhaustion issue. Implications:
1. Cannot validate CI changes by pushing to GitHub
2. All verification must be local (running tools directly)
3. The billing issue is SEPARATE from the `continue-on-error` problem
4. Once billing is restored, the existing workflow will show all the suppressed failures

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ (Python), Jest 30.x (JS/Node) |
| Config file | `pyproject.toml` [tool.pytest.ini_options], `config/testing/jest.config.cjs` |
| Quick run command | `pytest tests/ -x -q --tb=short` |
| Full suite command | `pytest tests/ -v --cov=. && npm run test:collections` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CI-01 | All 17 `continue-on-error` removed | grep/audit | `grep -c 'continue-on-error: true' .github/workflows/ci.yml .github/workflows/security-gate.yml .github/workflows/dast-scan.yml` | N/A -- shell command |
| CI-02a | black passes clean | format check | `black --check .` | N/A -- tool command |
| CI-02b | isort passes clean | format check | `isort --check-only .` | N/A -- tool command |
| CI-02c | ruff passes clean | lint check | `ruff check .` | N/A -- tool command |
| CI-02d | mypy passes clean | type check | `mypy . --ignore-missing-imports` | N/A -- tool command |
| CI-02e | ESLint passes clean | lint check | `cd frontend && npx eslint .` | N/A -- tool command |
| CI-02f | TypeScript passes clean | type check | `cd frontend && npx tsc --noEmit` | N/A -- tool command |
| CI-02g | Three.js tests pass | unit | `npm run test:collections` | Yes -- 8 test suites |

### Sampling Rate
- **Per task commit:** Run the specific tool being fixed (e.g., `black --check .` after formatting fixes)
- **Per wave merge:** Run all tool commands in sequence
- **Phase gate:** `grep -c 'continue-on-error: true' .github/workflows/*.yml` returns 0

### Wave 0 Gaps
- [ ] ESLint dependency in frontend `package.json` -- must be added before ESLint can run
- [ ] Node version in ci.yml -- must be updated from 20 to 22
- [ ] mypy config consolidation -- dual config (`mypy.ini` + `pyproject.toml`) causes ambiguity

## Open Questions

1. **GitHub Actions billing status**
   - What we know: All runs fail at infrastructure level with no runners assigned
   - What's unclear: Whether this is temporary (monthly quota reset) or requires admin action
   - Recommendation: Verify billing status via GitHub Settings; all Phase 1 work can proceed without CI runners (local validation sufficient)

2. **Security tool severity thresholds**
   - What we know: Removing `|| true` from security tools means ANY finding fails the pipeline
   - What's unclear: Whether the codebase currently has low/medium findings that would be flagged
   - Recommendation: Run each security tool locally before removing suppression; may need to configure severity thresholds (e.g., `bandit -lll` for HIGH-only)

3. **ruff vs isort overlap**
   - What we know: ruff has I001 rules enabled that replicate isort functionality
   - What's unclear: Whether `ruff check --fix` produces identical output to `isort .`
   - Recommendation: Run both, verify `isort --check-only` passes after `ruff check --fix .`; if yes, the isort CI step is redundant but harmless

4. **ESLint `@eslint/eslintrc` + ajv crash**
   - What we know: Running `npx eslint .` crashes with TypeError in ajv/eslintrc compatibility
   - What's unclear: Whether this is a local node_modules issue or a fundamental version incompatibility
   - Recommendation: In frontend, run `npm install` fresh and test ESLint; may need to update `@eslint/eslintrc` or rewrite config without `FlatCompat`

## Sources

### Primary (HIGH confidence)
- Local tool execution: `ruff check .` (70 errors, all auto-fixable)
- Local tool execution: `black --check .` (13 files need reformatting)
- Local tool execution: `isort --check-only .` (0 errors)
- Local tool execution: `mypy . --ignore-missing-imports` (1 error: duplicate module)
- Local tool execution: `tsc --noEmit` in frontend (0 errors)
- Local tool execution: `npm run test:collections` (408 tests pass)
- Local file inspection: all 3 workflow files read and analyzed
- GitHub API: `gh api repos/{owner}/{repo}/actions/runs/*/jobs` -- confirmed infrastructure-level failures

### Secondary (MEDIUM confidence)
- [Next.js 16 upgrade guide](https://nextjs.org/docs/app/guides/upgrading/version-16) -- confirms `next lint` removal
- [Next.js ESLint configuration](https://nextjs.org/docs/app/api-reference/config/eslint) -- updated ESLint docs
- [PR #83135 removing next lint](https://app.semanticdiff.com/gh/vercel/next.js/pull/83135/overview) -- implementation PR
- [Next.js 16 linting setup guide](https://chris.lu/web_development/tutorials/next-js-16-linting-setup-eslint-9-flat-config) -- migration tutorial

### Tertiary (LOW confidence)
- Security tool exit code behaviors -- based on training knowledge, should be verified with tool docs before relying on specific flags

## Metadata

**Confidence breakdown:**
- Directive inventory: HIGH -- direct file inspection of all 3 workflow files
- Formatting/lint fix scope: HIGH -- local tool execution with exact counts
- ESLint migration: HIGH -- verified Next.js 16 removal via official docs + local reproduction
- Security tool behavior: MEDIUM -- exit code semantics based on training data, not verified with current tool versions
- CI infrastructure issue: HIGH -- confirmed via GitHub API, all recent runs show same pattern

**Research date:** 2026-03-08
**Valid until:** 2026-04-08 (stable domain -- GitHub Actions yaml, Python tooling, ESLint CLI are mature)
