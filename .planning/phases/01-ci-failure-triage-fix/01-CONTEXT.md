# Phase 1: CI Failure Triage & Fix - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Remove all 17 `continue-on-error: true` directives from ci.yml, security-gate.yml, and dast-scan.yml, and fix the underlying failures they mask so CI passes green. The CI pipeline must produce hard failures on real problems — no check is silently swallowed.

</domain>

<decisions>
## Implementation Decisions

### Security scan handling
- Remove `continue-on-error` from all security steps in ci.yml and security-gate.yml
- Many security commands already use `|| true` at command level — refactor these to use proper exit codes
- Keep the existing gate pattern: individual tools report findings, "Fail on critical vulnerabilities" step enforces on HIGH+HIGH confidence
- For gitleaks/trufflehog in security-gate.yml: remove `continue-on-error` AND `|| true` — secrets in code should be a hard failure
- For pip-licenses: remove `continue-on-error`, add an allowlist for known acceptable licenses

### Lint and format fix strategy
- Auto-fix codebase FIRST: run `black .`, `isort .` to format all Python code
- Then remove `continue-on-error` from black and isort steps — they should pass clean
- For mypy: add targeted `# type: ignore` comments or configure `mypy.ini` to exclude known problematic modules — don't suppress the entire check
- For ESLint: fix real errors in frontend code, then remove `continue-on-error`
- For tsc (TypeScript): fix type errors in frontend, then remove `continue-on-error`

### Broken job disposition
- DAST workflow (dast-scan.yml): Remove the 2 `continue-on-error` directives; the workflow is already marked DISABLED and references non-existent scripts — add a clear early-exit guard so it fails fast with an informative message rather than silently swallowing errors
- Three.js tests: Verify whether `npm run test:collections` actually works; if tests exist and pass, remove `continue-on-error`; if they don't exist or are fundamentally broken, remove the entire job

### Deploy tag handling
- Remove `continue-on-error` from git tag step
- Make tag creation robust: use timestamp-based tags that won't conflict, or check-before-create
- Tag failure should not block the deploy — restructure so tagging is a post-deploy step that doesn't affect the deploy pipeline's exit code

### Claude's Discretion
- Exact mypy configuration (which modules to exclude vs fix)
- Whether to split ci.yml security steps into a separate job or keep in current structure
- Order of fixes (lint first vs security first)
- Whether to auto-fix ESLint issues with `--fix` or fix manually

</decisions>

<specifics>
## Specific Ideas

- User wants "best recommended for production" — prioritize reliability and clear failure signals over permissiveness
- The 17 directives are spread across 3 files: ci.yml (12), security-gate.yml (3), dast-scan.yml (2)
- ci.yml has a dual-layer pattern on security steps: `|| true` at command level AND `continue-on-error` at step level — both need addressing

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- ci.yml already has a "Fail on critical vulnerabilities" gate step (line 287-297) — this is the enforcement point for security
- Concurrency control already configured (`cancel-in-progress: true`)
- All action pins use SHA hashes (good security practice, preserve during edits)

### Established Patterns
- ci.yml uses 5-stage pipeline: Lint → Tests (parallel) → E2E → Deploy Staging → Deploy Production
- Security scanning runs parallel with tests (Stage 2)
- All artifact uploads use `if: always()` — this pattern is correct and should be preserved
- Environment-based deploy gates (staging vs production) with URL outputs

### Integration Points
- `security-gate.yml` runs on PR to main and push to main — separate from ci.yml
- `dast-scan.yml` is workflow_dispatch only (manual trigger) — least impact to change
- Frontend tests use `working-directory: frontend` — Node setup caches from `frontend/package-lock.json`
- Python tests use Redis service container — must be preserved

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-ci-failure-triage-fix*
*Context gathered: 2026-03-08*
