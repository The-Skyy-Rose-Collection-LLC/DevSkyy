# Phase 6: WordPress CI Integration - Research

**Researched:** 2026-03-09
**Domain:** GitHub Actions CI pipeline for PHP validation, WordPress theme build, and minification drift detection
**Confidence:** HIGH

## Summary

Phase 6 adds a new CI job to the existing `.github/workflows/ci.yml` that validates the WordPress theme before code can be merged. The scope is narrow and well-defined: (1) run `php -l` syntax checking on all 106 theme PHP files, (2) run `npm run build` to verify the build pipeline produces valid output, and (3) detect minification drift by comparing committed `.min` files against freshly built output using `git diff`.

The existing CI workflow (Phase 1) already has 4 parallel jobs: lint, python-tests, security, frontend-tests. Phase 4 configured branch protection requiring all 4 to pass. This phase adds a 5th job and must update the branch protection to require it. PHP 8.3.6 is pre-installed on ubuntu-latest (Ubuntu 24.04), so no `setup-php` action is needed -- `php -l` works out of the box. The theme's build pipeline (Phase 5) uses webpack for JS and clean-css for CSS, with `npm run build` as the single command. Minified files (41 `.min.js` + 53 `.min.css`) are tracked in git, while `.map` files are gitignored -- this is the correct setup for drift detection since git can diff the tracked minified files.

The drift detection pattern is: install npm deps, run `npm run build`, then `git diff --exit-code` on the minified files. If any `.min.js` or `.min.css` file differs from the committed version, `git diff --exit-code` returns exit code 1 (failure), meaning someone edited source without rebuilding. This is a well-established CI pattern that requires zero external tools.

**Primary recommendation:** Add a single new CI job `wordpress-theme` to `ci.yml` with 3 steps (PHP lint, build, drift check), then update `scripts/setup-branch-protection.sh` to require 5 checks instead of 4.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CI-03 | PHP syntax validation step added to CI pipeline for WordPress theme files | PHP 8.3.6 is pre-installed on ubuntu-latest. Use `find wordpress-theme/skyyrose-flagship -name "*.php" -not -path "*/node_modules/*" -not -path "*/vendor/*" -exec php -l {} +` or loop with the existing `scripts/php-lint.sh` pattern. 106 PHP files to validate. |
| CI-04 | CI runs WordPress theme build (npm run build) and validates output | Phase 5 created `npm run build` (webpack + clean-css) and `scripts/verify-build.sh` (7-check verification). CI installs deps with `npm ci`, runs `npm run build`, then runs `bash scripts/verify-build.sh` to validate output. |
| CI-05 | CI detects minification drift -- fails if .min files don't match freshly built output | 41 `.min.js` + 53 `.min.css` files are tracked in git. After `npm run build`, run `git diff --exit-code -- "*.min.js" "*.min.css"` in the theme directory. Non-zero exit = drift detected = CI failure. `.map` files are gitignored so they don't interfere. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| GitHub Actions | N/A | CI/CD platform | Already used by project, 4 existing jobs |
| PHP (pre-installed) | 8.3.6 | `php -l` syntax checking | Pre-installed on ubuntu-latest (Ubuntu 24.04), no setup action needed |
| Node.js | 22 | WordPress theme build | Already configured as `env.NODE_VERSION` in ci.yml |
| webpack | 5.105.4 | JS minification | Already installed in theme (Phase 5) |
| clean-css | 5.6.3 | CSS minification | Already installed in theme (Phase 5) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| actions/checkout | v4 | Clone repository | Every CI job |
| actions/setup-node | v6.2.0 | Install Node.js + npm cache | Required for `npm ci` and `npm run build` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pre-installed PHP | shivammathur/setup-php action | Unnecessary -- `php -l` only needs the syntax checker, pre-installed 8.3.6 is sufficient |
| `git diff --exit-code` for drift | Custom checksum comparison script | Overengineered -- git diff is the standard pattern and already available |
| Single job with 3 steps | Separate jobs per requirement | Slower (3 separate runners), more expensive, no benefit since checks are sequential within the theme |

