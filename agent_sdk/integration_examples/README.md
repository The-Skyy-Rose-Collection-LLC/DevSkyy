# Agent SDK Integration Examples

This directory contains three complete integration patterns for connecting the Claude Agent SDK with your existing DevSkyy agents.

## 📁 Files

### Implementation Examples

- **`approach_a_direct_import.py`** - Direct async call pattern (simplest)
- **`approach_b_message_queue.py`** - Redis queue + background workers (scalable)
- **`approach_c_http_api.py`** - HTTP API service pattern (decoupled)

### Documentation

- **`INTEGRATION_GUIDE.md`** - Complete comparison, decision tree, and recommendations

## 🚀 Quick Start

### 1. Read the Guide First

```bash
# Start here to understand the trade-offs
open INTEGRATION_GUIDE.md
```

### 2. Review the Implementations

```bash
# Read each approach's code and comments
cat approach_a_direct_import.py     # Simplest - start here
cat approach_b_message_queue.py     # For scaling
cat approach_c_http_api.py          # For microservices
```

### 3. Choose Your Approach

**For most projects, start with Approach A:**

```python
# Just works - no infrastructure needed
from agents.tripo_agent import Tripo3DAgent

@tool("generate_3d_model", "...", {...})
async def generate_3d_model(args):
    agent = Tripo3DAgent()
    result = await agent.generate_from_text(args["prompt"])
    return {"content": [{"type": "text", "text": result["model_url"]}]}
```

## 📊 Decision Matrix

| Your Situation | Use This |
|----------------|----------|
| Just getting started | **Approach A** |
| Need to scale horizontally | **Approach B** or **C** |
| Tasks take > 30 seconds | **Approach B** |
| Microservices architecture | **Approach C** |
| Multi-language system | **Approach C** |
| Background processing | **Approach B** |
| Budget conscious | **Approach A** |
| Need instant results | **Approach A** |

## 🎯 Implementation Checklist

### Approach A (Direct Import)

- [ ] Ensure agents are importable: `from agents.tripo_agent import Tripo3DAgent`
- [ ] Replace placeholders in `agent_sdk/custom_tools.py`
- [ ] Test imports: `python -c "from agents.tripo_agent import Tripo3DAgent"`
- [ ] Deploy as single application

**Estimated Time**: 30 minutes

### Approach B (Message Queue)

- [ ] Install Redis: `brew install redis` or Docker
- [ ] Install Python packages: `pip install redis celery`
- [ ] Start Redis: `redis-server`
- [ ] Create worker script based on `approach_b_message_queue.py`
- [ ] Start workers: `python worker.py`
- [ ] Update tools to queue tasks
- [ ] Add monitoring for queue depth

**Estimated Time**: 4-8 hours

### Approach C (HTTP API)

- [ ] Create FastAPI service: `services/devskyy_api/main.py`
- [ ] Install dependencies: `pip install fastapi uvicorn httpx`
- [ ] Implement API endpoints for each tool
- [ ] Start API server: `uvicorn main:app --port 8001`
- [ ] Update tools to call HTTP API
- [ ] Add health checks and monitoring
- [ ] Optional: Set up load balancer

**Estimated Time**: 6-12 hours

## 💡 Recommended Migration Path

### Phase 1: Proof of Concept (Day 1)

```python
# Use Approach A for everything
# Get it working end-to-end quickly
from agents.tripo_agent import Tripo3DAgent

@tool("generate_3d_model", "...", {...})
async def generate_3d_model(args):
    agent = Tripo3DAgent()
    result = await agent.generate_from_text(args["prompt"])
    return format_response(result)
```

### Phase 2: Identify Bottlenecks (Week 1)

```python
# Add timing to find slow operations
import time

@tool("generate_3d_model", "...", {...})
async def generate_3d_model(args):
    start = time.time()
    result = await agent.generate_from_text(args["prompt"])
    duration = time.time() - start

    print(f"3D generation took {duration:.2f}s")  # > 30s? Use queue!
    return format_response(result)
```

### Phase 3: Optimize Hot Paths (Week 2)

