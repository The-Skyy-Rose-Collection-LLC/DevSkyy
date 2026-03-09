# Phase 4: PR Branch Protection - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Configure GitHub branch protection rules on the `main` branch so no code reaches production without passing all CI checks via a pull request. Agents (Ralph, Claude Code) must still be able to create and merge PRs autonomously when CI passes.

</domain>

<decisions>
## Implementation Decisions

### Required CI checks
- Require all 4 main CI jobs to pass: `lint`, `python-tests`, `security-scan`, `frontend-tests`
- Do NOT require optional/triggered workflows (`dast-scan.yml`, `claude.yml`, `asset-generation.yml`)
- Status check names must match the exact job names as they appear in GitHub Actions

### Agent merge workflow
- Enable GitHub auto-merge so agents can use `gh pr create` + auto-merge
- No admin bypass needed — agents follow the same PR path as humans
- No required reviewers — CI is the reviewer (per Out of Scope decision)

### Direct push policy
- Block direct pushes to main — all changes must go through PRs
- Block force pushes to main — prevent history rewriting
- This is consistent with v2 requirements PROT-01 and PROT-02, pulled forward

### Enforcement method
- Use classic GitHub branch protection rules (not rulesets)
- Configure via `gh api` for automation — no manual GitHub UI steps
- Classic rules are simpler and sufficient for single-repo setup

### Branch up-to-date requirement
- Require branches to be up-to-date with main before merge (PR-02)
- This prevents merge conflicts and ensures CI ran against latest code

### Claude's Discretion
- Exact `gh api` payload structure for setting branch protection
- Whether to use strict or non-strict up-to-date requirement
- Error handling approach if API call fails

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.github/workflows/ci.yml`: CI pipeline with 4 jobs (lint, python-tests, security-scan, frontend-tests)
- `gh` CLI already authenticated and available

### Established Patterns
- All CI configuration in `.github/workflows/`
- Branch protection is pure GitHub API configuration — no codebase files to modify

### Integration Points
- CI job names must exactly match what GitHub reports as status checks
- Auto-merge depends on branch protection being enabled first (GitHub requirement)

</code_context>

<specifics>
## Specific Ideas

- Repo: `The-Skyy-Rose-Collection-LLC/DevSkyy` (public)
- Default branch: `main`
- Currently zero branch protection (confirmed via `gh api` — 404)
- Agent workflows: Ralph creates branches via `git checkout -b`, commits, pushes, creates PRs via `gh pr create`
- Claude Code: Same workflow — branch, commit, push, PR

</specifics>

<deferred>
## Deferred Ideas

- PROT-03 (auto-rollback on failed health check) — v2 requirement
- PROT-04 (agent-aware hook messaging) — v2 requirement
- PROT-05 (automatic theme version bump) — v2 requirement

</deferred>

---

*Phase: 04-pr-branch-protection*
*Context gathered: 2026-03-09*
