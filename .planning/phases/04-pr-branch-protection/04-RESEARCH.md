# Phase 4: PR Branch Protection - Research

**Researched:** 2026-03-09
**Domain:** GitHub branch protection rules, required status checks, auto-merge
**Confidence:** HIGH

## Summary

Phase 4 is a pure GitHub API configuration task with no codebase files to modify. The repo (`The-Skyy-Rose-Collection-LLC/DevSkyy`, public) currently has zero branch protection on `main` (confirmed 404). The implementation involves a single `gh api` PUT call to set branch protection rules and a PATCH call to enable repository-level auto-merge.

The critical technical detail is that GitHub Actions job names include emoji prefixes (e.g., `🔍 Lint & Static Analysis`), and these exact strings must be used as status check contexts in the API payload. The CONTEXT.md specifies requiring only the 4 main CI jobs from `ci.yml`, not the security-gate or other workflow jobs. The `checks` array format (with `context` and `app_id`) should be used instead of the deprecated `contexts` array.

**Primary recommendation:** Use a single `gh api` PUT call with the `checks` array format (app_id: -1 for any source) and `strict: true` for up-to-date requirement. Enable auto-merge via a separate `gh api` PATCH call to the repo endpoint. Create a shell script for reproducibility.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Require all 4 main CI jobs to pass: `lint`, `python-tests`, `security-scan`, `frontend-tests`
- Do NOT require optional/triggered workflows (`dast-scan.yml`, `claude.yml`, `asset-generation.yml`)
- Status check names must match the exact job names as they appear in GitHub Actions
- Enable GitHub auto-merge so agents can use `gh pr create` + auto-merge
- No admin bypass needed -- agents follow the same PR path as humans
- No required reviewers -- CI is the reviewer (per Out of Scope decision)
- Block direct pushes to main -- all changes must go through PRs
- Block force pushes to main -- prevent history rewriting
- Use classic GitHub branch protection rules (not rulesets)
- Configure via `gh api` for automation -- no manual GitHub UI steps
- Require branches to be up-to-date with main before merge (PR-02)

### Claude's Discretion
- Exact `gh api` payload structure for setting branch protection
- Whether to use strict or non-strict up-to-date requirement
- Error handling approach if API call fails

### Deferred Ideas (OUT OF SCOPE)
- PROT-03 (auto-rollback on failed health check) -- v2 requirement
- PROT-04 (agent-aware hook messaging) -- v2 requirement
- PROT-05 (automatic theme version bump) -- v2 requirement
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PR-01 | All CI status checks required to pass before PR can merge to main | Branch protection `required_status_checks` with exact check-run names verified from live CI runs; `checks` array format with `app_id: -1` |
| PR-02 | PR branch must be up-to-date with main before merge is allowed | `required_status_checks.strict: true` enforces this; requires re-running CI after rebasing |
</phase_requirements>

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| `gh` CLI | 2.x (installed) | GitHub API interaction | Already authenticated, simpler than raw curl |
| GitHub REST API | 2022-11-28 | Branch protection PUT endpoint | Stable, well-documented |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `gh api` | REST API calls with auth | All branch protection and repo settings |
| `gh pr merge --auto` | Agent auto-merge workflow | Post-protection for agents to merge PRs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Classic branch protection | GitHub rulesets | Rulesets are newer/more flexible but more complex -- classic is sufficient for single-repo |
| `gh api` | Raw `curl` with token | `gh` handles auth automatically, less error-prone |
| Shell script | Terraform/Pulumi | Infrastructure-as-code overkill for a single repo |

## Architecture Patterns

### Recommended Approach
```
scripts/
  setup-branch-protection.sh    # Idempotent protection setup script
```

This is a configuration-only phase. There are no new source files, tests, or application code. The deliverable is a shell script that configures GitHub and can be re-run safely.

