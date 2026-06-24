# Pathfinder — Handoff Prompts (Phase 4)

Four independent `/make-plan` handoffs. Each is self-contained and file:line-anchored. **Start with H1 — it is the keystone; H2–H4 are parallelizable after it.** All are code-level (no paid API, no production write).

---

## H1 — Wire the RAG manager + collapse the doc-context fork  (KEYSTONE)

```
/make-plan
Goal: Make RAGContextManager (the rich rewrite+rerank+cache doc reader) the live path for all 12 SuperAgents, and delete the primitive get_docs_context fork. Root cause is an unfinished DI wiring.

Context (verified file:line):
- RAGContextManager.get_context() lives at orchestration/rag_context_manager.py:296 and is correct (query rewrite, Cohere rerank, dedup, cache, scored RAGContext) but DEAD: core/registry/registrations.py:90-92 calls RAGContextManager() with no args while __init__ requires vector_store positionally (latent TypeError), and nothing resolves the "rag_manager" service.
- register_all_services() is NEVER called from main_enterprise.py lifespan (verified full read).
- api/dashboard.py:352 set_rag_manager() is defined but NEVER invoked.
- Live but primitive reader: orchestration/docs_context.py:62 get_docs_context(), called only at agents/base_super_agent/agent.py:562-566 (PromptTechnique.RAG, when no context kwarg). Returns raw top-k=3, no rewrite/rerank/cache, silent except: pass. Serves 12 agents (Commerce/Analytics/Creative/Marketing/Operations/Support/SkyyRoseContent/SkyyRoseImagery/CollectionContent/SecurityOps/WordPressAsset/CodingDoctor).
- Both read the SAME ChromaDB collection devskyy_docs. Writer = DocumentIngestionPipeline (document_ingestion.py:319/361), already on I1/I2.

Tasks:
1. Construct RAGContextManager with a real BaseVectorStore (prefer awaiting create_rag_context_manager() in an async startup hook over fixing the no-arg call).
2. Call register_all_services() from main_enterprise.py lifespan.
3. Inject the resolved "rag_manager" into EnhancedSuperAgent (wire set_rag_manager() or constructor injection).
4. Replace agent.py:562-566 with self._rag_manager.get_context(prompt).
5. Delete orchestration/docs_context.py::get_docs_context once no caller remains; grep to confirm zero callers.
6. VERIFY devskyy_docs is actually populated at runtime (the silent except:pass means agents may currently get empty context). If empty, add a startup ingest trigger or health check.
Constraints: TDD; tests/test_rag_integration.py already exercises the factory path — extend it. No behavior regression for SupportAgent which passes its own context=faq_context at lines 617/775.
```

---

## H2 — Consolidate embedding entrypoints onto I1

```
/make-plan
Goal: Every RAG embedding goes through orchestration/embedding_engine.py create_embedding_engine() (I1: providers + cache + config). Remove parallel/inline embedding instantiations.

Context (verified file:line):
- I1 factory: orchestration/embedding_engine.py:685.
- Bypass sites to fix: orchestration/auto_ingestion.py:279 (SentenceTransformer re-created PER CALL — perf bug); prompts/rag_mcp_hybrid.py:381 (a fully parallel local EmbeddingEngine class ignoring I1 cache/config).
- Removed for free by H1: orchestration/rag_context_manager.py:473 inline MiniLM fallback (engine becomes injected).
- LEAVE: orchestration/semantic_analyzer.py:415 (code-diff similarity) and llm/evaluation_metrics.py:73 (eval scoring) — specialized, not RAG. orchestration/reranker.py:427 voyageai.Client is rerank not embed — correct as separate.

Tasks: refactor the two actionable sites to call create_embedding_engine(); ensure dimension consistency with the devskyy_docs index; add a test asserting no module under orchestration/ except embedding_engine.py instantiates SentenceTransformer directly (guard against regression).
Constraints: do H1 first (removes the fallback site). TDD.
```

---

## H3 — Consolidate to one CLIP image embedder

```
/make-plan
Goal: One CLIP image-embedding module. Two exist with identical model (clip-vit-base-patch32, 512-d) and zero shared code.

Context (verified file:line):
- KEEP: skyyrose/core/clip_embedder.py:1 (thread-safe singleton; API embed_image/embed_text/cosine_similarity; wired into brand-gate via scripts/catalog_ml_audit.py:51 and scripts/measure_brand_centroid_gate.py:43).
- FOLD IN: scripts/image_embeddings/clip_embedder.py:14 (CLIPEmbedder; API encode_image/encode_batch/find_similar_images; only caller scripts/visual_product_recognition.py:108, CLI offline).
- LEAVE: skyyrose/core/dino_embedder.py (different model — DINO).

Tasks: port visual_product_recognition.py to the skyyrose/core singleton (map encode_image→embed_image, add a find_similar_images helper if needed); delete scripts/image_embeddings/ package (or reduce to a thin re-export); update scripts/image_embeddings/__init__.py consumers. Verify the .npy cache path in visual_product_recognition.py:125 still works.
Constraints: image-only island, no overlap with text I1/I2 — do not touch those. TDD where the package has tests.
```

---

## H4 — Remove dead RAG intent (housekeeping)

```
/make-plan
Goal: Eliminate dead/ambiguous RAG code so the map matches reality.

Context (verified file:line):
- orchestration/auto_ingestion.py AutoDocumentIngestion.ingest_all() (line 78) has ZERO production callers (grep across api/, agents/, scripts/, main_enterprise.py, core/registry). It also re-implements embedding inline (auto_ingestion.py:276-279). DECIDE: delete it, or wire it as the startup ingest for devskyy_docs (coordinate with H1's "verify populated" task). Do not leave dead.
- agents/base_super_agent/learning_module.py:307 flush_rag_queue() is a TODO stub writing an in-memory dict, referencing a non-existent Pinecone skyyrose-catalog index. Remove or implement.

Tasks: make the explicit keep/delete decision per item with the user; if deleting, grep-confirm zero references and remove cleanly (update __all__, __init__ exports); if wiring auto_ingestion, route its embedding through I1 (see H2).
Constraints: this is the "update EVERY file that references deleted code" rule — full grep sweep before and after.
```

---

## Map at a glance (for the planner)
- **Merge:** H1 (F1⊃F5), H2 (→I1), H3 (one CLIP). **Cleanup:** H4.
- **Keep separate (no handoff):** F3 catalog QA · F4 multimodal billing-gated KB · F6 brand SQLite feedback loop.
- **Not app-side (no change):** knowledge-base/ markdown, graphify graph.json — dev tooling, not runtime RAG corpora.
