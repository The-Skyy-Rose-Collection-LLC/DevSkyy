# Pipeline Completion Rollout — Every DevSkyy Pipeline, Evidence-Verified

**Date:** 2026-05-31
**Status:** Analysis complete — awaiting founder approval on batches + orphan decisions
**Source:** 3 parallel read-only codebase analyses (product/imagery, dev/ops, data/content), file:line-cited
**Companion:** the live build is `wf_68a0dfc5-f53` (imagery 3D + catalog→commerce + steward + orchestrator) — those 4 are NOT re-listed here.

---

## 1. Goal

Apply the evidence-verified completion harness (builder≠verifier, stub-grep gate, reproducible bundle, no-paid/no-prod) to every pipeline that has real code gaps — and honestly classify the ones it does NOT fit.

### The core finding
"Invoke it in every pipeline" splits four ways. Only **Bucket A** is a build job.

| Bucket | Meaning | Action |
|---|---|---|
| **A — Build-complete** | Real code gap, T1-buildable + testable offline | Evidence-completion workflow (build→verify→critic→evidence) |
| **B — Evidence-only** | Already working; just needs proof a monitor can re-run | Verifier-only pass (no build), produce evidence bundle |
| **C — Decide first** | Orphan/scaffold; no consumers or intentional stub | Founder: keep / build / delete — do NOT auto-build |
| **D — Out of code's reach** | Infra/account/prod/physical | Founder action item; no workflow can fix |

---

## 2. Full Pipeline Inventory (24, excluding the 4 in flight)

### Product / Imagery

| Pipeline | Entry | State | Tier | Bucket | Gap (file:line) |
|---|---|---|---|---|---|
| ADK render_pipeline | `agents/render_pipeline/cli.py:240` | working | T2 | A (small) | `DISPATCH_MODEL` hardcoded string not from `model_ids.py` (`agent.py:84`); RunBudget not mid-run in tools |
| ProductAssetPipeline | `orchestration/asset_pipeline.py:1254` | working (partial modes) | T2/T3 | B | Meshy gate fails-open on local images (`:485`); HF client internals unverified |
| Nano Banana 2 | `scripts/nano-banana-run.py:28` | working | T2 | A (small) + B | `fal_client` missing from requirements → FLUX ImportError; QA fail doesn't abort (`pipeline.py:364`) |
| Elite Studio graph | `skyyrose/elite_studio/graph/runner.py:28` | working | T2 | B | budget wiring gap at caller; 10s artificial batch delay |
| Creative hub | `skyyrose/elite_studio/creative/runner.py:18` | working | T1/T2 | B | router intent coverage unconfirmed for all 14 intents |
| Character creation | `skyyrose/elite_studio/character/agent.py` | partial | T2 | C | `_ROSIE_SPEC` var-name vs "Skyy"; no CLI; router wiring unconfirmed |
| FLUX synthesis | `skyyrose/elite_studio/synthesis/flux_pipeline.py:80` | working (live gap) | T2 | A (small) | **`fal_client` not in requirements — confirmed ImportError on br-006** |
| SDXL pipeline | `imagery/sdxl_pipeline.py:82` | scaffold, **orphan** | T3 | C | no `diffusers` dep, no GPU, no consumers |
| Premium 3D | `imagery/premium_3d_pipeline.py:614` | scaffold, **orphan** | T3 | C | raises `FileNotFoundError` at construction (no Wonder3D); no consumers |
| Clothing 3D | `pipelines/clothing_3d/pipeline.py:82` | working | T1 dry-run / T3 live | B | USDZ postprocess stage unconfirmed; IdempotencyCache bypass risk |
| Photo venture | `…/ventures/photo/pipeline.py:93` | scaffold (BETA, honest) | T1 | C | single initialize node — real nodes deferred by design |
| Video venture | `…/ventures/video/pipeline.py:65` | scaffold (ALPHA, honest) | T1 | C | single initialize node — all real nodes TODO |
| Social venture | `…/ventures/social/pipeline.py` | partial (publisher works) | T1/T2 | B | graphics/strategy nodes cost-gated + untested |

### Dev / Ops

