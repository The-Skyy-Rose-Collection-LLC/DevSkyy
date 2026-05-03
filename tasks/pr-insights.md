# PR Insights Report — DRY-RUN
**Generated:** 2026-04-29 | **Scope:** 50 open PRs analyzed

---

## Recurring Failure Modes

### 1. Universal CI Failure (48 of 48 dependabot PRs + 2 of 2 human PRs)
Every PR in the repo has failing CI. The failures are identical across PRs:
- `🔍 Lint & Static Analysis` — fails on all
- `🔑 Secrets Scan` — fails on all
- `📦 Dependency Review` — fails on all
- `CodeQL (python, javascript-typescript, actions)` — fails on all

**Pattern:** All failures complete in under 30 seconds. This is not a "tests ran and failed" pattern — this is a "workflow infrastructure error" pattern. Most likely causes:
- A required secret (e.g., `GITHUB_TOKEN` scope, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`) is misconfigured in repo settings
- A `.github/workflows/*.yml` change in a recent commit broke the shared workflow infrastructure
- A CodeQL version bump made the analysis jobs fail on language detection

**Evidence:** PR #411 (`actions/cache` bump) has **clean CI** — it's a GitHub Actions-only change that never triggers the Python/Node workflow paths. This suggests the code-path workflows (lint, secrets scan, CodeQL) share a broken config that GitHub's own Action workflows don't use.

### 2. Secrets Scan False Positives or Real Leak
`🔑 Secrets Scan` fails on every PR including pure dependency bumps with no source code changes. Either:
- The scan is misconfigured (scanning node_modules or .venv dirs), OR
- There is a real secret committed to the repo that every PR diff triggers a scan on

**Action required:** Run `git log -10 --all --full-diff -- "*.env" "**/.env*" "*.key" "*.pem"` and audit the secrets scan config in `.github/workflows/security-gate.yml`.

### 3. Dependabot PR Storm Without Grouping
48 open dependabot PRs for a 2-person (SkyyRoseLLC is the only human committer) repository. This volume:
- Obscures real security patches in the noise
- Makes `git log --oneline` unusable
- Creates merge conflict risk as packages update multiple times before any PR is merged

The same package bumped multiple times across workspaces creates duplicate PRs (e.g., Pillow has 3 separate PRs: #451, #452, #456 for root, /skyyrose, /mcp_servers). This is solved with dependabot grouped updates.

### 4. `claude-review` Workflow Failing on All PRs
`claude-review` (Claude Code Review workflow) fails on every PR. If this is a required check, it single-handedly blocks all merges. Check `.github/workflows/claude-code-review.yml` — likely missing the `ANTHROPIC_API_KEY` secret in the repo's Actions secrets.

---

## Author Patterns

| Author | Open PRs | Blocked | Pattern |
|--------|----------|---------|---------|
| SkyyRoseLLC | 2 | 2 (CI) | Both opened today (Apr 29). #468 is active work. #467 may be superseded. |
| app/dependabot | 48 | 48 (CI) | Accumulating since day ~37 ago. No merges happening. |

**Single-author risk:** The entire repo is driven by one human (SkyyRoseLLC). No peer review on any PR. No approvals exist. This means the "NEEDS_REVIEW" safeguard is theoretical — in practice, self-merge is the only option.

**Recommendation:** Add at minimum a 1-person required review from a trusted reviewer (or use the Claude Code Review bot properly if the secret is fixed).

---

## Dependency Cluster Opportunities

### Pillow (3 PRs → 1 PR)
- #451: root workspace, 11.0.0→12.2.0
- #452: /skyyrose, 12.1.1→12.2.0
- #456: /mcp_servers, 12.1.1→12.2.0

These should be one grouped PR. Close #452 and #456, keep #451 (largest jump, most security coverage).

### protobufjs (2 PRs → 1 PR)
- #457: /frontend
- #464: /skyyrose

Close one; squash-merge the other after CI fix.

### axios (2 PRs → 1 PR)
- #446: root
- #447: /skyyrose

### defu (2 PRs → 1 PR)
- #426: /skyyrose
- #427: root

### flatted (2 PRs → 1 PR)
- #417: (older)
- #463: (newer)
Close #417, keep #463.

### next (2 PRs → 1 PR)
- #409: 16.1.6→16.2.1 (36 days old)
- #443: 16.1.3→16.2.3 (19 days old)
Close #409 (lower target version), keep #443.

### langchain ecosystem (3 PRs → batch)
- #418: langchain-core
- #437: langchain
- #439: langchain-openai

Enable grouping in `.github/dependabot.yml` under `pip` ecosystem to collapse this automatically.

---

## Recommendations for Repo-Level Changes

### Immediate (before lifting dry-run)

1. **Audit Secrets Scan** — determine if `🔑 Secrets Scan` is flagging a real committed secret or a config error. Run GitGuardian locally: `ggshield secret scan repo .`
2. **Fix Claude Code Review secret** — add `ANTHROPIC_API_KEY` to GitHub Actions secrets (Settings → Secrets → Actions). The `claude-review` workflow failing on every PR is a systematic block.
3. **Check CodeQL config** — the `Analyze (actions)` and `Analyze (javascript-typescript)` jobs failing in under 5 seconds indicates a language detection or permissions issue in `.github/workflows/codeql.yml`.

### Short-term (within 1 week)

4. **Enable dependabot grouped updates** — add to `.github/dependabot.yml`:
   ```yaml
   groups:
     python-dependencies:
       patterns: ["*"]
     npm-dependencies:
       patterns: ["*"]
   ```
   This collapses the current 48-PR storm to ~5 PRs.

5. **Add branch protection on `main`** — require: (a) at least 1 approved review, (b) CI passing. Currently `main` has no merge gatekeeping.

6. **Close superseded dependabot PRs** — at least 6 pairs of duplicate workspace bumps exist. Close the older/lower-target-version PR in each pair.

### Strategic

7. **Consider Renovate Bot** as a dependabot replacement — Renovate has native grouping, semantic version awareness, and auto-merge rules. For a 1-developer repo with 48 open dependabot PRs, this is worth the setup cost.

8. **Require PR descriptions** — #467 has no body text. For a production commercial codebase, at minimum a 2-sentence summary should be required.

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total open PRs | 50 |
| Human PRs | 2 |
| Dependabot PRs | 48 |
| SAFE_MERGE eligible | 0 |
| CI green | 1 (PR #411 only) |
| PRs with security-relevant deps | 14 |
| Duplicate workspace bumps (closeable) | 6 pairs |
| Days without a merge (est.) | ~37 days |

---

*DRY-RUN: No actions were taken. All observations are read-only from `gh pr list` and `gh pr view`.*
