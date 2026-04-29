<claude-mem-context>

</claude-mem-context>

# services/ — internal service layer (45 Python files)

Reusable building blocks consumed by `agents/` and `api/`. Services are stateless or hold infrastructure clients (DB, cache, external APIs); they do not own user-facing flows.

## Key services

- `ai_image_enhancement.py` — image upscaling, restoration, color correction
- `image_deduplication.py` — perceptual-hash dedup for the imagery library
- `image_ingestion.py` — intake pipeline for uploaded assets
- `rag_anything_service.py` — RAG retrieval over the brand corpus
- `approval_queue_manager.py` — human-in-the-loop approval workflow
- subdirectories: `analytics/`, `competitive/`, `ml/`, `notifications/`, `storage/`, `three_d/`

## Conventions

- A service is a class or a small set of free functions with a clear init contract. No global state outside dependency injection.
- External-API calls go in `services/<vendor>_client.py` style modules; never embed vendor calls inside agents directly.
- All services that hit network or disk MUST be `async`. Sync services are only acceptable for pure CPU-bound work.
- Use structured logging with `logger = logging.getLogger(__name__)` at module level. Include correlation IDs when available.

## Don't

- Don't call services directly from frontend code; go through `api/`.
- Don't put feature flags or business rules in services. Those live in `agents/` or `config/`.
- Don't add a service that wraps a single function call — inline it. Services exist to share logic, not to add layers.

## Related

- Consumers: `agents/`, `api/`
- Storage backends: `services/storage/`, `database/`
- ML pipelines: `services/ml/`, `pipelines/`