| Pipeline | Entry | State | Tier | Bucket | Gap (file:line) |
|---|---|---|---|---|---|
| Elite Web Builder | `agents/elite_web_builder/run.py:301` | partial | T2 | A | imagery dispatcher returns hard error — target missing (`triggers.py:160`); social/photography/3D/competitor = stubs (`:219,:296`) |
| skyyrose-dev-team.js | workflow skill | working | T2 | B | `phpcs` needs composer install; budget-object dependency |
| self-healing-theme-loop.js | workflow skill | working | T2/T3 | B | `heal-log.jsonl` was missing; `theme-heal-doctor.md` unconfirmed |
| deploy-theme.sh | `scripts/deploy-theme.sh:833` | working | T3 (dry-run T1) | D | prod write — STOPSHOW gated; not a code gap |
| Frontend / Vercel | `frontend/package.json` | partial | T2 | D | `ENABLE_VERCEL_DEPLOY` unset; CI runner-blocked |
| SecurityOpsAgent | `agents/security_ops_agent.py:273` | partial | T2 | A | **JS scan defaults `pnpm` (absent) → FileNotFoundError (`:156`)**; auto-remediate/commit unconfirmed |
| ci.yml | GitHub | **broken** | T2/T3 | D | runner provisioning `runner_id=0` (account-level, since 2026-04-07) |
| security-gate.yml | GitHub | broken | T2 | D | same runner failure; placeholder license exemption |
| pr-agent.yml | GitHub | broken | T2 | A (the bug) + D | **bot-filter operator-precedence bug (`:31`)** is code-fixable; OAuth token expired + runner = D |
| asset-generation.yml | GitHub | partial | T2/T3 | D | runner failure; 7 secrets unprovisioned |
| catalog-validate.yml | GitHub | partial | T1 | D | runner failure only; logic correct |
| dossier-check.yml | GitHub | partial | T1 | D | runner failure; inline-import path risk |

### Data / Content / Platform

| Pipeline | Entry | State | Tier | Bucket | Gap (file:line) |
|---|---|---|---|---|---|
| RAG catalog indexing | `scripts/index_skyyrose_catalog.py` | working | T1/T2 | A (tiny) + B | non-canonical model id `catalog_retriever.py:337`; `for_production()` bypasses init guard `:659` |
| Catalog downstream sync | `sync/catalog_sync.py:253` | partial | T2 | A | **`_upload_media()` returns None (`:550`); `_sync_wordpress_product()` never calls WP (`:613`); `_find_product_by_sku()` always None (`:635`)** |
| Social media agent | `agents/social_media_agent.py:1054` | partial | T1/T3 | A (gen) / D (publish) | **`publish_post()` named stub (`:943`)**; `_llm_client` never invoked |
| Content generation | `agents/skyyrose_content_agent.py:272` | partial | T2 | A (overlaps in-flight) | most paths use hardcoded BrandDNA, not dossier (`:441`) |
| **AOS kernel** | `aos/kernel/kernel.py:57` | partial — **import-breaking** | T1 | **A (high value)** | **`AuditEventType.HEAL_ATTEMPTED/HEAL_ABORTED/HEAL_ESCALATED` missing from enum** — `AttributeError` on every healing path (`kernel.py:426,472,487,502`) |
| Document/brand ingestion | `orchestration/document_ingestion.py:527` | working | T1 | B | PDF path has no `pypdf` guard |
| Analytics/competitive/notif | `services/analytics/…`, `services/competitive/…` | partial | T1/T2 | A (small) / B | competitor store is in-memory, lost on restart (`competitor_analysis.py:41`) |

---

## 3. Execution — what runs, in what order

**Constraint:** the live `wf_68a0dfc5-f53` owns `gate.py`, `threed_round_table.py`, `api/three_d.py`, `wordpress_asset_agent.py`, `skyyrose_content_agent.py`, `scripts/catalog_to_wc.py`, steward, orchestrator. No batch may touch those until it finishes. All batches below are file-disjoint from it and from each other.

