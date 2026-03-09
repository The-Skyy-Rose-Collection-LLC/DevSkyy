---
phase: 03
slug: pre-commit-hook-checks
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | bash (shell verification) + manual commit testing |
| **Config file** | none — verification through git operations |
| **Quick run command** | `bash scripts/verify-hooks.sh` |
| **Full suite command** | `bash scripts/verify-pre-commit.sh` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run `bash scripts/verify-hooks.sh`
- **After every plan wave:** Run `bash scripts/verify-pre-commit.sh`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | HOOK-01 | integration | Create JS file with ESLint error, stage, attempt commit, verify fail | No — Wave 0 | pending |
| 03-01-02 | 01 | 1 | HOOK-02 | integration | Create Python file with ruff violation, stage, attempt commit, verify fail | No — Wave 0 | pending |
| 03-01-03 | 01 | 1 | HOOK-03 | integration | Create TS file with type error in frontend, stage, attempt commit, verify fail | No — Wave 0 | pending |
| 03-01-04 | 01 | 1 | HOOK-04 | integration | Create Python file with type error, stage, attempt commit, verify fail | No — Wave 0 | pending |
| 03-01-05 | 01 | 1 | HOOK-05 | integration | Create PHP file with missing semicolon, stage, attempt commit, verify fail | No — Wave 0 | pending |
| 03-01-06 | 01 | 1 | HOOK-06 | integration | Stage a Python file, attempt commit, verify pytest output | No — Wave 0 | pending |
| 03-01-07 | 01 | 1 | HOOK-08 | performance | Time a commit with 5 staged files across languages, verify <30s | No — Wave 0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `scripts/verify-pre-commit.sh` — comprehensive pre-commit verification script covering HOOK-01 through HOOK-08
- [ ] `scripts/php-lint.sh` — PHP lint wrapper for multi-file support
- [ ] `lint-staged.config.mjs` — lint-staged configuration with function syntax for tsc/mypy

*Existing infrastructure covers test framework needs — all linting/type tools already installed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Error messages are clear and actionable | HOOK-01..06 | Subjective clarity assessment | Review terminal output for each blocked commit type |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
