# Embeddings Reframe — Design Spec

**Date:** 2026-06-22
**Status:** Approved (design) — pending spec review
**Scope:** Reconfigure, enhance, and unify the visual/text embedding subsystem under `skyyrose/`,
**and close the full set of subsystem + render-pipeline gaps a 6-track audit surfaced (§6)** — because
pipeline gaps (stale/wrong/mislabeled image reaching the gate) corrupt the embedding verdict no
matter how clean the encoder is. The embeddings build is gated behind a no-break anchor (Phase 0)
and pipeline-integrity hardening (Phase 1) that feed it correct inputs.

---

## 1. Goal

Turn the two copy-pasted embedder singletons + a disconnected script duplicate + ad-hoc
sidecar persistence into one coherent, configurable embeddings package under
`skyyrose/core/embeddings/`, with a real vector store — **without breaking the live render
pipeline** that depends on the QC gates — **and** harden the render pipeline + QC/eval layer the
embedding gate depends on, so the gate scores the right pixels against a sound reference.

Three verbs from the original request, plus a fourth from the follow-up:
- **Configure** — one `EmbeddingConfig` instead of constants scattered across each embedder.
- **Enhance** — shared base (kill duplication), batch encode + caching, the missing `VectorStore`.
- **Redo/unify** — fold the `scripts/` CLIP duplicate and ad-hoc sidecars into the package.
- **Close all gaps first** — the audit register in §6 is in-scope; nothing builds until Phase 0 lands.

## 2. Current state (verified 2026-06-22)

| Piece | Where | Problem |
|---|---|---|
| CLIP embedder | `skyyrose/core/clip_embedder.py` | Singleton, 512-d (`clip-vit-base-patch32`), image+text. Hardcoded `MODEL_ID`/`EMBED_DIM`; re-implements `_select_device`/`_l2_normalize`/lazy-lock. No HF revision pin. |
| DINO embedder | `skyyrose/core/dino_embedder.py` | Singleton, 768-d (`facebook/dinov2-base`), image. **Duplicates** the same device/norm/lock helpers + constants. No revision pin. |
| Script duplicate | `scripts/image_embeddings/clip_embedder.py` | OOP `CLIPEmbedder`, reimplements CLIP, `print()` not logging, eager model load in `__init__`, no persistence. Disconnected from production. **Deleted** under Option B. |
| Persistence | `elite_studio/data/brand_centroid.npz` (+ ad-hoc) | No unified store; `load_centroid()` has **no dim/model guard**; `save_centroid()` is **non-atomic**. 512-d image vectors have no home. Pinecone `skyyrose-catalog` holds **Gemini/Voyage text** (1024-d), not CLIP images. |
| Config | none | Model IDs / dims / device policy hardcoded per-file. No frozen config; no env override. |

**Consumers (7 import sites):**
`skyyrose/elite_studio/quality/{brand_centroid:34, clip_alignment:25, embedding_gate:21, render_quality:35}`,
`skyyrose/elite_studio/platform/fidelity/metrics.py:38` (lazy),
`scripts/{catalog_ml_audit.py:51, measure_brand_centroid_gate.py:43}`.

**Live render path (must not break):**
`elite_studio/agents/compositor/orchestrator.py:743` and
`agents/compositor/stage_g_visual_qa.py:164` call **`embedding_gate.evaluate(shadow_path, centroid)`**
+ **`brand_centroid.load_centroid()`** (loading `brand_centroid.npz`). These call the *quality-module*
public API, not the embedders directly — that is the safety seam (full frozen-contract list in §6, Track 0).

## 3. Target architecture

