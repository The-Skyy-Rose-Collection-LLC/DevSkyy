# Pathfinder — Duplication Report (Phase 2)

Scope: DevSkyy **app-side** RAG / retrieval / embedding stack. Method: 7 per-feature flowcharts (Phase 1) + 2 cross-feature duplication subagents (Phase 2), every claim file:line-grounded. Discipline applied: **specialization ≠ duplication** — two stores serving different trust models / consumers / data are legitimately separate even when the code rhymes.

---

## Verdict table

| # | Candidate | Verdict | Action |
|---|-----------|---------|--------|
| D1 | **F5 `get_docs_context` vs F1 `RAGContextManager.get_context`** — both read ChromaDB `devskyy_docs` for the same 12 agents | **TRUE DUPLICATE (accidental fork)** | Collapse F5 into F1; fix F1's wiring |
| D2 | **Inline embedding instantiations** bypassing I1 `create_embedding_engine()` | **TRUE DUPLICATE (scattered)** | Route through I1 |
| D3 | **Two CLIP image embedders** — `scripts/image_embeddings/clip_embedder.py` (F7) vs `skyyrose/core/clip_embedder.py` | **TRUE DUPLICATE (parallel impl)** | Pick one image-embedder module |
| D4 | F3 `CatalogRetriever` "bypasses" I2 vector-store abstraction | **REFUTED — not a duplicate** | None; F3 uses I1/I2 factories correctly |
| D5 | F2 LightRAG `skyyrose-catalog` vs F3 Pinecone `skyyrose-catalog-v1` "duplicate catalog content" | **REFUTED — specialized** | Keep separate |
| D6 | F4 `RAGAnythingService` | **Specialized — distinct stack/trust** | Keep separate |
| D7 | F6 `brand-learning` | **Orthogonal — SQLite feedback loop, not RAG** | Exclude from RAG merge |
| S1 | **Dead DI wiring** — `register_all_services()` never called; `set_rag_manager()` never invoked | **Systemic gap (root cause of D1)** | Complete the wiring |

---

## D1 — F1 vs F5: the central accidental fork  (TRUE DUPLICATE)

Both target **the same ChromaDB collection `devskyy_docs`** to feed retrieved context to the same agents.

- **F5 `get_docs_context()`** (`orchestration/docs_context.py:62`) is the **live** reader. Sole call site: `agents/base_super_agent/agent.py:562-566`, fired when `PromptTechnique.RAG` is selected and no `context` kwarg was supplied. It serves **12 production agent classes** (Commerce, Analytics, Creative, Marketing, Operations, Support, SkyyRoseContent, SkyyRoseImagery, CollectionContent, SecurityOps, WordPressAsset, CodingDoctor). Returns raw top-k (k=3 hardcoded), **no rewrite, no rerank, no cache**, silent `except: pass`.
- **F1 `RAGContextManager.get_context()`** (`orchestration/rag_context_manager.py:296`) is the **richer, correct** abstraction (query rewrite incl. HyDE, Cohere rerank, dedup, cache, scored `RAGContext` dataclass) — but it is **dead at runtime**: its only registration (`core/registry/registrations.py:90-92`) calls `RAGContextManager()` with no args while `__init__` requires `vector_store` positionally → latent `TypeError`; and nothing ever resolves the `"rag_manager"` service or calls `set_rag_manager()`.

**Why this is a fork, not specialization:** identical consumer (the same agents), identical store (`devskyy_docs`), identical need (doc context). F5 exists *only because* F1 was never wired. The wired path is the worse one.

**Action:** delete F5; replace `agent.py:562-566` with an injected `self._rag_manager.get_context(prompt)`; fix F1's construction + DI resolution (see S1).

---

## D2 — Inline embedding paths bypassing I1  (TRUE DUPLICATE, scattered)

`orchestration/embedding_engine.py` (I1) is the shared engine (`create_embedding_engine()` :685, providers: SentenceTransformers/OpenAI/Cohere/Voyage, with cache + config). These sites re-instantiate models directly instead:

| Site | What | RAG-relevant? |
|------|------|---------------|
| `orchestration/auto_ingestion.py:279` | `SentenceTransformer("all-MiniLM-L6-v2")` re-created **per call** | YES — actionable (also dead code, see F4 map) |
| `prompts/rag_mcp_hybrid.py:381` | a **parallel local `EmbeddingEngine` class** lazy-loading MiniLM, ignoring I1 cache/config | YES — actionable |
| `orchestration/rag_context_manager.py:473` | inline MiniLM **fallback** when no embedder injected ("dimension-fragile") | YES — disappears once F1 wired with injected engine |
| `orchestration/semantic_analyzer.py:415` | MiniLM for **code-diff** similarity | No — specialized, leave |
| `llm/evaluation_metrics.py:73` | MiniLM for **eval scoring** | No — specialized, leave |
| `orchestration/reranker.py:427` | `voyageai.Client` for **rerank** (not embed) | No — correct separate concern |

