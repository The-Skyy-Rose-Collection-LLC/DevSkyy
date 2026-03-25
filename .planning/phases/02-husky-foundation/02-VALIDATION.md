---
phase: 2
slug: husky-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | bash scripts (shell-based verification) |
| **Config file** | scripts/verify-hooks.sh (created in this phase) |
| **Quick run command** | `test -x .husky/pre-commit && echo PASS` |
| **Full suite command** | `bash scripts/verify-hooks.sh` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `test -x .husky/pre-commit && echo PASS`
- **After every plan wave:** Run `bash scripts/verify-hooks.sh`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | HOOK-07 | integration | `test -x .husky/pre-commit && git config core.hooksPath` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | HOOK-07 | integration | `grep -c '"husky"' wordpress-theme/skyyrose-flagship/package.json \| grep -q '^0$'` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | HOOK-07 | integration | `bash scripts/verify-hooks.sh` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/verify-hooks.sh` — verification script (created as part of phase tasks)

*Existing infrastructure covers framework needs — only the verification script is new.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Hook fires on real commit | HOOK-07 | Requires actual git commit with staged files | Stage a file, run `git commit -m "test"`, observe hook output in terminal |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