```
skyyrose/core/embeddings/
├── __init__.py     # package exports: get_clip, get_dino, EmbeddingConfig, VectorStore, EmbeddingSpace, ...
├── config.py       # EmbeddingConfig (frozen): model IDs + revision SHAs, dims, device policy, store backend;
│                   #   env overrides; secrets NOT on this object (read at provider init)            [§6 E-config]
├── space.py        # EmbeddingSpace fingerprint + EmbeddingSpaceMismatch                            [§6 E-space]
├── errors.py       # EmbeddingError / EmbedError / EmbeddingSpaceMismatch (typed)                   [§6 E-errors]
├── device.py       # shared _select_device (dedupes clip↔dino↔scripts)                             [§6 E-dedup]
├── base.py         # Encoder protocol + _BaseEncoder: L2-normalize, thread-safe lazy singleton,
│                   #   transformers>=5 output handling, MAX_IMAGE_PIXELS guard; exposes .space
├── clip.py         # ClipEncoder(_BaseEncoder): embed_image / embed_text (512-d)
├── dino.py         # DinoEncoder(_BaseEncoder): embed_image (768-d)
├── cache.py        # CachedEncoder: content-hash (sha256) read-through cache, space-namespaced     [§6 E-cache]
└── store.py        # VectorStore protocol + LocalVectorStore (atomic, corruption-tolerant) +
                    #   PineconeImageStore; records carry an EmbeddingSpace stamp; query/upsert guard [§6 E-store]
```

Siblings (outside the package, in their existing trees):
- `monitoring/embedding_observer.py` — gate observability + PSI drift, ALERT-ONLY  [§6 OBS]
- pipeline hardening lands in `skyyrose/elite_studio/agents/compositor/*` + `evaluation/*` (Tracks P, Q)

- **`EmbeddingConfig`** (frozen dataclass): `clip_model_id` + `clip_revision`, `clip_dim`,
  `dino_model_id` + `dino_revision`, `dino_dim`, `device` (`auto`→cuda>mps>cpu), `store_backend`
  (`local`|`pinecone`), `store_path`, optional `pinecone_image_index`, PSI bands, cache size. One
  place to change models/dims/device/store. Env overrides with safe defaults. **API keys are not
  fields** — read at provider construction (avoid serializing secrets).
- **`_BaseEncoder`** absorbs the duplicated device-select (→`device.py`), `_l2_normalize`,
  double-checked-lock singleton, `transformers>=5` output handling, and the decompression-bomb guard
  — `clip.py`/`dino.py` become thin (model load + forward + `.space`).
- **`VectorStore` port** (Protocol): `upsert(id, vector, meta)`, `query(vector, k, filter)`,
  `get(id)`, `all()`, `delete(id)`, `save()/load()`. Default **`LocalVectorStore`** (SQLite + numpy
  cosine; FAISS deferred — YAGNI at this scale, §6 DEFER) — zero infra, zero cost, offline, **atomic
  tmp+rename writes**, corruption-tolerant. **`PineconeImageStore`** targets a *new* 512-d / 768-d
  **image** index — never the 1024-d text index. Resolves the dim mismatch by separation.
- `brand_centroid.npz` is read/written through the store (or a thin compat loader) so
  `brand_centroid.load_centroid()` keeps returning the same array — now with a space guard.

## 4. Migration — Option B (hard migrate) + render-path orchestration

**Principle:** the render pipeline calls `embedding_gate.evaluate()` and
`brand_centroid.load_centroid()`. Those two signatures + return types are a **frozen contract** for
this phase (full list §6, Track 0). Everything underneath can change; those cannot.

**Sequence (each step verified green before the next) — see §7 for the phased plan:**
1. **Phase 0 (no-break anchor):** pin the frozen contract with a characterization/golden test +
   split gate tests so CI actually runs them. Nothing else starts until this is green.
2. **Phase 1 (pipeline integrity):** fail-closed stages, content-addressed render paths, SKU-in-cache-key,
   SKU validation at entry, audit fingerprinting — so the gate scores the right pixels.
3. **Phase 2 (embeddings package):** build `skyyrose/core/embeddings/`, re-point the 7 consumers,
   delete the old embedders + script duplicate.
4. **Phase 3 (observability + QC safety):** embedding telemetry + PSI; evaluation cost cap + STOP-AND-SHOW.
5. **Render-path verification (gates every phase):** Stage-G visual-QA tests + an `embedding_gate.evaluate()`
   smoke against a fixture render + `brand_centroid.npz`; gate verdict unchanged vs current `main` (golden).

**Orchestration:** per-file edits inside a phase are independent → parallel review/edit units; the
render-path golden gates the whole change and runs last on the integrated result.

## 5. Enhancements (in scope)

- Batch encode (`embed_images(list)`) on the base — folds the script's `encode_batch`.
- Read-through cache: see **§6 E-cache** (content-hash keyed, supersedes the naive id-keyed `embed_or_get`).
- Central device + dim config; `transformers>=5` handling in one place.

