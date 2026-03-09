---
phase: 04
slug: pr-branch-protection
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Shell script + `gh api` verification |
| **Config file** | none — pure API configuration |
| **Quick run command** | `gh api repos/{owner}/{repo}/branches/main/protection --jq '.required_status_checks.checks[].context'` |
| **Full suite command** | `bash scripts/setup-branch-protection.sh --verify` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Read back protection settings via `gh api`
- **After every plan wave:** Full verification of all protection settings
- **Before `/gsd:verify-work`:** All smoke checks must pass
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | PR-01 | smoke | `gh api .../protection --jq '.required_status_checks.checks \| length'` (expect 4) | No — Wave 0 | pending |
| 04-01-02 | 01 | 1 | PR-02 | smoke | `gh api .../protection --jq '.required_status_checks.strict'` (expect true) | No — Wave 0 | pending |
| 04-01-03 | 01 | 1 | — | smoke | `gh api .../protection --jq '.enforce_admins.enabled'` (expect true) | No — Wave 0 | pending |
| 04-01-04 | 01 | 1 | — | smoke | `gh api .../protection --jq '.allow_force_pushes.enabled'` (expect false) | No — Wave 0 | pending |
| 04-01-05 | 01 | 1 | — | smoke | `gh api repos/{owner}/{repo} --jq '.allow_auto_merge'` (expect true) | No — Wave 0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `scripts/setup-branch-protection.sh` — setup and verification script (created by plan)

*No framework install needed — `gh` CLI already available and authenticated.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Agent can create PR and auto-merge | PR-01 | Requires real PR with passing CI | Create test branch, push trivial change, `gh pr create --auto --squash`, wait for CI, verify merge |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