### Pattern 1: Idempotent Configuration Script
**What:** A shell script that sets all branch protection rules and repo settings in one pass
**When to use:** Any time branch protection needs to be (re)applied or verified
**Example:**
```bash
#!/usr/bin/env bash
set -euo pipefail

OWNER="The-Skyy-Rose-Collection-LLC"
REPO="DevSkyy"
BRANCH="main"

# Step 1: Enable auto-merge on the repository
gh api --method PATCH "repos/$OWNER/$REPO" \
  -f allow_auto_merge=true

# Step 2: Set branch protection rules
gh api --method PUT "repos/$OWNER/$REPO/branches/$BRANCH/protection" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      {"context": "\ud83d\udd0d Lint & Static Analysis", "app_id": -1},
      {"context": "\ud83d\udc0d Python Tests", "app_id": -1},
      {"context": "\ud83d\udd10 Security Scan", "app_id": -1},
      {"context": "\u269b\ufe0f Frontend Tests", "app_id": -1}
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

### Pattern 2: Verification After Configuration
**What:** Verify protection was applied by reading it back
**When to use:** Immediately after setting protection, and in CI if desired
**Example:**
```bash
# Verify protection is set
gh api "repos/$OWNER/$REPO/branches/$BRANCH/protection" \
  --jq '.required_status_checks.checks[].context'
```

### Anti-Patterns to Avoid
- **Manual GitHub UI configuration:** Not reproducible, not auditable, easily changed accidentally
- **Using deprecated `contexts` array:** Use `checks` array with `app_id` instead
- **Setting `enforce_admins: false`:** Would allow admins to bypass protection, defeating the purpose
- **Requiring too many status checks:** Only require the 4 core CI jobs; other workflows (CodeQL, security-gate) are informational

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Branch protection | Custom webhook + merge bot | GitHub branch protection API | Native enforcement, no maintenance |
| Auto-merge | Custom polling script | `gh pr merge --auto --squash` | Built-in, handles edge cases |
| Status check matching | String matching logic | GitHub's built-in check matching | Handles unicode/emoji correctly |

**Key insight:** This entire phase is configuration of existing GitHub features. There is zero custom code to write beyond a setup script.

## Common Pitfalls

### Pitfall 1: Status Check Name Mismatch
**What goes wrong:** Required status checks don't match the names GitHub reports, so they appear as "Expected" but never resolve, blocking all merges permanently.
**Why it happens:** Job names in ci.yml include emoji prefixes. The `name:` field in the workflow YAML (not the job ID) is the status check context. For example, the job ID is `lint` but the check name is `🔍 Lint & Static Analysis`.
**How to avoid:** Use the exact names from `gh api repos/{owner}/{repo}/commits/{sha}/check-runs --jq '.check_runs[].name'`
**Warning signs:** PRs stuck with "Expected -- Waiting for status to be reported" that never resolves.

### Pitfall 2: Skipped Workflows Block Merges
**What goes wrong:** If a required check's entire workflow is skipped (via path filtering or branch filtering), the check stays in "Pending" state permanently, blocking merge.
**Why it happens:** GitHub distinguishes between a workflow being skipped (check never created) and a job being skipped within a workflow (reports as "Success"). If the workflow never triggers, the required check is never reported.
**How to avoid:** Only require checks from workflows that trigger on `pull_request` to `main`. The 4 CI jobs from `ci.yml` always trigger on PRs to main -- confirmed in the workflow definition.
**Warning signs:** PR checks page shows a required check as "Expected" with no run link.

### Pitfall 3: Auto-Merge Requires Branch Protection
**What goes wrong:** `gh pr merge --auto` fails or merges immediately without waiting for checks.
**Why it happens:** Auto-merge only works when branch protection rules are enabled. Without required checks, there is nothing to wait for.
**How to avoid:** Enable branch protection BEFORE enabling auto-merge. The setup script must set protection first, then enable auto-merge.
**Warning signs:** `gh pr merge --auto` returns an error about auto-merge not being available.

### Pitfall 4: Strict Up-to-Date Requirement Creates Merge Bottleneck
**What goes wrong:** With `strict: true`, every PR must be updated after another PR merges, causing a serialization bottleneck.
**Why it happens:** `strict: true` means the PR branch must include all commits from main before CI results are valid. If PR-A merges, PR-B must rebase and re-run CI.
**How to avoid:** Accept this tradeoff -- it is what PR-02 requires. The repo has low PR volume (agents create PRs, not a large team), so the bottleneck is manageable.
**Warning signs:** Multiple PRs waiting in sequence; CI runs doubling. Only a concern if PR volume is high.

### Pitfall 5: Unicode/Emoji in API Payloads
**What goes wrong:** JSON payload with emoji characters gets corrupted or doesn't match.
**Why it happens:** Shell heredocs, pipes, or encoding issues can mangle multi-byte unicode characters.
**How to avoid:** Use `gh api --input -` with a heredoc or `--input file.json` to pass the JSON body. Avoid `echo` or `-f` flag for multi-byte strings.
**Warning signs:** Protection API returns success but check names don't match.

### Pitfall 6: enforce_admins Interaction
**What goes wrong:** Admin users can bypass protection if `enforce_admins` is false.
**Why it happens:** By default, admins can force-merge even when checks fail.
**How to avoid:** Set `enforce_admins: true` so even the repo owner follows the same rules.
**Warning signs:** Admin pushes directly to main or merges without passing checks.

## Code Examples

Verified patterns from live repo data:

### Exact Status Check Names (from live CI runs)
```
Check-run names (context values for API):
1. "🔍 Lint & Static Analysis"     (ci.yml job: lint)
2. "🐍 Python Tests"                (ci.yml job: python-tests)
3. "🔐 Security Scan"              (ci.yml job: security)
4. "⚛️ Frontend Tests"             (ci.yml job: frontend-tests)

