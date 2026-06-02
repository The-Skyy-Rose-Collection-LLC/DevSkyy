# orchestration/ — Cross-cutting pipelines + RAG + LLM workflows (33 files)

Coordination layer composing agents/services into end-to-end async pipelines. RAG retrieval, asset generation, brand learning, vector indexing, LLM routing shim, LangGraph re-exports.

## Architecture

```
RAG STACK (5 components)            ASSET PIPELINE                 LLM SHIM
─────────────────────────           ────────────────────────       ────────────────
embedding_engine.py     ─┐          asset_pipeline.py    ─┐        llm_clients.py
vector_store.py         ─┤   →      huggingface_3d_client─┤   →    llm_orchestrator.py
query_rewriter.py       ─┼─→        huggingface_asset_*  ─┤        llm_registry.py
reranker.py             ─┤          (Tripo + FASHN + WP) ─┘        model_config.py
catalog_retriever.py    ─┘                                         (older shim — see note)

BRAND LEARNING                      DOCUMENT INGESTION             ROUND TABLE 3D
────────────────────                ────────────────────           ─────────────────
brand_learning.py     (51k)         document_ingestion.py          threed_round_table.py (65k)
brand_context.py                    docs_context.py                (multi-judge 3D quality vote)
brand_integration.py                auto_ingestion.py
feedback_tracker.py
```

## Lazy import pattern

`__init__.py` uses `__getattr__` + `_LAZY_IMPORTS` dict mapping name → `(module, attr)`. **All public symbols import lazily** — prevents `langgraph`, `chromadb`, `mistralai`, `pinecone-client`, etc. from being required at top-level import. Optional deps fail at first use, not at import.

```python
from orchestration import ProductAssetPipeline   # only imports asset_pipeline submodule
```

## Surface (selected high-traffic exports)

| Symbol | Module | Role |
|--------|--------|------|
| `ProductAssetPipeline`, `PipelineConfig`, `PipelineStage` | `asset_pipeline.py` | 3D + try-on + WP attach, batched async (5 concurrent), Redis cache (7d TTL), WebSocket progress, Tripo3D + FASHN + Meshy |
| `DocumentIngestionPipeline`, `TextChunker`, `IngestionConfig`, `ingest_docs_directory` | `document_ingestion.py` | RAG ingestion |
| `BaseEmbeddingEngine`, `OpenAIEmbeddingEngine`, `SentenceTransformerEngine`, `create_embedding_engine` | `embedding_engine.py` | Embedding generation |
| `BaseVectorStore`, `ChromaVectorStore`, `PineconeVectorStore`, `create_vector_store`, `VectorSearchCache` | `vector_store.py` | LRU-cached vector DB abstraction |
| `AdvancedQueryRewriter`, `QueryRewriterConfig`, `QueryRewriteStrategy`, `RAGPipelineWithRewriting` | `query_rewriter.py` | HyDE + multi-query + step-back rewriting |
| `DomainRouter`, `TaskDomain` | `domain_router.py` | Intent → agent routing |
| `LLMOrchestrator`, `CompletionResult`, `RoutingStrategy`, `TaskType` | `llm_orchestrator.py` | Older LLM router shim (see note below) |
| `LLMRegistry`, `ModelDefinition`, `ModelCapability`, `ModelTier` | `llm_registry.py` | Model metadata catalog |
| `BrandLearningLoop`, `BrandMemory`, `BrandSignal`, `BrandInsight`, `BrandAdaptor` | `brand_learning.py` | Adaptive brand-voice updates from signals |
| `PromptEngineer`, `PromptChain`, `PromptTemplate`, `PromptTechnique` | `prompt_engineering.py` | Advanced prompting (CoT, ToT, ReAct templates) |
| `WorkflowState`, `WorkflowStatus`, `WorkflowEdge`, `StateGraph`, `END`, `START`, `add_messages` | `langgraph_integration.py` | LangGraph re-exports + workflow state base |
| `ToolRegistry`, `ToolDefinition`, `ToolCategory`, `ToolParameter` | (re-export from `core.runtime.tool_registry`) | Tool registration surface |
| `ModeAgent`, `ModeConfig`, `ReminderTransport` | `orchestration_mode.py` (+ `orchestration_mode_tools.py`) | Standing-consent fan-out loop: mid-conversation mode reminders toggle "fan out to parallel subagents by default" + `effort="xhigh"`. First streaming tool-use feedback loop in the repo. Raw `AsyncAnthropic`; `asyncio.gather`+`Semaphore` fan-out; **local bash, no sandbox**. Spec: `docs/superpowers/specs/2026-06-01-orchestration-mode-design.html` |

## `ProductAssetPipeline` (canonical entry point)

