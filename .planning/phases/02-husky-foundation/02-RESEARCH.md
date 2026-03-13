# Phase 2: Husky Foundation - Research

**Researched:** 2026-03-08
**Domain:** Git hooks infrastructure (Husky v9), npm lifecycle scripts, monorepo hook management
**Confidence:** HIGH

## Summary

Husky v9.1.7 is already declared as a devDependency in root `package.json` and is installed in `node_modules`. The project has never been initialized with Husky -- no `.husky/` directory exists. Worse, `core.hooksPath` is currently set to `--version/_` (corrupted -- likely from someone running `npx husky --version` which Husky v9 interprets as "set hooks directory to `--version/`"). This means **no git hooks are currently functional** -- not even the Git LFS hooks in `.git/hooks/`.

The WordPress theme `package.json` has a broken Husky v4 configuration: a `husky.hooks` JSON block (which v9 ignores entirely), `husky: ^8.0.3` in devDependencies, and a `"prepare": "husky install"` script (deprecated v8 syntax). All three must be removed.

**Primary recommendation:** Run `npx husky init` at monorepo root, then fix the `prepare` script to chain `husky && npm run build`. Replace the generated pre-commit content with a proof-of-life echo. Remove all Husky artifacts from WordPress theme `package.json`. Create `scripts/verify-hooks.sh` for permanent verification. Add Git LFS commands to `.husky/post-checkout`, `.husky/post-commit`, `.husky/post-merge`, and `.husky/pre-push` so LFS continues working through the `core.hooksPath` redirect.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Pre-commit hook contains a bare proof-of-life echo ("pre-commit hook active") -- no lint/test logic
- Phase 3 owns the actual hook content (lint-staged, ESLint, ruff, etc.)
- Pre-commit only -- no pre-push hook in this phase
- Root `package.json` prepare script chains both: `"prepare": "husky && npm run build"`
- Full removal of Husky from WordPress theme package.json:
  - Delete the `husky.hooks` block (lines 136-141) -- broken v4 syntax
  - Remove `husky` from devDependencies (v8.0.3)
  - Remove `"prepare": "husky install"` script entirely (not replace with no-op)
- Run `npm install` in theme directory to regenerate package-lock.json without husky
- Theme's ESLint (v8) left alone -- out of scope for this phase
- Permanent verification script at `scripts/verify-hooks.sh`
- Script checks 3 things: `.husky/pre-commit` exists, is executable, and `git commit` triggers the hook (captures output)

### Claude's Discretion
- Exact echo message in pre-commit hook
- Whether to initialize Husky with `npx husky init` or manual setup
- Verification script implementation details (temp file strategy, cleanup)
- Whether existing .git/hooks/ files (post-checkout, post-commit, post-merge) need attention

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| HOOK-07 | Husky v9 replaces broken v4 config in WordPress theme package.json | Research confirms: theme has v4 `husky.hooks` block, v8 devDependency, deprecated v8 `prepare` script -- all must be removed. Root already has husky v9.1.7 installed but not initialized. Corrupted `core.hooksPath` must be fixed. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| husky | 9.1.7 | Git hooks manager | Already in root devDependencies. Uses `core.hooksPath` to redirect Git to `.husky/_/` directory. Industry standard for npm-based repos. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| git-lfs | 3.7.1 | Large file storage | Already installed system-wide. Hooks must be preserved via `.husky/` files since `core.hooksPath` bypasses `.git/hooks/`. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| husky | pre-commit (Python) | Wrong ecosystem per REQUIREMENTS.md Out of Scope -- npm-native is correct for this monorepo |
| husky | lefthook | Faster for large repos, but husky is already installed and is the standard choice |
| `npx husky init` | Manual `.husky/` creation | Both work; `init` is recommended by official docs and handles `core.hooksPath` setup automatically |

**Installation:**
```bash
# Already installed -- husky@9.1.7 in devDependencies
# Only needs initialization:
npx husky init
```

## Architecture Patterns

### How Husky v9 Works Internally

1. Running `husky` (the command) calls `git config core.hooksPath .husky/_`
2. This tells Git to look in `.husky/_/` for hook scripts instead of `.git/hooks/`
3. Husky generates stub scripts in `.husky/_/` for all 14 Git hook types
4. Each stub sources `~/.config/husky/init.sh` (if present), checks `HUSKY=0`, then executes the matching file in `.husky/` (parent directory)
5. User-authored hooks live in `.husky/pre-commit`, `.husky/commit-msg`, etc.
6. The `.husky/_/` directory is `.gitignore`d (auto-generated on each install)

