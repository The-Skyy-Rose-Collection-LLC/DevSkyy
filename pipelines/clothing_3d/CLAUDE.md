# pipelines/clothing_3d — LLM Execution Playbook

This file tells future agents EXACTLY how to drive the clothing 3D pipeline.
Read it before generating code that touches this directory.

For human-facing docs see `docs/CLOTHING_3D_PIPELINE.md` (architecture)
and `docs/CLOTHING_3D_PRODUCTION.md` (deploy + ops).

---

## What this pipeline is

End-to-end image|text → 3D garment asset. TRELLIS provider does the
generation; this directory orchestrates everything around it: validation,
preprocessing, retry, idempotency, cost guard, persistence, queue, worker,
metrics. Output: GLB + (optional) USDZ + thumbnail, stored to local FS or
S3, surfaced via REST API.

---

## Mental model (read this once)

```
PipelineRequest                    → caller intent
  ↓
ClothingPipeline.run(req)          → orchestrator (events, QC, stage reports)
  ↓
  ingest    → classify garment + validate input
  generate  → TrellisProvider (preprocess → backend → postprocess)
  qc        → polycount / size / thumbnail gate
  store     → ArtifactStore (Local | S3) — writes URLs back
  ↓
PipelineResult                     → glb_url, usdz_url, thumbnail_url, quality, stages
```

Sync caller → `pipeline.run(req)` directly.
Async caller → `queue.enqueue(job_id)` + JobStore + PipelineWorker pulls.
Both paths share the same `pipeline.run()` core, the same idempotency cache,
the same cost quota, the same metrics.

---

## Decision tree — pick the right entry point

| You want to… | Use |
|---|---|
| Run one generation from another async Python module | `from pipelines.clothing_3d import ClothingPipeline; await pipeline.run(req)` |
| Run one from a script / shell | `python -m pipelines.clothing_3d.cli generate --image ... --product ... --quality draft` |
| Run many concurrently from JSONL | `python -m pipelines.clothing_3d.cli batch input.jsonl --max-concurrent 4` |
| Test plumbing without a real backend | Add `--dry-run` (uses `StubClient`, <50 ms) |
| Run a long-lived worker | `python -m pipelines.clothing_3d.worker --concurrency 2` |
| Expose over HTTP | Mount `api.v1.clothing_3d.router` at `/v1/clothing-3d` |
| Check liveness | `GET /v1/clothing-3d/health` |
| Check readiness | `GET /v1/clothing-3d/ready` |
| Scrape Prometheus | `GET /v1/clothing-3d/metrics` |

---

## Minimal code recipes

### Generate from an image (in-process, async)

```python
from pipelines.clothing_3d import ClothingPipeline, PipelineRequest
from services.three_d.trellis import TrellisQualityPreset

pipeline = ClothingPipeline()  # reads env: TRELLIS_BACKEND, TRELLIS_QUALITY
try:
    result = await pipeline.run(PipelineRequest(
        image_url="https://skyyrose.co/uploads/hoodie.jpg",
        product_name="Black Rose Hoodie",
        product_sku="br-001",
        collection="black_rose",          # signature | black_rose | love_hurts | kids_capsule
        garment_type="hoodie",             # tee | hoodie | jacket | dress | pants | shorts | skirt | shoe | hat | bag | accessory
        quality=TrellisQualityPreset.PRODUCTION,
    ))
finally:
    await pipeline.close()                # always close — releases backend client
```

`result.glb_url`, `result.usdz_url`, `result.thumbnail_url`, `result.quality.score`,
`result.stages[i].duration_seconds`, `result.garment_category`.

### Generate from text

```python
result = await pipeline.run(PipelineRequest(
    prompt="oversized crimson hoodie with silver chrome zipper",
    product_name="LH Bomber",
    collection="love_hurts",
    garment_type="jacket",
    quality=TrellisQualityPreset.STANDARD,
))
```

Text-to-3D requires the LOCAL backend with TRELLIS-text-large weights.
HF Space / Replicate backends raise `BackendUnavailable` on text input.

### Wrap with idempotency + cost guard (production sync caller)

```python
from pipelines.clothing_3d import IdempotencyCache, CostQuota, QuotaExceededError

cache = IdempotencyCache(ttl_seconds=86_400)
quota = CostQuota(caps_usd={"replicate": 50.00, "modal": 200.00})

try:
    quota.charge(backend_in_use)
    result, was_cache_hit = await cache.get_or_run(req, runner=pipeline.run)
except QuotaExceededError as e:
    # Return 429 to caller; don't retry until window resets
    raise HTTPException(429, str(e))
```