```python
# Move slow operations (> 30s) to queue
@tool("generate_3d_model", "...", {...})
async def generate_3d_model(args):
    # This takes 2-5 minutes → use queue
    task_id = await task_queue.enqueue("generate_3d", args)
    return {"task_id": task_id, "status": "queued"}

@tool("manage_product", "...", {...})
async def manage_product(args):
    # This takes < 1s → keep direct
    agent = CommerceAgent()
    result = await agent.create_product(args)
    return format_response(result)
```

### Phase 4: Add Service Boundaries (Month 2+)

```python
# Move cross-team/polyglot services to HTTP
@tool("analyze_data", "...", {...})
async def analyze_data(args):
    # Analytics team maintains separate service
    api_client = DevSkyyAPIClient()
    result = await api_client.post("/analytics/analyze", args)
    return format_response(result)
```

## 🔍 Testing Each Approach

### Test Approach A

```bash
cd agent_sdk/integration_examples

# Ensure agents are importable
python3 -c "from agents.tripo_agent import Tripo3DAgent; print('✅ Import works')"

# Run the example
python3 approach_a_direct_import.py
```

### Test Approach B

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start worker
python3 approach_b_message_queue.py worker

# Terminal 3: Run client
python3 approach_b_message_queue.py
```

### Test Approach C

```bash
# Terminal 1: Start API service (you need to create this)
cd services/devskyy_api
uvicorn main:app --port 8001

# Terminal 2: Test API
curl -X POST http://localhost:8001/api/v1/3d/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "engagement ring", "style": "realistic"}'

# Terminal 3: Run client
cd agent_sdk/integration_examples
python3 approach_c_http_api.py
```

## 📈 Performance Expectations

### Approach A: Direct Import

```
Latency:       1-5ms overhead
Throughput:    Limited by single process (~100 req/min)
Memory:        Shared with agent process
Scalability:   Vertical only
```

### Approach B: Message Queue

```
Latency:       50-200ms (queue + network)
Throughput:    Scales linearly with workers (1000+ req/min)
Memory:        Distributed across workers
Scalability:   Horizontal (add more workers)
```

### Approach C: HTTP API

```
Latency:       10-50ms (HTTP overhead)
Throughput:    Scales with service instances (500+ req/min)
Memory:        Isolated per service
Scalability:   Horizontal (add more instances)
```

## ⚠️ Common Pitfalls

### Approach A

❌ **Don't**: Use for operations > 30 seconds
❌ **Don't**: Assume infinite scaling
✅ **Do**: Use for fast operations (< 5s)
✅ **Do**: Monitor memory usage

### Approach B

❌ **Don't**: Forget to start workers
❌ **Don't**: Queue tasks that need instant results
✅ **Do**: Monitor queue depth
✅ **Do**: Implement retry logic

### Approach C

❌ **Don't**: Skip error handling for network failures
❌ **Don't**: Forget authentication in production
✅ **Do**: Use connection pooling
✅ **Do**: Implement circuit breakers

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'agents'"

```bash
# Ensure agents/ directory is in Python path
export PYTHONPATH="${PYTHONPATH}:/Users/coreyfoster/DevSkyy"

# Or add to each script:
import sys
sys.path.insert(0, '/Users/coreyfoster/DevSkyy')
```

### "Connection refused" (Redis/HTTP)

```bash
# Check if service is running
redis-cli ping  # Should return "PONG"
curl http://localhost:8001/health  # Should return 200
```

### "Task timeout"

```python
# Increase timeout for long operations
result = await task_queue.get_result(task_id, timeout=300)  # 5 minutes
```

## 📚 Additional Resources

- **Claude Agent SDK Docs**: <https://platform.claude.com/docs/en/api/agent-sdk/python>
- **FastAPI Documentation**: <https://fastapi.tiangolo.com/>
- **Celery Documentation**: <https://docs.celeryq.dev/>
- **Redis Documentation**: <https://redis.io/docs/>

## 🤝 Contributing

If you discover a better pattern or optimization:

1. Document it thoroughly
2. Add code examples
3. Include performance benchmarks
4. Share with the team!

## 📝 License

Same as DevSkyy project.

---

**Questions?** Review `INTEGRATION_GUIDE.md` for detailed comparisons and recommendations.

**Ready to implement?** Start with `approach_a_direct_import.py` and iterate from there!
