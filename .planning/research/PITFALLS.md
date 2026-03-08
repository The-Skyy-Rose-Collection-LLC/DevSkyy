# Pitfalls Research: Production Armor & WordPress Build Autonomy

**Research Date:** 2026-03-08
**Dimension:** Pitfalls
**Confidence:** HIGH

## Critical Pitfalls

### 1. Husky v4 vs v9 Config Mismatch

**The Problem:** The WordPress theme `package.json` has Husky v8 in devDependencies but uses the v4 configuration format (`husky.hooks` object). This format was deprecated in v5+. Running `husky install` won't read the old config — hooks will silently not work.

**Warning Signs:**
- `package.json` has `"husky": { "hooks": { ... } }` block
- No `.husky/` directory exists
- `npx husky` commands succeed but hooks don't fire

**Prevention:**
- Delete the `husky.hooks` block from package.json entirely
- Use Husky v9 with `.husky/pre-commit` shell scripts
- Put Husky at the **root** package.json (monorepo root), not in the WordPress theme
- Verify hooks work: `git commit --allow-empty -m "test"` should trigger hook

**Phase:** Local git hooks setup

### 2. lint-staged Running in Wrong Directory

**The Problem:** In a monorepo, lint-staged commands may run from root but file paths reference subdirectories. A command like `eslint` may not find its config if run from root when the eslint config lives in `wordpress-theme/`.

**Warning Signs:**
- lint-staged passes locally but files aren't actually linted
- "No ESLint configuration found" errors
- Commands succeed but produce no output

**Prevention:**
- Use lint-staged's `cwd` option or per-directory configs
- Test with a deliberately broken file to confirm hooks catch it
- Use absolute paths or `--config` flags in lint-staged commands

**Phase:** Local git hooks setup

### 3. `continue-on-error` Removal Breaking CI

**The Problem:** The 17 `continue-on-error: true` directives exist because those checks currently FAIL. Removing them will cause CI to fail on every PR until the underlying issues are fixed.

**Warning Signs:**
- CI turns red immediately after removing `continue-on-error`
- PRs pile up because nothing can merge
- Pressure to add `continue-on-error` back

**Prevention:**
- **Fix the failures first**, then remove `continue-on-error`
- Or: Remove `continue-on-error` but add `|| true` temporarily with a tracking issue
- Prioritize: which checks actually matter? Black formatting vs mypy type errors have different severity
- Consider a phased approach: remove for critical checks first (ruff, tsc), then formatting, then type-checking

**Phase:** CI hardening

### 4. Minification Drift (Stale .min Files)

**The Problem:** The theme has `.min.css` and `.min.js` files committed to git. If the build pipeline doesn't cover all files, developers/agents may edit source files but not rebuild — the `.min` files become stale and the live site serves old code.

**Warning Signs:**
- Source file changes don't appear on live site
- `.min` file timestamps older than source file timestamps
- `git diff` shows only source changes, not `.min` changes

**Prevention:**
- CI step: `npm run build && git diff --exit-code` — fails if build produces different output than committed
- Or: Don't commit `.min` files — build them in CI/deploy only
- Or: Git hook that auto-builds on commit (but may be slow)

**Phase:** WordPress build pipeline

### 5. SSH Key Management for Deploys

**The Problem:** Automated deploys need SSH access to the WordPress server. Storing SSH keys in GitHub Secrets is standard, but mishandling can expose the key or lock out manual access.

**Warning Signs:**
- Deploy works locally but fails in CI (different SSH key)
- "Host key verification failed" errors
- Key rotation breaks automated deploys

**Prevention:**
- Generate a **dedicated deploy key** (not a personal SSH key)
- Store in GitHub Secrets (not committed to repo)
- Add the server's host key to `known_hosts` in the workflow
- Use `ssh-agent` in GitHub Actions for key handling
- Test the SSH connection step before adding rsync/WP-CLI commands

**Phase:** Deploy automation

### 6. WP-CLI Maintenance Mode Stuck On

**The Problem:** If a deploy fails mid-way after enabling maintenance mode, the live site stays in maintenance mode. No customers can access it.

**Warning Signs:**
- Deploy script errors out after `wp maintenance-mode activate`
- Site shows "Briefly unavailable for scheduled maintenance"
- No one notices until customers complain

**Prevention:**
- Always wrap deploy in try/finally that disables maintenance mode
- Set a timeout: if deploy hasn't completed in N minutes, disable maintenance mode
- Health check step must verify maintenance mode is OFF
- Consider skipping maintenance mode for small updates (CSS/JS only)

**Phase:** Deploy automation

### 7. Monorepo Hook Performance

**The Problem:** Running all checks (Python lint + JS lint + PHP lint + type-check + tests) on every commit will blow past the 30-second budget, even with lint-staged.

**Warning Signs:**
- Hooks take >30 seconds
- Agents use `--no-verify` to bypass slow hooks
- Developer frustration with commit speed

**Prevention:**
- lint-staged only checks staged files in the language that changed
- Use `--changedSince` for test runners
- Type checking is the slowest — consider making it pre-push instead of pre-commit
- Profile hook execution time and optimize the slowest step

**Phase:** Local git hooks setup

### 8. Branch Protection Locking Out Agents

**The Problem:** If branch protection requires PR reviews or specific CI checks that agents can't satisfy, the autonomous workflow breaks. Agents need to be able to merge when CI passes.

**Warning Signs:**
- Agents create PRs but can't merge them
- "Required review" blocks merge
- CI check names don't match required status checks

**Prevention:**
- Do NOT require human reviews (explicitly out of scope)
- Map exact CI job names to required status checks
- Test with a real PR before enabling enforcement
- Use `gh api` to configure programmatically (can be version-controlled)

**Phase:** PR protection setup

## Risk Matrix

| Pitfall | Likelihood | Impact | Phase |
|---------|-----------|--------|-------|
| Husky version mismatch | HIGH (confirmed) | MEDIUM | Hooks |
| lint-staged wrong directory | MEDIUM | LOW | Hooks |
| continue-on-error removal breaks CI | HIGH (confirmed) | HIGH | CI |
| Minification drift | HIGH (confirmed) | MEDIUM | Build |
| SSH key management | MEDIUM | HIGH | Deploy |
| Maintenance mode stuck | LOW | CRITICAL | Deploy |
| Hook performance | MEDIUM | MEDIUM | Hooks |
| Branch protection locks agents | MEDIUM | HIGH | PR |

---
*Research completed: 2026-03-08*
