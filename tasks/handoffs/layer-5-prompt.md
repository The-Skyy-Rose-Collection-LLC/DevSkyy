# Elite Studio Layer 5 — API & Observability

## Context

You are working in the `elite/layer-5-api-observability` branch (worktree at `../elite-layer-5`).

Layers 1-4 are merged. Your job is the REST API, webhooks, Prometheus metrics, Grafana dashboard, and A/B comparison tracking.

**Pre-reads (do these first):**
- `api/v1/` — existing FastAPI router pattern to follow
- `main_enterprise.py` — where to register the new router
- `monitoring/prometheus_metrics.py` — existing metrics to extend
- `skyyrose/elite_studio/queue/producer.py` (Layer 3) — `enqueue_produce()` to call from API
- `skyyrose/elite_studio/queue/job_types.py` (Layer 3) — `EliteStudioJobResult` response model
- `docker-compose.yml` — Prometheus + Grafana stack already configured

---

## Goal

Expose Elite Studio as a proper REST service with job lifecycle management, webhook notifications, and full observability.

---

## New File: `api/v1/elite_studio.py`

FastAPI router with prefix `/api/v1/elite-studio`. Endpoints:

```
POST   /produce                    → enqueue job, return {job_id, status: "queued"}
POST   /produce-batch              → enqueue multiple, return {job_ids: [...]}
GET    /jobs/{job_id}              → job status (queued/running/success/error)
GET    /jobs/{job_id}/result       → full ProductionResult JSON
DELETE /jobs/{job_id}              → cancel queued job
GET    /jobs                       → list recent jobs (paginated, filter by status/sku)
GET    /skus                       → list all discoverable SKUs
GET    /health                     → pipeline health check
```

Request/Response models (Pydantic V2):
```python
class ProduceRequest(BaseModel):
    sku: str
    view: str = "front"
    enable_compositor: bool = False
    priority: int = 5
    webhook_url: str | None = None   # notified on completion

class ProduceResponse(BaseModel):
    job_id: str
    sku: str
    status: str
    queued_at: str

class JobListResponse(BaseModel):
    jobs: list[EliteStudioJobResult]
    total: int
    page: int
    page_size: int
```

Authentication: use existing `get_current_user` dependency from `api/auth.py` (or equivalent).

---

## New File: `api/v1/elite_studio_webhooks.py`

```python
class WebhookManager:
    def register(self, url: str, events: list[str], secret: str) -> str:
        """Register webhook. Returns webhook_id."""

    def fire(self, event: str, payload: dict) -> None:
        """Fire webhook for all registered URLs for this event."""
```

Events: `job.completed`, `job.failed`, `job.review_required`

Security: HMAC-SHA256 signature in `X-SkyyRose-Signature` header:
```python
signature = hmac.new(secret.encode(), json_payload.encode(), hashlib.sha256).hexdigest()
```

Storage: Redis hash `elite_studio:webhooks:{webhook_id}`.
Delivery: fire-and-forget via `httpx.AsyncClient.post()` (non-blocking, log failures).

---

## New File: `monitoring/elite_studio_metrics.py`

Prometheus metrics:
```python
elite_studio_jobs_total          # Counter, labels: status (success/error/skipped)
elite_studio_stage_duration_s    # Histogram, labels: stage (vision/generation/quality/...)
elite_studio_cost_dollars        # Counter, labels: provider (gemini/openai/anthropic)
elite_studio_qc_score            # Histogram (0.0-1.0)
elite_studio_active_jobs         # Gauge
elite_studio_queue_depth         # Gauge
elite_studio_retry_total         # Counter
```

Use `prometheus_client` library. Register all metrics at module level (no re-registration errors).

**Instrument nodes:** In `graph/nodes.py`, emit timing to `elite_studio_stage_duration_s` after each node completes.

---

## New File: `monitoring/ab_comparison.py`

```python
class ABComparisonTracker:
    """Track QC scores per model/provider for A/B comparison."""

    def record(self, provider: str, model: str, qc_score: float, job_id: str) -> None:
        """Record a QC score for a provider/model combo."""

    def report(self, since_hours: int = 24) -> ABReport:
        """Generate statistical comparison report."""
```

`ABReport` (frozen dataclass):
```python
@dataclass(frozen=True)
class ABReport:
    generated_at: str
    providers: dict[str, ProviderStats]

@dataclass(frozen=True)
class ProviderStats:
    provider: str
    model: str
    sample_count: int
    mean_score: float
    std_dev: float
    p50: float
    p95: float
    win_rate: float   # % of jobs where this provider scored highest
```

Storage: Redis sorted set `elite_studio:ab:{provider}:{model}` (score = qc_score, member = job_id).

---

## New File: `monitoring/grafana/elite_studio_dashboard.json`

Grafana dashboard JSON with panels:
1. **Throughput** — jobs/minute line chart
2. **Stage Latency Heatmap** — p50/p95/p99 per stage
3. **Cost Breakdown** — cumulative cost by provider (bar chart)
4. **QC Score Distribution** — histogram
5. **Queue Depth** — gauge
6. **Error Rate** — % failed over time
7. **A/B Winner** — current leading provider by mean QC score

Use Prometheus data source. Variable: `$job_status` filter. Time range: last 1h default.

---

## Files to Modify

| File | Change |
|------|--------|
| `main_enterprise.py` | Register `elite_studio_router` from `api/v1/elite_studio.py` |
| `api/__init__.py` or router registry | Include new router |
| `monitoring/prometheus_metrics.py` | Register Elite Studio metrics (import from `elite_studio_metrics.py`) |
| `skyyrose/elite_studio/graph/nodes.py` | Emit Prometheus timing after each node |
| `prometheus.yml` | Verify `elite_studio` metrics are scraped (already covered by main `/metrics` endpoint) |

---

## Tests to Create

| File | Covers |
|------|--------|
| `tests/test_elite_api.py` | All endpoints with `httpx.AsyncClient` + `TestClient` |
| `tests/test_elite_webhooks.py` | register, fire, HMAC verification (mock httpx) |
| `tests/test_elite_metrics.py` | Counters/histograms increment correctly |
| `tests/test_ab_comparison.py` | record + report with fake Redis |

---

## Standards

- All endpoints: return 422 on validation errors, 404 on missing job_id, 503 if Redis unavailable
- Webhook delivery failures: log warning, don't raise (fire-and-forget)
- Prometheus metrics: use `REGISTRY` to avoid duplicate registration in tests
- Files: <800 lines, functions <50 lines
- `pytest` — all passing

---

## Verification

1. `pytest tests/test_elite_api.py -v` — all endpoint tests pass
2. Start API: `uvicorn main_enterprise:app --reload`
3. `POST /api/v1/elite-studio/produce` with `{"sku": "br-001"}` → returns `job_id`
4. `GET /api/v1/elite-studio/jobs/{job_id}` → returns status
5. `curl localhost:8000/metrics | grep elite_studio` → metrics visible
6. Import `monitoring/grafana/elite_studio_dashboard.json` into Grafana → dashboard loads
