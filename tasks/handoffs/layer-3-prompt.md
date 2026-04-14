# Elite Studio Layer 3 — Production Infrastructure

## Context

You are working in the `elite/layer-3-production-infra` branch (worktree at `../elite-layer-3`).

Layer 1 (LangGraph engine) is already merged. Your job is to add async job processing, cost tracking, rate limiting, and a dead letter queue so Elite Studio can run as a background worker service.

**Pre-reads (do these first):**
- `skyyrose/elite_studio/graph/runner.py` — `run_single()` is what the worker calls
- `agent_sdk/task_queue.py` — existing Redis queue (ZADD/ZPOPMAX/Pub/Sub/DLQ patterns to reuse)
- `agent_sdk/worker.py` — existing worker pattern to extend
- `skyyrose/elite_studio/config.py` — where to add new constants
- `skyyrose/elite_studio/cli.py` — where to add new commands
- `docker-compose.yml` — where to add the elite-worker service

---

## Goal

Elite Studio gets an async job queue so long-running generation jobs don't block the HTTP request. Architecture:

```
CLI/API → enqueue_produce() → Redis ZADD
                                    ↓
                              EliteStudioWorker (ZPOPMAX)
                                    ↓
                              run_single() → ProductionResult
                                    ↓
                              Redis store_result + Pub/Sub notify
```

The sync path (`produce --graph`) remains unchanged.

---

## New Package: `skyyrose/elite_studio/queue/`

### `__init__.py`
Package init, exports: `enqueue_produce`, `enqueue_batch`, `EliteStudioWorker`

### `job_types.py`
Pydantic models:
```python
class EliteStudioJobData(BaseModel):
    sku: str
    view: str = "front"
    enable_compositor: bool = False
    max_retries: int = 2
    priority: int = 5  # 1-10, higher = sooner
    submitted_at: str  # ISO datetime

class EliteStudioJobResult(BaseModel):
    job_id: str
    sku: str
    status: str  # "queued", "running", "success", "error", "skipped"
    output_path: str = ""
    error: str = ""
    completed_at: str = ""
    stage_timings: dict[str, float] = {}
    cost_usd: float = 0.0
```

### `producer.py`
```python
def enqueue_produce(sku: str, view: str = "front", priority: int = 5, **kwargs) -> str:
    """Enqueue a single SKU. Returns job_id."""

def enqueue_batch(skus: list[str], view: str = "front", **kwargs) -> list[str]:
    """Enqueue multiple SKUs. Returns list of job_ids."""
```
Uses `agent_sdk/task_queue.py`'s `enqueue()` method. Job ID = `f"elite:{sku}:{uuid4().hex[:8]}"`.

### `consumer.py`
```python
class EliteStudioWorker:
    def __init__(self, concurrency: int = 1): ...
    def run_forever(self) -> None: ...  # main loop: ZPOPMAX → run_single → store_result
    def process_job(self, job_id: str, job_data: EliteStudioJobData) -> None: ...
```
- Calls `run_single()` from `graph/runner.py`
- Stores result in Redis: `SET elite_studio:result:{job_id} <json> EX 86400`
- Publishes on `elite_studio:events`: `{"event": "job.completed", "job_id": ..., "status": ...}`
- On exception: moves to DLQ via `dead_letter.move_to_dlq(job_id, error)`

### `cost_tracker.py`
```python
class CostTracker:
    """Records API token usage and estimated cost per job."""
    def record(self, job_id: str, provider: str, tokens: int, cost_usd: float) -> None: ...
    def get_job_cost(self, job_id: str) -> float: ...
    def get_total_cost(self, since_hours: int = 24) -> float: ...
```
Storage: Redis hash `elite_studio:costs:{job_id}` with fields: `gemini_tokens`, `openai_tokens`, `anthropic_tokens`, `total_usd`.
Pricing (hardcoded constants, easy to update):
- Gemini Flash: $0.000075/1K tokens
- GPT-4o: $0.005/1K input tokens
- Claude Sonnet: $0.003/1K input tokens

### `rate_limiter.py`
```python
class ProviderRateLimiter:
    """Token bucket rate limiter per provider using Redis."""
    LIMITS = {
        "gemini": 60,      # requests/min
        "openai": 500,     # requests/min
        "anthropic": 50,   # requests/min
    }
    def acquire(self, provider: str, timeout: float = 30.0) -> bool: ...
    def release(self, provider: str) -> None: ...
```
Uses Redis sorted sets (sliding window). Raise `RateLimitExceeded` if can't acquire within timeout.

### `dead_letter.py`
```python
class DeadLetterQueue:
    def move_to_dlq(self, job_id: str, error: str) -> None: ...
    def list_failed(self) -> list[dict]: ...
    def retry(self, job_id: str) -> str: ...   # re-enqueue, return new job_id
    def purge(self, older_than_hours: int = 72) -> int: ...  # returns purged count
```
DLQ key: `elite_studio:dlq` (Redis list, LPUSH/LRANGE).

---

## Files to Modify

| File | Change |
|------|--------|
| `agent_sdk/worker.py` | Register `"elite_studio_produce"` task type, dispatch to `EliteStudioWorker.process_job` |
| `skyyrose/elite_studio/cli.py` | Add `produce-async`, `job-status`, `job-result`, `dlq-list`, `dlq-retry` commands |
| `skyyrose/elite_studio/config.py` | Add `REDIS_URL`, rate limit constants, cost tracking toggle, worker concurrency |
| `skyyrose/elite_studio/graph/nodes.py` | Call `CostTracker.record()` after each node that makes an API call |
| `docker-compose.yml` | Add `elite-worker` service (same image as main API, CMD: `python -m skyyrose.elite_studio worker`) |

---

## CLI Commands to Add

```bash
python -m skyyrose.elite_studio produce-async br-001   # enqueue, print job_id
python -m skyyrose.elite_studio job-status <job_id>    # print status
python -m skyyrose.elite_studio job-result <job_id>    # print full result
python -m skyyrose.elite_studio dlq-list               # list failed jobs
python -m skyyrose.elite_studio dlq-retry <job_id>     # re-enqueue from DLQ
python -m skyyrose.elite_studio worker                  # start worker process
```

---

## Tests to Create

| File | Covers |
|------|--------|
| `tests/test_elite_queue_producer.py` | enqueue_produce, enqueue_batch (mock Redis) |
| `tests/test_elite_queue_consumer.py` | EliteStudioWorker process_job (mock run_single + Redis) |
| `tests/test_elite_cost_tracker.py` | record, get_job_cost, get_total_cost |
| `tests/test_elite_rate_limiter.py` | acquire/release with fake Redis |
| `tests/test_elite_dead_letter.py` | move_to_dlq, list, retry, purge |

All tests: mock Redis with `fakeredis` (add to dev dependencies if not present).

---

## Standards

- All Redis operations: wrap in try/except, log warnings, degrade gracefully (no Redis = sync mode)
- Pydantic models for all job data (V2 syntax)
- Worker loop: handle SIGTERM cleanly (finish current job, then exit)
- Files: <800 lines, functions <50 lines
- `pytest skyyrose/elite_studio/tests/ -v` — all Layer 1 + Layer 3 tests pass

---

## Verification

1. `pytest skyyrose/elite_studio/tests/ -v` — all tests pass
2. Start Redis locally, run worker: `python -m skyyrose.elite_studio worker`
3. Enqueue a job: `python -m skyyrose.elite_studio produce-async br-001`
4. Check status: `python -m skyyrose.elite_studio job-status <job_id>`
5. `docker compose up elite-worker` — service starts and logs "Worker ready"
