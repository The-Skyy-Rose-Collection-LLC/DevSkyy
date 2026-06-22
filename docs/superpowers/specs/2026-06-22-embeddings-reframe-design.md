# Embeddings Reframe — Design Spec

**Date:** 2026-06-22
**Status:** Approved (design) — pending spec review
**Scope:** Reconfigure, enhance, and unify the visual/text embedding subsystem under `skyyrose/`.

---

## 1. Goal

Turn the two copy-pasted embedder singletons + a disconnected script duplicate + ad-hoc
sidecar persistence into one coherent, configurable embeddings package under
`skyyrose/core/embeddings/`, with a real vector store — **without breaking the live render
pipeline** that depends on the QC gates.

Three verbs from the request:
- **Configure** — one `EmbeddingConfig` instead of constants scattered across each embedder.
- **Enhance** — shared base (kill duplication), batch encode + caching, the missing `VectorStore`.
- **Redo/unify** — fold the `scripts/` CLIP duplicate and ad-hoc sidecars into the package.

## 2. Current state (verified 2026-06-22)

| Piece | Where | Problem |
|---|---|---|
| CLIP embedder | `skyyrose/core/clip_embedder.py` | Singleton, 512-d (`clip-vit-base-patch32`), image+text. Hardcoded `MODULE_ID`/`EMBED_DIM`; re-implements `_select_device`/`_l2_normalize`/lazy-lock. |
| DINO embedder | `skyyrose/core/dino_embedder.py` | Singleton, 768-d (`facebook/dinov2-base`), image. **Duplicates** the same device/norm/lock helpers + constants. |
| Script duplicate | `scripts/image_embeddings/clip_embedder.py` | OOP `CLIPEmbedder`, reimplements CLIP, used only by `scripts/image_embeddings/config.py`. Disconnected from production. |
| Persistence | `elite_studio/data/brand_centroid.npz` (+ ad-hoc) | No unified store; the 512-d image vectors have no home. Pinecone `skyyrose-catalog` (1024-d) holds **Gemini text**, not CLIP images. |
| Config | none | Model IDs / dims / device policy are hardcoded per-file. |

**Consumers (7 import sites):**
`skyyrose/elite_studio/quality/{brand_centroid:34, clip_alignment:25, embedding_gate:21, render_quality:35}`,
`skyyrose/elite_studio/platform/fidelity/metrics.py:38` (lazy),
`scripts/{catalog_ml_audit.py:51, measure_brand_centroid_gate.py:43}`.

**Live render path (must not break):**
`elite_studio/agents/compositor/orchestrator.py:733-742` and
`agents/compositor/stage_g_visual_qa.py:156-164` call **`embedding_gate.evaluate(shadow_path, centroid)`**
+ **`brand_centroid.load_centroid()`** (loading `brand_centroid.npz`). These call the *quality-module*
public API, not the embedders directly — that is the safety seam.

## 3. Target architecture

```
skyyrose/core/embeddings/
├── __init__.py     # package exports: get_clip, get_dino, EmbeddingConfig, VectorStore, ...
├── config.py       # EmbeddingConfig (frozen): model IDs, dims, device policy, store backend
├── base.py         # Encoder protocol + _BaseEncoder: shared device-select, L2-normalize,
│                   #   thread-safe lazy singleton, transformers>=5 output handling
├── clip.py         # ClipEncoder(_BaseEncoder): embed_image / embed_text (512-d)
├── dino.py         # DinoEncoder(_BaseEncoder): embed_image (768-d)
└── store.py        # VectorStore protocol + LocalVectorStore (default) + PineconeImageStore (adapter)
```

- **`EmbeddingConfig`** (frozen dataclass): `clip_model_id`, `clip_dim`, `dino_model_id`, `dino_dim`,
  `device` (`auto`→cuda>mps>cpu), `store_backend` (`local`|`pinecone`), `store_path`, optional
  `pinecone_index`. One place to change models/dims/device/store. Read from env with safe defaults.
- **`_BaseEncoder`** absorbs the duplicated `_select_device`, `_l2_normalize`, double-checked-lock
  singleton, and the `transformers>=5` `BaseModelOutputWithPooling` handling — `clip.py`/`dino.py`
  become thin (model load + forward).
