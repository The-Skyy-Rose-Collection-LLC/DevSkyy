# PR Action Plan — DRY-RUN
**Generated:** 2026-04-29 | **Status:** DRY-RUN — no actions have been taken

> This document describes what WOULD execute if `--dry-run` were lifted.
> Current blocker: CI is failing on every single PR in the repository.
> **Fix CI first. Nothing else can proceed safely until CI is green.**

---

## Step 0 — PREREQUISITE: Fix CI (blocks everything else)

**What's wrong:** Both human PRs (#467, #468) and 47 of 48 dependabot PRs are failing CI. The failures start at the earliest workflow jobs (`🔍 Lint & Static Analysis`, `🔑 Secrets Scan`, `CodeQL`) which suggests a CI config regression rather than per-PR code failures. Cascading failures then knock out every downstream job.

**Action before lifting dry-run:**
1. Push a CI-only fix branch. Verify CI goes green on `main`.
2. Check whether `🔑 Secrets Scan` is detecting a real secret or misconfigured. If real: rotate immediately, fix, re-push.
3. Re-run failed checks on #467 and #468 after the CI fix lands on main.

**Risk:** HIGH — merging anything before CI is fixed could land broken code or masked secrets.

---

## Priority 1 — Security Patches (fast-track after CI fixed)

| PR | Action | Justification | Risk |
|----|--------|---------------|------|
| #459 | `gh pr merge 459 --squash` | `cryptography` security group bump — likely CVE fixes in the Python crypto library | LOW (dep-only) |
| #451 | `gh pr merge 451 --squash` | Pillow 11.0→12.2 — large jump, covers multiple known image processing CVEs | LOW (dep-only) |
| #425 | `gh pr merge 425 --squash` | `tar` 7.5.6→7.5.13 — tar has documented path traversal CVE history | LOW (dep-only) |
| #416 | `gh pr merge 416 --squash` | `socket.io-parser` 4.2.5→4.2.6 — ReDoS/prototype pollution history | LOW (dep-only) |
| #411 | `gh pr merge 411 --squash` | `actions/cache` bump — the **only** PR with clean CI right now; low risk GitHub Actions dep | LOW |

*Gate: confirm Secrets Scan is passing before merging any of these.*

---

## Priority 2 — Verify and Close Possible Duplicate (#467)

| PR | Action | Justification | Risk |
|----|--------|---------------|------|
| #467 | Investigate, then `gh pr close 467` with comment | Commits `b72bb4cc8`, `79f07ad86`, `9049ad885` on `main` all reference "vision-audit stage-1.5 hardening" — this work may already be merged. Run `git log --oneline main..fix/vision-audit-stage-15-hardening` to confirm delta. If empty: close with "Superseded by direct commits to main." | LOW |

---

## Priority 3 — Human PR Review (#468)

| PR | Action | Justification | Risk |
|----|--------|---------------|------|
| #468 | Do NOT auto-merge — requires human review | This is the user's just-opened Phase B2-C3 PR. 128 tests passing locally per PR body. 390 files changed (+28k / -4k lines). Needs: (a) CI to go green, (b) human code review, (c) explicit merge decision. | HIGH |

*Gate: CI green + explicit user approval.*

---

## Priority 4 — Dependabot Batch Strategy

The 48 dependabot PRs should be collapsed into batches by ecosystem + workspace. Suggested batches:

### Batch A — Security (handle individually, not grouped)
PRs: #459, #451, #452, #456 (Pillow), #464, #457 (protobufjs), #447, #446 (axios), #425 (tar), #421 (node-forge), #420 (path-to-regexp), #419 (handlebars), #416 (socket.io-parser), #412 (tornado)

Action: Close duplicates (e.g., keep highest-numbered Pillow PR, close earlier ones). Merge individually after CI fix.

### Batch B — Python ML / AI deps
PRs: #439 (langchain-openai), #437 (langchain), #418 (langchain-core), #436 (torch), #438 (onnxruntime), #435 (psutil), #424 (bentoml), #414 (pyasn1), #401 (faiss-cpu)

Action: Enable dependabot grouped PRs for `pip` ecosystem in `.github/dependabot.yml` to auto-consolidate future bumps. Merge current batch as one squash after CI fix.

### Batch C — npm / frontend deps
PRs: #443, #409 (next), #463, #417 (flatted), #462 (basic-ftp), #461 (mcp/sdk), #445 (simple-git), #440, #441 (vite), #422 (rollup), #408 (webpack-cli), #410 (vite-plugin-react), #407 (lucide-react), #406 (speed-insights), #405 (rate-limiter), #404 (@wordpress/env), #427, #426 (defu)

Action: Enable dependabot grouped PRs for `npm` in `.github/dependabot.yml`. Close stale duplicates.

### Batch D — Actions workflow deps
PR: #411 (actions/cache) — already has clean CI; merge standalone.

### Batch E — /skyyrose workspace npm
PRs: #464, #455, #454, #442, #441, #447 — same workspace, batch together.

---

## Priority 5 — Stale PR Strategy

No PRs exceed 60 days old yet (oldest is 37 days). Revisit at 60-day mark if unmerged.

Dependabot PRs older than 30 days that are superseded by newer bumps of the same package should be closed:
- #409 (next 16.1.6→16.2.1) superseded by #443 (next 16.1.3→16.2.3) — close #409
- #417 (flatted) superseded by #463 — close #417
- #426 (defu /skyyrose) may overlap with #427 — verify and close one

---

## Recommended Repo-Level Changes (lift dry-run to implement)

1. **Enable dependabot grouped updates** in `.github/dependabot.yml` — this eliminates the 48→1 ratio problem.
2. **Add branch protection rule** requiring at least 1 approval + CI green before merge on `main`.
3. **Investigate CI root cause** — the pattern of every workflow failing on the same PR suggests a shared secret or env var that CI is unable to resolve.

---

*DRY-RUN: No `gh pr merge`, `gh pr close`, `gh pr review --approve`, or `git push` commands were executed.*
