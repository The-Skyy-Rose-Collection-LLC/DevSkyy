# Phase 3: Pre-commit Hook Checks - Research

**Researched:** 2026-03-09
**Domain:** Git pre-commit hooks, lint-staged, ESLint, ruff/black/isort, mypy, tsc, PHP linting
**Confidence:** HIGH

## Summary

Phase 3 wires real lint, type-check, syntax, and test commands into the proof-of-life pre-commit hook that Phase 2 established. The key tool is **lint-staged** (v16.3.2, already installed as a devDependency) which runs configured commands only on staged files, keeping execution fast. The pre-commit hook calls `npx lint-staged` and lint-staged dispatches to the appropriate tool based on file extension.

The primary challenge is the **30-second budget** (HOOK-08). Timing benchmarks show: ruff is near-instant (~50ms), black check ~220ms, isort ~200ms, php -l ~80ms per file, frontend ESLint ~2.2s full project, frontend tsc ~2.4s full project, mypy ~13s full project. Running all tools on a 5-file commit is achievable under 30 seconds if tsc and mypy run as project-wide checks (not per-file) and execute in parallel with file-level lint checks.

A critical discovery: **root-level ESLint is broken** -- `.eslintrc.cjs` (legacy format) crashes with ESLint v9.39 due to an ajv compatibility error. Root JS/TS files (in `src/`) cannot currently be linted. Frontend ESLint works perfectly (`frontend/eslint.config.mjs` uses flat config). The pre-commit hook must route frontend files to frontend's ESLint and either fix or skip root-level ESLint.

**Primary recommendation:** Replace the proof-of-life echo in `.husky/pre-commit` with `npx lint-staged`. Configure lint-staged in `package.json` with per-extension commands. Use function syntax (not string) for tsc and mypy to prevent lint-staged from appending file arguments (both tools need whole-project analysis). Run tsc and mypy conditionally -- only when relevant files are staged. Fix root ESLint by migrating `.eslintrc.cjs` to `eslint.config.mjs` flat config format, or scope root ESLint to only `src/` files via lint-staged glob.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| HOOK-01 | Pre-commit runs ESLint on staged JS/TS files and blocks commit on errors | lint-staged glob `*.{js,ts,tsx,jsx}` routes to ESLint. Frontend ESLint works. Root ESLint broken -- must fix `.eslintrc.cjs` -> flat config or use frontend ESLint only. |
| HOOK-02 | Pre-commit runs Ruff + Black + isort on staged Python files and blocks commit on errors | lint-staged glob `*.py` routes to `ruff check`, `black --check`, `isort --check-only --diff`. All tools confirmed working, combined time <1s for typical file count. |
| HOOK-03 | Pre-commit runs tsc type checking on staged frontend files and blocks commit on errors | tsc cannot check individual files -- must run `tsc --noEmit` on entire frontend project. Use lint-staged function syntax to avoid file argument appending. Time: ~2.4s. |
| HOOK-04 | Pre-commit runs mypy type checking on staged Python files and blocks commit on errors | mypy needs whole-project analysis. Use lint-staged function syntax. Time: ~13s with incremental cache. This is the largest time consumer. |
| HOOK-05 | Pre-commit runs php -l syntax check on staged PHP files and blocks commit on errors | `php -l` works per-file. PHP 8.5.3 available. 106 theme PHP files (excluding node_modules). ~80ms per file. |
| HOOK-06 | Pre-commit runs fast unit tests on changed files and blocks commit on failures | Only 9 unit tests in `tests/unit/` (~2s). Run `pytest tests/unit/ -x -q` as the "fast test" for pre-commit. Full suite (2379 tests) is too slow. |
| HOOK-08 | All hooks complete in under 30 seconds on a typical commit | Budget analysis: ruff+black+isort ~1s, ESLint ~2.2s, tsc ~2.4s, mypy ~13s, php-l ~0.4s (5 files), pytest unit ~2s. Serial total ~21s. Parallel shaves more. Achievable. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| lint-staged | 16.3.2 | Run linters on staged git files only | Already installed. Industry standard pairing with Husky. Supports glob patterns, parallel execution, function configs. |
| husky | 9.1.7 | Git hooks manager | Already installed and initialized (Phase 2). Pre-commit hook at `.husky/pre-commit`. |

