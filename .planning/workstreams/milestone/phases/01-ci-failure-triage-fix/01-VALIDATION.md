---
phase: 1
slug: ci-failure-triage-fix
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4+ (Python), Jest 30.x (JS/Node) |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options], `config/testing/jest.config.cjs` |
| **Quick run command** | `pytest tests/ -x -q --tb=short` |
| **Full suite command** | `pytest tests/ -v --cov=. && npm run test:collections` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run the specific tool being fixed (e.g., `black --check .` after formatting fixes)
- **After every plan wave:** Run all tool commands in sequence
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds
- **Phase gate:** `grep -c 'continue-on-error: true' .github/workflows/*.yml` returns 0

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | CI-02 | format | `black --check .` | N/A — tool | ⬜ pending |
| 01-01-02 | 01 | 1 | CI-02 | format | `isort --check-only .` | N/A — tool | ⬜ pending |
| 01-01-03 | 01 | 1 | CI-02 | lint | `ruff check .` | N/A — tool | ⬜ pending |
| 01-01-04 | 01 | 1 | CI-02 | type | `mypy . --ignore-missing-imports` | N/A — tool | ⬜ pending |
| 01-01-05 | 01 | 1 | CI-02 | lint | `cd frontend && npx eslint .` | N/A — tool | ⬜ pending |
| 01-01-06 | 01 | 1 | CI-02 | type | `cd frontend && npx tsc --noEmit` | N/A — tool | ⬜ pending |
| 01-01-07 | 01 | 1 | CI-02 | unit | `npm run test:collections` | Yes — 8 suites | ⬜ pending |
| 01-02-01 | 02 | 2 | CI-01 | grep | `grep -c 'continue-on-error: true' .github/workflows/ci.yml .github/workflows/security-gate.yml .github/workflows/dast-scan.yml` | N/A — shell | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] ESLint dependency in frontend `package.json` — must be added before ESLint can run
- [ ] Node version in ci.yml — update from 20 to 22 to match `.nvmrc`
- [ ] mypy config consolidation — dual config (`mypy.ini` + `pyproject.toml`) causes ambiguity

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CI pipeline fails on broken lint rule | CI-01 | Requires GitHub Actions runner | Push a commit with deliberate lint error, verify red status |
| CI pipeline passes green without continue-on-error | CI-01 | Requires GitHub Actions runner | Push clean commit after all fixes, verify green status |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
