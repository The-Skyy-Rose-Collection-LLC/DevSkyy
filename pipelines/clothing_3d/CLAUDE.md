# pipelines/clothing_3d/ — Clothing 3D Pipeline

**End-to-end orchestration around `services.three_d.trellis.TrellisProvider`.** Production-hardened with retries, idempotency, cost quotas, persistent job state, and pluggable queue/store backends.

12 modules. Canonical template for any future cross-service pipeline.

## Stage Sequence

```
ingest → preprocess → TRELLIS generate → postprocess (mesh + USDZ + thumbnail) → QC gate → store → emit events
```

Stages return `(StageReport, stage_output)`. Orchestrator (`pipeline.py:ClothingPipeline`) owns timing, retries, event emission; stages stay focused.

## Public Surface (`pipelines/clothing_3d/__init__.py`)

| Group | Symbols | Source |
|-------|---------|--------|
| Orchestrator | `ClothingPipeline` | `pipeline.py` |
| Worker | `PipelineWorker` | `worker.py` |
| Models | `PipelineRequest`, `PipelineResult`, `PipelineStage`, `PipelineStatus`, `PipelineQualityReport`, `StageReport` | `models.py` |
| Queue | `JobQueue` (Protocol), `QueueMessage`, `InMemoryQueue`, `RedisStreamsQueue`, `build_queue()` | `queue.py` |
| Job store | `JobStore` (Protocol), `JobRecord`, `InMemoryJobStore`, `RedisJobStore`, `build_job_store()` | `job_store.py` |
| Reliability | `RetryPolicy`, `IdempotencyCache`, `IdempotencyStore`, `InMemoryIdempotencyStore`, `CostQuota`, `QuotaExceededError`, `request_fingerprint()` | `reliability.py` |
| Storage | `ArtifactStore` (Protocol), `ArtifactBundle`, `LocalArtifactStore` | `storage.py` |
| Events | `PipelineEvent`, `PipelineEventBus` | `events.py` |
| Observability | `PipelineMetrics`, `configure_logging`, `get_metrics`, `metrics_event_subscriber`, `render_metrics` | `observability.py` |

## Reliability Primitives (`reliability.py`)

| Primitive | Behavior |
|-----------|----------|
| `RetryPolicy` | Exponential backoff with **full jitter**, capped attempts. Default: `max_attempts=3`, `base_delay=2s`, `max_delay=60s`, `multiplier=2.0`. Retries `TimeoutError`, `ConnectionError`, `asyncio.TimeoutError` |
| `request_fingerprint(req)` | Content-addressed hash (image bytes + options). Same fingerprint → same cached `PipelineResult` |
| `IdempotencyCache` | Lookup by fingerprint; returns cached result if hit. **Wraps every paid backend dispatch** |
| `CostQuota` | Per-backend spend ceiling with token-bucket-style rolling window. Short-circuits before dispatch if quota exceeded |

## Hard Rules

- **`IdempotencyCache.get_or_run()` is the mandatory gate for paid backend dispatch** — Replicate, Modal. Skipping it bypasses both cost quota AND result reuse. Same rule as `api/v1/clothing_3d/*`
- **Two-tier queue envelope** — `QueueMessage` carries only `job_id` (small); full `JobRecord` lives in `JobStore`. Do not stuff `PipelineRequest` into the queue
- **Redis Streams with consumer groups** for production (`RedisStreamsQueue`). At-least-once delivery; `XACK` only on success; crashed worker's job auto-reclaimed via `XCLAIM`. `InMemoryQueue` is dev/test only
- **Protocol-typed swap-in everywhere** — `JobStore`, `JobQueue`, `IdempotencyStore`, `ArtifactStore` are all `@runtime_checkable Protocol`. `InMemory*` defaults, swap to Redis / disk in prod via env-driven `build_*()` factories
- **Stages own one job** — no cross-stage state mutation. Hand off via `PipelineContext` tuple return
- **QC gate is mandatory** — `stage_qc` produces `PipelineQualityReport`. Pipeline returns `PipelineStatus.FAILED` if thresholds not met. Do not skip QC for "trusted" requests
- All events flow through `PipelineEventBus` — never log lifecycle state outside the bus. `metrics_event_subscriber` and `log_event_subscriber` are default subscribers
- **`PipelineRequest` / `PipelineResult` are Pydantic v2 frozen DTOs** — never mutate after construction
- New garment categories: extend `services.three_d.trellis.garment_aware.GarmentCategory`, not pipeline-local code
- Worker lifecycle: `PipelineWorker.run()` consumes from queue → loads `JobRecord` from store → runs `ClothingPipeline` → updates record → ACKs message. Crash before ACK = redelivery

## Entry Points

```python
# Programmatic
from pipelines.clothing_3d import ClothingPipeline, PipelineRequest

pipeline = ClothingPipeline()
result = await pipeline.run(
    PipelineRequest(
        image_url="https://...",
        product_name="Black Rose Hoodie",
        collection="black_rose",
        garment_type="hoodie",
    )
)

# Worker
python -m pipelines.clothing_3d.worker

# CLI
python -m pipelines.clothing_3d.cli ...
```

## Consumers

- `api/v1/clothing_3d/*` — async job submission/polling. **Same `IdempotencyCache.get_or_run()` quota gate is enforced at the API layer too**
- `agents/core/creative/*` — agent-initiated 3D generation
- `skyyrose/elite_studio/*` — round-table 3D generation routes through this pipeline for clothing requests

## Module Index

| Module | Purpose |
|--------|---------|
| `cli.py` | CLI entry point |
| `events.py` | Event bus + structured events |
| `job_store.py` | Persistent job state (in-memory + Redis) |
| `models.py` | Pydantic v2 DTOs |
| `observability.py` | Structured logging + Prometheus metrics |
| `pipeline.py` | `ClothingPipeline` orchestrator |
| `queue.py` | `JobQueue` Protocol + in-memory + Redis Streams impls |
| `reliability.py` | `RetryPolicy`, `IdempotencyCache`, `CostQuota`, `request_fingerprint` |
| `stages.py` | `stage_ingest`, `stage_generate`, `stage_qc`, `stage_store` |
| `storage.py` | `ArtifactStore` Protocol + `LocalArtifactStore` |
| `worker.py` | Background worker consuming the queue |
