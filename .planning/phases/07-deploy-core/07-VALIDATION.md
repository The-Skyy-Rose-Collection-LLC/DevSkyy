---
phase: 7
slug: deploy-core
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | bash + pytest (shell script testing via subprocess) |
| **Config file** | tests/conftest.py (existing) |
| **Quick run command** | `bash scripts/deploy-theme.sh --dry-run` |
| **Full suite command** | `pytest tests/scripts/test_deploy_theme.py -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `bash scripts/deploy-theme.sh --dry-run`
- **After every plan wave:** Run dry-run + shellcheck
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-07 | integration | `bash scripts/deploy-theme.sh --dry-run` | Wave 0 | pending |
| 07-01-02 | 01 | 1 | DEPLOY-02, DEPLOY-03, DEPLOY-07 | unit | `pytest tests/scripts/test_deploy_theme.py -v` | Wave 0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `scripts/deploy-theme.sh` — the deploy script itself (core deliverable)
- [ ] `tests/scripts/test_deploy_theme.py` — subprocess tests for script behavior
- [ ] `tests/scripts/__init__.py` — package init (if directory is new)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Files actually transfer to production | DEPLOY-01 | Requires live server access | Run `bash scripts/deploy-theme.sh` (not dry-run), verify files appear on server |
| WP-CLI maintenance mode activates on live site | DEPLOY-02 | Requires live server | Check site shows maintenance page during deploy |
| Cache flush works on live site | DEPLOY-03 | Requires live server | Verify site loads fresh content after deploy |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
