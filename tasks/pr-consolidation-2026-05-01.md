# Repo-Wide PR Consolidation — 2026-05-01

> Refresh of `tasks/pr-action-plan.md` (2026-04-29) and `tasks/pr-insights.md`.
> Prior plan stands. State has barely moved in 2 days.

---

## State change since 2026-04-29

| Metric | Apr 29 | May 1 | Δ |
|---|---|---|---|
| Open PRs | 50 | **60** | +10 |
| Human PRs open | 2 | 1 (#468) | #467 merged |
| Dependabot PRs open | 48 | 57 | +9 (new weekly bumps) |
| Dupe-pair PRs identified | 6 pairs / 13 PRs | **6 pairs / 13 PRs (all still open)** | 0 closed |
| CI globally broken | Yes | **Still yes** | Unchanged |

The merge throughput is essentially zero. The April 29 plan correctly identified the cause: every workflow fails before any per-PR code is even touched.

---

## Step 0 — The blocker hasn't moved

Every workflow fails on every PR, including ones that should be no-ops:

- A `cryptography` Python bump (#459) fails `🎮 Three.js Tests`, `🏗️ WordPress Theme`, `⚛️ Frontend Tests` — none of which read Python deps.
- The current feature PR (#468) fails the same checks plus `Analyze (actions)`, `Analyze (javascript-typescript)`, `Analyze (python)` from the **separate top-level CodeQL workflow** that re-runs alongside Security Gate's CodeQL job.

**Diagnosis (high confidence):** workflow-infrastructure regression, not code. The signature is:

1. Same checks fail on every PR, regardless of language scope of the diff.
2. PR #411 (`actions/cache` bump) is the **only** green PR — and it's the only one that doesn't trigger the language-path workflows.
3. Failures complete in <30s — too fast to be real test runs.

**Most likely root cause(s)** — all should be checked in this order:

1. **Missing/expired `ANTHROPIC_API_KEY`** — `claude-review` workflow fails on every PR. Settings → Secrets → Actions.
2. **Duplicate CodeQL invocations** — PR #468 shows `Analyze (python)` listed twice plus `🔬 CodeQL Analysis (python)`. Two separate CodeQL workflows are racing; one likely fails because the other holds the language lock.
3. **Secrets Scan misconfig** — runs against every PR but fails in <10s. Likely scanning a path that was deleted (e.g., the recently-removed `assets/models/skyy-*.glb` blobs that show as `D` in `git status`) or a missing tool binary.

---

## Action plan — phased

### Phase 1 — Unblock CI (no merges before this lands)

Goal: get **at least one** dependency-only PR (e.g., #459) to green before consolidating anything.

```bash
# Branch off main
git fetch origin main && git checkout -b fix/ci-unblock origin/main

# Audit secret presence
gh secret list

# Inspect each broken workflow file
ls .github/workflows/
# Read claude-code-review.yml, security-gate.yml, codeql.yml
```

Specific things to check:

- [ ] `ANTHROPIC_API_KEY` exists and isn't expired
- [ ] `.github/workflows/codeql.yml` and `.github/workflows/security-gate.yml` aren't both running CodeQL on the same languages
- [ ] Secrets-scan job's tool/config (likely `gitleaks` or `trufflehog`) — verify the binary install step still works on `ubuntu-latest`
- [ ] `🏗️ WordPress Theme` job — likely failing because of a missing PHPCS/Composer step after the recent theme refactor

Acceptance: a trivial CI-only commit on `fix/ci-unblock` should produce green checks. **Do not lift any merge gate until #411 is no longer the only green PR.**

### Phase 2 — Close superseded duplicates (zero-risk, do before fixing CI)

These can be closed right now without touching CI — `gh pr close` doesn't require checks to pass. **All 6 pairs are still open from the Apr 29 analysis.**

```bash
# Each "keep" listed below is the higher-version-target PR
gh pr close 452 -c "Superseded by #451 (root, 11.0→12.2 covers wider security gap)."
gh pr close 456 -c "Superseded by #451."
gh pr close 457 -c "Superseded by #464 (consolidating protobufjs to /skyyrose workspace)."
gh pr close 447 -c "Superseded by #446 (root axios bump)."
gh pr close 426 -c "Superseded by #427 (root defu bump)."
gh pr close 417 -c "Superseded by #463 (newer flatted bump)."
gh pr close 409 -c "Superseded by #443 (next 16.2.3 > 16.2.1)."
```

Net effect: 60 → 53 open PRs, no CI work required.

### Phase 3 — Once CI is green: priority merge order

Same priority list as the Apr 29 plan. Reproduced here for one-stop reference.

1. **Security**: #459 (cryptography group), #451 (Pillow 11→12), #425 (tar), #416 (socket.io-parser), #421 (node-forge), #420 (path-to-regexp), #419 (handlebars).
2. **GitHub Actions** (smallest blast radius): #411, #389, #388, #374.
3. **Dev-only deps**: #408 (webpack-cli, dev), #423 (linting group), #404 (@wordpress/env, dev), #462 (basic-ftp, dev).
4. **Python framework bumps** (after dev-only): #436 (torch — biggest jump, watch for breakage), #437/#418/#439 (langchain trio), #399 (pydantic-settings), #438 (onnxruntime).
5. **NPM major-version-adjacent**: #443 (next 16.2.3), #410 (vitejs/plugin-react 5→6), #406 (@vercel/speed-insights 1→2), #405 (rate-limiter-flexible 9→10), #407 (lucide-react 0→1), #383 (vite 7→8 — **major, hold until last**).

After each merge, dependabot should auto-rebase the rest. Re-check mergeability on remaining ones every 5 merges.

### Phase 4 — PR #468 (the active feature)

This is the only human PR. Stats: 392 files, +28,601 / −4,087, 22 commits, currently `MERGEABLE / UNSTABLE` against main.

**Recommendation:** do NOT block on the dependabot consolidation. Once Phase 1 unblocks CI, this PR should land first — every dependabot bump rebased on top is a fresh clean diff, but a 392-file feature PR rebased through 30+ dep bumps is a merge-conflict factory.

Order to land:
1. CI fix branch → main
2. PR #468 → main
3. Phase 2 closes (already done by then)
4. Phase 3 dependabot merges in priority order

### Phase 5 — Stop the leak

The 60-PR backlog accumulated because the dependabot grouping config doesn't dedupe across **directories**. The current `.github/dependabot.yml` only declares each ecosystem at `directory: "/"`, but Dependabot is auto-creating PRs for `/skyyrose`, `/frontend`, `/mcp_servers` (proven by branch names like `dependabot/pip/skyyrose/pillow-12.2.0`). Result: 3 separate Pillow PRs for one upgrade.

Fix using Dependabot v2 multi-directory groups:

```yaml
# .github/dependabot.yml — add these directories explicitly
- package-ecosystem: "pip"
  directories:           # plural, supports list
    - "/"
    - "/skyyrose"
    - "/mcp_servers"
  groups:
    all-python:          # single group across all directories
      patterns: ["*"]
      update-types: ["minor", "patch"]
    security-python:
      applies-to: security-updates
      patterns: ["*"]
```

Apply the same `directories: [...]` + `groups` pattern to npm (root, /frontend, /skyyrose). After this lands, Dependabot will collapse the next Tuesday's npm storm to ~3 PRs (one per group), not ~25.

---

## Catalog of duplicates and supersession

(Same as Apr 29 — none have closed. Including for command convenience.)

| Pair | Keep | Close | Reason |
|---|---|---|---|
| Pillow | #451 (root, 11.0→12.2) | #452, #456 | Largest jump, broadest CVE coverage |
| protobufjs | #464 (/skyyrose) | #457 | Same version, /skyyrose is the active workspace |
| axios | #446 (root) | #447 | Root takes precedence; /skyyrose is downstream |
| defu | #427 (root) | #426 | Root takes precedence |
| flatted | #463 (/frontend, newer) | #417 | Newer, /frontend is the active surface |
| next | #443 (16.2.3) | #409 | Higher version target |

---

## Numbers at a glance

| Bucket | Count | Action |
|---|---|---|
| Total open | 60 | |
| Will be closed in Phase 2 | 7 | `gh pr close` (zero risk) |
| Security patches (Phase 3a) | 7 | Merge first after CI green |
| GH Actions (Phase 3b) | 5 | Merge second |
| Dev deps (Phase 3c) | 4 | Merge third |
| Framework deps (Phase 3d/3e) | 17+ | Merge with monitoring |
| Lockfile-only large diffs | 16 | Squash-merge in batches; rebase in between |
| Active feature PR | 1 (#468) | Land first after CI fix |

---

*Generated 2026-05-01. Read-only analysis; no `gh` write commands have been run from this session.*
