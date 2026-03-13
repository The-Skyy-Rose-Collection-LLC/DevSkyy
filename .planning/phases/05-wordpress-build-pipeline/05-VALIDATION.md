---
phase: 5
slug: wordpress-build-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Shell script + file existence checks |
| **Config file** | N/A (no test framework — build output verification) |
| **Quick run command** | `cd wordpress-theme/skyyrose-flagship && npm run build` |
| **Full suite command** | `cd wordpress-theme/skyyrose-flagship && npm run build && bash scripts/verify-build.sh` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd wordpress-theme/skyyrose-flagship && npm run build`
- **After every plan wave:** Run full suite command (build + verify)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | BUILD-01 | smoke | `cd wordpress-theme/skyyrose-flagship && npm run build:js` | N/A (inline) | pending |
| 05-01-02 | 01 | 1 | BUILD-02 | smoke | `cd wordpress-theme/skyyrose-flagship && npm run build:css` | N/A (inline) | pending |
| 05-01-03 | 01 | 1 | BUILD-03 | smoke | `find wordpress-theme/skyyrose-flagship/assets -name "*.map" \| wc -l` | N/A (inline) | pending |
| 05-01-04 | 01 | 1 | BUILD-04 | smoke | `cd wordpress-theme/skyyrose-flagship && npm run build` (exit 0) | N/A (inline) | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers JS minification (webpack 5.105 installed)
- Existing infrastructure covers CSS minification (clean-css-cli 5.6.3 installed)
- No new test frameworks needed — verification is file-existence based

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Source maps load in browser DevTools | BUILD-03 | Browser-only verification | Open site in Chrome, check Sources panel shows original source via .map files |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