**Installation:**
```bash
# No new packages needed -- everything is already installed or pre-installed on runners
```

## Architecture Patterns

### CI Job Structure
```yaml
# New job added to .github/workflows/ci.yml
wordpress-theme:
  name: "WordPress Theme"  # Display name for required status check
  runs-on: ubuntu-latest
  timeout-minutes: 10
  defaults:
    run:
      working-directory: wordpress-theme/skyyrose-flagship
  steps:
    # 1. Checkout
    # 2. Setup Node.js (for build)
    # 3. PHP syntax check (CI-03)
    # 4. npm ci (install deps)
    # 5. npm run build (CI-04)
    # 6. verify-build.sh (CI-04 validation)
    # 7. git diff --exit-code (CI-05 drift detection)
```

### Pattern 1: PHP Syntax Validation in CI
**What:** Run `php -l` on all PHP files in the WordPress theme to catch syntax errors
**When to use:** Every CI run -- PHP syntax errors are fatal to the live site
**Example:**
```yaml
- name: PHP syntax check
  # Run from repo root since file paths are relative to repo
  working-directory: .
  run: |
    error_count=0
    while IFS= read -r file; do
      if ! php -l "$file" 2>&1 | grep -q "No syntax errors"; then
        echo "::error file=$file::PHP syntax error"
        error_count=$((error_count + 1))
      fi
    done < <(find wordpress-theme/skyyrose-flagship \
      -name "*.php" \
      -not -path "*/node_modules/*" \
      -not -path "*/vendor/*")
    if [ "$error_count" -gt 0 ]; then
      echo "PHP syntax errors found in $error_count file(s)"
      exit 1
    fi
    echo "All PHP files passed syntax check"
```

### Pattern 2: Minification Drift Detection
**What:** After building, check if any tracked minified files differ from what's committed
**When to use:** After `npm run build` completes -- catches stale .min files
**Example:**
```yaml
- name: Check for minification drift
  run: |
    if ! git diff --exit-code -- '*.min.js' '*.min.css'; then
      echo ""
      echo "::error::Minification drift detected!"
      echo "The committed .min files do not match the build output."
      echo "Run 'cd wordpress-theme/skyyrose-flagship && npm run build' and commit the result."
      exit 1
    fi
    echo "No minification drift detected"
```

### Pattern 3: Branch Protection Update
**What:** Add the new CI job to required status checks so it blocks merges
**When to use:** After the CI job is confirmed working
**Example:**
```json
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      {"context": "🔍 Lint & Static Analysis", "app_id": -1},
      {"context": "🐍 Python Tests", "app_id": -1},
      {"context": "🔐 Security Scan", "app_id": -1},
      {"context": "⚛️ Frontend Tests", "app_id": -1},
      {"context": "🏗️ WordPress Theme", "app_id": -1}
    ]
  }
}
```

### Anti-Patterns to Avoid
- **Using `setup-php` action when only `php -l` is needed:** Adds 30-60 seconds for no benefit -- PHP is pre-installed
- **Running PHP lint on `node_modules/` or `vendor/` directories:** The theme has 3863 PHP files total but only 106 are theme files -- the rest are in node_modules
- **Using `continue-on-error: true` on any step:** Phase 1 removed all 17 instances -- do not reintroduce
- **Putting the drift check before the build:** Must run `npm run build` first, then check git diff
- **Using `git diff` on `.map` files:** Source maps are gitignored and not tracked -- they would not appear in git diff anyway, but explicitly excluding them avoids confusion
- **Creating a separate workflow file:** All CI should be in one workflow for branch protection simplicity

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PHP syntax checking | Custom PHP parser | `php -l` (pre-installed) | Built-in, authoritative, zero-dependency |
| Drift detection | File hash comparison script | `git diff --exit-code` | Already tracks the files, zero-dependency, shows exact diff |
| Build verification | Custom file counting script | `scripts/verify-build.sh` (Phase 5) | Already exists with 7 checks, battle-tested |
| CI job definition | Reusable workflow or composite action | Inline job in ci.yml | Single-use, simple, consistent with existing 4 jobs |

