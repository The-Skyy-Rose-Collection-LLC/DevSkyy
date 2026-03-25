# DevSkyy Worker Architecture

> Production-grade background task processing for 3D generation, marketing, and ML operations

---

## Overview

The DevSkyy worker infrastructure provides asynchronous, distributed task processing for compute-intensive operations that should not block the main API.

**Key Features:**
- Multi-stage Docker builds for minimal image size
- Non-root user execution for security
- Redis-based task queue with priority support
- Dead Letter Queue (DLQ) for failed tasks
- Health checks and graceful shutdown
- Horizontal scaling with replicas

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI App                          │
│                   (main_enterprise.py)                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ Enqueue Task
                  ▼
         ┌────────────────────┐
         │   Redis Queue      │
         │  (Sorted Sets)     │
         └────────┬───────────┘
                  │
       ┌──────────┼──────────┐
       │          │           │
       ▼          ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Worker 1 │ │ Worker 2 │ │ Worker N │
└────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │
     │ Process    │ Process    │ Process
     ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│  Agent   │ │  Agent   │ │  Agent   │
│ Execution│ │ Execution│ │ Execution│
└──────────┘ └──────────┘ └──────────┘
```

---

## Task Types

### 1. 3D Asset Generation (`generate_3d`)

**Purpose:** Generate 3D models via Tripo3D API

**Input Schema:**
```python
{
    "prompt": str,              # Text description
    "image_url": str | None,    # Optional image for image-to-3D
    "style": str,               # "realistic", "cartoon", etc.
    "user_id": str,             # User ID for tracking
    "product_name": str | None, # Product name
    "collection": str,          # "SIGNATURE", "BLACK", etc.
    "garment_type": str         # "tee", "hoodie", etc.
}
```

**Output:**
```python
{
    "status": "success" | "failed",
    "task_id": str,
    "result": {
        "task_id": str,
        "model_url": str,
        "texture_url": str,
        "preview_url": str
    },
    "completed_at": str  # ISO timestamp
}
```

**Agent:** `TripoAssetAgent`

**Timeout:** 600 seconds (10 minutes)

**Retry Policy:** 3 retries with exponential backoff

---

### 2. Marketing Campaign (`marketing_campaign`)

**Purpose:** Execute email, social, or SEO campaigns

**Input Schema:**
```python
{
    "campaign_id": str,
    "campaign_type": "email" | "social" | "seo",
    "recipients": list[str],
    "content": dict[str, Any],
    "schedule_at": str | None,  # ISO timestamp
    "user_id": str
}
```

**Output:**
```python
{
    "status": "success" | "failed",
    "campaign_id": str,
    "result": {
        "sent_count": int,
        "failed_count": int,
        "campaign_type": str,
        "sent_at": str
    },
    "completed_at": str
}
```

**Agent:** `MarketingAgent`

**Timeout:** 300 seconds (5 minutes)

**Retry Policy:** 2 retries

---

### 3. ML Model Training (`ml_training`)

**Purpose:** Train ML models (sentiment, trend prediction, segmentation)

**Input Schema:**
```python
{
    "model_id": "sentiment_analyzer" | "trend_predictor" | "customer_segmentation",
    "training_data_path": str,
    "hyperparameters": dict[str, Any],
    "epochs": int,
    "user_id": str
}
```

**Output:**
```python
{
    "status": "success" | "failed",
    "model_id": str,
    "result": {
        "accuracy": float,
        "precision": float,
        "recall": float,
        "f1_score": float,
        "epochs_completed": int,
        "training_samples": int
    },
    "completed_at": str
}
```

**Agent:** `MLCapabilitiesModule`

**Timeout:** 600 seconds (10 minutes)

**Retry Policy:** 1 retry

---

### 4. ML Prediction (`ml_prediction`)

**Purpose:** Run ML model predictions

**Input Schema:**
```python
{
    "model_id": str,
    "input_data": dict[str, Any] | list[dict[str, Any]],
    "user_id": str
}
```

**Output:**
```python
{
    "status": "success" | "failed",
    "model_id": str,
    "result": {
        "predictions": dict | list,
        "model_version": str
    },
    "completed_at": str
}
```

**Agent:** `MLCapabilitiesModule`

**Timeout:** 60 seconds

**Retry Policy:** 2 retries

---

## Docker Configuration

### Dockerfile.worker

**Multi-stage build:**
1. **Builder Stage:** Install dependencies with build tools
2. **Production Stage:** Copy dependencies, minimal runtime image

**Security Features:**
- Non-root user (`worker:worker`)
- Minimal system dependencies
- Read-only filesystem (data written to volumes)
- Health checks

**Build Command:**
```bash
docker build -f Dockerfile.worker -t devskyy-worker:latest .
```

### docker-compose.yml

**Worker Service Configuration:**
```yaml
worker:
  build:
    context: .
    dockerfile: Dockerfile.worker
  environment:
    - REDIS_URL=redis://:redispassword@redis:6379/0
    - DATABASE_URL=postgresql://devskyy:password@postgres:5432/devskyy
    - TRIPO_API_KEY=${TRIPO_API_KEY}
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    # ... more env vars
  deploy:
    replicas: 2
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
```

**Run Command:**
```bash
docker-compose up worker
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://user:pass@host:5432/db` |