### Recommended Project Structure
```
.husky/
  pre-commit           # User hook: echo "pre-commit hook active"
  post-checkout         # Git LFS: git lfs post-checkout "$@"
  post-commit           # Git LFS: git lfs post-commit "$@"
  post-merge            # Git LFS: git lfs post-merge "$@"
  pre-push              # Git LFS: git lfs pre-push "$@"
  _/                    # Auto-generated by husky (gitignored)
    .gitignore          # Contains "*"
    h                   # Husky's hook dispatcher script
    husky.sh            # Deprecation notice for v10
    pre-commit          # Generated stub that calls .husky/pre-commit
    post-checkout       # Generated stub
    ...                 # (all 14 hook types)
scripts/
  verify-hooks.sh       # Permanent verification script
```

### Pattern 1: Proof-of-Life Pre-Commit Hook
**What:** Minimal hook that proves the hook system works without blocking commits on lint/test failures
**When to use:** Phase 2 (foundation) -- real checks added in Phase 3
**Example:**
```bash
# .husky/pre-commit
echo "pre-commit hook active"
```

### Pattern 2: Git LFS Hooks via Husky
**What:** Since `core.hooksPath` redirects Git away from `.git/hooks/`, Git LFS hooks must be recreated in `.husky/`
**When to use:** Any repo that uses Git LFS alongside Husky
**Example:**
```bash
# .husky/post-checkout
command -v git-lfs >/dev/null 2>&1 || exit 0
git lfs post-checkout "$@"
```
Note: Using `exit 0` (not `exit 2`) because this project doesn't actively track files with LFS (assets are on HuggingFace Hub). The hooks are a safety net, not a hard requirement.

### Pattern 3: Chained Prepare Script
**What:** The `prepare` lifecycle script runs after every `npm install`. Chain `husky` with the existing build.
**When to use:** When the project already has a prepare script
**Example:**
```json
{
  "scripts": {
    "prepare": "husky && npm run build"
  }
}
```
The `&&` ensures the build only runs if husky succeeds. If `HUSKY=0` is set (CI), husky exits 0 silently and build still runs.

### Anti-Patterns to Avoid
- **`"prepare": "husky install"`** -- This is v8 syntax. In v9, the command is just `husky` (no `install` subcommand). `husky install` prints a deprecation warning.
- **`husky.hooks` in package.json** -- This is v4 syntax. Completely ignored by v9. Must be deleted.
- **Running `npx husky --version`** -- This is the likely cause of the corrupted `core.hooksPath=--version/_`. Husky v9 interprets the first argument as the hooks directory if it isn't a recognized command.
- **Putting hook logic in `.husky/_/`** -- The `_/` subdirectory is auto-generated and gitignored. All user hooks go in `.husky/` (parent).
- **Skipping `npm install` after removing theme husky** -- The theme's `package-lock.json` will still reference husky unless regenerated.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Git hook management | Custom `.git/hooks/` scripts | Husky v9 | `core.hooksPath` ensures hooks survive across clones and are version-controlled |
| Hook bootstrapping for collaborators | README instructions | `prepare` script | Automatic -- runs on `npm install`, zero manual steps |
| Corrupted hooksPath cleanup | Manual git config editing | `npx husky init` or `npx husky` | The husky command sets `core.hooksPath` to the correct value automatically |

**Key insight:** Husky v9 is extremely lightweight (2KB, ~1ms). It's just a thin wrapper around `git config core.hooksPath`. The real value is the `prepare` script auto-setup for collaborators.

## Common Pitfalls

### Pitfall 1: Corrupted core.hooksPath (ACTIVE IN THIS REPO)
**What goes wrong:** `core.hooksPath` is set to `--version/_` -- a nonsense path. No hooks fire at all.
**Why it happens:** Running `npx husky --version` in v9 -- Husky's CLI interprets unknown first arguments as the hooks directory path.
**How to avoid:** Never pass flags to `husky` CLI. To check version: `npm ls husky` or check `node_modules/husky/package.json`.
**Warning signs:** `git config core.hooksPath` returns anything other than `.husky/_` (or is unset).

### Pitfall 2: Git LFS Hooks Lost
**What goes wrong:** After Husky sets `core.hooksPath`, Git stops reading `.git/hooks/`. LFS operations silently stop working.
**Why it happens:** `core.hooksPath` overrides `.git/hooks/` entirely -- Git does not merge hook directories.
**How to avoid:** Create corresponding LFS hook files in `.husky/` that call `git lfs <hook-name> "$@"`.
**Warning signs:** `git push` stops uploading LFS objects; `git checkout` stops downloading them.
**Note for this repo:** `.gitattributes` says "No LFS tracking" and assets are on HuggingFace Hub, so this is low-risk. However, LFS hooks should still be preserved as a safety net since `git lfs install` was run at some point.

