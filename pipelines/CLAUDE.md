# pipelines/ — Cross-Service Orchestration

**Multi-stage workflows that compose `services/`, `agents/`, and `llm/` into end-to-end operations.** A pipeline is more than a service: it owns ordered stages, QC gates, event emission, idempotency, retries, and persistence.

## Shipped Pipelines

| Pipeline | Subpackage | Purpose |
|----------|------------|---------|
| Clothing 3D | `clothing_3d/` | image/text → preprocess → TRELLIS → postprocess (GLB/USDZ) → QC → storage → events |

## Design Doctrine

A pipeline lives here (not in `services/`) when ALL apply:

1. **Multiple stages** — not a single API call. Stages run in order with explicit handoff
2. **Cross-service** — composes `services/`, `agents/`, or `llm/` rather than wrapping one vendor
3. **Persistent job state** — has a `JobStore` and supports resumption / status polling
4. **QC gate** — produces a quality report before declaring success
5. **Event-emitting** — publishes lifecycle events to subscribers (logging, metrics, downstream agents)

Anything not meeting all five belongs in `services/` (single-purpose) or `agents/` (decision-making).

## Hard Rules

- **Pipelines depend on `services/`, never the reverse** — circular import = architectural smell
- Stages own one job; orchestrator owns timing, retries, and event emission (`pipelines/clothing_3d/stages.py:7-9`)
- Every pipeline MUST expose:
  - A `PipelineRequest` / `PipelineResult` Pydantic pair (Pydantic v2)
  - A `JobStore` Protocol with `InMemory*` default + Redis prod impl
  - A `JobQueue` Protocol with `InMemory*` default + Redis Streams prod impl
  - A `RetryPolicy` with explicit retryable exception list
  - A `CostQuota` for any paid-backend dispatch
  - A `PipelineEventBus` with structured event types
- **Two-tier message envelope** — queue messages carry only `job_id`; full `JobRecord` lives in `JobStore`. Avoids dumping large request bodies into the queue twice
- **Content-addressed idempotency** — `request_fingerprint(request)` hashes image bytes + options; duplicate requests reuse cached `PipelineResult`
- New pipelines: copy the `clothing_3d/` structure (`models`, `stages`, `pipeline`, `worker`, `queue`, `job_store`, `reliability`, `storage`, `observability`, `events`, `cli`). Do not invent new conventions

## Consumers

- `api/v1/clothing_3d/*` — async job submission, status polling, result retrieval
- Background workers — `python -m pipelines.clothing_3d.worker` or via `cli.py`
- `agents/core/creative/*` — agent-initiated 3D generation