### 3D Generation

| Variable | Description | Required |
|----------|-------------|----------|
| `TRIPO_API_KEY` | Tripo3D API key | Yes (for 3D tasks) |
| `FASHN_API_KEY` | FASHN API key | No (stub only) |

### Marketing

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes (for marketing) |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional |
| `GOOGLE_AI_API_KEY` | Google AI API key | Optional |

### WordPress Integration

| Variable | Description | Required |
|----------|-------------|----------|
| `WORDPRESS_URL` | WordPress site URL | Yes (for asset upload) |
| `WOOCOMMERCE_KEY` | WooCommerce consumer key | Yes |
| `WOOCOMMERCE_SECRET` | WooCommerce consumer secret | Yes |

### Worker Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKER_PROCESSES` | 2 | Number of worker processes |
| `WORKER_THREADS` | 4 | Threads per process |
| `TASK_TIMEOUT` | 600 | Task timeout in seconds |

---

## Task Queue

### Queue Keys

Tasks are stored in Redis sorted sets with priority:

```
queue:generate_3d         # 3D generation tasks
queue:fashn_tryon         # Virtual try-on tasks (stub)
queue:marketing_campaign  # Marketing campaigns
queue:ml_training         # ML training tasks
queue:ml_prediction       # ML prediction tasks
```

### Task Metadata

Task data stored in Redis hash:

```
devskyy:tasks:{task_id}
{
    "task_type": str,
    "status": "pending" | "processing" | "completed" | "failed",
    "data": dict,
    "created_at": str,
    "started_at": str | None,
    "completed_at": str | None,
    "worker_host": str | None
}
```

### Dead Letter Queue (DLQ)

Failed tasks are preserved for 7 days:

```
devskyy:dlq:{task_id}
{
    "task_id": str,
    "task_data": dict,
    "error": str,
    "error_type": str,
    "failed_at": str,
    "worker_host": str
}
```

---

## Monitoring

### Health Checks

**Endpoint:** Internal health check (not exposed)

**Command:** `python -c "import sys; sys.exit(0)"`

**Interval:** 30 seconds

**Retries:** 3

### Logs

Worker logs to stdout/stderr with structured logging:

```
2024-01-05 12:00:00 - worker - INFO - 🚀 Background worker started
2024-01-05 12:00:01 - worker - INFO - 📋 Processing task task-abc123 (type: generate_3d)
2024-01-05 12:05:30 - worker - INFO - ✅ Task task-abc123 completed (status: success)
```

### Metrics

**Prometheus Metrics (if enabled):**
- `worker_tasks_total{type, status}` - Total tasks processed
- `worker_task_duration_seconds{type}` - Task duration histogram
- `worker_errors_total{type}` - Total errors by task type
- `worker_queue_size{type}` - Current queue size

---

## Deployment

### Local Development

