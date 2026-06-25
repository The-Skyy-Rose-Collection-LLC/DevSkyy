# Handoff — brand-centroid embedding gate

**Date:** 2026-05-03
**Branch:** `feat/phase-b2-c3-pipeline-eval-architecture`
**Session origin:** `/grill-with-docs` on `docs/superpowers/plans/2026-05-01-embedding-quality-gates.md` (now retired by commit `93f9cb08e` — design content was already shipped in the working tree under different naming)
**Status:** all decisions captured; nothing committed. Pick up cold from this doc.

---

## Pickup in a new terminal

```bash
cd ~/DevSkyy
git status --short                     # see untracked + modified set (matches list below)
git log --oneline -5                   # confirm you're at 93f9cb08e or later
cat CONTEXT.md                         # term glossary (load into head before working)
cat docs/adr/0001-*.md docs/adr/0002-*.md
cat tasks/centroid-gate-measurement-analysis.md   # full empirical writeup
```

If you want to re-run the harness against the same fixtures:

```bash
PYTHONPATH=. .venv/bin/python3 scripts/measure_brand_centroid_gate.py \
  --good-dir tests/fixtures/centroid_gate/good \
  --bad-dir  tests/fixtures/centroid_gate/bad \
  --centroid skyyrose/elite_studio/data/brand_centroid.npz \
  --centroid skyyrose/elite_studio/data/brand_centroid_dino.npz \
  --json-out tasks/centroid-gate-measurement.json
```

If the curated fixture dirs ever drift:

```bash
PYTHONPATH=. .venv/bin/python3 scripts/curate_centroid_test_set.py --clean
```

---

## What was decided this session (durable)

1. **ADR-0001** (`docs/adr/0001-compositor-is-agent-inside-langgraph-node.md`):
   The compositor is an agent inside a LangGraph node, not a procedural script.
   `scripts/run_compositor_pipeline.py` (697L) is transitional and slated for retirement.
   `CompositorAgent` rebuild is the prerequisite that un-blocks the LangGraph compositor stage.
   The gutted 68-line shell exists at `skyyrose/elite_studio/agents/compositor_agent.py`; the 544-line stale test file at `skyyrose/elite_studio/tests/test_compositor_agent.py` is the de-facto API spec for the rebuild.

2. **ADR-0002** (`docs/adr/0002-brand-centroid-global-pending-data.md`):
   Brand centroid is global (one CLIP + one DINOv2, both pooling all 23 approved hero shots) — per-collection refactor was deferred pending false-pass measurement.
   Status: **measured but inconclusive on its original question.** The data argues neither for global-is-fine nor for per-collection — it argues for ensemble. Not yet superseded. A follow-up ADR-0003 will resolve once the ensemble decision is made.

3. **JSON sidecar machinery** added to `skyyrose/elite_studio/quality/brand_centroid.py`:
   - new fields: `BrandCentroid.sample_paths: list[str]`
   - new functions: `write_metadata_sidecar`, `save_centroid_with_sidecar`, `_sample_paths_hash`, `_file_sha256`
   - sidecar schema v1 records: encoder, model_id, sample_count, threshold, centroid_dim, centroid_l2_norm, sample_paths, sample_paths_hash, npz_filename, npz_sha256, generated_at
   - 8/8 tests passing in `skyyrose/elite_studio/tests/test_brand_centroid_sidecar.py`

