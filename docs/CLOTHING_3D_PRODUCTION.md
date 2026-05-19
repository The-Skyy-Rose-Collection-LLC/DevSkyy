# Clothing 3D — Production Deployment Guide

Complements [`CLOTHING_3D_PIPELINE.md`](./CLOTHING_3D_PIPELINE.md) with the
operational layer: queue + worker + persistent job store + idempotency +
metrics + deploy manifests. This is what turns "runs on my laptop" into
"runs at scale 24/7 with kill switches."

## Topology

```
                ┌──────────────────────────────────────┐
                │            API replicas              │
                │  /v1/clothing-3d/generate            │
                │  /v1/clothing-3d/generate/async ─┐   │
                │  /v1/clothing-3d/jobs/{id}       │   │
                │  /v1/clothing-3d/{health,ready,  │   │
                │                   info,metrics}  │   │
                └──────────────────────────────────┼───┘
                                                   ▼
                                       ┌────────────────────┐
                                       │   Redis Streams    │
                                       │  clothing3d:queue  │
                                       └────────┬───────────┘
                                                ▼
                ┌────────────────────────────────────────────────┐
                │                Worker pool                      │
                │   PipelineWorker × N (HPA-scaled)              │
                │   xreadgroup → run → xack                      │
                └────────┬───────────────────────────────────────┘
                         ▼
              ┌──────────────────────┐
              │  ClothingPipeline    │  Stub | HF Space | Local | Replicate
              │  (with TRELLIS)      │
              └────────┬─────────────┘
                       ▼
              ┌──────────────────────┐       ┌────────────────────┐
              │  RedisJobStore       │ ◀──── │  /v1/...jobs/{id}  │
              │  clothing3d:job:{id} │       └────────────────────┘
              └────────┬─────────────┘
                       ▼
              ┌──────────────────────┐
              │  ArtifactStore       │  LocalArtifactStore (dev)
              │  S3 / R2 in prod     │
              └──────────────────────┘
```

## Components shipped

| Module                                  | What it does                                         |
|-----------------------------------------|------------------------------------------------------|
| `pipelines.clothing_3d.queue`           | `JobQueue` Protocol + `InMemoryQueue` / `RedisStreamsQueue` |
| `pipelines.clothing_3d.job_store`       | `JobStore` Protocol + in-memory + Redis backends     |
| `pipelines.clothing_3d.worker`          | `PipelineWorker` long-running async worker           |
| `pipelines.clothing_3d.reliability`     | `RetryPolicy` · `IdempotencyCache` · `CostQuota`     |
| `pipelines.clothing_3d.observability`   | JSON logging · Prometheus metrics · event-bus bridge |
| `deploy/clothing_3d/Dockerfile`         | Worker container (Python 3.13-slim, non-root)        |
| `deploy/clothing_3d/docker-compose.yml` | API + worker + Redis (drop-in)                       |
| `deploy/clothing_3d/k8s.yaml`           | Deployment + HPA + ConfigMap + PVC + Service         |
| `scripts/smoke_test_clothing_3d.sh`     | <5s end-to-end CI check (stub backend)               |

## Environment matrix

| Variable | Default | Effect |
|---|---|---|
| `TRELLIS_BACKEND` | `hf_space` | `hf_space` · `local` · `replicate` · `modal` · `stub` |
| `TRELLIS_QUALITY` | `standard` | `draft` · `standard` · `production` |
| `TRELLIS_OUTPUT_DIR` | `./assets/3d-models-generated` | Where GLB/USDZ land |
| `TRELLIS_EXPORT_USDZ` | `true` | Emit iOS AR USDZ alongside GLB |
| `TRELLIS_RETRIES` | `2` | Per-generation retries inside the provider |
| `TRELLIS_TIMEOUT` | `420` | Hard timeout per generation call (s) |
| `REDIS_URL` | unset | Set → Redis queue + Redis job store automatically |
| `CLOTHING_3D_QUEUE` | `auto` | Force `memory` or `redis` |
| `CLOTHING_3D_JOB_STORE` | `auto` | Force `memory` or `redis` |
| `CLOTHING_3D_CONCURRENCY` | `1` | In-flight jobs per worker |
| `CLOTHING_3D_METRICS_NS` | `clothing_3d` | Prometheus metric namespace |
| `LOG_LEVEL` | `INFO` | Stdlib log level |
| `HUGGINGFACE_TOKEN` | — | Raises HF Space rate limits (recommended) |
| `REPLICATE_API_TOKEN` | — | Required when `TRELLIS_BACKEND=replicate` |

## Reliability primitives

### Retry policy
Wrap any external call:
```python
from pipelines.clothing_3d import RetryPolicy

policy = RetryPolicy(max_attempts=3, base_delay_seconds=2.0, max_delay_seconds=60.0)
result = await policy.run(lambda: backend.generate(req))
```
Exponential backoff with **full jitter** so a horde of retrying workers
doesn't synchronize on a backend recovery.

### Idempotency cache
Skip duplicate runs (e.g. retried webhooks, accidental double-clicks):
```python
from pipelines.clothing_3d import IdempotencyCache

cache = IdempotencyCache(ttl_seconds=86_400)
result, was_cache_hit = await cache.get_or_run(req, runner=pipeline.run)
```
- Keys: SHA-256 of input image bytes + prompt + product/collection/quality.
- Failures never cached. Only `SUCCEEDED` results are kept.
- Swap the in-memory store for a shared `RedisIdempotencyStore` to share
  hits across workers.

