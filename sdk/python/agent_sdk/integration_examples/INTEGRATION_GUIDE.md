# DevSkyy Agent SDK Integration Guide

## Three Integration Approaches

This guide compares three patterns for integrating the Claude Agent SDK with your existing DevSkyy agents.

---

## Quick Comparison Table

| Factor | Approach A<br/>Direct Import | Approach B<br/>Message Queue | Approach C<br/>HTTP API |
|--------|------------------------------|------------------------------|-------------------------|
| **Complexity** | ⭐ Simple | ⭐⭐⭐ Complex | ⭐⭐ Moderate |
| **Latency** | ⭐⭐⭐ Fast (1-5ms) | ⭐ Slow (50-200ms) | ⭐⭐ Medium (10-50ms) |
| **Scalability** | ⭐ Single process | ⭐⭐⭐ Horizontal | ⭐⭐⭐ Horizontal |
| **Debugging** | ⭐⭐⭐ Easy | ⭐ Difficult | ⭐⭐ Moderate |
| **Deployment** | ⭐ Monolithic | ⭐⭐⭐ Decoupled | ⭐⭐⭐ Decoupled |
| **Infrastructure** | None | Redis + Workers | HTTP server |
| **Cost** | $ Low | $$$ High | $$ Medium |

---

## Approach A: Direct Import

### When to Use

✅ **Use when you have:**

- Single server deployment
- Low to medium traffic (< 1000 requests/day)
- Latency is critical (< 100ms response time)
- Development/staging environment
- Tight budget (no infrastructure costs)

❌ **Don't use when:**

- You need horizontal scaling
- Operations take > 30 seconds
- You want independent service deployment
- Traffic is unpredictable or spiky

### Example Use Cases

- Internal admin tools
- Development prototypes
- Low-traffic customer portals
- Single-tenant SaaS

### Code Example

```python
from agents.tripo_agent import Tripo3DAgent

@tool("generate_3d_model", "...", {...})
async def generate_3d_model(args: Dict[str, Any]) -> Dict[str, Any]:
    agent = Tripo3DAgent()
    result = await agent.generate_from_text(args["prompt"])
    return {"content": [{"type": "text", "text": f"Model: {result['model_url']}"}]}
```

### Setup Steps

1. No additional infrastructure needed
2. Import agents directly
3. Deploy as single application

### Performance Characteristics

- **Latency**: 1-5ms overhead
- **Throughput**: Limited by single process
- **Memory**: Shared with agent process
- **CPU**: Competes with agent for resources

---

## Approach B: Message Queue

### When to Use

✅ **Use when you have:**

- High traffic (> 1000 requests/day)
- Long-running operations (> 30 seconds)
- Need horizontal scaling
- Background processing requirements
- Fault tolerance is critical
- Budget for infrastructure

❌ **Don't use when:**

- You need immediate results
- Simple CRUD operations
- Tight latency requirements (< 100ms)
- Small team without DevOps expertise

### Example Use Cases

- 3D model generation (2-5 minutes per model)
- Bulk data processing
- Email campaign scheduling
- Video rendering
- ML model training

### Code Example

```python
task_id = await task_queue.enqueue(
    task_type="generate_3d",
    task_data={"prompt": args["prompt"]},
    priority=5
)

# Return immediately with task ID
# Background worker processes asynchronously
```

### Setup Steps

1. Install Redis: `brew install redis` or Docker
2. Start worker: `python approach_b_message_queue.py worker`
3. Queue tasks from agent
4. Poll for results

### Performance Characteristics

- **Latency**: 50-200ms (queue + network)
- **Throughput**: Scales with worker count
- **Memory**: Distributed across workers
- **CPU**: Isolated per worker

### Infrastructure Requirements

- **Redis**: 1+ instance (clustered for HA)
- **Workers**: 2-10+ instances
- **Monitoring**: Queue depth, worker health
- **Cost**: Redis + worker instances

---

## Approach C: HTTP API

### When to Use

✅ **Use when you have:**

- Microservices architecture
- Polyglot systems (different languages)
- Cross-team boundaries
- Need API versioning
- Want service isolation
- Load balancing requirements

❌ **Don't use when:**

- You want minimal latency
- Single language stack
- Small team/simple architecture
- Tight coupling is acceptable

### Example Use Cases

- Multi-language system (Python agent → Node.js service)
- Public-facing APIs
- Cross-team integrations
- Third-party service wrappers
- Multi-tenant systems