- **`VectorStore` port** (Protocol): `upsert(id, vector, meta)`, `query(vector, k)`, `get(id)`,
  `all()`, `save()/load()`. Default **`LocalVectorStore`** (SQLite + numpy cosine; FAISS optional if
  installed) — zero infra, zero cost, offline. **`PineconeImageStore`** adapter targets a *new*
  512-d (and 768-d) **image** index — never the 1024-d text index. Resolves the dim mismatch by
  separation, not by re-indexing.
- The existing `brand_centroid.npz` sidecar is read/written through `LocalVectorStore` (or a
  thin compat loader) so `brand_centroid.load_centroid()` keeps returning the same array.

## 4. Migration — Option B (hard migrate) + render-path orchestration

**Principle:** the render pipeline calls `embedding_gate.evaluate()` and
`brand_centroid.load_centroid()`. Those two function signatures + return types are a **frozen
contract** for this phase. Everything underneath can change; those cannot.

**Sequence (each step verified green before the next):**
1. Build the new `skyyrose/core/embeddings/` package + tests (no consumer touched yet).
2. Re-point the **4 quality consumers** (`brand_centroid`, `clip_alignment`, `embedding_gate`,
   `render_quality`) + `platform/fidelity/metrics.py` to `from skyyrose.core.embeddings import ...`.
   Keep their *own* public APIs (`embedding_gate.evaluate`, `brand_centroid.load_centroid`,
   `render_quality.*`) byte-identical in signature/return.
3. Re-point the **2 scripts** (`catalog_ml_audit`, `measure_brand_centroid_gate`).
4. Replace `scripts/image_embeddings/clip_embedder.py` (OOP duplicate) with a thin wrapper over
   the package, or delete + update `scripts/image_embeddings/config.py`.
5. Delete the old `skyyrose/core/clip_embedder.py` + `dino_embedder.py` (no shim — Option B).
6. **Render-path verification:** run the compositor Stage-G visual-QA tests + an
   `embedding_gate.evaluate()` smoke against a fixture render + `brand_centroid.npz`; confirm the
   gate verdict is unchanged vs current `main` (golden value).

**Orchestration:** steps 2-4 are independent per-file → can be done as parallel review/edit units,
but the **render-path verification (step 6) gates the whole change** and runs last on the integrated result.

## 5. Enhancements (in scope)

- Batch encode (`embed_images(list)`) on the base — folds the script's `encode_batch`.
- Optional cache: `VisualIndex`-style `embed_or_get(id, source)` backed by the store (skip recompute).
- Central device + dim config; `transformers>=5` handling in one place.

## 6. Error handling

- Encoders raise `ValueError` on empty/blank input (preserve current `embed_text` behavior); never
  return un-normalized vectors. Device selection never raises (falls back to cpu).
- `LocalVectorStore` is corruption-tolerant: a missing/garbage store file → empty store + WARNING,
  never a crash on the render path.
- Model load failure surfaces a clear `EmbeddingError` (not a bare HF traceback).

## 7. Testing

- **Encoders:** dim/normalization/determinism with a mocked model; device fallback.
- **Store:** local round-trip (upsert→query→get), cosine ordering, corruption tolerance, save/load.
- **Migration safety:** every re-pointed consumer imports + its public API unchanged (signature test).
- **Render-path golden:** `embedding_gate.evaluate(fixture, brand_centroid.npz)` verdict == current
  `main` value (the no-break proof).
- Target ≥85% on the new package; `ruff`/`black`/`mypy` clean; full `pytest` green.

## 8. Out of scope / risks

- The `.[all]` cryptography/mlflow dependency break is **separate** (a concurrent fix exists) — this
  reframe doesn't depend on `mlflow`.
- Pinecone *image* index creation is optional/deferred — `LocalVectorStore` is the default; the
  adapter ships but isn't wired to a live index this phase (no paid call, no STOP-AND-SHOW).
- Re-embedding the catalog is a follow-up; this phase preserves existing vectors/sidecars.

## 9. Success criteria

1. One `skyyrose/core/embeddings/` package; old duplicate embedders + script duplicate gone.
2. All 7 consumers migrated (Option B); render-path golden verdict unchanged.
3. `EmbeddingConfig` is the single place to change model/dim/device/store.
4. `VectorStore` local default works with zero infra; Pinecone-image adapter present behind the port.
5. Tests green (≥85% new-package coverage), lint/type clean, full suite passing.