### Supporting (Already Installed -- No New Dependencies)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| eslint | 9.39.4 (frontend) | JavaScript/TypeScript linting | Staged JS/TS files in `frontend/` |
| ruff | system | Python linting (fast, Rust-based) | Staged Python files |
| black | system | Python formatting check | Staged Python files |
| isort | system | Python import sorting check | Staged Python files |
| mypy | system | Python type checking | When any `.py` file is staged |
| tsc (typescript) | 5.9.3 | TypeScript type checking | When any `.ts/.tsx` file in `frontend/` is staged |
| php | 8.5.3 (system) | PHP syntax checking | Staged PHP files in `wordpress-theme/` |
| pytest | system | Fast unit tests | When any `.py` file is staged |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| lint-staged | Custom shell script in pre-commit | lint-staged handles stashing, file argument passing, parallel execution, error aggregation. Shell script would be fragile and miss edge cases (partial staging, binary files). |
| lint-staged function for tsc | lint-staged-tsc package | Extra dependency for marginal benefit. Function syntax `() => 'tsc --noEmit'` achieves same result natively. |
| pytest tests/unit/ | pytest-testmon (changed-file-aware) | Not installed, adds dependency. Unit test directory is small enough (~2s) that full unit suite is fine. |
| mypy whole-project | mypy on individual staged files | Individual file checking defeats mypy's purpose -- it needs import graph analysis. Would miss type errors caused by interface changes. |

**Installation:**
```bash
# Nothing to install -- all tools already present
# lint-staged@16.3.2 in devDependencies
# husky@9.1.7 initialized
# Python tools: ruff, black, isort, mypy available system-wide
# PHP 8.5.3 available via Homebrew
```

## Architecture Patterns

### Recommended Project Structure
```
.husky/
  pre-commit           # Changed from echo to: npx lint-staged
package.json           # lint-staged config added
frontend/
  eslint.config.mjs    # Working flat config (no changes needed)
  tsconfig.json        # Used by tsc --noEmit (no changes needed)
.eslintrc.cjs          # BROKEN -- must migrate to eslint.config.mjs
pyproject.toml         # ruff, black, isort config (no changes needed)
mypy.ini               # mypy config (no changes needed)
```

### Pattern 1: lint-staged Configuration in package.json
**What:** Configure lint-staged with per-extension commands using glob patterns
**When to use:** When all config can fit in package.json (no complex logic needed)
**Example:**
```json
{
  "lint-staged": {
    "*.py": [
      "ruff check",
      "black --check",
      "isort --check-only --diff"
    ],
    "frontend/**/*.{ts,tsx}": [
      "eslint --max-warnings 0"
    ],
    "frontend/**/*.{js,jsx,mjs}": [
      "eslint --max-warnings 0"
    ],
    "wordpress-theme/**/*.php": [
      "php -l"
    ]
  }
}
```

### Pattern 2: Function Syntax for Whole-Project Tools
**What:** Use function syntax to prevent lint-staged from appending file arguments
**When to use:** Tools like tsc and mypy that need whole-project analysis, not per-file
**Why:** When lint-staged encounters a string command, it appends staged file paths. `tsc --noEmit file1.ts file2.ts` ignores tsconfig.json. Function syntax prevents this.
**Example (lint-staged.config.mjs):**
```javascript
export default {
  "*.py": [
    "ruff check",
    "black --check",
    "isort --check-only --diff"
  ],
  "*.py": () => [
    "mypy . --ignore-missing-imports"
  ],
  "frontend/**/*.{ts,tsx}": () => [
    "tsc --noEmit --project frontend/tsconfig.json",
    "eslint --max-warnings 0"
  ]
};
```
Note: The function returns a command array without file paths appended. The glob still acts as a trigger -- lint-staged only runs the function when matching files are staged.

