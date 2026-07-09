---
name: devflow-security
description: Parallel security gate — bandit + secret scan + npm audit on changed files. Hard-fails on any HIGH/CRITICAL or hardcoded secret. Use before committing, before a PR, and inside ship.
---

# Devflow Security

## Run the gate

```bash
# Changed files vs last commit (default — use before committing)
bash scripts/devworkflows/security.sh

# Staged only (pre-commit hook check)
bash scripts/devworkflows/security.sh --staged

# Full branch diff (before opening a PR)
bash scripts/devworkflows/security.sh --base main

# Specific files
bash scripts/devworkflows/security.sh --files path/a.py path/b.ts

# Also audit dependency CVEs (slow, network — pip-audit)
bash scripts/devworkflows/security.sh --deps
```

**Exit 0** = clean. **Exit 1** = HIGH/CRITICAL code finding or a hardcoded secret — do not commit until resolved.

## What it covers

| Layer | Tool | Gate |
|-------|------|------|
| Python code | `bandit` | severity HIGH, confidence MEDIUM+ |
| Hardcoded secrets | grep (no tool dep) | private keys, AWS/GCP keys, `sk-`/`sk-ant-`/`ghp_`/`glpat-`/`xox*` tokens, `key=…`/`secret=…` literals ≥12 chars |
| JS/TS deps | `npm audit` | HIGH + CRITICAL (runs only if JS or `package.json` changed) |
| Python deps | `pip-audit` | known CVEs (only with `--deps`) |

Secret scan **excludes** (false-positive killers, baked in): `tests/`, `docs/`, `node_modules/`, `vendor/`, `.venv*/`, `__pycache__/`, `.wolf/`, `*.example`, `*.sample`, `*.md`, `*.min.*`, lock files.

## Suppressing a verified false positive

| Scope | How |
|-------|-----|
| One line | append `devflow:allow-secret` as a comment on that line |
| Whole file | put `devflow:allow-secrets-file` anywhere in the first 5 lines |

A suppression with **no adjacent comment explaining why** is a code-review failure. Never suppress a real secret — rotate it (project protocol: STOP, rotate, scan codebase for siblings).

## Loop until green

```bash
# 1. See what fails
bash scripts/devworkflows/security.sh

# 2. For each finding:
#    - bandit Bxxx  → fix the unsafe call (never blanket # nosec)
#    - secret       → move to env var (.env / .env.secrets), ROTATE the leaked value
#    - npm/pip CVE  → bump the dependency; if no fix exists, document the accepted risk
# 3. Re-run. Repeat until "Findings: 0" and exit: 0.
```

Termination: once `Findings: 0` and `exit: 0`, the gate is clear. Stop looping.

## Severity → action

| Finding | Severity | Action |
|---------|----------|--------|
| Hardcoded secret | CRITICAL | Stop. Rotate the value. Move to env. Scan for siblings. |
| bandit HIGH (e.g. B602 shell, B301 pickle, B324 weak hash) | HIGH | Fix the call. No `# nosec` without a justifying comment. |
| npm/pip CRITICAL dep | HIGH | Bump now. |
| npm/pip HIGH dep | MEDIUM | Bump this cycle or document accepted risk. |

## Hard rules

- Do NOT commit if exit code is 1.
- A hardcoded secret is never "fix later" — rotate immediately (project STOP-AND-SHOW security protocol).
- `# nosec` / `devflow:allow-secret` require an adjacent comment with the reason.
- Pairs with `devflow-review` (correctness) and `devflow-tdd` (tests). All three compose into `devflow-ship`.
