<claude-mem-context>

</claude-mem-context>

# api/v1/clothing_3d/ — TRELLIS clothing 3D pipeline (sync + async)

FastAPI surface for the TRELLIS-backed clothing-to-3D pipeline. Sync execution for internal callers; async job queue (Redis Streams) for production. Mount: `app.include_router(clothing_3d_router, prefix="/v1/clothing-3d")`.

## Key files

- `router.py` — endpoints + lazy process-level singletons (`get_pipeline`, `get_queue`, `get_store`, `get_idempotency`).
- `schemas.py` — Pydantic wrappers (`GenerateRequest` subclasses `PipelineRequest`; `GenerateResponse`, `JobAcceptedResponse`, `JobStatusResponse`, `HealthResponse`).
- `__init__.py` — re-exports `router`.

## Endpoints

| Path | Purpose |
|------|---------|
| `POST /generate` | Synchronous pipeline run; returns `GenerateResponse` |
| `POST /generate/async` | Enqueue job, returns `202` + `job_id` + `status_url` |
| `GET /jobs/{job_id}` | Poll async job status |
| `GET /jobs` | List up to 100 recent jobs |
| `GET /health` | TRELLIS provider liveness + capabilities |
| `GET /ready` | Queue + store reachable (503 if not) |
| `GET /info` | Active config (backend, quality, sampling, capabilities, queue depth) |
| `GET /metrics` | Prometheus scrape (`include_in_schema=False`) |

## Conventions

- Async path: `JobQueue` (Redis Streams when `REDIS_URL` set, in-memory otherwise) + `JobStore` for persistence. The worker (`python -m pipelines.clothing_3d.worker`) picks up jobs — the router never blocks on pipeline execution.
- Sync + async both share `IdempotencyCache` keyed on `request_fingerprint(body)` — identical inputs return cached result instead of re-running. `cache_total{outcome="hit"|"miss"}` Prometheus counter tracks rates.
- Process-level singletons: pipeline, queue, store, and idempotency cache are lazy-initialized via module-level globals. Tests inject by replacing `_pipeline` etc. before request.
- Error envelope: `502 Bad Gateway` for pipeline runtime failures, `503 Service Unavailable` for queue failures, `429 Too Many Requests` for `QuotaExceededError` (cost cap breach).
- `correlation_id` defaults to `job_id` when caller omits it — keeps traces linkable across worker/store/observability.

## Don't

- Don't call `pipeline.run()` from a sync handler without going through `IdempotencyCache.get_or_run()` — the cache also enforces the cost quota gate.
- Don't reach into `pipeline.provider._backend` outside the health endpoint; the underscore signals test injection territory.
- Don't return raw `PipelineResult` from a `FAILED` state with `ok=True`. The endpoint inspects `result.status` and flips `ok` accordingly — preserve that contract.

## Related

- Pipeline impl: `pipelines/clothing_3d/{pipeline,job_store,queue,reliability,observability,worker}.py`
- TRELLIS config: `services/three_d/trellis/config.py`
- Worker entry: `python -m pipelines.clothing_3d.worker`
- Models: `pipelines/clothing_3d/models.py` (`PipelineRequest`, `PipelineResult`, `PipelineStatus`)
