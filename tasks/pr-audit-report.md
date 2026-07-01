# PR Audit Report — DRY-RUN
**Generated:** 2026-06-30 | **Mode:** audit --dry-run (read-only, nothing executed)
**Repo:** The-Skyy-Rose-Collection-LLC/DevSkyy

---

## Global Notes

- **Vercel deployment fails on every open PR** — this is a systemic Vercel build misconfiguration, not a per-PR fault. Do not treat Vercel failure as a blocker for individual PRs.
- **PR Agent Analysis** fails on most PRs (post-2026-06-26) — appears to be a GitHub Actions configuration issue unrelated to PR quality.
- **New PRs (#672+) did not trigger the full GitHub Actions CI suite** (Python, Frontend, WordPress, CodeQL, Secrets Scan) — only Vercel + CodeRabbit + GitGuardian ran. These PRs need rebase or manual trigger to get a full green CI signal.
- **UNKNOWN mergeable** = GitHub has not computed merge state yet (or branch is very old). Not the same as CONFLICTING.

---

## Per-PR Table

| # | Title | Category | Branch | Checks | Mergeable | Classification |
|---|-------|----------|--------|--------|-----------|----------------|
| #690 | docs(claude-md): scoped CLAUDE.md coverage + Karpathy guidelines | docs | docs/claude-md-coverage | Vercel FAIL (systemic), GG pass, CR pass | MERGEABLE | NEEDS-CI — no full CI suite run |
| #689 | feat(theme): resolve product images through SOT, no-hardcoded gate | feat | feat/sot-image-resolver-clean | Vercel FAIL (systemic), GG pass, CR pass | MERGEABLE | NEEDS-CI — no full CI suite run |
| #688 | feat(agent-sdk): SkyyRose commerce agent (Agent SDK starter) | feat | feat/agent-sdk-starter | Vercel FAIL (systemic), GG pass | MERGEABLE | NEEDS-CI — large (+1669) |
| #687 | refactor(embeddings): structlog event-name logging | refactor | refactor/embedding-engine-structlog | Vercel FAIL (systemic), GG pass, CR pass | MERGEABLE | NEEDS-CI — no full CI suite |
| #686 | fix(catalog): canonical-loader routing + 5 invariants (Phase 2) | fix | feat/catalog-hardening | Vercel FAIL (systemic), GG pass, CR disabled | MERGEABLE | NEEDS-CI — no full CI suite |
| #685 | feat(theme): SOT-resolve product images + asset-hub chain | feat | feat/sot-image-resolver | Vercel FAIL, **GitGuardian FAIL** | **CONFLICTING** | **BLOCKED** — conflicts + GitGuardian fail; superseded by #689 |
| #684 | fix(catalog+theme): single-source v7-cards/sot + V7 card | fix | feat/v7-catalog-sot | Vercel FAIL (systemic), GG pass, CR pass | MERGEABLE | NEEDS-CI — large (+4507/-2390) |
| #683 | deps: bump @ai-sdk/google-vertex 4→5 (major) | deps | dependabot/npm... | Vercel FAIL (systemic), GG pass | MERGEABLE | DEPS — major bump, API-breaking |
| #682 | deps: bump @ai-sdk/cohere 3→4 (major) | deps | dependabot/npm... | Vercel FAIL (systemic), GG pass | MERGEABLE | DEPS — major bump |
| #681 | deps: bump @pinecone-database/pinecone 7→8 (major) | deps | dependabot/npm... | Vercel FAIL (systemic), GG pass | MERGEABLE | DEPS — major bump |
| #680 | deps: bump next 16.2.6→16.2.9 (patch) | deps | dependabot/npm... | Vercel FAIL (systemic), GG pass | MERGEABLE | DEPS — patch, safe |
| #679 | deps: bump graphql 16→17 (major) | deps | dependabot/npm... | Vercel FAIL (systemic), GG pass | MERGEABLE | DEPS — major bump |
| #678 | deps: bump sharp 0.34→0.35 (minor) | deps | dependabot/npm... | Vercel FAIL (systemic), GG pass | MERGEABLE | DEPS — minor, safe |
| #677 | deps: bump pica 9→10 (major) | deps | dependabot/npm... | Vercel FAIL (systemic), GG pass | MERGEABLE | DEPS — major bump |
| #676 | deps-dev: bump @types/node 25→26 (major) | deps | dependabot/npm... | Vercel FAIL (systemic), GG pass | MERGEABLE | DEPS — dev-only, safe |
| #675 | deps-dev: testing group (3 updates) | deps | dependabot/npm... | Vercel FAIL (systemic), GG pass | MERGEABLE | DEPS — dev-only, safe |
| #674 | deps: three-js group (2 updates) | deps | dependabot/npm... | Vercel FAIL (systemic), GG pass | MERGEABLE | DEPS — minor |
| #673 | Add CI/CD workflow for product matcher (Copilot) | chore | copilot/setup-ci-cd... | Vercel FAIL (systemic), GG pass | MERGEABLE | **BLOCKED/DRAFT** — 0 additions, Copilot-generated stub |
| #672 | fix(collections): single-source sot.json drift guard | fix | feat/collection-sot-guard | Vercel FAIL (systemic), GG pass, CR pass | MERGEABLE | NEEDS-CI — large (+6649/-2394), foundation for #684/#685/#689 |
| #668 | feat(qc-tools): file://-robust GLB + render-review QC sheets | feat | feat/glb-render-file-robust | **ALL CI PASS** (Python, Frontend, WP, API, CodeQL, Security, License) except PR Agent (infra) + Secrets Scan (needs review) | UNKNOWN | **NEAR-SAFE** — only blocking items are infra-level failures; full test suite green |
| #666 | deps(python): update usd-core >=24→>=26.5 | deps | dependabot/pip/usd-core | Security, CodeQL pass; PR Agent fail (infra) | UNKNOWN | DEPS — major Python dep |
| #665 | deps(python): update together >=1.0→>=2.19.0 | deps | dependabot/pip/together | All CI checks pass | UNKNOWN | DEPS — safe |
| #663 | deps(python): bump numba 0.63→0.65 | deps | dependabot/pip/numba | Security, CodeQL pass; PR Agent fail (infra) | UNKNOWN | DEPS |
| #662 | deps(python): bump torchvision 0.24→0.27 | deps | dependabot/pip/torchvision | Security, CodeQL pass; **Playwright E2E FAIL** | UNKNOWN | **NEEDS-WORK** — E2E test failure |
| #659 | deps(python): update replicate >=0.30→>=1.0.7 | deps | dependabot/pip/replicate | Security, CodeQL pass; PR Agent fail (infra) | UNKNOWN | DEPS |
| #656 | feat(evaluation): Q-mode wire + Q-data centroid allowlist | feat | feat/track-q-mode-data | Full CI green except PR Agent (infra) | UNKNOWN | NEAR-SAFE — full test suite green |
| #655 | feat(theme): V7 lookbook product card + verified-hub imagery | feat | feat/v7-lookbook-card | Vercel FAIL, CodeQL pass, GG pass | UNKNOWN | NEEDS-CI — large (+3512/-2314) |
| #650 | feat(api): /api/v1/lora/* → imagery SDXL (LoRA Phase 1) | feat | feat/track-lora-phase1 | **ALL CI PASS** — green across all checks | UNKNOWN | **SAFE-TO-MERGE** — cleanest PR in the queue |
| #648 | fix(render): judge-unavailable QC → mandatory review, not fail-open | fix | feat/track-q-unavail | Vercel FAIL, CodeQL pass, GG pass | UNKNOWN | NEEDS-CI |
| #645 | feat(compositor): Phase 1 pipeline integrity (embeddings-reframe) | feat | feat/embeddings-phase1-pipeline | Vercel FAIL, CodeQL pass, GG pass | UNKNOWN | NEEDS-CI — foundation for #656 |

---

## Classification Summary

| Classification | Count | PR Numbers |
|----------------|-------|-----------|
| SAFE-TO-MERGE | 1 | #650 |
| NEAR-SAFE (full CI green, minor infra failures) | 2 | #668, #656 |
| NEEDS-CI (no full CI suite ran) | 10 | #690, #689, #688, #687, #686, #684, #672, #655, #648, #645 |
| DEPS — safe/minor | 6 | #680, #678, #676, #675, #674, #665 |
| DEPS — major bumps (breaking) | 6 | #683, #682, #681, #679, #677, #666, #663, #659 |
| NEEDS-WORK (real failures) | 2 | #685 (conflict + GG), #662 (E2E fail) |
| BLOCKED/DRAFT | 1 | #673 |

**Total open PRs: 30**