## 6. Gap register — full-subsystem audit (6 tracks, 2026-06-22)

Six read-only audits (3 embedding clusters + 3 pipeline clusters) surfaced ~75 findings; deduped to
the register below. **Verification key:** ✓ = re-read first-hand this session · ⊘ = audit-reported,
grounded at a real `file:line`, not yet re-read · ✗ = refuted on re-read. Every FILL_NOW gap is
closed by this project; every DEFER is named with a reason (a named deferral is a *filled* gap, not
an ignored one). Each fix names an industry-proven practice.

### Track 0 — No-break anchor (FILL_NOW · must land FIRST)

The reframe has **no regression net today**: every gate test is `@pytest.mark.integration`/`slow`,
so CI (`-m "not slow and not integration"`) runs **zero** of them. Fix before touching code.

| id | file:line | gap | fix (precedent) | sev | ✓ |
|---|---|---|---|---|---|
| T0-contract | `embedding_gate.py:33,39`; `clip_alignment.py:28,35`; `render_quality.py:109`; `metrics.py:20,36`; `stage_g_visual_qa.py:131`; `brand_centroid.py:120` | Frozen-contract functions are unpinned by any test | Pin signatures+returns with a **contract test** | HIGH | ✓ |
| T0-golden | `tests/elite_studio/` (none) | No characterization test pins the current gate verdict for a known image+centroid → a silent score/threshold-logic drift would ship | **Golden/characterization test**: deterministic synthetic centroid+embedding, assert verdict+score to 1e-4 (no model needed) | HIGH | ✓ |
| T0-ci | `tests/elite_studio/test_embedding_gate.py:18`, `test_compositor_gate_integration.py`, `test_brand_centroid.py` | All gate tests excluded from CI; monkeypatch tests need no model but are marked `integration` | Split: monkeypatch tests → `@pytest.mark.unit`; keep real-model tests `integration` | HIGH | ✓ |
| T0-mutable | `test_compositor_gate_integration.py:21` | Test forces acceptance by mutating a loaded `BrandCentroid`; breaks if reframe makes it `frozen` | Construct a fresh `BrandCentroid(threshold=-1.0)` instead of mutating | MED | ⊘ |

**Frozen contract (preserve exactly):** `score_against_centroid(image, centroid)->float` ·
`evaluate(image, centroid)->GateVerdict` · `score_alignment(prompt, image)->float` ·
`score_alignment_batch(prompts, image)->list[float]` ·
`evaluate_render(render_path, prompt, centroid_path, *, min_dimension, alignment_threshold)->RenderVerdict` ·
`composite_score(*, dino, clip, ssim)->float` · `score_view(render_path, reference_path, *, sku, angle)->VisibleScore` ·
`maybe_apply_gate(shadow_path, scene_name, collection, *, analyze_vision, centroid_path=None)->dict` ·
`load_centroid(path)->BrandCentroid` · dataclasses `GateVerdict`, `RenderVerdict`, enum `Verdict{SHIP,REVIEW,KILL}`.

### Track E — Embeddings package (the reframe core · FILL_NOW)