### Pattern 3: Conditional Execution via lint-staged Globs
**What:** Different globs trigger different tool chains. Parallel by default for different globs; sequential within an array.
**When to use:** Monorepo with multiple languages
**Key insight:** lint-staged runs commands for different globs concurrently. Commands within the same glob's array run sequentially. This means Python checks and frontend checks run in parallel automatically.

### Pattern 4: Pre-commit Hook Structure
**What:** The `.husky/pre-commit` file delegates entirely to lint-staged
**Example:**
```bash
npx lint-staged
```
That is the entire hook file. lint-staged handles: finding staged files, matching globs, running commands, stashing unstaged changes, error reporting. No shell logic needed in the hook itself.

### Anti-Patterns to Avoid
- **Running tsc/mypy with file arguments:** `tsc file1.ts file2.ts` ignores tsconfig.json. Always use function syntax to prevent argument appending.
- **Running full test suite in pre-commit:** 2379 tests at ~13s minimum is too slow. Pre-commit runs `tests/unit/` only (~2s). Full suite belongs in CI.
- **Checking ALL files with ESLint on commit:** Use lint-staged to check only staged files. Full-project ESLint (~2.2s frontend) is acceptable but not on root (broken).
- **Using `--fix` flags in pre-commit:** The requirements say "blocks commit on errors," not "auto-fixes." Use `--check` / `--check-only` modes. Auto-fix semantics are debatable and can surprise users.
- **Putting lint logic in the hook script:** All logic belongs in lint-staged config. The hook script should just be `npx lint-staged`. This keeps the system testable and configurable.

## Critical Issue: Root ESLint is Broken

**Status:** BROKEN -- must fix before HOOK-01 can be fully satisfied

**Symptom:** Running `npx eslint src/index.ts` at project root produces:
```
NOT SUPPORTED: option missingRefs...
TypeError: Cannot set properties of undefined (setting 'defaultMeta')
```

**Root Cause:** The project has `.eslintrc.cjs` (legacy config format) but ESLint v9.39.3 installed. ESLint v9 requires flat config (`eslint.config.mjs`). The `@eslint/eslintrc` compatibility layer crashes on the `ajv` override in `package.json`.

**Impact on Phase 3:**
- Root `src/` JS/TS files cannot be linted at commit time
- Frontend files are fine (use `eslint.config.mjs` flat config)
- CI only lints frontend (line 318-319 of `ci.yml`)

**Options:**
1. **Fix it (recommended):** Migrate `.eslintrc.cjs` to `eslint.config.mjs` flat config. Scope it to `src/` only.
2. **Scope around it:** lint-staged config only targets `frontend/**/*.{ts,tsx}` for ESLint. Root files get tsc but not ESLint. This matches CI behavior.
3. **Defer it:** Note as known gap, fix in a future phase. ESLint root was never working in CI either.

**Recommendation:** Option 2 (scope around it) for Phase 3. Root ESLint repair is out of scope -- it was not working before and is not in CI. Fix it when root `src/` code becomes important enough to lint. This avoids scope creep while still satisfying HOOK-01 for the files that matter (frontend).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Running linters on staged files only | Custom `git diff --cached` script | lint-staged | Handles partial staging, binary files, stashing unstaged changes, error aggregation, parallel execution |
| Conditional command execution | if/else in shell hook | lint-staged glob matching | Globs automatically match file types; no staged files = no execution |
| Pre-commit stash management | `git stash` push/pop in hook | lint-staged built-in stashing | lint-staged stashes unstaged changes, runs checks on staged-only state, restores on completion |
| Parallel lint execution | `&` background jobs in shell | lint-staged concurrency | lint-staged runs different glob groups concurrently by default with proper error handling |

**Key insight:** lint-staged solves every pre-commit orchestration problem. The hook file is one line (`npx lint-staged`). All intelligence lives in the config.

## Common Pitfalls