**Action:** route auto_ingestion + rag_mcp_hybrid through `create_embedding_engine()`. The two "specialized" code/eval uses are legitimately separate.

---

## D3 — Two CLIP image embedders  (TRUE DUPLICATE, parallel impl)

- `scripts/image_embeddings/clip_embedder.py:14` (F7) — `CLIPEmbedder`, model `clip-vit-base-patch32` (512-d), API `encode_image/encode_batch/find_similar_images`. Offline CLI only.
- `skyyrose/core/clip_embedder.py:1` — a thread-safe singleton, **same model**, different API `embed_image/embed_text/cosine_similarity`. Used by `catalog_ml_audit.py:51` + `measure_brand_centroid_gate.py:43`.
- (`skyyrose/core/dino_embedder.py` is a different model — DINO — legitimately separate.)

Two implementations of the identical CLIP model with zero shared code. **Action:** consolidate to one CLIP module (prefer the `skyyrose/core/` singleton — it's the one wired into the brand-gate path).

---

## D4 — REFUTED: F3 does NOT bypass I2

`orchestration/catalog_retriever.py` imports `create_embedding_engine` + `create_vector_store` (no `import pinecone`). `for_production()` (`:626-660`) builds `EmbeddingConfig(provider=VOYAGE)` + `VectorStoreConfig(db_type=PINECONE)` through the factories. I2's `PineconeVectorStore` (`vector_store.py:588`) is a **real implementation** (all 5 methods, real `Pinecone()` client at :605), not a stub. F3 is a correct consumer of the shared substrate. **No action.**

---

## D5 — REFUTED: F2 and F3 hold DIFFERENT content

- F3 → Pinecone `skyyrose-catalog-v1` / ns `catalog`: one vector per SKU, composed from CSV+dossier (`branding_block+scene_setting+garment_type_lock+name+collection+description`). Flat semantic SKU index.
- F2 → LightRAG `data/raganything/skyyrose-catalog/`: a knowledge **graph** + NanoVectorDB built from **user-uploaded multimodal files** via `POST /collections/{c}/ingest`. **No production code auto-populates it from the CSV** (`commerce_agent.py:614-620` only *queries* it). Service docstring (`rag_anything_service.py:13`): "does not bridge to the existing ChromaDB/Pinecone stack."

Shared `skyyrose-catalog` name prefix is coincidental intent, not shared data. Merging would destroy F2's graph traversal. **Keep separate.**

> Note: `agents/base_super_agent/learning_module.py:307` has a `TODO: wire to Pinecone (skyyrose-catalog index)` stub (`flush_rag_queue()` only writes an in-memory dict) — a *third* dangling reference to a catalog index that isn't wired. Not a duplicate; a dead intent. Flag for cleanup.

---

## D6 / D7 — Specialized, exclude from RAG merge

- **F4 `RAGAnythingService`** — LightRAG graph+vector stack, multimodal ingest, **billing-gated** (`EntitlementChecker`/`UsageMetering`), tenant-scoped. Distinct trust model. Keep separate lane.
- **F6 `brand-learning`** — SQLite (`data/brand_learning.db`, 3 tables), statistical accept/reject pattern analysis, **zero embedding/vector imports** (bi-directional grep clean vs I1/I2). It's a feedback loop, not retrieval. Does **not** belong in a unified RAG proposal.

---

## S1 — Systemic root cause: the DI wiring was never completed

The richer RAG abstraction (F1 + I1–I4) **exists and is correct**, but the dependency-injection chain that would put it into production was never finished:
- `register_all_services()` is **never called** from `main_enterprise.py`'s lifespan (verified full read).
- `api/dashboard.py:set_rag_manager()` is **defined but never invoked**.
- `registrations.py:92` would `TypeError` even if resolved.

This single gap is *why* D1 exists (agents fell back to the primitive F5) and *why* D2's `rag_context_manager.py:473` fallback embedder exists. **Fixing S1 is the keystone** — it makes the good path reachable and collapses D1 + part of D2 as a consequence.

---

## What is genuinely ONE thing vs MANY

**Should be one:** the document-context reader (D1: F1 swallows F5) · the embedding entrypoint (D2: I1) · the CLIP image embedder (D3).
**Legitimately many:** catalog QA retriever (F3, Pinecone+Voyage+Haiku compose) · multimodal billing-gated KB (F4, LightRAG) · brand feedback loop (F6, SQLite). Different consumers, stores, trust models — each earns its separation.