```bash
# Start worker only
docker-compose up worker

# Start full stack
docker-compose up

# View worker logs
docker-compose logs -f worker

# Scale workers
docker-compose up --scale worker=4
```

### Production

```bash
# Build optimized image
docker build -f Dockerfile.worker -t devskyy-worker:v1.0.0 .

# Run with production config
docker run -d \
  --name devskyy-worker-1 \
  --env-file .env.production \
  --restart unless-stopped \
  devskyy-worker:v1.0.0

# Check logs
docker logs -f devskyy-worker-1
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devskyy-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: devskyy-worker
  template:
    metadata:
      labels:
        app: devskyy-worker
    spec:
      containers:
      - name: worker
        image: devskyy-worker:v1.0.0
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: devskyy-secrets
              key: redis-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

---

## Troubleshooting

### Worker Not Processing Tasks

**Check 1:** Verify Redis connectivity
```bash
docker exec devskyy-worker python -c "import redis.asyncio as r; import asyncio; asyncio.run(r.from_url('redis://redis:6379/0').ping())"
```

**Check 2:** Verify tasks in queue
```bash
redis-cli ZRANGE queue:generate_3d 0 -1 WITHSCORES
```

**Check 3:** Check worker logs
```bash
docker-compose logs worker | tail -100
```

### Tasks Failing

**Check DLQ:**
```bash
redis-cli KEYS devskyy:dlq:*
redis-cli GET devskyy:dlq:task-abc123
```

**Common Issues:**
- Missing API keys (TRIPO_API_KEY, OPENAI_API_KEY)
- Invalid task input schema
- Network connectivity issues
- Resource exhaustion (memory/CPU)

### Performance Issues

**Symptoms:** Slow task processing, queue backlog

**Solutions:**
1. Scale workers: `docker-compose up --scale worker=4`
2. Increase resources: Edit `docker-compose.yml` limits
3. Enable Redis persistence: Add AOF/RDB
4. Monitor queue sizes: Add Prometheus alerts

---

## Security

### Best Practices

1. **Secrets Management:**
   - Never commit API keys
   - Use environment variables or secrets manager
   - Rotate credentials every 90 days

2. **Network Isolation:**
   - Workers communicate only with Redis/DB
   - Use private Docker network
   - No external ports exposed

3. **Resource Limits:**
   - Set memory/CPU limits
   - Enable timeout for long-running tasks
   - Implement rate limiting

4. **Audit Logging:**
   - Log all task executions
   - Track task ownership (user_id)
   - Preserve DLQ for forensics

---

## File Structure

```
DevSkyy/
├── Dockerfile.worker                    # Worker container build
├── docker-compose.yml                   # Service orchestration
├── agent_sdk/
│   ├── worker.py                        # Main worker implementation
│   └── task_queue.py                    # Queue interface
├── orchestration/
│   └── tasks.py                         # Task definitions (NEW)
├── agents/
│   ├── tripo_agent.py                   # 3D generation agent
│   ├── marketing_agent.py               # Marketing agent
│   └── base_super_agent.py              # ML capabilities
└── docs/
    └── WORKER_ARCHITECTURE.md           # This file
```

---

## Future Enhancements

### Phase 2: Advanced Features

- [ ] Task prioritization by user tier
- [ ] Scheduled/cron tasks
- [ ] Task chaining (workflows)
- [ ] Result caching
- [ ] Metrics dashboard
- [ ] Auto-scaling based on queue size

### Phase 3: Enterprise Features

- [ ] Multi-region workers
- [ ] Task deduplication
- [ ] Rate limiting per user
- [ ] SLA monitoring
- [ ] Cost attribution per task
- [ ] Batch processing optimization

---

## References

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Sorted Sets](https://redis.io/docs/data-types/sorted-sets/)
- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

---

## Support

**Issues:** Create GitHub issue with `worker` label

**Questions:** <support@skyyrose.com>

**Security:** <security@skyyrose.com>

---

**Version:** 1.0.0
**Last Updated:** 2026-01-05
**Author:** DevSkyy Platform Team