| id | file:line | gap | fix (precedent) | sev | ✓ |
|---|---|---|---|---|---|
| E-space | `brand_centroid.py:120-127`; new `store.py` | `load_centroid()` does **no** model/dim check; a 768-d DINO centroid in the 512-d CLIP gate (or post-model-swap) scores meaningless cosine with confident verdicts; store has same exposure | **Embedding-space fingerprint** `(model_id, dim, preprocess_version, normalized)` stamped on every record + centroid; `EmbeddingSpaceMismatch` guard on `load_centroid`/`query`/`upsert` (Pinecone/Weaviate per-index dim pin; LangChain `namespace=model`, Context7) | HIGH | ✓ |
| E-encoder-gate | `embedding_gate.py:33-36` | `score_against_centroid` calls `clip_embedder.embed_image` **unconditionally** — ignores `centroid.model_id`; a DINO centroid → numpy shape error / garbage. `render_quality._score_centroid` is already encoder-aware | Dispatch encoder by `centroid.space`/`model_id` (mirror render_quality); the space guard (E-space) backstops it | HIGH | ✓ |
| E-revpin | `clip_embedder.py:66`, `dino_embedder.py:68` | `from_pretrained()` has **no `revision=`**; HF resolves branch HEAD → silent weight drift; the `nosec B615` comment falsely claims pinning ("revision pinned via MODEL_ID" — MODEL_ID is a repo id) | **Pin `revision=<sha>` + `use_safetensors=True`**; make the nosec truthful (OSSF Scorecard / Bandit B615) | HIGH | ✓ |
| E-determinism | `clip_embedder.py:66`, `dino_embedder.py:68,93` | `torch_dtype` unpinned (MPS/CUDA bit-drift); preprocessing (resize/crop/normalize) unpinned → vectors not stable across `transformers` versions | Pin `torch_dtype=float32`; snapshot/pin processor config; carry a `preprocess_version` in the space | HIGH | ⊘ |
| E-dedup | `clip_embedder.py:47-52,75-79` vs `dino_embedder.py:49-54,77-81` | `_select_device` + `_l2_normalize` + lock-singleton copy-pasted verbatim across 2–3 files | Extract `device.py` + `_BaseEncoder` (DRY) | MED | ✓ |
| E-errors | `clip_embedder.py:97`, `dino_embedder.py:87` | No corrupt/empty-image handling (`PIL.UnidentifiedImageError` raw-propagates onto the render path); no typed error | `try/except → EmbedError`; typed `errors.py` | HIGH | ⊘ |
| E-zeronorm | `clip_embedder.py:76`, `dino_embedder.py:77` | `_l2_normalize` silently returns the vector when `norm<1e-9` (blank/black image) → cosine 0.0 accepted as valid | Raise `ValueError("zero-norm embedding")` | MED | ⊘ |
| E-bomb | 7 `Image.open` sites incl. `embedding_gate`, `render_quality.py:136` | `Image.MAX_IMAGE_PIXELS` never set → a 50k×50k PNG = multi-GB OOM | Set `Image.MAX_IMAGE_PIXELS` once in `base.py` (decompression-bomb guard) | HIGH | ⊘ |
| E-fd | `clip_embedder.py:97`, `dino_embedder.py:87` | `Image.open(path)` not closed → fd leak under bulk re-embed | `with Image.open(...) as raw:` | MED | ⊘ |
| E-batch | `clip_embedder.py:93-106` | No batch `embed_image` API → 33 separate forward passes on re-embed | Add `embed_images(list)` (same GPU matmul cost) | MED | ✓ |
| E-config | `clip_embedder.py:32`, `dino_embedder.py:35`, `embedding_engine.py` config | Model id/dim hardcoded; `EmbeddingConfig` (where present) is mutable Pydantic; API keys live on the config object (serialized → secret leak) | **Frozen `EmbeddingConfig`** + env overrides; keys read at provider init via pydantic-settings, never a model field | HIGH | ⊘ |
| E-cache | new `cache.py` | Render pipeline **overwrites** shadow PNGs at stable paths → an id-keyed cache returns a stale vector for changed pixels | **Content-hash cache** `sha256(bytes)` namespaced by space (LangChain `CacheBackedEmbeddings`, Context7); read-through, corruption-tolerant | MED | ✓ |
| E-store | `brand_centroid.py:109-117`; `orchestration/vector_store.py` | `save_centroid` non-atomic (crash → truncated `.npz` → render abort); Pinecone image vectors must use a **separate** index from the 1024-d text `skyyrose-catalog` (dim clash = API error) | **Atomic tmp+rename**; corruption-tolerant load; separate 512/768-d image index pinned in config | HIGH | ✓ |
| E-delete | `scripts/image_embeddings/*` | Disconnected CLIP duplicate (eager load → CI 429s, `print()`, wrong `get_embedding_dim` for ViT-H, no persistence) | **Delete**; fold callers onto the core singleton (Option B). Closes the scripts-path findings as moot (incl. the refuted ✗ `_projected` claim — `get_image_features` returns a projected tensor) | MED | ✓ |

### Track P — Pipeline input integrity (FILL_NOW · feeds the gate)

Garbage-in: if the wrong/stale/partial image reaches `evaluate()`, the verdict is meaningless.

