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
- `docs_context.py`, `document_ingestion.py` — docs loading for RAG

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