### Cost quota
Stop runaway spend on paid backends:
```python
from pipelines.clothing_3d import CostQuota

quota = CostQuota(caps_usd={"replicate": 50.00, "modal": 200.00})
quota.charge("replicate")  # raises QuotaExceededError when cap hit
```
Window resets every 24h by default. The worker calls `charge()` before
dispatching, so a hot SKU can't drain the monthly budget in an hour.

## Observability

Every component emits structured events:

| Event name             | Payload keys                                  |
|------------------------|-----------------------------------------------|
| `pipeline.started`     | (just `correlation_id`)                       |
| `stage.started`        | `stage`                                       |
| `stage.finished`       | `stage`, stage `detail`                       |
| `pipeline.rejected`    | `issues`, `score`                             |
| `pipeline.failed`      | `error`                                       |
| `pipeline.succeeded`   | `artifact_id`, `glb_url`, `duration`          |

### Prometheus metrics
Exposed at `GET /v1/clothing-3d/metrics`:

| Metric (with `clothing_3d_` namespace prefix) | Type | Labels |
|---|---|---|
| `runs_total` | counter | `status` · `backend` |
| `run_duration_seconds` | histogram | `status` · `backend` |
| `stage_duration_seconds` | histogram | `stage` |
| `stage_failures_total` | counter | `stage` |
| `queue_depth` | gauge | — |
| `backend_cost_usd_total` | counter | `backend` |
| `cache_total` | counter | `outcome` (`hit` \| `miss`) |

Alerting recipes:
- **High failure rate**: `sum(rate(clothing_3d_runs_total{status="failed"}[5m])) / sum(rate(clothing_3d_runs_total[5m])) > 0.05`
- **Backlog growing**: `clothing_3d_queue_depth > 50` for 10m
- **p95 latency regression**: `histogram_quantile(0.95, rate(clothing_3d_run_duration_seconds_bucket[5m])) > 90`
- **Spend overflow**: `increase(clothing_3d_backend_cost_usd_total{backend="replicate"}[1h]) > 5`

### Structured logging
Every record is a JSON object with `ts`, `level`, `logger`, `msg`, plus
arbitrary `extra={...}` keys. Auto-enabled when stdout isn't a TTY
(Docker, k8s, systemd).

## Deployment

### Docker Compose (single host)

```bash
# Build the worker image
docker build -f deploy/clothing_3d/Dockerfile -t devskyy/clothing-3d-worker:latest .

# Start API + 2× worker + Redis
docker compose -f deploy/clothing_3d/docker-compose.yml up -d
```

Scale workers without restarting the API:
```bash
docker compose -f deploy/clothing_3d/docker-compose.yml \
  up -d --scale clothing-3d-worker=8
```

### Kubernetes

```bash
# One-time: create the secrets the manifest expects
kubectl create secret generic clothing-3d-secrets \
  --from-literal=REDIS_URL=redis://redis.default.svc:6379/0 \
  --from-literal=REPLICATE_API_TOKEN=$REPLICATE_API_TOKEN \
  --from-literal=HUGGINGFACE_TOKEN=$HUGGINGFACE_TOKEN

# Apply manifests
kubectl apply -f deploy/clothing_3d/k8s.yaml
```

HPA scales 2 → 12 replicas based on CPU + queue depth. Tune
`averageValue` on the `clothing_3d_queue_depth_per_pod` metric for your
desired backlog tolerance.

## Smoke testing

Drop into CI:
```bash
bash scripts/smoke_test_clothing_3d.sh
```

Exercises imports, garment classifier, full pipeline, idempotency cache,
cost quota, retry policy, and a worker-round-trip — all against the Stub
backend in <5 s with no network, GPU, or paid credits.

## Operations runbook

### Symptom → action

| Symptom | First investigation | Likely cause |
|---|---|---|
| `/ready` returning 503 | Check Redis: `redis-cli -u $REDIS_URL ping` | Redis unreachable |
| Workers stuck `running` | Compare `started_at` to now in `/v1/clothing-3d/jobs` | Worker crashed before ACK — Redis Streams will reclaim after `reclaim_idle_ms`; manually `xautoclaim` if urgent |
| `quota exceeded` errors | `GET /v1/clothing-3d/info` → cost snapshot | Bump cap or switch backend |
| HF Space cold starts | Check provider `latency_ms` in `/health` | Pre-warm with a synthetic request every 5 min |
| `queue_depth` growing | `kubectl scale deploy/clothing-3d-worker --replicas=N` | Demand spike — HPA should already be scaling |

### Graceful shutdown

The worker installs `SIGINT` / `SIGTERM` handlers. On signal, it stops
pulling new messages and waits up to `terminationGracePeriodSeconds: 60`
(see k8s.yaml) for in-flight jobs to drain. Unfinished jobs land back on
the stream and another worker picks them up.

### Killswitch

Stop dispatching to a specific backend without redeploying:
```bash
kubectl set env deployment/clothing-3d-worker TRELLIS_BACKEND=stub
```
Workers will run with the stub (artifacts marked failed by QC), giving
you a clean way to halt spend while debugging.