`was_cache_hit=True` means we reused a prior successful run — no backend call
happened. Failures are NOT cached; identical-input retries always go through.

### Async submit + poll (e.g. webhook flow)

```python
from pipelines.clothing_3d import build_queue, build_job_store, JobRecord, PipelineStatus

queue = build_queue()          # Redis if REDIS_URL set, else in-memory
store = build_job_store()      # same selection logic

job_id = "job_" + uuid.uuid4().hex[:16]
record = JobRecord(
    job_id=job_id,
    status=PipelineStatus.PENDING,
    request=req,
)
await store.put(record)
await queue.enqueue(job_id)

# Caller polls separately via store.get(job_id) until status is terminal:
# SUCCEEDED | FAILED | REJECTED
```

The worker process picks up the job. NEVER call `pipeline.run()` directly
from request-handling code if you've gone async — that would defeat the
queue's backpressure and crash-safety.

### Run the worker programmatically (e.g. embedded in a service)

```python
from pipelines.clothing_3d import PipelineWorker

worker = PipelineWorker(
    pipeline=pipeline,    # share with API process if same memory; else build separately
    queue=queue,
    store=store,
    concurrency=2,
    # owns_dependencies=False is the default when you inject pipeline/queue/store —
    # worker will NOT close them on shutdown
)

task = asyncio.create_task(worker.run())
# … later …
await worker.shutdown()  # idempotent; drains in-flight jobs
await task
```

---

## Configuration matrix (env vars)

Driving knobs the LLM will encounter:

| Env var | Default | Purpose |
|---|---|---|
| `TRELLIS_BACKEND` | `hf_space` | `hf_space` (free, slow) `local` (CUDA) `replicate` (paid, fast) `modal` (paid, fastest) `stub` (tests) |
| `TRELLIS_QUALITY` | `standard` | `draft` (40k tris, 1024² tex) `standard` (80k, 1024²) `production` (150k, 2048²) |
| `TRELLIS_TIMEOUT` | `420` | Hard cap on one backend call (seconds) |
| `TRELLIS_RETRIES` | `2` | Retries inside the provider (provider-level, not pipeline-level) |
| `TRELLIS_EXPORT_USDZ` | `true` | Emit `.usdz` alongside `.glb` for iOS AR |
| `TRELLIS_BG_REMOVE` | `true` | Run rembg on inputs before generation |
| `TRELLIS_POSTPROCESS` | `true` | Run trimesh cleanup / decimation / normalize after generation |
| `TRELLIS_OUTPUT_DIR` | `./assets/3d-models-generated` | Where artifacts land |
| `THREE_D_OUTPUT_DIR` | (alias of above) | Same — older code uses this name |
| `TRELLIS_CACHE_DIR` | `./.cache/trellis` | Preprocessing intermediates |
| `TRELLIS_SEED` | `42` | Generation seed; unset for stochastic |
| `REDIS_URL` | — | Set → Redis queue + Redis job store auto-enabled |
| `CLOTHING_3D_QUEUE` | `auto` | Force `memory` or `redis` |
| `CLOTHING_3D_JOB_STORE` | `auto` | Force `memory` or `redis` |
| `CLOTHING_3D_CONCURRENCY` | `1` | Worker in-flight jobs |
| `CLOTHING_3D_METRICS_NS` | `clothing_3d` | Prometheus metric prefix |
| `HUGGINGFACE_TOKEN` | — | Raises HF Space rate limits |
| `REPLICATE_API_TOKEN` | — | Required when `TRELLIS_BACKEND=replicate` |
| `LOG_LEVEL` | `INFO` | Stdlib log level |

---

## Quality presets — choose deliberately

| Preset | Use for | Cost (HF Space) | Cost (Replicate) | Wall time |
|---|---|---|---|---|
| `draft` | Internal previews, batch validation, QC iteration | free | ~$0.05 | 30–60 s |
| `standard` | PDP defaults, regular catalogue | free | ~$0.05 | 60–120 s |
| `production` | Hero collection drops, AR-ready masters | free | ~$0.10 | 90–180 s |

Don't burn `production` on a 100-SKU catalogue refresh. Don't ship `draft`
on a flagship drop. The QC stage thresholds auto-relax for draft and
tighten for production — see `pipelines/clothing_3d/stages.py:default_thresholds_for`.

---

## Common failure modes — how to handle each

| `result.status` | Meaning | What to do |
|---|---|---|
| `succeeded` | Artifact stored, URLs valid | Hand to downstream (web viewer, AR, catalog) |
| `rejected` | Generation ran, QC failed | Read `result.quality.issues`; either re-run with `production` or queue for human review |
| `failed` | A stage errored before terminal | Inspect `result.stages[*].error` (last failed stage first); retryable if `ConnectionError`/`TimeoutError`, surface otherwise |
| `pending` / `running` | Async job still in flight | Poll `GET /jobs/{id}` or `store.get(job_id)` |

