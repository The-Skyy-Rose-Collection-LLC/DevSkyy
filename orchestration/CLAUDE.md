<claude-mem-context>

</claude-mem-context>

# orchestration/ — cross-cutting pipelines (32 Python files)

Coordination logic that spans multiple agents/services. Pipelines, routers, retrieval, indexing.

## Key files

- `asset_pipeline.py` — `ProductAssetPipeline` (Tripo3D + FASHN + WP upload). Async, batched (5 concurrent), Redis-cached (7-day TTL on 3D models), WebSocket progress, retry-with-exp-backoff.
- `agent_counter.py` — runtime metrics for agent invocation
- `auto_ingestion.py` — automatic asset ingestion from sources
- `brand_context.py`, `brand_integration.py`, `brand_learning.py` — brand-voice context loading and adaptive updates
- `catalog_retriever.py` — catalog retrieval over the WooCommerce corpus
- `domain_router.py` — routes incoming intents to the right agent
- `embedding_engine.py`, `enterprise_index.py` — vector indexing
- `vector_store.py` — `BaseVectorStore` + Chroma/Pinecone impls. **Namespace contract:** `namespace=None` means "no filter / default partition"; pass a string to scope writes/reads/deletes. Chroma emulates via `_namespace` metadata + `$and`-wrapped where clauses; Pinecone uses native namespaces. Cache keys participate in namespace.
- `docs_context.py`, `document_ingestion.py` — docs loading for RAG

## Embedding providers

`embedding_engine.py` ships four implementations behind `BaseEmbeddingEngine`:

| Provider | Class | Native dim | Asymmetric? | Notes |
|---|---|---|---|---|
| `sentence_transformers` | `SentenceTransformerEngine` | varies | no | local, default |
| `openai` | `OpenAIEmbeddingEngine` | 1536/3072 | no | needs `OPENAI_API_KEY` |
| `cohere` | `CohereEmbeddingEngine` | 1024/384 | yes (search_query / search_document) | needs `COHERE_API_KEY` |
| `voyage` | `VoyageEmbeddingEngine` | 1024 (configurable via MRL) | yes (query / document) | needs `VOYAGE_API_KEY`; sync SDK wrapped via `asyncio.to_thread` |

**Voyage notes:**
- Voyage's SDK is sync only — no `AsyncClient`. The engine wraps `client.embed()` with `asyncio.to_thread` to keep the event loop free.
- Use `embed_text()` / `embed_batch()` for indexing (sets `input_type="document"`) and `embed_query()` for retrieval (sets `input_type="query"`). Mismatching the type degrades retrieval quality measurably (~5–10% on MTEB).
- `voyage_output_dimension` triggers MRL truncation. Cache keys include `model + output_dimension` so config changes don't return stale embeddings from prior runs.
- SDK floor on Python 3.14: `voyageai>=0.2.4` (0.3.x is prerelease).

## Conventions

- Every pipeline is async. Public interface is a single `process_*()` method that takes a typed request and returns a typed result.
- Long-running pipelines emit progress via callback or WebSocket (see `asset_pipeline.py` for the pattern).
- Retry policy: exponential backoff, max 3 attempts unless overridden. Use `tenacity` if reaching for it.
- Cache reads/writes go through `services/storage/` clients, not direct Redis.

## Don't

- Don't put per-request HTTP handling here. That's `api/`.
- Don't replicate agent logic. Orchestrators COMPOSE agents; they do not reimplement.
- Don't run synchronous I/O inside an async pipeline. If you must call sync, wrap in `asyncio.to_thread`.

## Related

- Agents composed: `agents/` (especially the SuperAgents)
- Services used: `services/storage/`, `services/notifications/`
- Triggered from: `api/dashboard.py`, scheduled tasks in `tasks/`
