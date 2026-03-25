# Worker Quick Start Guide

> Get the DevSkyy background worker running in 5 minutes

---

## Prerequisites

- Docker and Docker Compose installed
- Redis running (or use docker-compose)
- Environment variables configured

---

## Step 1: Configure Environment

Create `.env` file in project root:

```bash
# Core Services
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://devskyy:password@localhost:5432/devskyy

# 3D Generation (required for 3D tasks)
TRIPO_API_KEY=your-tripo-api-key-here

# LLM Providers (required for marketing tasks)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# WordPress (optional, for asset upload)
WORDPRESS_URL=https://yoursite.com
WOOCOMMERCE_KEY=ck_...
WOOCOMMERCE_SECRET=cs_...
```

---

## Step 2: Start Worker with Docker Compose

```bash
# Start full stack (app + worker + redis + postgres)
docker-compose up

# Or start worker only (if services already running)
docker-compose up worker

# View worker logs
docker-compose logs -f worker

# Scale to 4 workers
docker-compose up --scale worker=4
```

**Expected Output:**
```
worker_1    | 🚀 Background worker started
worker_1    | 📋 Monitoring queues: generate_3d, fashn_tryon, marketing_campaign, ml_training, ml_prediction
worker_1    | 📡 Redis: redis://:redispassword@redis:6379/0
```

---

## Step 3: Enqueue a Test Task

### Option A: Via Python API

```python
import asyncio
from agent_sdk.task_queue import TaskQueue

async def enqueue_test_task():
    queue = TaskQueue(redis_url="redis://localhost:6379/0")
    await queue.connect()

    # Enqueue 3D generation task
    task_id = await queue.enqueue_task(
        task_type="generate_3d",
        data={
            "prompt": "Black Rose luxury t-shirt with gold embroidery",
            "user_id": "user-test-123",
            "style": "realistic",
        },
        priority=100,  # Higher = higher priority
    )

    print(f"Task enqueued: {task_id}")

    # Wait for result
    result = await queue.get_result(task_id, timeout=300)
    print(f"Result: {result}")

asyncio.run(enqueue_test_task())
```

### Option B: Via Redis CLI

```bash
# Connect to Redis
redis-cli

# Enqueue task manually
ZADD queue:generate_3d 100 task-test-001

# Set task data
SET devskyy:tasks:task-test-001 '{"task_type":"generate_3d","data":{"prompt":"Test model","user_id":"user-123"},"status":"pending"}'

# Check queue
ZRANGE queue:generate_3d 0 -1 WITHSCORES

# Check result (after processing)
GET devskyy:tasks:task-test-001:result
```

---

## Step 4: Monitor Task Execution

### Check Worker Logs

```bash
docker-compose logs -f worker
```

**Look for:**
- `📋 Processing task task-test-001 (type: generate_3d)`
- `✅ Task task-test-001 completed (status: success)`

### Check Task Result in Redis

```bash
redis-cli GET devskyy:tasks:task-test-001:result
```

**Expected Output:**
```json
{
  "status": "success",
  "task_id": "task-test-001",
  "result": {
    "task_id": "tripo-abc123",
    "model_url": "https://example.com/model.glb",
    "texture_url": "https://example.com/texture.png"
  },
  "completed_at": "2024-01-05T12:00:00Z"
}
```

### Check Dead Letter Queue (if failed)

```bash
redis-cli KEYS devskyy:dlq:*
redis-cli GET devskyy:dlq:task-test-001
```

---

## Step 5: Test All Task Types

### 3D Generation

```python
await queue.enqueue_task(
    task_type="generate_3d",
    data={
        "prompt": "Premium hoodie with embroidery",
        "user_id": "user-123",
        "style": "realistic",
        "collection": "BLACK",
    }
)
```

### Marketing Campaign