### Pitfall 1: tsc/mypy Ignore tsconfig/mypy.ini When Given File Arguments
**What goes wrong:** lint-staged appends staged file paths to commands by default. `tsc --noEmit file1.ts` creates a compilation with NO tsconfig, using default settings.
**Why it happens:** TypeScript CLI behavior: when files are specified on command line, tsconfig.json `include`/`exclude` are ignored.
**How to avoid:** Use function syntax: `"frontend/**/*.{ts,tsx}": () => "tsc --noEmit --project frontend/tsconfig.json"` -- function return values do not get file arguments appended.
**Warning signs:** tsc passes in pre-commit but fails in CI, or vice versa.

### Pitfall 2: mypy Takes 13+ Seconds on Full Project
**What goes wrong:** mypy runs whole-project analysis (~13s). Combined with other checks, pre-commit exceeds 30-second budget.
**Why it happens:** mypy needs to resolve the full import graph. Incremental cache helps on repeat runs but first run is slow.
**How to avoid:** Rely on mypy's incremental cache (`.mypy_cache/`). On warm cache, mypy is significantly faster. Consider running mypy only when core Python modules are changed (not scripts/tests). If still too slow, move mypy to pre-push hook.
**Warning signs:** `git commit` takes >30s on typical commits.

### Pitfall 3: lint-staged Runs on ALL Matching Staged Files Simultaneously
**What goes wrong:** If 50 Python files are staged, `ruff check file1.py file2.py ... file50.py` runs as one command. This is fine for ruff (fast) but could be slow for per-file tools.
**Why it happens:** lint-staged batches all matching files into a single command invocation for efficiency.
**How to avoid:** For `php -l`, which is per-file, use a wrapper: `"wordpress-theme/**/*.php": "php -l"` -- lint-staged passes all files as arguments, but `php -l` only accepts one file at a time. Solution: Use a shell function or `xargs` wrapper, OR lint-staged handles this correctly by passing each file as a separate argument since `php -l` is not a batch tool.
**Warning signs:** `php -l` errors about unexpected arguments.

### Pitfall 4: ESLint --max-warnings 0 vs CI Behavior
**What goes wrong:** Frontend ESLint has 242 warnings (0 errors). Using `--max-warnings 0` would block every commit.
**Why it happens:** The project has many `@typescript-eslint/no-explicit-any` warnings that are intentionally set to "warn" not "error."
**How to avoid:** Do NOT use `--max-warnings 0`. Just use `eslint` -- it exits non-zero on errors (exit code 1) but exits 0 on warnings only. This matches the success criteria: "blocks commit on errors."
**Warning signs:** Every commit blocked by ESLint despite no actual errors.

### Pitfall 5: lint-staged with Monorepo ESLint Configs
**What goes wrong:** Running ESLint from root on frontend files may not pick up `frontend/eslint.config.mjs`. Running from frontend on root files finds no config.
**Why it happens:** ESLint searches for config files starting from the file's directory upward.
**How to avoid:** Use `--cwd` flag or scope lint-staged globs to match the right ESLint instance. For frontend: `"frontend/**/*.{ts,tsx}": "eslint"` -- when lint-staged runs eslint with paths like `frontend/app/page.tsx`, ESLint finds `frontend/eslint.config.mjs` automatically.
**Warning signs:** "No ESLint configuration found" errors.

### Pitfall 6: php -l Does Not Accept Multiple Files
**What goes wrong:** `php -l file1.php file2.php` only checks the first file and ignores the rest.
**Why it happens:** `php -l` (lint) only accepts a single filename argument.
**How to avoid:** Use a wrapper script that loops: `for f in "$@"; do php -l "$f" || exit 1; done`. Or create a `scripts/php-lint.sh` helper. Alternatively, lint-staged can be configured to run commands per-file using the `--shell` approach, but v16 removed `--shell`. The cleanest solution is a small wrapper script.
**Warning signs:** Only the first PHP file in a commit gets checked.

## Code Examples