```python
from orchestration import ProductAssetPipeline

pipeline = ProductAssetPipeline()
result = await pipeline.process_product(
    product_id="12345",
    title="Signature Hoodie",
    description="...",
    images=["path/to/product.jpg"],
    category="apparel",
)

# Batch with progress callback
results = await pipeline.process_batch(products, progress_callback=cb)
```

- **Concurrency:** semaphore-bounded 5 concurrent products.
- **Caching:** Redis `devskyy:asset_pipeline:` prefix, 7-day TTL on 3D models. Graceful fallback if `redis.asyncio` unavailable.
- **Retry:** failed operations re-enqueued with exponential backoff.
- **Progress:** WebSocket callback per stage transition.
- **Metrics:** Prometheus counters/gauges/histograms (only if `prometheus_client` installed).

## `langgraph_integration.py` — Anti-reimplementation lesson

This module previously contained a parallel reimplementation of LangGraph (`WorkflowGraph`, `WorkflowManager`, `AgentNode`). The custom engine was **never used in production**. Only the data types (`WorkflowState`, `WorkflowStatus`) escaped, as base classes for `devskyy_workflows/`.

Now: re-exports canonical `langgraph.graph` primitives (`StateGraph`, `END`, `START`, `add_messages`) + keeps data types describing workflow shape. Canonical workflow wiring lives at `skyyrose/elite_studio/creative/router.py`.

**Lesson:** when an external library exists and works, do not write a parallel implementation. If you're tempted, write a thin adapter that re-exports.

## RAG pipeline (5-component stack)

```
query → query_rewriter.AdvancedQueryRewriter (HyDE/multi-query/step-back)
      → embedding_engine.SentenceTransformerEngine.embed()
      → vector_store.ChromaVectorStore.search() (LRU cache, 256 entries, 5min TTL)
      → reranker.CrossEncoderReranker.rerank() (cross-encoder model)
      → catalog_retriever.CatalogRetriever (WooCommerce join)
      → LLM completion w/ retrieved context
```

Cache hit/miss tracked in `VectorSearchCache._hits` / `_misses`. Persistence to ChromaDB by default; Pinecone available for cloud-scale (`skyyrose-catalog` index, us-west-2, dim=1024, cosine — per project memory).

## Conventions

- **Async-only public API.** Every pipeline exposes a single `process_*()` async method taking a typed request, returning a typed result dataclass.
- **Long-running progress:** WebSocket callback or `progress_callback: Callable[[Stage], None]`. See `asset_pipeline.py` for the canonical pattern.
- **Retry policy:** exponential backoff, max 3 attempts unless overridden. Use `tenacity` when you need declarative retry policies.
- **Cache reads/writes go through `services/storage/`** clients, not direct Redis calls. Exception: `asset_pipeline.py` predates the storage layer abstraction — fine for now, but new pipelines route through `services/`.
- **No sync I/O inside async pipelines.** If a sync vendor SDK is unavoidable, wrap in `asyncio.to_thread`.
- **Structlog, not stdlib logging.** Orchestration uses `structlog.get_logger(__name__)` for structured JSON logs. (api/ layer uses stdlib `logging` — don't mix.)

## Don't

- Don't put per-request HTTP handling here. That's `api/`.
- Don't replicate agent business logic. Orchestrators **compose** agents; they do not reimplement.
- Don't add a new orchestrator that synchronously blocks. If you must call sync code, wrap in `asyncio.to_thread`.
- Don't import from `orchestration/llm_clients.py` for new code. Use `llm/providers/` directly — the orchestration LLM shim predates the canonical `llm/` package and is kept only for back-compat.
- Don't introduce a parallel reimplementation of an external library (see `langgraph_integration.py` lesson above).

## Related

- Agents composed: `agents/` (especially the 6 SuperAgents)
- LLM providers: `llm/providers/` (canonical) — `orchestration/llm_clients.py` is legacy shim
- Services used: `services/storage/`, `services/notifications/`
- Triggered from: `api/dashboard.py`, scheduled tasks in `tasks/`
- LangGraph workflows live at: `skyyrose/elite_studio/creative/router.py`, `devskyy_workflows/`

## Recent learnings

- `orchestration/`, `llm/`, and `core/` have overlapping LLM infrastructure. **Canonical layer is `llm/`.** `orchestration/llm_clients.py` + `llm_orchestrator.py` + `llm_registry.py` are the older parallel codepath kept for back-compat.
- `threed_round_table.py` (65k) is the multi-judge 3D quality vote — separate from `llm/round_table.py` (which is text-completion only).
- `huggingface_3d_client.py` + `huggingface_asset_enhancer.py` are the HF Spaces clients for 3D + enhancement (each 40-50k lines).
- Phase 0 (Pathfinder, 2026-05-04): asset_pipeline.py + F2 LangGraph pipeline + F8 verdict documented as PARALLEL_INDEPENDENT (no shared state, safe to run concurrently).


<claude-mem-context>

</claude-mem-context>