---
phase: 8
slug: deploy-verification-orchestration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | bash + pytest (subprocess testing, same as Phase 7) |
| **Config file** | tests/conftest.py (existing) |
| **Quick run command** | `bash scripts/deploy-pipeline.sh --dry-run` |
| **Full suite command** | `pytest tests/scripts/test_verify_deploy.py tests/scripts/test_deploy_pipeline.py -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `bash scripts/deploy-pipeline.sh --dry-run`
- **After every plan wave:** Run `bash scripts/deploy-pipeline.sh --dry-run && shellcheck scripts/verify-deploy.sh scripts/deploy-pipeline.sh`
- **Before `/gsd:verify-work`:** Full pytest suite must be green + dry-run passes + shellcheck clean
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | DEPLOY-04 | unit (subprocess) | `pytest tests/scripts/test_verify_deploy.py -x` | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 1 | DEPLOY-05 | unit (subprocess dry-run) | `pytest tests/scripts/test_deploy_pipeline.py -x` | ❌ W0 | ⬜ pending |
| 08-02-02 | 02 | 1 | DEPLOY-06 | unit (subprocess) | `bash scripts/deploy-pipeline.sh --dry-run` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/verify-deploy.sh` — post-deploy content verification script
- [ ] `scripts/deploy-pipeline.sh` — orchestration pipeline script
- [ ] `tests/scripts/test_verify_deploy.py` — subprocess tests for verification script
- [ ] `tests/scripts/test_deploy_pipeline.py` — subprocess tests for pipeline script

*Tests validate script behavior via subprocess invocations and dry-run mode. Actual live site verification requires production access and is manual-only.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live site content verification after real deploy | DEPLOY-04 | Requires production access and actual deploy | Run `bash scripts/deploy-pipeline.sh` (no --dry-run), confirm all health checks pass against live skyyrose.co |
| CDN cache propagation timing | DEPLOY-04 | Cache behavior varies by hosting environment | After deploy, verify pages in browser (incognito) within 30s |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