Wrap calls with the retry policy when calling external backends directly
(the worker already does this for queue-driven jobs):

```python
from pipelines.clothing_3d import RetryPolicy
policy = RetryPolicy(max_attempts=3, base_delay_seconds=2.0, max_delay_seconds=60.0)
result = await policy.run(lambda: pipeline.run(req))
```

---

## Garment classification — what gets picked

`classify_garment()` (services/three_d/trellis/garment_aware.py) picks the
category in this order:

1. `request.garment_type` if set (highest trust)
2. Substring match in `request.product_name` (e.g. "Bomber" → `jacket`)
3. Aspect ratio of the input image (height/width)
4. `UNKNOWN` (neutral prompt)

ALWAYS pass `garment_type` when you know it. The aspect heuristic guesses
wrong on lifestyle shots (model wearing the item shifts the aspect).
Available categories: `tee`, `hoodie`, `sweatshirt`, `jacket`, `dress`,
`pants`, `shorts`, `skirt`, `shoe`, `hat`, `bag`, `accessory`, `unknown`.

---

## Prompt construction — what gets sent to TRELLIS

`build_clothing_prompt()` composes the prompt in this order:

1. `product_name`
2. `user_prompt` (free-form caller input)
3. Category-specific geometry hints (drape, seams, hood, sole, etc.)
4. Brand context (collection accent + aesthetic)
5. Universal render hints (photorealistic, studio, neutral background)

Then deduplicates phrases case-insensitively. Result is a comma-separated
string optimized for TRELLIS.

To inspect what the pipeline will send before calling:

```python
from services.three_d.trellis.garment_aware import build_garment_prompt_bundle

bundle = build_garment_prompt_bundle(
    product_name="Black Rose Hoodie",
    collection="black_rose",
    declared_category="hoodie",
)
print(bundle.prompt)   # → "Black Rose Hoodie, heavyweight cotton hoodie, raised hood …"
print(bundle.category) # → GarmentCategory.HOODIE
```

---

## Extending the pipeline — common changes

### Add a new garment category

1. Add the enum value in `services/three_d/trellis/garment_aware.py::GarmentCategory`.
2. Add a `GarmentKnowledge` entry in `_KNOWLEDGE` with geometry hints + polycount + aspect.
3. Add keyword(s) to `_NAME_KEYWORDS` for the substring classifier.
4. (Optional) Add a branch to `_classify_by_aspect()` if the new category
   has a distinct aspect signature.
5. Add a test case to `tests/three_d/trellis/test_garment_aware.py::TestClassify`.

### Add a new TRELLIS backend

1. Add the enum value in `services/three_d/trellis/config.py::TrellisBackend`.
2. Implement a class in `services/three_d/trellis/client.py` satisfying
   `TrellisBackendClient` (Protocol with `generate_from_image`,
   `generate_from_text`, `healthy`, `close`, `backend_name`).
3. Register it in `build_backend()` switch in the same file.
4. Add an env-var note to `docs/CLOTHING_3D_PIPELINE.md` and this CLAUDE.md.

### Add a new export format (e.g. `.fbx`)

1. Extend `services/three_d/trellis/postprocess.py::MeshPostprocessor.process()` to emit it.
2. Add the path to `PostprocessResult` and propagate through
   `provider.py::_build_response()` → `pipeline.py::_summary_metadata()` → `models.py::PipelineResult`.
3. Add to `ArtifactBundle` and `LocalArtifactStore._move_into_base` calls.

### Tighten/relax QC thresholds

Override per-pipeline:

```python
from pipelines.clothing_3d.stages import QCThresholds
pipeline = ClothingPipeline(
    thresholds=QCThresholds(min_polycount=20_000, max_file_kb=15_000)
)
```

Or tune presets in `stages.py::default_thresholds_for()`.

---

## Wiring into a FastAPI app

```python
# main_enterprise.py (or any FastAPI app)
from api.v1.clothing_3d import router as clothing_3d_router
app.include_router(clothing_3d_router, prefix="/v1/clothing-3d")
```

Endpoints exposed:
`POST /generate` (sync), `POST /generate/async` + `GET /jobs/{id}` (async),
`GET /jobs` (list), `GET /health`, `GET /ready`, `GET /info`, `GET /metrics`.

The router lazily builds singletons for pipeline / queue / store /
idempotency cache; first request triggers init. Pre-warm by hitting `/info`
on startup if you need cold-start latency below 200 ms.