### Code Example

```python
api_client = DevSkyyAPIClient(base_url="http://localhost:8001")

response = await api_client.post("/3d/generate", data={
    "prompt": args["prompt"],
    "style": args["style"]
})

return {"content": [{"type": "text", "text": f"Model: {response['model_url']}"}]}
```

### Setup Steps

1. Create FastAPI service: `services/devskyy_api/main.py`
2. Start service: `uvicorn main:app --port 8001`
3. Call from agent via HTTP
4. Optional: Add load balancer (nginx/ALB)

### Performance Characteristics

- **Latency**: 10-50ms (HTTP overhead)
- **Throughput**: Scales with service instances
- **Memory**: Isolated per service
- **CPU**: Isolated per service

### Infrastructure Requirements

- **API Server**: 2+ instances (for HA)
- **Load Balancer**: nginx/HAProxy/ALB
- **Monitoring**: HTTP metrics, health checks
- **Cost**: Server instances + LB

---

## Decision Tree

```
Start Here
│
├─ Do you need horizontal scaling?
│  ├─ No → Do you need < 100ms latency?
│  │       ├─ Yes → **Use Approach A** (Direct Import)
│  │       └─ No → Consider Approach C (HTTP API)
│  │
│  └─ Yes → Are operations long-running (> 30s)?
│           ├─ Yes → **Use Approach B** (Message Queue)
│           └─ No → **Use Approach C** (HTTP API)
│
└─ Special Cases:
   ├─ Polyglot system → **Use Approach C**
   ├─ Background jobs → **Use Approach B**
   ├─ Tight budget → **Use Approach A**
   └─ Microservices → **Use Approach C**
```

---

## Hybrid Approach (Recommended)

**Best Practice**: Use different approaches for different operations!

```python
from agent_sdk.custom_tools import (
    generate_3d_model,      # Approach B (Queue) - long-running
    manage_product,         # Approach A (Direct) - fast CRUD
    analyze_data,           # Approach C (HTTP) - service boundary
)
```

### Example Hybrid Architecture

```
Agent SDK
    │
    ├─ 3D Generation ──────> Message Queue ──> Worker ──> Tripo3D
    │                         (Approach B - Long tasks)
    │
    ├─ Product CRUD ────────> Direct Import ──> CommerceAgent
    │                         (Approach A - Fast ops)
    │
    └─ Analytics ───────────> HTTP API ──> Analytics Service
                              (Approach C - Service boundary)
```

**Why Hybrid?**

- **3D Generation**: 2-5 minutes per model → Queue it (Approach B)
- **Product CRUD**: < 1 second → Call directly (Approach A)
- **Analytics**: Separate team/service → HTTP API (Approach C)

---

## Implementation Roadmap

### Phase 1: Start Simple (Week 1)

**Use Approach A for everything**

- Get it working quickly
- Understand the patterns
- Identify bottlenecks
- Deploy to staging

### Phase 2: Optimize Hot Paths (Week 2-3)

**Move slow operations to Approach B**

- Identify operations > 30 seconds
- Set up Redis + workers
- Migrate 3D generation
- Test background processing

### Phase 3: Scale (Week 4+)

**Add Approach C for service boundaries**

- Identify cross-team APIs
- Create FastAPI services
- Add load balancing
- Implement monitoring

---

## Code Migration Examples

### From Direct Import → Message Queue

**Before (Approach A):**

```python
@tool("generate_3d_model", "...", {...})
async def generate_3d_model(args: Dict[str, Any]) -> Dict[str, Any]:
    agent = Tripo3DAgent()
    result = await agent.generate_from_text(args["prompt"])
    return {"content": [{"type": "text", "text": result["model_url"]}]}
```

**After (Approach B):**

```python
@tool("generate_3d_model", "...", {...})
async def generate_3d_model(args: Dict[str, Any]) -> Dict[str, Any]:
    task_id = await task_queue.enqueue("generate_3d", args)

    if args.get("wait_for_completion"):
        result = await task_queue.get_result(task_id, timeout=300)
        return {"content": [{"type": "text", "text": result["model_url"]}]}
    else:
        return {"content": [{"type": "text", "text": f"Task queued: {task_id}"}]}
```

### From Direct Import → HTTP API

**Before (Approach A):**