GitHub Actions app_id: 15368
```

### Enable Auto-Merge on Repository
```bash
# Source: GitHub REST API docs
gh api --method PATCH "repos/The-Skyy-Rose-Collection-LLC/DevSkyy" \
  -f allow_auto_merge=true
```

### Set Branch Protection (Full Payload)
```bash
# Source: GitHub REST API - PUT /repos/{owner}/{repo}/branches/{branch}/protection
gh api --method PUT \
  "repos/The-Skyy-Rose-Collection-LLC/DevSkyy/branches/main/protection" \
  --input - <<'PAYLOAD'
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      {"context": "🔍 Lint & Static Analysis", "app_id": -1},
      {"context": "🐍 Python Tests", "app_id": -1},
      {"context": "🔐 Security Scan", "app_id": -1},
      {"context": "⚛️ Frontend Tests", "app_id": -1}
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
PAYLOAD
```

### Read Back Protection (Verification)
```bash
# Verify protection was applied
gh api "repos/The-Skyy-Rose-Collection-LLC/DevSkyy/branches/main/protection" \
  --jq '{
    required_checks: .required_status_checks.checks,
    strict: .required_status_checks.strict,
    enforce_admins: .enforce_admins.enabled,
    allow_force_pushes: .allow_force_pushes.enabled
  }'
```

### Agent Workflow (Post-Protection)
```bash
# Agent creates PR and enables auto-merge
git checkout -b feat/my-change
# ... make changes, commit ...
git push -u origin feat/my-change
gh pr create --title "feat: my change" --body "Description"
gh pr merge --auto --squash --delete-branch
# PR will auto-merge once all 4 required checks pass
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `contexts` array (strings) | `checks` array (objects with context + app_id) | 2022 | `contexts` deprecated; `checks` allows source filtering |
| Classic branch protection | GitHub Rulesets | 2023 | Rulesets are more flexible but classic is simpler for single-repo |
| Manual merge after CI | `gh pr merge --auto` | 2021 | Agents can fire-and-forget; PR merges when checks pass |

**Deprecated/outdated:**
- `required_status_checks.contexts` array: Deprecated in favor of `checks` array. Still works but should not be used for new configurations.

## Open Questions