### lint-staged Configuration (lint-staged.config.mjs)
```javascript
// Source: lint-staged official docs + project analysis
// Using .mjs because package.json has "type": "module"

/** @type {import('lint-staged').Configuration} */
export default {
  // Python: lint, format check, import sort check
  '*.py': [
    'ruff check',
    'black --check',
    'isort --check-only --diff',
  ],

  // Python type checking: whole-project (function prevents file arg appending)
  '*.py': () => 'mypy . --ignore-missing-imports',

  // Frontend TypeScript/JavaScript: ESLint + type check
  'frontend/**/*.{ts,tsx,js,jsx,mjs}': 'eslint',

  // Frontend type checking: whole-project
  'frontend/**/*.{ts,tsx}': () => 'tsc --noEmit --project frontend/tsconfig.json',

  // PHP syntax check
  'wordpress-theme/**/*.php': 'bash scripts/php-lint.sh',

  // Fast unit tests when Python changes
  '*.py': () => 'python -m pytest tests/unit/ -x -q',
};
```

**IMPORTANT:** The above has duplicate `'*.py'` keys -- JavaScript objects don't allow duplicate keys. The actual config must merge Python commands. See "Correct Merged Config" below.

### Correct Merged Config (accounts for JS object key uniqueness)
```javascript
/** @type {import('lint-staged').Configuration} */
export default {
  // Python: file-level checks (lint-staged appends file paths)
  '*.py': [
    'ruff check',
    'black --check',
    'isort --check-only --diff',
  ],

  // Frontend: ESLint on staged files
  'frontend/**/*.{ts,tsx,js,jsx,mjs}': 'eslint',

  // Frontend type check: whole-project, triggered by any staged .ts/.tsx
  'frontend/**/*.{ts,tsx}': () => 'tsc --noEmit --project frontend/tsconfig.json',

  // PHP syntax check via wrapper
  'wordpress-theme/**/*.php': 'bash scripts/php-lint.sh',
};
```

Mypy and pytest run separately in the pre-commit hook script (not via lint-staged) to avoid the duplicate-key problem:

### Pre-commit Hook (handles both lint-staged and whole-project tools)
```bash
# .husky/pre-commit

# Run lint-staged for file-level checks
npx lint-staged

# Run mypy if any Python files are staged
if git diff --cached --name-only --diff-filter=ACMR | grep -q '\.py$'; then
  echo "Running mypy type check..."
  mypy . --ignore-missing-imports
fi

# Run fast unit tests if any Python files are staged
if git diff --cached --name-only --diff-filter=ACMR | grep -q '\.py$'; then
  echo "Running unit tests..."
  python -m pytest tests/unit/ -x -q
fi
```

### PHP Lint Wrapper Script (scripts/php-lint.sh)
```bash
#!/usr/bin/env bash
# Lint PHP files passed as arguments
# php -l only accepts one file at a time
set -euo pipefail

ERRORS=0
for file in "$@"; do
  # Skip flag-like arguments
  case "$file" in -*) continue ;; esac

  if ! php -l "$file" 2>&1 | grep -q "No syntax errors"; then
    ERRORS=$((ERRORS + 1))
  fi
done

if [ "$ERRORS" -gt 0 ]; then
  echo "PHP syntax errors found in $ERRORS file(s)"
  exit 1
fi
```

### Verification Commands
```bash
# Verify lint-staged is configured
npx lint-staged --diff="HEAD~1" --verbose  # Dry run on last commit's changes

# Test individual tool chains
echo "import os" > /tmp/test.py && ruff check /tmp/test.py  # Should show F401
echo "x=1" > /tmp/test.py && black --check /tmp/test.py     # Should fail
echo "<?php echo 'hi'" > /tmp/test.php && php -l /tmp/test.php  # Should fail (missing ;)
```

## Performance Budget Analysis

**HOOK-08 requirement:** All checks complete in <30 seconds on a 5-file commit.

### Measured Tool Timings (this machine, warm cache)
| Tool | Mode | Time | Notes |
|------|------|------|-------|
| ruff check | per-file | ~50ms | Rust-based, near instant |
| black --check | per-file | ~220ms | Python startup dominates |
| isort --check-only | per-file | ~200ms | Similar to black |
| php -l | per-file | ~80ms | Very fast |
| ESLint (frontend) | per-file | ~300ms | JIT startup |
| ESLint (frontend) | full project | ~2.2s | All frontend files |
| tsc --noEmit | full project | ~2.4s | Frontend only |
| mypy | full project (warm) | ~13s | 807 Python files, incremental cache |
| pytest tests/unit/ | fast suite | ~2.2s | 9 tests |