```python
await queue.enqueue_task(
    task_type="marketing_campaign",
    data={
        "campaign_id": "camp-001",
        "campaign_type": "email",
        "recipients": ["user1@example.com", "user2@example.com"],
        "content": {
            "subject": "New Collection Launch",
            "body": "Check out our latest BLACK collection!"
        },
        "user_id": "user-123",
    }
)
```

### ML Training

```python
await queue.enqueue_task(
    task_type="ml_training",
    data={
        "model_id": "sentiment_analyzer",
        "training_data_path": "/data/reviews.csv",
        "epochs": 10,
        "user_id": "user-123",
    }
)
```

### ML Prediction

```python
await queue.enqueue_task(
    task_type="ml_prediction",
    data={
        "model_id": "sentiment_analyzer",
        "input_data": {"text": "This product is amazing!"},
        "user_id": "user-123",
    }
)
```

---

## Common Issues

### Issue: Worker Not Starting

**Error:** `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solution:**
```bash
# Check Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis

# Verify connection
redis-cli ping
```

### Issue: Tasks Not Processing

**Check 1:** Verify task in queue
```bash
redis-cli ZRANGE queue:generate_3d 0 -1
```

**Check 2:** Check worker logs
```bash
docker-compose logs worker | grep ERROR
```

**Check 3:** Verify environment variables
```bash
docker-compose exec worker env | grep TRIPO_API_KEY
```

### Issue: Task Failed

**Check DLQ:**
```bash
redis-cli KEYS devskyy:dlq:*
redis-cli GET devskyy:dlq:task-xxx
```

**Common Failures:**
- Missing API keys → Set in `.env`
- Invalid task input → Check schema in `orchestration/tasks.py`
- Network timeout → Increase `TASK_TIMEOUT` in docker-compose.yml

---

## Local Development (Without Docker)

### Option A: Run Worker Directly

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export REDIS_URL=redis://localhost:6379/0
export TRIPO_API_KEY=your-key-here
export OPENAI_API_KEY=sk-...

# Run worker
python -m agent_sdk.worker
```

### Option B: Use Development Mode

```bash
# Start Redis only
docker-compose up redis -d

# Run worker locally with hot reload
watchmedo auto-restart -p "*.py" -R python -m agent_sdk.worker
```

---

## Testing

### Run Unit Tests

```bash
# Run all tests
pytest tests/test_orchestration_tasks.py -v

# Run specific test
pytest tests/test_orchestration_tasks.py::test_process_3d_asset_generation_success -v

# Run with coverage
pytest tests/test_orchestration_tasks.py --cov=orchestration.tasks --cov-report=html
```

### Run Integration Tests (requires Redis)

```bash
# Start test services
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/test_orchestration_tasks.py -m integration -v

# Cleanup
docker-compose -f docker-compose.test.yml down
```

---

## Production Checklist

Before deploying to production:

- [ ] Environment variables configured (all required keys)
- [ ] Redis persistence enabled (AOF or RDB)
- [ ] Worker replicas set (minimum 2 for redundancy)
- [ ] Resource limits configured (CPU/memory)
- [ ] Health checks enabled
- [ ] Monitoring/alerts configured (Prometheus/Grafana)
- [ ] Secrets in secrets manager (not .env files)
- [ ] Rate limiting enabled (if needed)
- [ ] DLQ retention policy set (7 days default)
- [ ] Backup strategy for failed tasks

---

## Next Steps

1. **Read Full Docs:** See `docs/WORKER_ARCHITECTURE.md`
2. **Add Custom Tasks:** Extend `orchestration/tasks.py`
3. **Configure Monitoring:** Set up Prometheus metrics
4. **Scale Workers:** Increase replicas in `docker-compose.yml`
5. **Deploy to Production:** Use Kubernetes or cloud-native services

---

## Support

**Documentation:** `docs/WORKER_ARCHITECTURE.md`

**Issues:** Create GitHub issue with `worker` label

**Questions:** <support@skyyrose.com>

**Security:** <security@skyyrose.com>

---

**Last Updated:** 2026-01-05