**Key insight:** Every tool needed already exists -- PHP is pre-installed, git diff is built-in, the build pipeline was created in Phase 5, and the verification script is already written. This phase is purely wiring.

## Common Pitfalls

### Pitfall 1: Wrong Working Directory for PHP Lint
**What goes wrong:** `php -l` runs but doesn't find any PHP files, or finds thousands in node_modules
**Why it happens:** The job defaults `working-directory` to the theme dir, but `find` with node_modules exclusion needs the right starting path
**How to avoid:** Run the PHP lint step with `working-directory: .` (repo root) and use the full path `wordpress-theme/skyyrose-flagship`, OR run from theme dir with `-not -path "*/node_modules/*"` exclusion
**Warning signs:** Step passes instantly (found 0 files) or takes 5+ minutes (scanning node_modules)

### Pitfall 2: git diff Scope Too Broad
**What goes wrong:** `git diff --exit-code` shows changes in files unrelated to the build (e.g., other staged changes)
**Why it happens:** `git diff` without path restrictions checks the entire repo
**How to avoid:** Scope the diff to the theme directory: `git diff --exit-code -- wordpress-theme/skyyrose-flagship/'*.min.js' wordpress-theme/skyyrose-flagship/'*.min.css'`
**Warning signs:** CI fails on drift but the diff shows files outside the theme

### Pitfall 3: npm ci Fails Without package-lock.json
**What goes wrong:** `npm ci` requires `package-lock.json` but the theme's `.gitignore` excludes it
**Why it happens:** Phase 5 noted that `package-lock.json` is gitignored per existing `.gitignore`
**How to avoid:** Use `npm install` instead of `npm ci` for the theme, OR un-ignore `package-lock.json` in CI. The safer approach is `npm install` since it generates the lock file from `package.json`
**Warning signs:** `npm ci` step fails with "package-lock.json not found"

### Pitfall 4: Branch Protection Check Count Mismatch
**What goes wrong:** Branch protection script expects 4 checks but now there are 5 -- verification fails
**Why it happens:** The `verify()` function in `setup-branch-protection.sh` hardcodes `check_count = "4"`
**How to avoid:** Update both the payload (add 5th check) AND the verification (expect 5 checks)
**Warning signs:** `setup-branch-protection.sh --verify` fails after adding the new CI job

### Pitfall 5: CI Job Name Must Match Branch Protection Context Exactly
**What goes wrong:** Branch protection requires a check that never reports, so PRs can never merge
**Why it happens:** The `name:` field in the CI job YAML must exactly match the `context` string in branch protection
**How to avoid:** Use a simple ASCII name for the CI job (no emoji, or verify the exact emoji encoding works). The existing jobs use emoji in names -- follow the same pattern but verify the exact string
**Warning signs:** PR checks page shows "Expected -- Waiting for status to be reported" for the new check

### Pitfall 6: Clean Checkout Required for Drift Detection
**What goes wrong:** git diff shows changes that were already in the working tree before the build
**Why it happens:** actions/checkout might leave modified files in the working tree
**How to avoid:** `actions/checkout@v4` produces a clean checkout by default. No special handling needed unless the workflow modifies files before the build step
**Warning signs:** Drift detected on the very first CI run even though nothing changed

## Code Examples