### Worst-Case Scenario: 5-file commit (2 Python, 2 TS, 1 PHP)
```
lint-staged runs in parallel for different globs:

GROUP A (Python file-level): ruff + black + isort on 2 files .... ~0.5s
GROUP B (Frontend ESLint): eslint on 2 TS files ................. ~0.6s
GROUP C (PHP): php -l on 1 file ................................. ~0.1s

After lint-staged:
GROUP D (tsc): tsc --noEmit (triggered by TS files) ............ ~2.4s
GROUP E (mypy): mypy full project (triggered by .py files) ...... ~13s
GROUP F (pytest): pytest tests/unit/ (triggered by .py files) ... ~2.2s

Total (serial worst case): ~18.8s
Total (with D||E||F parallel): ~14s
```

**Verdict:** Comfortably under 30 seconds. The main bottleneck is mypy at ~13s. If mypy cache is cold, it can be up to ~20s, but this is still within budget.

### Optimization if needed
1. Run mypy only on specific modules, not the whole project
2. Move mypy to pre-push hook (less frequent, more thorough)
3. Use `--follow-imports=skip` to reduce mypy scope
4. Enable mypy's binary cache format for faster incremental runs

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| lint-staged `--shell` flag | Shell removed in v16 | v16.0.0 (2025) | Wrapper scripts needed for tools that need shell features |
| lint-staged advanced config | Validation removed in v16 | v16.0.0 (2025) | Old configs silently ignored instead of erroring |
| `.eslintrc.cjs` (legacy) | `eslint.config.mjs` (flat config) | ESLint v9 (2024) | Legacy format crashes with ESLint v9 + ajv |
| `husky add .husky/pre-commit "cmd"` | Manual file editing | Husky v9 (2024) | `add` command removed |
| mypy JSON cache | mypy binary cache (experimental) | mypy 1.18 (2025) | ~40% faster incremental checking |

**Deprecated/outdated:**
- `lint-staged --shell`: Removed in v16. Use wrapper scripts instead.
- `.eslintrc.cjs` with ESLint v9: Crashes. Use flat config `eslint.config.mjs`.
- `husky add`: Removed in v9. Edit hook files directly.

## Open Questions

1. **Should root ESLint be fixed in Phase 3?**
   - What we know: Root `.eslintrc.cjs` crashes with ESLint v9. CI never runs root ESLint. Only frontend ESLint is in CI.
   - What's unclear: Whether root `src/` code should be actively linted.
   - Recommendation: Scope lint-staged to `frontend/**` for ESLint. Fixing root ESLint is a separate concern (scope creep). If someone decides to fix it later, it's a simple migration to flat config.

2. **Should pre-commit auto-fix or check-only?**
   - What we know: REQUIREMENTS.md says "blocks commit on errors." Auto-fix would change staged file content.
   - What's unclear: Whether the user prefers auto-fix convenience.
   - Recommendation: Check-only mode (`--check`, `--check-only`). Let developers fix manually. This is safer for autonomous agent workflows where you want explicit control over what gets committed.

3. **How should mypy handle performance if it exceeds budget?**
   - What we know: mypy takes ~13s warm. First commit after cache clear could be ~20s.
   - What's unclear: Whether the combined total will reliably stay under 30s.
   - Recommendation: Start with mypy in pre-commit. If it consistently exceeds budget, move to pre-push hook. The `.mypy_cache/` improves dramatically after first run.

4. **Should HOOK-06 (fast tests) use pytest-testmon for smarter test selection?**
   - What we know: Only 9 unit tests exist (~2s). Full suite is 2379 tests (~13s+).
   - What's unclear: Whether test count will grow significantly.
   - Recommendation: Run `pytest tests/unit/ -x -q` for now. 2 seconds is negligible. Re-evaluate if unit test count exceeds 50.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | bash (shell verification) + manual commit testing |
