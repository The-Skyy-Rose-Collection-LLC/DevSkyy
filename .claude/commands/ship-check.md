---
description: Run the full pre-deployment gate. Composes lint, type-check, tests, and preflight (when relevant). Use before any push to main or any wp-theme deploy. Argument is the deployment target (api | frontend | wp | all).
argument-hint: [api|frontend|wp|all]
allowed-tools: Bash, Read, Grep, Glob, Task
---

You are running the pre-ship gate. Default target is `all` if none provided.

Target: $ARGUMENTS (default: all)

## Gate sequence (stop on first failure)

### 1. Lint (always)
```bash
make lint
```

### 2. Type-check (target-dependent)
- For `api` or `all`: `uv run mypy .`
- For `frontend` or `all`: `cd frontend && npm run type-check`
- For `wp` or `all`: `cd wordpress-theme && npm run lint:php`

### 3. Tests (target-dependent)
- For `api` or `all`: `make test-fast`
- For `frontend` or `all`: `cd frontend && npm test -- --run`
- For `wp` or `all`: `cd wordpress-theme && npm run verify`

### 4. Preflight (only when target involves renders)
- If the diff (run `git diff --name-only origin/main...HEAD`) touches `renders/`, `agents/garment_fidelity/`, or `assets/manifest`: invoke `/preflight` first.
- If preflight returns BLOCK, abort the ship-check.

### 5. Recent-change scope (always)
- Run `git diff --name-only origin/main...HEAD | head -50` to enumerate what's actually shipping.
- For each changed `*.py`, `*.ts`, `*.tsx`, run `ruff check <file>` or `tsc --noEmit <file>`.

## Output format

Return a single PASS / FAIL block:

```
## Ship-Check: <PASS | FAIL>

| Stage         | Status | Notes                          |
|---------------|--------|--------------------------------|
| Lint          | ✓/✗    | <count> issues                 |
| Type-check    | ✓/✗    | <count> errors                 |
| Tests         | ✓/✗    | <pass>/<total> passed          |
| Preflight     | ✓/✗/-  | <BLOCK reason or n/a>          |
| Diff scope    | -      | <N> files in shipping diff     |

## Decision
<one sentence: SHIP, FIX-FIRST, or HOLD-FOR-REVIEW>

## If FIX-FIRST
<exact commands or files the user needs to address, in priority order>
```

## What NOT to do

- Do NOT push, deploy, or merge. This command only inspects. The user runs the actual ship.
- Do NOT skip stages because they "should be fine" — run every stage.
- Do NOT mark FAIL stages as PASS to keep momentum. Honest signal is the whole point.