---

## Verifying changes (MANDATORY before claiming "done")

Run BOTH of these and they MUST pass:

```bash
# 1. Smoke test — 7 checks in <5s using Stub backend
bash scripts/smoke_test_clothing_3d.sh

# 2. CLI dry-run — exercises full orchestration path
python -m pipelines.clothing_3d.cli generate \
  --prompt "test" --product "T" --garment-type tee \
  --quality draft --dry-run
```

For changes that touch the API: run the in-process endpoint verifier
that exists in tmp/verify_endpoints.py — see PR #508 commit `09aa0d0`
for the canonical pattern (49 assertions across all 8 routes).

---

## Hard rules — DO NOT VIOLATE

1. **NEVER call `pipeline.run()` synchronously from a long-running API
   handler if the request can take >5 s.** Use `/generate/async`.
2. **NEVER cache failed results in `IdempotencyCache`.** The cache already
   filters; don't bypass that.
3. **NEVER let the worker call `store.close()` on a store the API is also
   using.** The worker code already handles this via `owns_dependencies`;
   don't disable it.
4. **NEVER `pip install gradio_client` without pinning** — the HF Space
   client API has broken twice in 2025. Pin in `requirements-trellis.txt`.
5. **NEVER add a new top-level package without listing it in
   `pyproject.toml [tool.setuptools.packages.find]`.** Otherwise
   `pip install -e .` silently drops it (this bit us in PR #508).
6. **NEVER add a real HTTP/GPU/$$ call to the smoke test.** Keep it Stub-only.
7. **NEVER mutate `PipelineRequest` after `pipeline.run()` accepts it.**
   The idempotency fingerprint is computed from the request; mutation
   invalidates cache hits silently.
8. **ALWAYS pass `garment_type` from your catalog when known.** The
   aspect-ratio fallback is correct ~60% of the time, no more.
9. **ALWAYS handle `QuotaExceededError`** at the call site — usually
   convert to HTTP 429 with `Retry-After`.

---

## File map — what lives where

| File | Owns |
|---|---|
| `__init__.py` | Public re-exports — import from `pipelines.clothing_3d` directly |
| `models.py` | `PipelineRequest` / `PipelineResult` / `StageReport` / `PipelineQualityReport` Pydantic models |
| `pipeline.py` | `ClothingPipeline` orchestrator with stage runner, event emission |
| `stages.py` | Per-stage callables + `QCThresholds` + `default_thresholds_for()` |
| `events.py` | `PipelineEventBus` + built-in subscribers (`log_event_subscriber`, `webhook_subscriber`) |
| `storage.py` | `ArtifactStore` Protocol + `LocalArtifactStore` + `S3ArtifactStore` |
| `reliability.py` | `RetryPolicy` + `IdempotencyCache` + `CostQuota` + `request_fingerprint` |
| `job_store.py` | `JobStore` Protocol + `InMemoryJobStore` + `RedisJobStore` + `build_job_store()` |
| `queue.py` | `JobQueue` Protocol + `InMemoryQueue` + `RedisStreamsQueue` + `build_queue()` |
| `worker.py` | `PipelineWorker` (long-running) + `python -m pipelines.clothing_3d.worker` |
| `observability.py` | JSON logger + Prometheus `PipelineMetrics` + event-bus bridge |
| `cli.py` | `python -m pipelines.clothing_3d.cli generate|batch|health` |

External deps (read these too when changing those areas):
- `services/three_d/trellis/` — provider, backends, garment knowledge,
  preprocess, postprocess. Owned separately; same conventions.
- `services/three_d/provider_factory.py` — TRELLIS registered here as
  primary image-to-3D provider, alongside Tripo/Replicate/HF fallbacks.

---

## Anti-patterns observed in this codebase — DO NOT REPLICATE

- ❌ Calling `services/__init__.py` for a leaf import — that file eagerly
  loads the entire service tree (numpy, httpx, redis, …). Import the
  specific module instead: `from services.three_d.trellis.config import …`.
- ❌ Using `dataclass(slots=True).__dict__` — slotted dataclasses don't
  have `__dict__`. Use `dataclasses.asdict()`.
- ❌ Returning `bool` from a stage that should return `(StageReport,
  payload)`. Stages must follow the contract in `stages.py`.
- ❌ Adding feature flags via env vars without documenting them HERE.
- ❌ Writing tests against the project-wide `tests/conftest.py` without
  realizing it eagerly imports `security.rate_limiting` (and therefore
  passlib, argon2, etc.). For pure-unit tests of this directory, use
  the in-script verification pattern from PR #508 or run pytest with
  `--no-header -p no:cacheprovider` only after installing deps.