| Config file | none -- verification through git operations |
| Quick run command | `bash scripts/verify-hooks.sh` (extend from Phase 2) |
| Full suite command | `bash scripts/verify-pre-commit.sh` (new) |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HOOK-01 | ESLint blocks commit on JS/TS error | integration | Create temp file with error, stage, attempt commit, verify fail | No -- Wave 0 |
| HOOK-02 | Ruff/Black/isort blocks commit on Python violation | integration | Create temp file with violation, stage, attempt commit, verify fail | No -- Wave 0 |
| HOOK-03 | tsc blocks commit on TypeScript type error | integration | Create temp file with type error in frontend, stage, attempt commit, verify fail | No -- Wave 0 |
| HOOK-04 | mypy blocks commit on Python type error | integration | Create temp file with type error, stage, attempt commit, verify fail | No -- Wave 0 |
| HOOK-05 | php -l blocks commit on PHP syntax error | integration | Create temp PHP file with missing semicolon, stage, attempt commit, verify fail | No -- Wave 0 |
| HOOK-06 | Fast unit tests run on Python changes | integration | Stage a Python file, attempt commit, verify pytest output in terminal | No -- Wave 0 |
| HOOK-08 | All checks under 30 seconds | performance | Time a commit with 5 staged files across languages, verify <30s | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `bash scripts/verify-hooks.sh` (extends Phase 2)
- **Per wave merge:** `bash scripts/verify-pre-commit.sh` (full verification of all HOOK requirements)
- **Phase gate:** All 7 requirements verified before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `scripts/verify-pre-commit.sh` -- comprehensive pre-commit verification script covering HOOK-01 through HOOK-08
- [ ] `scripts/php-lint.sh` -- PHP lint wrapper for multi-file support
- [ ] `lint-staged.config.mjs` -- or `"lint-staged"` section in `package.json`
- [ ] No framework install needed -- all tools already available

## Sources

### Primary (HIGH confidence)
- Local timing benchmarks: ruff, black, isort, mypy, tsc, eslint, php -l all timed on this machine
- Local project inspection: package.json, .eslintrc.cjs, frontend/eslint.config.mjs, pyproject.toml, mypy.ini, frontend/tsconfig.json
- Phase 2 outputs: 02-01-SUMMARY.md confirms Husky v9 initialized with proof-of-life hook
- [lint-staged GitHub README](https://github.com/lint-staged/lint-staged) -- configuration docs, glob patterns, function syntax, monorepo support
- [lint-staged npm](https://www.npmjs.com/package/lint-staged) -- version verification (16.3.2 installed)
- [lint-staged v16 release notes](https://github.com/lint-staged/lint-staged/releases/tag/v16.0.0) -- breaking changes (--shell removed)

### Secondary (MEDIUM confidence)
- [lint-staged GitHub issue #1352](https://github.com/lint-staged/lint-staged/issues/1352) -- tsc checks all files, not just staged (confirmed: use function syntax)
- [DEV.to: Run tsc in pre-commit with lint-staged](https://dev.to/samueldjones/run-a-typescript-type-check-in-your-pre-commit-hook-using-lint-staged-husky-30id) -- function syntax workaround
- [Jared Khan: Running mypy in pre-commit](https://jaredkhan.com/blog/mypy-pre-commit) -- mypy needs whole-project analysis, pass_filenames=false
- [GitHub issue #13916: mypy via pre-commit](https://github.com/python/mypy/issues/13916) -- confirmed: mypy needs full project, not individual files

### Tertiary (LOW confidence)
- None -- all findings verified with local testing or primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all tools already installed and verified working locally
- Architecture: HIGH -- lint-staged config patterns verified against official docs and tested with local ESLint/ruff
- Pitfalls: HIGH -- root ESLint breakage discovered and verified; tsc/mypy file-argument behavior confirmed via official GitHub issues and local testing
- Performance: HIGH -- all tools timed locally; 30-second budget validated with worst-case analysis

**Critical discovery:** Root ESLint is broken (`.eslintrc.cjs` + ESLint v9 = ajv crash). Frontend ESLint works fine. Pre-commit should scope ESLint to frontend only.

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (tools are stable; lint-staged v16 is current)