| id | file:line | gap | fix (precedent) | sev | ✓ |
|---|---|---|---|---|---|
| P-failclosed | `stage_f_shadows.py:86-88`; `stage_c_relight.py:92`; `stage_g_visual_qa.py:87-103` | Stages **fail-open**: on any exception they return the prior-stage image (un-shadowed/unrelit) labeled as the new path; Gemini errors/parse-fails return `"warn"` not `"fail"` → bad render proceeds, no audit signal | **Fail-closed**: re-raise or return a typed skip; gate refuses to score a degraded/`None` output | CRITICAL | ✓ |
| P-paths | `stage_f_shadows.py:83`; `orchestrator.py:325` | Output `{sku}-shadow.png` / `{sku}-composite.png` has **no scene/run component** → concurrent same-SKU different-scene renders overwrite; writes non-atomic → gate reads partial PNG | **Content-addressed paths** `renders/output/{sku}/{scene}/{run_id}/…` + atomic `os.replace` | CRITICAL | ✓ |
| P-cachekey | `stage_a_matte.py:84-88`, `stage_d_rasterize.py:94-101` | Cache key = input-bytes hash with **no SKU** → two SKUs sharing a source photo collide (wrong garment downstream) | Bind cache key to `(sku, scene, input_hash)` (canonical-sources-only) | HIGH | ⊘ |
| P-skuvalidate | `orchestrator.py` (entry) | `sku` flows as an unvalidated string; a typo runs the full paid pipeline and scores an unapprovable image | Validate `sku` against the catalog CSV at entry (`ValueError` if unknown) | HIGH | ⊘ |
| P-existcheck | `embedding_gate.py:39`; `stage_g_visual_qa.py:159` | `evaluate()` does not pre-check the image path exists → unhandled PIL error if upstream deleted/missing | Pre-check; return `GateVerdict(accepted=False, reason="missing image")` | HIGH | ⊘ |
| P-auditfp | `audit.py`; `stage_g_visual_qa.py` | Audit log records `output_path` (string) but **no sha256/size of the scored image** nor centroid sha256/sample_count → past verdicts unfalsifiable; stale-file swaps undetectable | Record `scored_image_sha256+size` + `centroid_sha256+sample_count+mtime` (content fingerprint) | HIGH | ⊘ |
| P-noop | `stage_e_cleanup.py:44` | GIMP stage is a no-op but records itself as "ran" → false audit confidence | Mark `"skipped": true` when `commands == []` | LOW | ⊘ |

### Track Q — QC / eval safety + calibration (mixed)