1. **Emoji encoding in heredocs**
   - What we know: `gh api --input -` with heredoc should handle UTF-8 correctly on macOS and Linux.
   - What's unclear: Whether the specific emoji characters (🔍, 🐍, 🔐, ⚛️) survive the heredoc-to-stdin pipe in all environments.
   - Recommendation: Test with a dry-run read-back immediately after setting protection. If encoding fails, fall back to `--input file.json` with an explicit UTF-8 file.

2. **Strict mode + agent PR volume**
   - What we know: `strict: true` serializes merges (each PR must rebase after another merges). Current agent volume is low.
   - What's unclear: Whether agent workflows (Ralph, Claude Code) already handle rebase-on-conflict gracefully.
   - Recommendation: Use `strict: true` as required by PR-02. Monitor for merge bottlenecks. Switch to `false` if it becomes a problem (but this would violate PR-02).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Shell script + `gh api` verification |
| Config file | None -- pure API configuration |
| Quick run command | `gh api repos/{owner}/{repo}/branches/main/protection --jq '.required_status_checks.checks[].context'` |
| Full suite command | `scripts/setup-branch-protection.sh && gh api repos/{owner}/{repo}/branches/main/protection` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PR-01 | CI status checks required before merge | smoke | `gh api repos/{owner}/{repo}/branches/main/protection --jq '.required_status_checks.checks \| length'` (expect 4) | No -- Wave 0 |
| PR-02 | Branch must be up-to-date before merge | smoke | `gh api repos/{owner}/{repo}/branches/main/protection --jq '.required_status_checks.strict'` (expect true) | No -- Wave 0 |

### Additional Verification Tests
| Behavior | Test Type | Automated Command |
|----------|-----------|-------------------|
| Direct push blocked | smoke | `gh api repos/{owner}/{repo}/branches/main/protection --jq '.enforce_admins.enabled'` (expect true) |
| Force push blocked | smoke | `gh api repos/{owner}/{repo}/branches/main/protection --jq '.allow_force_pushes.enabled'` (expect false) |
| Auto-merge enabled | smoke | `gh api repos/{owner}/{repo} --jq '.allow_auto_merge'` (expect true) |
| No required reviewers | smoke | `gh api repos/{owner}/{repo}/branches/main/protection --jq '.required_pull_request_reviews'` (expect null) |

### Sampling Rate
- **Per task commit:** Read back protection settings via `gh api`
- **Per wave merge:** Full verification of all protection settings
- **Phase gate:** All smoke checks pass before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `scripts/setup-branch-protection.sh` -- the setup script itself (to be created)
- [ ] Verification commands documented above -- to be run after setup

## Sources

### Primary (HIGH confidence)
- Live `gh api repos/{owner}/{repo}/commits/main/check-runs` -- exact check-run names with emoji and app_id=15368
- Live `gh api repos/{owner}/{repo}/branches/main/protection` -- confirmed 404 (no current protection)
- Live `gh api repos/{owner}/{repo}` -- confirmed `allow_auto_merge: false`
- `.github/workflows/ci.yml` -- verified 4 jobs with `name:` fields matching check-run names
- `gh pr merge --help` -- confirmed `--auto` flag behavior

### Secondary (MEDIUM confidence)
- [GitHub REST API - Branch Protection](https://docs.github.com/en/rest/branches/branch-protection) -- PUT endpoint, `checks` array format, `enforce_admins` parameter
- [GitHub Troubleshooting Required Status Checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks) -- skipped workflow pitfall, 7-day check history requirement
- [GitHub Auto-Merge Docs](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request) -- prerequisites, interaction with branch protection
- [GitHub Managing Auto-Merge](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-auto-merge-for-pull-requests-in-your-repository) -- repository-level setting, write permissions required

### Tertiary (LOW confidence)
- None -- all findings verified against live repo data or official docs.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- `gh` CLI is already in use; REST API endpoints are stable and documented
- Architecture: HIGH -- pure API configuration, no architectural decisions needed
- Pitfalls: HIGH -- status check names verified from live CI runs; skipped-workflow pitfall confirmed in official docs
- Code examples: HIGH -- exact check-run names extracted from live repo data

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (stable -- GitHub branch protection API has been unchanged for 2+ years)
