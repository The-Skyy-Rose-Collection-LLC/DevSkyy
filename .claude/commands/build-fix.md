# Build and Fix

Incrementally fix build, lint, and type errors across any workspace in this repo.

## Step 1: Detect workspace and build system

Determine context from the current working directory and present files:

| Signals | Workspace | Build / Lint commands (in order) |
|---------|-----------|----------------------------------|
| `pyproject.toml` or `Makefile` at root, `.venv/` present | Python API (root) | `make lint` → `make test-fast` |
| `frontend/` as cwd OR the user names "dashboard" / "Next.js" | Next.js dashboard | `npm run type-check` → `npm run lint` → `npm run build` |
| `wordpress-theme/skyyrose-flagship/` as cwd OR user names "theme" / "PHP" | WordPress theme | `npm run lint:php` → `npm run verify` |
| `skyyrose/elite_studio/` or `scripts/` or any `.py` file named | Python package | `make lint` → `python -m pytest <file> -x --timeout=10` |
| Explicit Makefile target named | Make | `make <target>` |
| Fallback — unknown cwd | Auto-detect | Try `make lint` first; if no Makefile, try `npm run lint` |

If the workspace is ambiguous, ask before running. Do NOT assume npm when Python files are involved.

## Step 2: Run the first command and capture output

Run the first command from the detected set. Capture stdout + stderr in full.

## Step 3: Parse errors

Group all errors by file. Within each file, sort by line number. Treat each distinct error message as one work item.

Error severity mapping:
- **CRITICAL** — syntax errors, import failures, type mismatches that block execution
- **HIGH** — logic errors, missing required attributes, unresolved references
- **MEDIUM** — unused imports, wrong return types, style violations that tools report as errors
- **LOW** — warnings that don't fail the build

Process CRITICAL → HIGH → MEDIUM → LOW.

## Step 4: Fix one error at a time

For each error:

1. Show the error message verbatim
2. Read the relevant file section (5 lines before and after the flagged line)
3. Explain the root cause in one sentence
4. Apply the minimal fix — do not refactor unrelated code
5. Re-run only the command that caught this error
6. Confirm the error is gone before moving to the next

**Language-specific patterns:**

### Python (ruff / mypy / pytest)
- Ruff `F401` unused import → remove the import line
- Ruff `E501` line too long → wrap at 100 chars (project standard)
- mypy "Module has no attribute X" → check actual module API; do not cast away with `# type: ignore` unless the attribute genuinely exists at runtime
- pytest `ImportError` → check `sys.path`, `__init__.py` presence, virtual env activation
- pytest fixture errors → read `conftest.py` before guessing

### TypeScript / Node (npm / eslint / tsc)
- `tsc` errors → fix the type, do not use `any` or `as unknown as T` casts
- ESLint → respect `.eslintrc.cjs` rules; do not disable rules inline without asking
- Missing module → check `package.json` deps; do not add packages without asking

### PHP / WordPress (phpcs / phpcbf)
- phpcs violations → auto-fix with `phpcbf` where safe; manual fixes for sniffs that require judgement
- Always run: `cd wordpress-theme/skyyrose-flagship && ~/.local/bin/composer exec phpcs -- --standard=.phpcs.xml -s <file>`
- Do NOT modify `functions.php` includes array without confirming the change won't break the site

### WordPress theme build (npm run verify)
- Lint failures → read `lint-staged.config.mjs` for the exact linter used per file type
- PHP parse errors → run `/opt/homebrew/bin/php -l <file>` to confirm

## Step 5: Stop conditions

Stop and report (do not continue fixing) if:
- A fix introduces a **new** error not present before
- The same error recurs after 3 fix attempts on the same line
- The error requires a structural change (new file, dependency install, schema migration) — describe what is needed and wait for confirmation
- A fix would touch production data or a paid-API call

## Step 6: Run the full suite

After all individual errors are fixed, run the complete command sequence for the workspace:
- Python: `make lint && make test-fast`
- Next.js: `npm run type-check && npm run lint && npm run build`
- WordPress: `npm run lint:php && npm run verify`

Report pass/fail for each.

## Step 7: Summary

```
=== BUILD FIX SUMMARY ===
Workspace   : <detected workspace>
Commands    : <commands run>
Errors fixed: N
Errors left : N
New errors  : N (should be 0)
```

If errors remain, list each with file:line and the blocker reason.
