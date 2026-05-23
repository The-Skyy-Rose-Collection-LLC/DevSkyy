# services/ — Internal Service Layer (52 Python files)

Reusable building blocks consumed by `agents/`, `api/`, and `pipelines/`. Services are stateless or hold infrastructure clients (DB, cache, external APIs); they do not own user-facing flows.

## Top-level services

- `ai_image_enhancement.py` — `LuxuryImageEnhancer` (bg removal, upscale, product image generation, vision interrogation)
- `image_deduplication.py` — perceptual-hash dedup for the imagery library
- `image_ingestion.py` — intake pipeline for uploaded assets
- `rag_anything_service.py` — RAG retrieval over the brand corpus
- `approval_queue_manager.py` — human-in-the-loop approval workflow (~6.6k tok module)

## Subpackages (each has its own CLAUDE.md)

| Subpackage | Purpose |
|------------|---------|
| `analytics/` | Event collector → rollup scheduler → alert engine → notifier |
| `competitive/` | Competitor asset extraction + price/style analytics |
| `ml/` | Replicate, Gemini (optional), pipeline orchestrator, processing queue, watermarking |
| `ml/enhancement/` | Background removal, upscaling, lighting normalization, format optimization, authenticity validation |
| `ml/prompts/` | Vision model prompt templates (description, SEO, tags, features) |
| `ml/schemas/` | Pydantic schemas for image-to-description pipeline |
| `notifications/` | Email service + alerting transports |
| `storage/` | Cloudflare R2 + asset versioning with retention policies |
| `three_d/` | 3D provider abstraction with failover (Replicate, Tripo, HF, Gemini, TRELLIS) |
| `three_d/trellis/` | Microsoft Structured 3D Latents pipeline for clothing |

## Conventions

- A service is a class or a small set of free functions with a clear init contract. No global state outside dependency injection
- External-API calls go in `services/<vendor>_client.py` style modules; never embed vendor calls inside agents directly
- All services that hit network or disk MUST be `async`. Sync services are only acceptable for pure CPU-bound work
- Use structured logging with `logger = logging.getLogger(__name__)` at module level. Include correlation IDs when available

## Cross-Cutting Patterns

These three patterns recur across many services — when adding new services, follow the same conventions:

- **Optional-import guards** — heavy SDK deps (e.g., `google-genai`) are imported in try/except blocks. The symbol becomes `None` if unavailable. Consumers MUST guard before use. Examples: `GeminiClient` (`services/ml/__init__.py:73-77`), `GeminiImageProvider` (`services/three_d/__init__.py:34-38`)
- **Process-level singletons** — `get_*_service()` / `get_*_engine()` / `get_*_factory()` accessors return cached process-scoped instances. Tests must reset or mock between cases. Examples: `get_email_service`, `get_alert_engine`, `get_alert_notifier`, `get_provider_factory`
- **STOP-AND-SHOW gate** — every paid ML / 3D / vision call surfaces SKU + cost estimate before dispatch (per project STOP-AND-SHOW protocol). Enforced inside `services/ml/processing_queue.ProcessingQueue` and `services/three_d/provider_factory.ThreeDProviderFactory`

## Don't

- Don't call services directly from frontend code; go through `api/`
- Don't put feature flags or business rules in services. Those live in `agents/` or `config/`
- Don't add a service that wraps a single function call — inline it. Services exist to share logic, not to add layers
- Don't bypass `services/storage/AssetVersionManager` for catalog imagery — direct `R2Client.put()` loses version tracking
- Don't invoke paid ML / 3D providers directly — always route through `services/ml/processing_queue.FallbackChain` or `services/three_d/provider_factory.ThreeDProviderFactory`

## Related

- Consumers: `agents/`, `api/`, `pipelines/`
- Storage backends: `services/storage/`, `database/`
- ML pipelines: `services/ml/`, `pipelines/clothing_3d/`
- Brand-voice canon (drives vision prompts): `knowledge-base/seed/from-interview.md`


<claude-mem-context>

</claude-mem-context>