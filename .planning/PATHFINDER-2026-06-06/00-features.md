# Pathfinder — Feature Map (Phase 0)  ·  DevSkyy app-side RAG/retrieval/embedding

Seed: `#S1336` (graphify KB update) → interpreted as **map the app-side knowledge/retrieval/RAG/embedding systems, find duplication, propose one architecture**. NOT the Claude-Code session-memory layer (.wolf / claude-mem / Serena / auto-memory) — that serves a different consumer/trust model and is a legitimately separate opt-in target.

This file is the index. Per-feature flowcharts → `01-flowcharts/`. Duplication verdicts → `02-duplication-report.md`. Architecture → `03-unified-proposal.md`. Handoffs → `04-handoff-prompts.md`.

> Reconciled to final verified state (Phase 2). Where Phase 0 first-pass guesses were later refuted, the refutation is noted inline.

---

## Core features (7) — each mapped in 01-flowcharts/

| ID | Feature | Entry (file:line) | Store | Verdict |
|----|---------|-------------------|-------|---------|
| **F1** | orchestration-rag-pipeline | `orchestration/rag_context_manager.py:296` `get_context()` | ChromaDB `devskyy_docs` | **KEEP+WIRE** (rich reader, currently dead) |
| **F2** | raganything-multimodal-rag | `api/v1/rag_anything.py:116,163` → `services/rag_anything_service.py` | LightRAG NanoVectorDB (separate) | **KEEP SEPARATE** (billing-gated, multimodal) |
| **F3** | catalog-retriever | `orchestration/catalog_retriever.py:352` `answer_question()` | Pinecone `skyyrose-catalog-v1` ns `catalog` (Voyage) | **KEEP SEPARATE** (specialized; uses I1/I2 correctly) |
| **F4** | document-ingestion | `orchestration/document_ingestion.py:319/361` (live); `auto_ingestion.py:78` (dead) | writes ChromaDB `devskyy_docs` | writer of F1's store; dead AutoDocumentIngestion → H4 |
| **F5** | docs-context | `orchestration/docs_context.py:62` `get_docs_context()` | ChromaDB `devskyy_docs` (same as F1) | **DELETE** (primitive fork of F1) |
| **F6** | brand-learning | `orchestration/brand_learning.py:948` `BrandLearningLoop` | SQLite `brand_learning.db` | **EXCLUDE** (feedback loop, not RAG) |
| **F7** | image-embeddings | `scripts/image_embeddings/clip_embedder.py:14` | none (optional .npy cache) | **CONSOLIDATE** w/ `skyyrose/core/clip_embedder.py` |

## Shared infrastructure (4)

| ID | Component | file:line | Role |
|----|-----------|-----------|------|
| **I1** | embedding-engine | `orchestration/embedding_engine.py:685` `create_embedding_engine()` | ST/OpenAI/Cohere/Voyage + cache + config |
| **I2** | vector-store | `orchestration/vector_store.py:810` `create_vector_store()` | ChromaDB + Pinecone (both real impls) |
| **I3** | query-rewriter | `orchestration/query_rewriter.py:40` | HyDE / sub-query / step-back |
| **I4** | reranker | `orchestration/reranker.py` (Voyage client :427) | Cohere/Voyage rerank |

## Out of scope (verified, no app-side change)
- **knowledge-base/** markdown — NOT ingested by app RAG (AutoDocumentIngestion scans `docs/`, `README.md`, `CLAUDE.md`, `.claude/` only — `auto_ingestion.py:47-52`).
- **graphify graph.json** — dev tool output, not read by app code. The `#S1336` seed points at the legend, not the territory.
- **CC session-memory layer** (.wolf / claude-mem / Serena / auto-memory) — different consumer/trust model; separate opt-in target, never folded into product RAG.

---

## Duplication signals (Phase 0 hypotheses → Phase 2 outcome)

| Signal | Phase 0 guess | Phase 2 outcome |
|--------|---------------|-----------------|
| F1 vs F5 over `devskyy_docs` | duplicate | **CONFIRMED** — accidental fork (D1) |
| Inline embedding bypassing I1 | duplicate | **CONFIRMED** — scattered (D2) |
| Two CLIP embedders | duplicate | **CONFIRMED** — parallel impl (D3) |
| F3 hand-rolls Pinecone, bypasses I2 | suspected | **REFUTED** — F3 uses I1/I2 factories (D4) |
| F2 vs F3 duplicate catalog content | suspected | **REFUTED** — different content, name-prefix collision only (D5) |
| Root cause | — | **S1: DI wiring (`register_all_services`) never called from lifespan** — the keystone |

> Phase 0 first-pass also described F3's catalog content as `branding_spec+description+name` — that was an OLDER code version. Verified actual composition: `dossier_loader.get_product_with_dossier()` = name+collection+garment_type_lock+branding_block+scene_setting+description. Corrected here.

**Boundary decision (self-approved):** flowchart F1–F7; treat I1–I4 as shared substrate (not separate features); exclude enterprise-index peripheral and the 3 opt-in out-of-scope targets above.