### Complete CI Job Definition
```yaml
# Add to .github/workflows/ci.yml after the existing frontend-tests job
wordpress-theme:
  name: "🏗️ WordPress Theme"
  runs-on: ubuntu-latest
  timeout-minutes: 10

  steps:
    - name: Checkout code
      uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4

    - name: Set up Node.js
      uses: actions/setup-node@6044e13b5dc448c55e2357c09f80417699197238  # v6.2.0
      with:
        node-version: ${{ env.NODE_VERSION }}

    - name: PHP syntax check (CI-03)
      run: |
        error_count=0
        while IFS= read -r file; do
          if ! php -l "$file" 2>&1 | grep -q "No syntax errors"; then
            echo "::error file=$file::PHP syntax error"
            error_count=$((error_count + 1))
          fi
        done < <(find wordpress-theme/skyyrose-flagship \
          -name "*.php" \
          -not -path "*/node_modules/*" \
          -not -path "*/vendor/*")
        if [ "$error_count" -gt 0 ]; then
          echo "$error_count PHP file(s) have syntax errors"
          exit 1
        fi
        echo "All PHP files passed syntax check"

    - name: Install theme dependencies
      working-directory: wordpress-theme/skyyrose-flagship
      run: npm install

    - name: Build theme assets (CI-04)
      working-directory: wordpress-theme/skyyrose-flagship
      run: npm run build

    - name: Verify build output (CI-04)
      working-directory: wordpress-theme/skyyrose-flagship
      run: bash scripts/verify-build.sh

    - name: Check for minification drift (CI-05)
      run: |
        if ! git diff --exit-code -- 'wordpress-theme/skyyrose-flagship/**/*.min.js' 'wordpress-theme/skyyrose-flagship/**/*.min.css'; then
          echo ""
          echo "::error::Minification drift detected! Committed .min files do not match build output."
          echo "Fix: cd wordpress-theme/skyyrose-flagship && npm run build && git add -A && git commit"
          exit 1
        fi
        echo "No minification drift -- committed .min files match build output"
```

### Updated Branch Protection Payload
```json
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      {"context": "🔍 Lint & Static Analysis", "app_id": -1},
      {"context": "🐍 Python Tests", "app_id": -1},
      {"context": "🔐 Security Scan", "app_id": -1},
      {"context": "⚛️ Frontend Tests", "app_id": -1},
      {"context": "🏗️ WordPress Theme", "app_id": -1}
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```

