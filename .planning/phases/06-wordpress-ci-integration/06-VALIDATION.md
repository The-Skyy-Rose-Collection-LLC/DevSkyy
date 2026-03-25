---
phase: 6
slug: wordpress-ci-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | GitHub Actions CI + shell scripts |
| **Config file** | `.github/workflows/ci.yml` |
| **Quick run command** | `find wordpress-theme/skyyrose-flagship -name "*.php" -not -path "*/node_modules/*" -not -path "*/vendor/*" -exec php -l {} +` |
| **Full suite command** | Push to branch and verify CI passes on GitHub |
| **Estimated runtime** | ~60 seconds (CI job) |

---

## Sampling Rate

- **After every task commit:** Run PHP lint locally + `npm run build` in theme dir
- **After every plan wave:** Push to branch, verify CI job passes on GitHub
- **Before `/gsd:verify-work`:** Full CI suite must be green
- **Max feedback latency:** 60 seconds (CI runner)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | CI-03, CI-04, CI-05 | integration | `find wordpress-theme/skyyrose-flagship -name "*.php" -exec php -l {} + && cd wordpress-theme/skyyrose-flagship && npm install && npm run build && git diff --exit-code -- '**/*.min.js' '**/*.min.css'` | N/A (CI step) | pending |
| 06-01-02 | 01 | 1 | PR-01 | smoke | `bash scripts/setup-branch-protection.sh --verify` | scripts/setup-branch-protection.sh | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements:*
- PHP is pre-installed on CI runners (CI-03)
- `npm run build` and `scripts/verify-build.sh` exist from Phase 5 (CI-04)
- `.min.js` and `.min.css` files are tracked in git for drift detection (CI-05)
- `scripts/setup-branch-protection.sh` exists from Phase 4 (needs update only)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CI fails on PHP syntax error | CI-03 | Requires real CI run | Push a branch with intentional PHP syntax error, verify CI fails |
| CI fails on stale minified files | CI-05 | Requires real CI run | Edit a source JS/CSS file without rebuilding, push, verify CI fails |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