| id | file:line | gap | fix (precedent) | sev | scope | ✓ |
|---|---|---|---|---|---|---|
| Q-costcap | `evaluation/core.py:49-70`, `judge.py:66` | `gate()` loops `cap=2` with **no cost accumulation/ceiling** → up to 3 paid Anthropic calls/SKU; ~$15/33-SKU batch, **no STOP-AND-SHOW** | **Cost accumulator + `max_cost_usd` ceiling + pre-batch STOP-AND-SHOW manifest** (matches project gate; memory #18753) | CRITICAL | FILL_NOW | ✓ |
| Q-modelpin | `judge.py:56`, `agents.py` | Judge model is caller-supplied with no default; accidental Opus = 5× cost; no temperature/seed | Default to `QC_JUDGE_MODEL_ANTHROPIC` (sonnet) + `temperature=0` (reproducible verdicts) | MED | FILL_NOW | ✓ |
| Q-unavail | `scripts/oai_render/qc.py:532` | `_unavailable()` returns `passed=True` on judge-infra failure → unreviewed render ships; tag only in JSONL | **Mandatory review queue**: `judge_unavailable` renders block on human sign-off | HIGH | FILL_NOW | ⊘ |
| Q-fusion | `evaluation/domains/imagery.py` vs `qc.py` | Centroid gate (cosine) and VLM judge are orthogonal — a render can pass one, fail the other, no rollup | **Verdict fusion**: accept iff centroid-gate AND judge pass; log both for joint calibration | MED | FILL_NOW | ⊘ |
| Q-kappa | `observer.py` vs `calibration.py:37` | Two disagreeing "agreement" metrics (raw proportion vs Cohen's κ) | Unify on κ (corrects for chance) | MED | FILL_NOW | ⊘ |
| Q-mode | `evaluation/calibration.py`, `core.py` | `decide_mode()` output (`soft_signal`/`hard_gate`) is computed but **never consumed** — gate behaves identically regardless of judge accuracy | Wire `verdict.mode` into the gate action | HIGH | FILL_NOW | ⊘ |
| Q-data | `scripts/build_brand_centroid.py:47` | Default `approved_dir` = live product dir (mixes techflats/source/branding); no curated allowlist; no min-sample floor → contaminated/noisy centroid | Curated `manifest.json` allowlist + `MIN_APPROVED` floor + `--approved-dir` required | HIGH | FILL_NOW | ⊘ |
| Q-calib | `measure_brand_centroid_gate.py`, `imagery.py:load_ground_truth` | Calibration never run (labeled fixtures depend on renders deleted 2026-06-09); `review-state.json` absent | **DEFER** — blocked on render rebuild; add `skipif` + tracked note; run when renders land | HIGH | DEFER | ⊘ |

### Track OBS — Observability (mixed)

| id | seam | gap | fix (precedent) | sev | scope |
|---|---|---|---|---|---|
| OBS-wire | `core/token_tracker.py` `TaskType`, `record()` | No `TaskType.EMBED`; encode path emits **zero** telemetry → `FleetObserver` blind to cost/latency/errors | Add `TaskType.EMBED`; `record()` one row/encode (latency, cache-hit, success) | HIGH | FILL_NOW |
| OBS-gate | `monitoring/embedding_observer.py` (new) | No accept/reject-ratio or verdict telemetry on the gate | New ALERT-ONLY observer mirroring `fleet_observer.py` (pure-read) | MED | FILL_NOW |
| OBS-psi | sidecar + observer | Threshold frozen at build time; no signal when the live score distribution drifts off it | Persist build-time score histogram as PSI **reference**; `TICKET` at PSI>0.2, `PAGE`>0.25 (Vertex/Evidently). **Never auto-retunes** — recalibration human-initiated | MED | FILL_NOW |
| OBS-struct | `embedding_engine.py` logging | stdlib `logging` not `structlog` → can't join fleet traces | Swap to `structlog` (mechanical) | LOW | FILL_NOW |

### DEFER register (named, with reason)

- **ANN / FAISS index** — brute-force numpy cosine at 33 SKUs / hundreds of renders is faster than any
  ANN (index build overhead dominates until ~100k vectors). YAGNI; revisit at 4 orders of magnitude more.
- **Provider circuit-breaker + retry/backoff on embeddings** — needs `tenacity`; do in a Phase-3 follow-up
  *after* OBS telemetry lands so the breaker's alerts are visible.
- **Generic `_Singleton[T]` extraction** — `_BaseEncoder` is enough; a generic adds abstraction for 2 uses.
- **Calibration run + OOD-negative mining + fixture-freshness CI** (Q-calib) — blocked on the deleted
  renders; unblock when new renders are reviewed.
- **PSI rolling-window auto-tune** — ship the alert first; auto-tune is out of scope (human recalibrates).
- **`product-embeddings.json` in-memory cache / ETag** — 1.2 MB at 33 SKUs is negligible.

## 7. Phased closure plan

Each phase is verified green (tests + lint + render-path golden) before the next. Within a phase,
independent files are parallel edit/review units.

- **Phase 0 — No-break anchor (Track 0).** Contract test + golden verdict test + CI test-split. The
  regression net. *Gate:* golden verdict captured from current `main`; CI now exercises the gate.
- **Phase 1 — Pipeline integrity (Track P).** Fail-closed stages, content-addressed atomic paths,
  SKU-in-cache-key, SKU validation, gate existence pre-check, audit fingerprinting. *Gate:* the bytes
  the gate scores are provably the correct, complete, current render for the correct SKU.
- **Phase 2 — Embeddings package (Track E).** Build `skyyrose/core/embeddings/`; space guard +
  encoder-aware gate + revision pin + determinism + typed errors + bomb/fd guards + batch + frozen
  config + content-hash cache + atomic store; re-point 7 consumers; delete old embedders + script
  duplicate. *Gate:* render-path golden unchanged; ≥85% new-package coverage.
- **Phase 3 — Observability + QC safety (Tracks OBS, Q).** `TaskType.EMBED` + telemetry + PSI
  observer; **evaluation cost cap + STOP-AND-SHOW + model pin + temperature 0**; verdict fusion; κ
  unify; `decide_mode` wired; curated centroid-build inputs. *Gate:* a drifted distribution raises a
  `TICKET`; a batch over `max_cost_usd` is blocked before any paid call.

> **STOP-AND-SHOW note:** Q-costcap, Q-modelpin, Q-unavail *reduce* spend risk and add no paid call.
> Running calibration or re-rendering remains a separate, explicitly-confirmed paid action.

## 8. Error handling

- Encoders raise `EmbedError`/`ValueError` on empty/blank/corrupt input; never return un-normalized or
  zero-norm vectors. Device selection never raises (falls back to cpu).
- `LocalVectorStore` is corruption-tolerant: missing/garbage store file → empty store + WARNING, never
  a crash on the render path. Writes are atomic (tmp+rename).
- Model load failure surfaces a clear `EmbeddingError` (not a bare HF traceback).
- Pipeline stages **fail-closed**: a stage that cannot do its job returns a typed skip/raise, never a
  silently-degraded image labeled as success.

## 9. Testing

- **Encoders:** dim/normalization/determinism with a mocked model; device fallback; revision pinned.
- **Store:** local round-trip (upsert→query→get), cosine ordering, corruption tolerance, atomic write,
  space-stamp round-trip.
- **Space guard (E-space):** dim + model mismatch raise `EmbeddingSpaceMismatch`; legacy `.npz` loads
  with inferred space (warns, no raise); matching space passes.
- **Cache (E-cache):** identical bytes → one underlying encode; changed bytes at the same path →
  recompute; different spaces don't collide; corrupt row → silent live-encode fallback.
- **Migration safety:** every re-pointed consumer imports + its public API unchanged (contract test).
- **Render-path golden (Track 0):** `embedding_gate.evaluate(fixture, brand_centroid.npz)` verdict ==
  current `main` value — the no-break proof, captured in Phase 0.
- **Pipeline (Track P):** fail-closed assertions per stage; path-collision test (same SKU, two scenes →
  distinct outputs); audit record contains the scored-image sha256.
- **QC safety (Track Q):** `gate()` over `max_cost_usd` raises before any judge call; PSI == 0 on
  identical distributions and rises on a shift; observer is pure-read (never mutates the threshold).
- Target ≥85% on the new package; `ruff`/`black`/`mypy` clean; full `pytest` green.

## 10. Out of scope / risks

- The `.[all]` cryptography/mlflow dependency break is **separate** (a concurrent fix exists) — this
  reframe doesn't depend on `mlflow`.
- Pinecone *image* index creation is optional/deferred — `LocalVectorStore` is the default; the
  adapter ships but isn't wired to a live index this phase (no paid call, no STOP-AND-SHOW).
- Re-embedding the catalog + running calibration are follow-ups; this phase preserves existing
  vectors/sidecars and only *recommends* recalibration via the PSI alert.
- See the §6 DEFER register for every consciously-postponed gap and its reason.

## 11. Success criteria

1. **Phase 0:** a golden test pins the current gate verdict and CI runs the gate suite on every push.
2. **Phase 1:** the gate provably scores the correct, complete, current render for the correct SKU;
   the audit log carries a content fingerprint of what was scored.
3. One `skyyrose/core/embeddings/` package; old duplicate embedders + script duplicate gone; 7
   consumers migrated (Option B); render-path golden verdict unchanged.
4. `EmbeddingConfig` (frozen, no secrets) is the single place to change model/revision/dim/device/store.
5. **E-space:** space mismatch is caught, not silent (`load_centroid` + `VectorStore` guarded); the
   gate is encoder-aware; legacy centroids still load.
6. **E-cache:** cache keys by content hash namespaced by space; a re-rendered image at a stable path
   recomputes instead of returning a stale vector.
7. **E-store:** atomic, corruption-tolerant; image vectors use a separate index from the 1024-d text index.
8. **Track Q:** an evaluation batch over `max_cost_usd` is blocked before any paid call; the judge model
   is pinned + `temperature=0`; centroid-build inputs are a curated allowlist.
9. **OBS:** the gate path emits telemetry; a drifted score distribution raises a `TICKET`; the observer
   never mutates the threshold.
10. Tests green (≥85% new-package coverage), lint/type clean, full suite passing; every DEFER named in §6.