### Batch 1 — High-value isolated bug fixes (Bucket A, all T1, fast)
Each is a small, self-contained, offline-testable fix. Highest signal-to-cost.
1. **AOS healing enum** — add `HEAL_ATTEMPTED/HEAL_ABORTED/HEAL_ESCALATED` to `aos/governance/types.py`; failing test exercises `kernel.execute` healing path.
2. **fal_client requirement** — add `fal-client` to `requirements-imagery.txt`; import test for `synthesis/clients/fal.py` + nano_banana FLUX path.
3. **security_ops pnpm→npm** — default `package_manager="npm"`; test asserts no pnpm call.
4. **pr-agent.yml bot-filter** — fix operator precedence at `:31`; lint/parse proof.
5. **RAG model-id** — canonical Haiku id at `catalog_retriever.py:337`; init-guard fix at `:659`.
6. **render_pipeline DISPATCH_MODEL** — import from `model_ids.py`.

### Batch 2 — Partial-pipeline completion (Bucket A, T1 build with mocked boundaries)
7. **Catalog downstream sync** — implement `_upload_media`, `_sync_wordpress_product`, `_find_product_by_sku` against mocked WC client; dry-run default for live writes.
8. **Social publish** — implement `publish_post()` against mocked platform clients; wire `_llm_client` caption path; live publish stays gated.
9. **Elite Web Builder dispatchers** — `_dispatch_social`, theme/photography/3D/competitor stubs → real delegations (mocked at paid boundary); imagery dispatcher points at the now-built elite_studio.

### Batch 3 — Evidence-only verification (Bucket B, NO build — prove + bundle)
Run each verifier, capture output, write to the same EVIDENCE bundle. No code changes.
- nano-banana `dry-run`; clothing_3d `--dry-run` → `PipelineStatus.COMPLETED`; render_pipeline preflight; elite_studio graph `run_single` with mock generator; doc ingestion `ingest_docs_directory`; RAG index dry-run; analytics alert-engine test; dev-team.js + self-healing.js return-object inspection.

### Bucket C — Decisions required (do NOT auto-build)
- **SDXL pipeline** + **Premium 3D pipeline** — orphans, no consumers, T3 GPU/Wonder3D/Blender. Keep, build, or delete?
- **Character creation** — finish + wire into creative router, or defer?
- **Photo / Video ventures** — intentionally scaffolded (BETA/ALPHA). Build now or leave staged?

### Bucket D — Founder action items (no workflow can fix)
- **CI runner provisioning** (`runner_id=0`, account-level, since 2026-04-07) — unblocks 5 CI workflows at once. Highest infra leverage.
- **Renew `CLAUDE_CODE_OAUTH_TOKEN`** — restores pr-agent + claude-code-review.
- **Set `ENABLE_VERCEL_DEPLOY` + Vercel/Render secrets.**
- **Prod/paid executions** (deploy-theme.sh, asset-generation, paid 3D gen) — STOPSHOW-gated by design.
- **Golden reference photography** (23 backs + 99 angles) — the camera wall on imagery delivery.

---

## 4. The harness applied to every Bucket A/B item

Identical anti-false-completion contract as `wf_68a0dfc5-f53`:
- builder ≠ verifier (independent re-run from scratch)
- schemas demand raw captured output, not booleans
- stub-grep gate (`NotImplementedError|TODO|FIXME|bare pass|placeholder|mock-outside-tests`)
- TDD: failing test first — phantom gaps (already-fixed) are dropped, not fake-fixed
- completeness critic hunts for fakes
- no paid API, no live prod writes — those stay T2/T3 gated
- one reproducible `EVIDENCE.md` the monitor re-runs

Honest reporting: every item lands as **green (proven) / partial (evidence of what's left) / blocked** — never a blanket "100%".

---

## 5. Success criteria

- Every Bucket A gap: failing test → green, stub-grep clean, independent verifier confirms, in the evidence bundle.
- Every Bucket B pipeline: a reproducible verifier command + captured passing output in the bundle.
- Bucket C: explicit founder keep/build/delete decision recorded per orphan.
- Bucket D: action list handed off; nothing in D falsely claimed "built".
- The monitor can reproduce every green claim by re-running the listed commands.