### Summary Job Update
```yaml
# Update the summary job's needs array to include the new job
summary:
  name: "📊 Pipeline Summary"
  runs-on: ubuntu-latest
  needs: [lint, python-tests, security, frontend-tests, threejs-tests, wordpress-theme]
  if: always()
  steps:
    - name: Generate summary
      run: |
        echo "## 📊 CI/CD Pipeline Summary" >> $GITHUB_STEP_SUMMARY
        # ... existing lines ...
        echo "| 🏗️ WordPress Theme | ${{ needs.wordpress-theme.result }} |" >> $GITHUB_STEP_SUMMARY
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No PHP validation in CI | `php -l` on all theme files | Standard since PHP 4+ | Catches fatal syntax errors before deploy |
| Manual build verification | `npm run build` + `verify-build.sh` | Phase 5 (2026-03-09) | Automated, 7-check verification |
| Trust committed .min files | Drift detection via `git diff --exit-code` | Common CI pattern | Prevents stale minified files |

**Deprecated/outdated:**
- `setup-php` action for simple `php -l`: Unnecessary when PHP is pre-installed
- Separate CI workflow for WordPress: Adds branch protection complexity -- single workflow is better
- File hash comparison scripts for drift: `git diff` is simpler and more informative

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | GitHub Actions CI + shell scripts |
| Config file | `.github/workflows/ci.yml` |
| Quick run command | `php -l wordpress-theme/skyyrose-flagship/functions.php` |
| Full suite command | Push to branch and verify CI passes on GitHub |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CI-03 | PHP syntax error causes CI failure | integration | `find wordpress-theme/skyyrose-flagship -name "*.php" -not -path "*/node_modules/*" -not -path "*/vendor/*" -exec php -l {} +` | N/A (CI step) |
| CI-04 | Build step passes in CI | integration | `cd wordpress-theme/skyyrose-flagship && npm install && npm run build && bash scripts/verify-build.sh` | verify-build.sh exists |
| CI-05 | Stale .min files cause CI failure | integration | `cd wordpress-theme/skyyrose-flagship && npm install && npm run build && git diff --exit-code -- '*.min.js' '*.min.css'` | N/A (CI step) |

### Sampling Rate
- **Per task commit:** Run `php -l` locally on theme PHP files + `npm run build` in theme dir
- **Per wave merge:** Push to branch, verify CI job passes on GitHub
- **Phase gate:** All 3 CI-0x requirements pass in CI + branch protection updated to require 5 checks

### Wave 0 Gaps
None -- existing infrastructure covers all phase requirements:
- PHP is pre-installed on runners (CI-03)
- `npm run build` and `scripts/verify-build.sh` exist from Phase 5 (CI-04)
- `.min.js` and `.min.css` files are tracked in git for drift detection (CI-05)
- `scripts/setup-branch-protection.sh` exists from Phase 4 (needs update only)

## Open Questions

1. **npm ci vs npm install for theme in CI**
   - What we know: The theme's `package-lock.json` is gitignored (per `.gitignore`). `npm ci` requires a lock file. `npm install` generates one from `package.json`.
   - What's unclear: Whether to un-ignore `package-lock.json` or use `npm install`.
   - Recommendation: Use `npm install` in CI. It is safe because `package.json` has pinned major versions (`^` semver). Un-ignoring package-lock.json would require committing it first (separate concern). The build output is deterministic enough for drift detection since the same minification logic runs regardless of minor dependency differences.

2. **Emoji in CI job name for branch protection**
   - What we know: Existing 4 jobs all use emoji in their `name:` field and Phase 4 verified these work with branch protection. The temp-file approach for the JSON payload handles emoji encoding.
   - What's unclear: Nothing -- this is solved.
   - Recommendation: Use emoji (consistent with existing jobs). Follow the same temp-file pattern from Phase 4.

3. **git diff glob pattern for minified files**
   - What we know: `git diff --exit-code -- '*.min.js'` matches files in any directory. The minified files are in `wordpress-theme/skyyrose-flagship/assets/js/` and `wordpress-theme/skyyrose-flagship/assets/css/`.
   - What's unclear: Whether a broad glob could match unrelated `.min.js` files elsewhere in the repo.
   - Recommendation: Scope to the theme directory: `git diff --exit-code -- 'wordpress-theme/skyyrose-flagship/**/*.min.js' 'wordpress-theme/skyyrose-flagship/**/*.min.css'`. This is precise and avoids false positives.

## Sources

### Primary (HIGH confidence)
- **Local CI workflow** -- `.github/workflows/ci.yml` (direct examination, 704 lines)
- **Branch protection script** -- `scripts/setup-branch-protection.sh` (Phase 4 output, direct examination)
- **Theme package.json** -- `wordpress-theme/skyyrose-flagship/package.json` (Phase 5 output, direct examination)
- **Build verification** -- `wordpress-theme/skyyrose-flagship/scripts/verify-build.sh` (Phase 5 output, 7 checks)
- **Theme .gitignore** -- confirms `.min.js` and `.min.css` are tracked (un-ignored via `!` rules), `.map` files are ignored
- **Git ls-files** -- verified 41 `.min.js` + 53 `.min.css` files are tracked; 0 `.map` files tracked
- **PHP file count** -- 106 theme PHP files (excluding node_modules/vendor), verified via `find`

### Secondary (MEDIUM confidence)
- **GitHub Actions runner-images** -- PHP 8.3.6 pre-installed on Ubuntu 24.04 (ubuntu-latest), verified via [runner-images README](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md)
- **`git diff --exit-code` pattern** -- standard CI pattern for detecting uncommitted changes after build, documented in git man pages

### Tertiary (LOW confidence)
- None -- all findings verified against local codebase or official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all tools pre-installed or already configured in prior phases
- Architecture: HIGH - straightforward addition to existing CI workflow, pattern matches existing jobs
- Pitfalls: HIGH - identified through direct examination of existing config and prior phase decisions

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (stable tooling, no version-sensitive findings)