```python
agent = CommerceAgent()
result = await agent.create_product(product_data)
```

**After (Approach C):**

```python
api_client = DevSkyyAPIClient()
result = await api_client.post("/products", data=product_data)
```

---

## Testing Strategies

### Approach A (Direct Import)

```python
# Easy - just import and test
from agent_sdk.custom_tools import generate_3d_model

result = await generate_3d_model({"prompt": "test ring"})
assert "model_url" in result
```

### Approach B (Message Queue)

```python
# Need to mock queue or use test Redis
from unittest.mock import patch

with patch("task_queue.enqueue") as mock_enqueue:
    mock_enqueue.return_value = "test-task-id"
    result = await generate_3d_model({"prompt": "test"})
```

### Approach C (HTTP API)

```python
# Use httpx test client or mock
from httpx import AsyncClient

async with AsyncClient(app=app, base_url="http://test") as client:
    response = await client.post("/3d/generate", json={"prompt": "test"})
    assert response.status_code == 200
```

---

## Monitoring & Observability

### Approach A

```python
# Add logging
import structlog
logger = structlog.get_logger()

@tool("generate_3d_model", "...", {...})
async def generate_3d_model(args: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("3d_generation_started", prompt=args["prompt"])
    start = time.time()
    result = await agent.generate_from_text(args["prompt"])
    duration = time.time() - start
    logger.info("3d_generation_completed", duration=duration)
    return result
```

### Approach B

```python
# Monitor queue metrics
queue_depth = await redis.zcard("queue:generate_3d")
worker_count = len(await redis.smembers("workers:active"))

metrics.gauge("queue.depth", queue_depth, tags=["queue:generate_3d"])
metrics.gauge("workers.active", worker_count)
```

### Approach C

```python
# Standard HTTP metrics
from prometheus_client import Counter, Histogram

http_requests = Counter("http_requests_total", "Total HTTP requests",
                        ["method", "endpoint", "status"])
http_duration = Histogram("http_request_duration_seconds", "HTTP request latency")

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    http_requests.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    http_duration.observe(duration)
    return response
```

---

## Cost Analysis (Monthly Estimates)

### Approach A: Direct Import

- **Infrastructure**: $0 (runs in same process)
- **Development**: 2-4 hours
- **Maintenance**: 1-2 hours/month
- **Total**: ~$50/month (dev time only)

### Approach B: Message Queue

- **Redis**: $20-100/month (managed service)
- **Workers**: $50-500/month (2-10 instances)
- **Monitoring**: $20-50/month
- **Development**: 8-16 hours (initial setup)
- **Maintenance**: 4-8 hours/month
- **Total**: ~$400-1000/month

### Approach C: HTTP API

- **API Servers**: $50-300/month (2-6 instances)
- **Load Balancer**: $20-50/month
- **Monitoring**: $20-50/month
- **Development**: 6-12 hours (initial setup)
- **Maintenance**: 2-4 hours/month
- **Total**: ~$250-700/month

---

## Recommendations by Company Stage

### Startup / MVP (< 100 users)

**→ Use Approach A (Direct Import)**

- Fastest time to market
- Minimal infrastructure costs
- Easy to change later
- Focus on product-market fit

### Growth Stage (100-10,000 users)

**→ Use Hybrid (A + B)**

- Direct import for fast operations
- Queue for slow operations
- Start measuring bottlenecks
- Prepare for scale

### Enterprise (> 10,000 users)

**→ Use All Three**

- Direct import for critical path
- Queue for background jobs
- HTTP API for service boundaries
- Full observability stack

---

## Summary

| Need | Recommended Approach |
|------|---------------------|
| **Fastest to implement** | Approach A |
| **Best for scaling** | Approach B or C |
| **Lowest latency** | Approach A |
| **Highest throughput** | Approach B |
| **Best for microservices** | Approach C |
| **Easiest to debug** | Approach A |
| **Most flexible** | Approach C |
| **Best for long tasks** | Approach B |

**Default Recommendation**: Start with **Approach A**, migrate hot paths to **Approach B** as needed, add **Approach C** for service boundaries.

---

## Next Steps

1. **Read all three implementations** in this directory
2. **Choose your approach** based on your requirements
3. **Replace placeholders** in `agent_sdk/custom_tools.py`
4. **Test thoroughly** with your existing agents
5. **Monitor performance** and adjust as needed

Questions? See the individual approach files for detailed examples.
