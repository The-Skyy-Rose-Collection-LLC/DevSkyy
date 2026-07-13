# PR Action Plan — DRY-RUN
**Generated:** 2026-06-30 | **Mode:** audit --dry-run — NOTHING EXECUTED

---

## Immediate Actions (no conflicts, proceed in order)

### 1. Merge #650 first — cleanest PR, all CI green
- **Action:** Merge to main
- **Why:** Every check passes (Python, Frontend, WordPress, API, CodeQL, Secrets, License). Standalone LoRA API router, no conflicts with anything else.
- **Risk:** LOW

### 2. Resolve Vercel systemic failure BEFORE merging anything else
- **Action:** Debug Vercel build (NOT per-PR — it fails on all 30 PRs)
- **Likely cause:** Vercel project config, missing env var, or Next.js build error introduced somewhere on main
- **Method:** `npx vercel inspect dpl_<any-dpl-id> --logs` to read the actual error
- **Unblocks:** All subsequent merges that currently show "Vercel fail"

### 3. Close #685 — superseded, conflicting, GitGuardian fail
- **Action:** Close PR #685 (do NOT merge)
- **Why:** CONFLICTING with main, GitGuardian security check fails, and #689 is the clean replacement for the same feature (SOT image resolver)
- **Risk:** NONE — the work lives in #689

### 4. Close or reset #673 — Copilot-generated draft stub
- **Action:** Close PR #673
- **Why:** Draft, 0 additions, Copilot-generated CI/CD stub with no real content

---

## Stacked SOT/Catalog/Asset-Hub Family — Merge Order

This is the largest risk area: multiple PRs touch overlapping files (`functions.php`, product-card templates, `catalog.py`, `sot.json`). Merge order matters to avoid cascading conflicts.

```
RECOMMENDED MERGE ORDER (after Vercel is fixed + full CI runs):

  Step A: #645  feat(compositor): embeddings Phase 1 pipeline integrity
          └─ foundation for evaluation/embedding stack

  Step B: #648  fix(render): judge-unavailable QC → mandatory review
          └─ depends on #645 eval infrastructure

  Step C: #656  feat(evaluation): Q-mode wire + Q-data centroid allowlist
          └─ depends on #648 (Track Q series)

  Step D: #672  fix(collections): single-source sot.json drift guard
          └─ foundation for all SOT/catalog theme PRs

  Step E: #684  fix(catalog+theme): v7-cards/sot + badge invariant + V7 card
          └─ depends on #672 SOT guard being merged first

  Step F: #686  fix(catalog): canonical-loader routing + 5 invariants (Phase 2)
          └─ catalog hardening on top of #684

  Step G: #689  feat(theme): SOT-resolve product images + no-hardcoded gate
          └─ REPLACES #685; depends on #672 + #684 SOT foundation

  Step H: #687  refactor(embeddings): structlog event-name logging
          └─ standalone refactor, can go anytime after #645

  Step I: #690  docs(claude-md): scoped CLAUDE.md + Karpathy guidelines
          └─ pure docs, can merge any time; lowest risk
```

**Before any step D–G:** Verify full CI has run (Python + Frontend + WordPress checks must appear). These PRs currently only have Vercel + CodeRabbit checks — rebase against main or trigger CI manually.

---

## Standalone Feature PRs (order-independent)

| PR | Action | Notes |
|----|--------|-------|
| #668 | Merge after Secrets Scan investigation | Full CI green. Secrets Scan fail needs manual review (may be false positive from file:// paths in QC sheets) |
| #655 | Rebase + run full CI, then merge | V7 lookbook card — large change, no CI results beyond CodeQL |
| #688 | Rebase + run full CI, then merge | Agent SDK starter — large new module, needs full test run |

---

## Dependabot — Safe Batch (npm)

These can be merged together in one batch. All MERGEABLE, GitGuardian passes. The Vercel failure is systemic and unrelated.

**Batch 1 — safe/minor (merge immediately once Vercel is fixed):**
- #680 next 16.2.6→16.2.9 (patch)
- #678 sharp 0.34→0.35 (minor)
- #676 @types/node 25→26 (dev-only)
- #675 testing group 3 updates (dev-only)
- #674 three-js group 2 updates

**Batch 2 — major bumps (test after merge, watch for breaking changes):**
- #683 @ai-sdk/google-vertex 4→5 — Vercel AI SDK major; check provider API changes
- #682 @ai-sdk/cohere 3→4 — major; check model name changes
- #681 @pinecone-database/pinecone 7→8 — major; check index/query API changes
- #679 graphql 16→17 — major; check schema/AST API
- #677 pica 9→10 — image processing major

---

## Dependabot — Python (pip)

| PR | Action | Notes |
|----|--------|-------|
| #665 | Merge | All CI green, together >=2.19.0 |
| #659 | Merge after CI confirms | replicate >=1.0.7 — PR Agent infra fail only |
| #663 | Merge after CI confirms | numba 0.65 — PR Agent infra fail only |
| #666 | Merge after testing | usd-core >=26.5 — major version; test 3D pipeline |
| #662 | **INVESTIGATE** | Playwright E2E fail on torchvision bump — real test failure |

---

## Do NOT Merge

| PR | Reason |
|----|--------|
| #685 | CONFLICTING + GitGuardian fail + superseded by #689 |
| #673 | Draft, 0 additions, Copilot stub |
| #662 | Playwright E2E failure (real) |