### Pitfall 3: Theme npm install After Cleanup
**What goes wrong:** Removing husky from theme `package.json` without running `npm install` leaves stale `package-lock.json` with husky references.
**Why it happens:** `package-lock.json` is a lockfile -- it only updates when you run npm install.
**How to avoid:** Always run `npm install` in the theme directory after modifying its `package.json`.
**Warning signs:** `npm ci` fails in CI because lockfile doesn't match `package.json`.

### Pitfall 4: prepare Script in CI
**What goes wrong:** The `prepare` script runs during CI `npm install`, attempting to set up Husky in a CI environment where it's not needed.
**Why it happens:** npm's `prepare` lifecycle runs for all `npm install` invocations.
**How to avoid:** Husky v9 handles this gracefully -- when `HUSKY=0` is set, it exits silently. The `husky || true` pattern in prepare script also works but is unnecessary with v9.
**Warning signs:** CI logs show husky errors during install. Not a problem if CI already sets `HUSKY=0` or `--ignore-scripts`.

### Pitfall 5: Hook File Permissions
**What goes wrong:** Hook files created without execute permission don't fire.
**Why it happens:** Text editors and file creation commands don't always set `+x`.
**How to avoid:** `npx husky init` creates files with correct permissions. If creating manually: `chmod +x .husky/pre-commit`.
**Warning signs:** `git commit` works without any hook output.

## Code Examples

Verified patterns from official sources and source code analysis:

### Initializing Husky v9 (npx husky init)
```bash
# Source: https://typicode.github.io/husky/get-started.html
# This command:
# 1. Creates .husky/ directory
# 2. Creates .husky/pre-commit with default content (npm test)
# 3. Sets core.hooksPath to .husky/_
# 4. Updates package.json "prepare" script to "husky"
npx husky init
```

### Manual Husky Setup (alternative to init)
```bash
# If init modifies prepare script in unwanted ways, do it manually:
# 1. Create the hooks directory
mkdir -p .husky

# 2. Create the pre-commit hook
echo 'echo "pre-commit hook active"' > .husky/pre-commit
chmod +x .husky/pre-commit

# 3. Run husky to set core.hooksPath and generate .husky/_/
npx husky

# 4. Manually update prepare script in package.json
# "prepare": "husky && npm run build"
```

### WordPress Theme Cleanup (exact removals)
```json
// REMOVE from wordpress-theme/skyyrose-flagship/package.json:

// 1. Delete this entire block (lines 136-141):
"husky": {
  "hooks": {
    "pre-commit": "npm run lint:js && npm run test:js",
    "pre-push": "npm run test:all"
  }
}

// 2. Delete from devDependencies:
"husky": "^8.0.3"

// 3. Delete from scripts:
"prepare": "husky install"
```

### Git LFS Hook Template
```bash
# .husky/post-checkout (and similar for post-commit, post-merge, pre-push)
command -v git-lfs >/dev/null 2>&1 || exit 0
git lfs post-checkout "$@"
```

### Verification Script Pattern
```bash
#!/usr/bin/env bash
# scripts/verify-hooks.sh -- Verify Husky git hooks are functional
set -euo pipefail

PASS=0
FAIL=0

check() {
  if "$@" >/dev/null 2>&1; then
    echo "PASS: $1"
    ((PASS++))
  else
    echo "FAIL: $1"
    ((FAIL++))
  fi
}

# 1. .husky/pre-commit exists
test -f .husky/pre-commit
# 2. .husky/pre-commit is executable
test -x .husky/pre-commit
# 3. core.hooksPath points to .husky/_
test "$(git config core.hooksPath)" = ".husky/_"
# 4. Hook fires on git commit (use --allow-empty with temp branch)
# Implementation details at Claude's discretion
```

### Fixing Corrupted core.hooksPath
```bash
# Current state (broken):
git config core.hooksPath  # outputs: --version/_

# Fix by running husky (sets it to .husky/_):
npx husky
git config core.hooksPath  # outputs: .husky/_

# Alternative manual fix:
git config core.hooksPath .husky/_
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `husky.hooks` in package.json (v4) | `.husky/pre-commit` files (v9) | v5 (2021) | JSON config completely ignored in v5+ |
| `husky install` command (v8) | `husky` command (v9) | v9.0.0 (2024) | `install` subcommand deprecated, prints warning |
| `husky add .husky/pre-commit "cmd"` (v8) | Manual file creation (v9) | v9.0.0 (2024) | `add` command removed entirely |
| `.husky/_/husky.sh` sourced in hooks (v8) | Auto-generated stubs in `.husky/_/` (v9) | v9.0.0 (2024) | No more `. "$(dirname "$0")/_/husky.sh"` boilerplate in hook files |
| `HUSKY_SKIP_HOOKS=1` (v4) | `HUSKY=0` (v9) | v5 (2021) | Env var renamed |

**Deprecated/outdated:**
- `husky install`: Deprecated in v9, replaced by just `husky`
- `husky add`: Removed in v9 -- create files manually
- `husky.hooks` in package.json: v4 syntax, completely ignored by v5+
- `#!/usr/bin/env sh` + `. "$(dirname "$0")/_/husky.sh"` boilerplate: Not needed in v9 hook files

