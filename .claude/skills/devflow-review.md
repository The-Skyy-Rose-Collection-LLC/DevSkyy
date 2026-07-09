---
name: devflow-review
description: Parallel lint gate — ruff + tsc + phpcs on changed files. Hard-fails on any finding. Use before committing or merging.
---

# Devflow Review

## Run the gate

```bash
# All changes vs last commit (default — use this before committing)
bash scripts/devworkflows/review.sh

# Staged only (pre-commit check)
bash scripts/devworkflows/review.sh --staged

# Full branch diff (use before opening a PR)
bash scripts/devworkflows/review.sh --base main

# Specific files
bash scripts/devworkflows/review.sh --files path/a.py path/b.ts
```

**Exit 0** = no findings. **Exit 1** = findings exist — do not proceed until resolved.

## Loop until green (auto-fix + re-check)

Run this mode when fixing a batch of issues:

```bash
# Step 1: auto-fix what ruff can fix
FIX=1 bash scripts/devworkflows/review.sh

# Step 2: check what remains
bash scripts/devworkflows/review.sh
```

**If exit is still 1 after Step 2:** read every remaining finding, fix each one in code, then re-run `bash scripts/devworkflows/review.sh`. Repeat until exit 0.

Loop termination rule: once `Findings: 0` and `exit: 0`, the gate is clear. Stop looping.

---

## After running (single pass)

Read the output. Group findings by severity:

| Source | Severity |
|--------|----------|
| php syntax error | CRITICAL — file won't load |
| tsc `error TS` | HIGH — type contract broken |
| ruff `E` (error) | HIGH — correctness issue |
| ruff `W` (warning) | MEDIUM |
| phpcs ERROR | MEDIUM |
| ruff `C/N` (convention) | LOW |
| phpcs WARNING | LOW |

Present findings as: `path:line: SEVERITY: message. Fix: <one-line fix>`

## Hard rules

- Do NOT commit if exit code is 1
- Do NOT suppress findings with `# noqa` / `@ts-ignore` / `phpcs:ignore` without adding a comment explaining why
- Fix CRITICAL and HIGH before anything else
- LOW findings can be batched into a separate cleanup commit

## What it covers

| Layer | Tool | Config |
|-------|------|--------|
| Python | ruff 0.15.x | `pyproject.toml` |
| TypeScript | tsc --noEmit | `frontend/tsconfig.json` |
| PHP syntax | php -l | (built-in) |
| PHP style | phpcs | `wordpress-theme/skyyrose-flagship/.phpcs.xml` |

Not covered here — use the sibling gates: `bandit`/secret-scan/`npm audit` → **devflow-security**. `pytest` RED/GREEN/coverage → **devflow-tdd**. All three compose into **devflow-ship** (the pre-push gate).