4. **Backfilled sidecars** for both shipped centroids (legacy: `sample_paths: []` because that field didn't exist at build time):
   - `skyyrose/elite_studio/data/brand_centroid.metadata.json` (CLIP, threshold 0.7631)
   - `skyyrose/elite_studio/data/brand_centroid_dino.metadata.json` (DINOv2, threshold 0.3905)

---

## Empirical findings (executive)

**Test set:** 75 known-good + 37 known-bad symlinked from existing repo images (via `scripts/curate_centroid_test_set.py`). No paid renders generated.

**Per-encoder, per-category false-pass at stored threshold:**

| Bad category | n | CLIP @ 0.7631 | DINOv2 @ 0.3905 |
|---|---|---|---|
| branding (closeup detail crops) | 22 | 0% ✅ | 13.6% |
| design (flat mockups) | 4 | 0% ✅ | 0% ✅ |
| source (raw product photography) | 6 | **83.3% ⚠️** | **0% ✅** |
| techflat (orthographic on white) | 5 | 60% ⚠️ | 40% |

**Aggregate:** CLIP false-pass 21.6%, DINOv2 false-pass 13.5%. Both fail ADR-0002's 10% rule.

**Decision-relevant insight:** Failures are encoder-specific and category-specific, NOT collection-specific. CLIP's dominant failure mode is "same SKU, no model, no scene" passing as a hero shot — visual content dominates over semantic context. Per-collection refactor would not fix this. DINOv2 catches all source photos (0% FP), validating the docstring's "~2x discrimination" claim, but is stricter on legitimate goldens (40% pass vs CLIP's 60%). **Encoders have complementary failure modes** → ensemble is the right answer.

**Caveat I am keeping honest:** The curated bad set is not fully representative of compositor outputs (compositor produces model+scene renders by construction, not techflats or source photos). A definitive production go/no-go would need paid "off-brand model+scene" renders — gated by STOP AND SHOW.

---

## Open work / next grilling pass

The natural next conversation is **the ensemble decision**. Specific branches that need answers:

1. **Where does the AND happen?**
   - Inside `embedding_gate.evaluate()` — extend signature to take `list[BrandCentroid]` and require all to accept?
   - Or as a higher-layer policy in the gate's caller (compositor decides per-render whether to require ensemble)?

2. **Threshold tuning under ensemble.**
   - Current per-encoder thresholds are 10th-percentile of in-cluster similarities for that encoder's centroid. Under AND, the effective false-fail rate is approximately `1 - (P_CLIP_pass × P_DINO_pass)` — which means current thresholds may be too strict in conjunction. Need a coupled tuning pass.

3. **Does the test-set bias matter for the production decision?**
   - If the gate's job is "catch off-brand compositor outputs," and compositor outputs are always model+scene renders, then the bad/source false-pass on CLIP may be irrelevant in practice. CLIP-alone may be sufficient for the gate's actual purpose.
   - Counter: defense-in-depth. The gate shouldn't trust the compositor to never produce a non-hero-shot output (e.g., if a future stage swap ships a regression).

4. **Sample-paths backfill for the existing two centroids.**
   - The .npz files predate the `sample_paths` field. Easiest backfill is rebuilding from the original `--approved-dir` (whichever 23 images were originally used). Can `git log` on the .npz files identify the build script invocation? Worth checking before any ensemble work to ensure the centroid input set is actually clean (no source photos, etc.).

5. **CompositorAgent rebuild plan** (from ADR-0001) — independent of the ensemble work but blocks Task 4 of the original embedding-quality-gates plan.

---

## Untracked + modified files (this session's surface)

```
?? CONTEXT.md
?? docs/adr/0001-compositor-is-agent-inside-langgraph-node.md
?? docs/adr/0002-brand-centroid-global-pending-data.md
 M skyyrose/elite_studio/quality/brand_centroid.py
?? skyyrose/elite_studio/data/brand_centroid.metadata.json
?? skyyrose/elite_studio/data/brand_centroid_dino.metadata.json
?? skyyrose/elite_studio/tests/test_brand_centroid_sidecar.py
?? scripts/curate_centroid_test_set.py
?? scripts/measure_brand_centroid_gate.py
?? scripts/regenerate_centroid_sidecars.py
?? tasks/centroid-gate-measurement.json
?? tasks/centroid-gate-measurement-analysis.md
?? tests/fixtures/centroid_gate/         (75 + 37 symlinks + manifest.json + README.md)
?? tasks/handoff-centroid-gate-2026-05-03.md   (this file)
```

Other unrelated modifications visible in `git status` are pre-existing and **not** mine: `.devskyy/scopes.toml`, `.wolf/buglog.json`, `.wolf/memory-audit.json`, `api/v1/catalog.py`, `orchestration/catalog_retriever.py`, `tests/api/test_catalog_endpoint.py`, `skyyrose/core/memory/`, `tasks/pr-auto-report-2026-05-02.md`. Leave those for whatever workstream owns them.

---

## Suggested commit split

Three logical commits, in this order:

1. **`feat(quality): add JSON metadata sidecars for brand centroids`**
   - `skyyrose/elite_studio/quality/brand_centroid.py` (the new functions + `sample_paths` field)
   - `skyyrose/elite_studio/tests/test_brand_centroid_sidecar.py`
   - `scripts/regenerate_centroid_sidecars.py`
   - `skyyrose/elite_studio/data/brand_centroid.metadata.json`
   - `skyyrose/elite_studio/data/brand_centroid_dino.metadata.json`

2. **`docs(adr): record compositor architecture + brand-centroid scope decisions`**
   - `CONTEXT.md`
   - `docs/adr/0001-compositor-is-agent-inside-langgraph-node.md`
   - `docs/adr/0002-brand-centroid-global-pending-data.md`

3. **`feat(quality): add brand-centroid gate measurement harness + curated test set`**
   - `scripts/curate_centroid_test_set.py`
   - `scripts/measure_brand_centroid_gate.py`
   - `tests/fixtures/centroid_gate/` (entire dir — symlinks + manifest + README)
   - `tasks/centroid-gate-measurement.json`
   - `tasks/centroid-gate-measurement-analysis.md`
   - `tasks/handoff-centroid-gate-2026-05-03.md` (this file, optional — could be `.gitignore`d)

The order matters because (3) imports from the file (1) edits, and the analysis in (3) cites the ADRs from (2).

---

## What I deliberately did NOT do

- **No commits.** Per CLAUDE.md, commits are user-triggered.
- **No paid API calls.** STOP AND SHOW gate held — no FASHN, no Gemini, no FLUX, no compositor invocations. CLIP and DINOv2 inference is local-only.
- **No ensemble implementation.** Real architectural choice; warrants its own grilling pass before code lands.
- **No per-collection refactor.** Data argues against it; would be wasted work.
- **No modifications to ADR-0002.** Marked as "measured but inconclusive on its original question" via the analysis md and CONTEXT.md, but the ADR itself is preserved as written. A future ADR-0003 (ensemble decision) will explicitly link back.
- **No production deployment of the gate.** None of this is wired into the compositor pipeline yet — the gate library exists, the centroids exist, but `compositor_node` doesn't invoke `embedding_gate.evaluate()` because `CompositorAgent.composite()` is still the gutted 68-line shell (see ADR-0001).

---

## Decision rule cheat-sheet for next session

When you re-grill the ensemble question, the data table in `tasks/centroid-gate-measurement-analysis.md` is the authoritative empirical input. Don't rebuild it from memory; read it. Key numbers to anchor on:

- CLIP good/back-model pass: **92%**
- CLIP good/golden-front pass: **60%**
- CLIP bad/source pass: **83.3%** (the dominant failure mode)
- DINOv2 bad/source pass: **0%**
- DINOv2 good/golden-front pass: **40%**
- DINOv2 good/back-model pass: **92%**

If you find yourself proposing per-collection again, re-read the per-category breakdown — collection split does not address the bad/source failure.