## Open Questions

1. **Should `npx husky init` or manual setup be used?**
   - What we know: `npx husky init` creates a pre-commit with `npm test` content and overwrites the prepare script to just `"husky"`. Manual setup gives full control.
   - What's unclear: Whether `init` will clobber the existing `prepare` script cleanly or cause issues.
   - Recommendation: Use `npx husky init` then immediately fix the prepare script and pre-commit content. It handles directory creation, permissions, and `core.hooksPath` in one command. Alternatively, manual setup (mkdir, echo, chmod, npx husky) gives identical results with more control -- both approaches are equally valid.

2. **Git LFS hooks: include them or skip?**
   - What we know: `.gitattributes` explicitly says "No LFS tracking." LFS hooks in `.git/hooks/` are vestigial. No files are tracked with LFS.
   - What's unclear: Whether a future contributor might enable LFS tracking.
   - Recommendation: Include LFS hooks in `.husky/` with `exit 0` fallback (not `exit 2`). Zero cost, prevents future confusion. This falls under Claude's Discretion per CONTEXT.md.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | bash (shell script verification) |
| Config file | none -- verification is a standalone script |
| Quick run command | `bash scripts/verify-hooks.sh` |
| Full suite command | `bash scripts/verify-hooks.sh` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HOOK-07 | Husky v9 replaces broken v4 config | smoke | `bash scripts/verify-hooks.sh` | No -- Wave 0 |
| HOOK-07a | .husky/pre-commit exists and is executable | smoke | `test -f .husky/pre-commit && test -x .husky/pre-commit` | No -- Wave 0 |
| HOOK-07b | core.hooksPath set to .husky/_ | smoke | `test "$(git config core.hooksPath)" = ".husky/_"` | No -- Wave 0 |
| HOOK-07c | git commit triggers pre-commit hook | integration | `bash scripts/verify-hooks.sh` (commit test section) | No -- Wave 0 |
| HOOK-07d | v4 husky.hooks block removed from theme | unit | `! grep -q '"husky"' wordpress-theme/skyyrose-flagship/package.json` (rough check) | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `bash scripts/verify-hooks.sh`
- **Per wave merge:** `bash scripts/verify-hooks.sh` (same -- single verification script)
- **Phase gate:** Full script green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `scripts/verify-hooks.sh` -- covers all HOOK-07 sub-behaviors
- [ ] No framework install needed -- uses bash + git (already available)

## Sources

### Primary (HIGH confidence)
- [Husky official docs: Get Started](https://typicode.github.io/husky/get-started.html) -- init command, prepare script
- [Husky official docs: How To](https://typicode.github.io/husky/how-to.html) -- monorepo, HUSKY env var, skip hooks
- [Husky official docs: Migrate from v4](https://typicode.github.io/husky/migrate-from-v4.html) -- v4 to v9 migration steps
- [Husky official docs: Troubleshoot](https://typicode.github.io/husky/troubleshoot.html) -- core.hooksPath verification
- [Husky GitHub: bin.js source](https://github.com/typicode/husky) -- CLI behavior, init vs default command
- [Husky GitHub: index.js source](https://github.com/typicode/husky) -- core.hooksPath mechanism, directory setup
- Local verification: `npm ls husky` confirms 9.1.7 installed; `git config core.hooksPath` confirms corrupted state

### Secondary (MEDIUM confidence)
- [Husky GitHub Issue #1431](https://github.com/typicode/husky/issues/1431) -- Git LFS compatibility workarounds
- [Itenium: Git Hooks with Husky v9](https://itenium.be/blog/dev-setup/git-hooks-with-husky-v9/) -- internal mechanism walkthrough
- [remarkablemark: Migrate from Husky 8 to 9](https://remarkablemark.org/blog/2024/02/04/how-to-migrate-from-husky-8-to-9/) -- migration steps

### Tertiary (LOW confidence)
- None -- all findings verified with primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- husky v9.1.7 already installed, verified via npm ls
- Architecture: HIGH -- internal mechanism verified by reading Husky source code (bin.js, index.js)
- Pitfalls: HIGH -- corrupted core.hooksPath confirmed by local git config inspection; LFS hooks verified by reading .git/hooks/ files and .gitattributes

**Critical discovery:** `core.hooksPath` is set to `--version/_` (corrupted). This MUST be fixed as the first action. Running `npx husky` or `npx husky init` will overwrite it with the correct `.husky/_` value.

**Research date:** 2026-03-08
**Valid until:** 2026-04-08 (Husky v9 is stable; v10 may change things but not expected soon)
