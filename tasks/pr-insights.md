# PR Insights — DRY-RUN
**Generated:** 2026-06-30 | **Mode:** audit --dry-run

---

## Systemic Issues (affect all PRs)

### 1. Vercel build is broken repo-wide
Every single open PR (all 30) shows "Vercel: fail". This is not a per-PR problem — it is a broken Vercel deployment configuration affecting the entire project. Until this is fixed, no PR can get a real Vercel preview or have deploy-gating checks pass.

**Impact:** High. Blocks confident merging of any PR that touches frontend/theme.
**Action:** Run `npx vercel inspect dpl_<id> --logs` on any PR's deployment ID to read the error. Fix on main before bulk-merging.

### 2. Full CI suite not running on PRs #672 and newer
PRs created from 2026-06-29 onward (including #672, #684, #685, #686, #687, #688, #689, #690) only triggered Vercel + CodeRabbit + GitGuardian — not the full GitHub Actions suite (Python Tests, Frontend Tests, WordPress Theme, API Integration Tests, CodeQL, Secrets Scan).

**Impact:** Medium-high. Cannot confirm these PRs don't break tests without a rebase or manual CI trigger.
**Action:** Rebase each NEEDS-CI PR against current main to trigger the full suite before merging.

### 3. PR Agent Analysis consistently fails (infra)
The "PR Agent Analysis" check fails on most PRs where it runs. This is an infrastructure/configuration issue with the pr-agent GitHub Action, not actual PR quality. Confirmed infra-level because high-quality PRs (#650, #656) fail this check while passing all real tests.

**Impact:** Low (this check is not gating). But it's noise that makes CI status harder to read.

---

## Duplicate Commits / Stacking Analysis

### The SOT/Catalog/Theme stack
The following PRs share a logical progression and likely have overlapping file changes:

```
#645 (embeddings Phase 1) 
  → #648 (judge-unavail QC fix) 
    → #656 (Q-mode wire)         [Track Q series]

#672 (collection SOT guard)      [SOT foundation — large, +6649 lines]
  → #684 (v7-catalog-sot)       [depends on 672 SOT infrastructure]
    → #686 (catalog hardening)  [Phase 2 on top of 684]
    → #689 (sot-image-resolver-clean) [theme side of 672]

#685 (sot-image-resolver)        [SUPERSEDED by #689 — close this]
```

**Stacking risk:** #684, #686, #689 were all created the same day (2026-06-30) within ~1 hour of each other, branching from similar points. If merged out of order, later PRs will conflict. Merge in order: 672 → 684 → 686 → 689.

**Overlap between #685 and #689:** Both modify the same SOT image resolution code in the WordPress theme. #685 is the larger original branch (CONFLICTING, +10945/-2668) and #689 is the clean rewrite (+219/-13). Merging #685 would create significant conflicts. It must be closed.

### The V7 Card family
#655 (V7 lookbook card, +3512/-2314) and #684 (v7-catalog-sot, +4507/-2390) both touch V7 card templates and theme files. #684 appears to be the more recent, more complete version. Relationship unclear — check if #684 supersedes #655 before merging both.

### Track Q series
#648 and #656 are sequentially tagged "Track Q" in the embeddings-reframe initiative. #648 should merge before #656.

---

## Risk Register

| Risk | Severity | Affected PRs | Mitigation |
|------|----------|-------------|-----------|
| Vercel build broken globally | HIGH | All 30 | Fix Vercel config on main first |
| No full CI on 10 feature PRs | HIGH | #672, #684–#690, #655 | Rebase to trigger CI |
| Merge order violations in SOT stack | HIGH | #684, #686, #689 | Enforce order: 672→684→686→689 |
| #685 supersedes conflict | HIGH | #685 | Close immediately |
| Playwright E2E fail on torchvision | MEDIUM | #662 | Investigate E2E failure before merge |
| Major npm deps (AI SDK, Pinecone, GraphQL) | MEDIUM | #679,#681,#682,#683 | Test API compatibility after merge |
| #673 Copilot stub adds no value | LOW | #673 | Close |
| PR Agent infra noise | LOW | Multiple | Fix PR Agent action config |

---

## Dependabot Batch Candidates

### Safe to merge as a batch (patch/minor/dev-only):
#680 (next patch) + #678 (sharp minor) + #676 (@types/node dev) + #675 (testing group) + #674 (three-js group)
→ All MERGEABLE, GitGuardian clean, no functional risk

### Major npm bumps — review individually:
#683 (@ai-sdk/google-vertex 4→5), #682 (@ai-sdk/cohere 3→4), #681 (pinecone 7→8), #679 (graphql 16→17), #677 (pica 9→10)
→ All MERGEABLE but each is a major version with potential breaking changes. Merge one-at-a-time and watch CI.

### Python pip deps:
#665 (together) — safe
#659 (replicate), #663 (numba) — safe pending CI
#666 (usd-core major) — test 3D pipeline after
#662 (torchvision) — blocked by Playwright E2E failure

---

## Notable Positive Signal

**PR #650** is the cleanest PR in the entire queue: every GitHub Actions check passes (Python, Frontend, WordPress, API Integration, CodeQL js+python, Secrets, License, SBOM, Dependency Review, Security Scan). It is standalone and touches only the `/api/v1/lora/*` router. This should be the first merge.

**PR #668** (current working branch: feat/glb-render-file-robust) has a complete green CI signal on all real tests. The two failures — "PR Agent Analysis" (infra) and "Secrets Scan" — are both non-real-test failures. The Secrets Scan result should be reviewed manually (file:// URIs in QC scripts may have triggered it) but is likely a false positive.
