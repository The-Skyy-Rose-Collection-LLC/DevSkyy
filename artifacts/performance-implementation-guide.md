# Performance Implementation Guide
## DevSkyy Platform - SLO Compliance & Optimization

**Quick Start:** Implement these changes to achieve Truth Protocol P95 < 200ms compliance

---

## Phase 1: Real-Time SLO Tracking (Week 1)

### Step 1: Create Performance Middleware

```python
# middleware/performance_tracking.py
import time
from typing import Callable
from fastapi import Request, Response
from monitoring.observability import performance_tracker, metrics_collector
import logging

logger = logging.getLogger(__name__)

async def performance_middleware(request: Request, call_next: Callable) -> Response:
    """
    Track request performance and enforce SLO monitoring.

    Metrics tracked:
    - Request latency (P50, P95, P99)
    - Error rates
    - Throughput
    """
    start_time = time.time()

    # Execute request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Record metrics
    performance_tracker.record_request(
        endpoint=request.url.path,
        duration_ms=duration_ms,
        status_code=response.status_code
    )

    # Update Prometheus histogram
    metrics_collector.observe_histogram(
        "http_request_duration_seconds",
        duration_ms / 1000,
        labels={
            "method": request.method,
            "endpoint": request.url.path.split("/")[1] if len(request.url.path.split("/")) > 1 else "root"
        }
    )

    # Increment request counter
    metrics_collector.increment_counter(
        "http_requests_total",
        value=1,
        labels={
            "method": request.method,
            "endpoint": request.url.path.split("/")[1] if len(request.url.path.split("/")) > 1 else "root",
            "status_code": str(response.status_code)
        }
    )

    # Add response time header
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

    # Check SLO compliance
    stats = performance_tracker.get_endpoint_stats(request.url.path)
    if stats.get("requests", 0) > 100:  # Only check after 100 requests
        p95 = stats.get("latency_ms", {}).get("p95", 0)
        error_rate = stats.get("error_rate", 0)

        # P95 SLO violation
        if p95 > 200:
            logger.error(
                f"SLO VIOLATION: P95 latency {p95:.2f}ms exceeds 200ms threshold",
                extra={
                    "slo_violation": "p95_latency",
                    "endpoint": request.url.path,
                    "p95_ms": p95,
                    "threshold_ms": 200,
                    "current_requests": stats["requests"]
                }
            )

        # Error rate SLO violation
        if error_rate > 0.5:
            logger.error(
                f"SLO VIOLATION: Error rate {error_rate:.2f}% exceeds 0.5% threshold",
                extra={
                    "slo_violation": "error_rate",
                    "endpoint": request.url.path,
                    "error_rate_percent": error_rate,
                    "threshold_percent": 0.5,
                    "total_errors": stats["errors"],
                    "total_requests": stats["requests"]
                }
            )

    return response
```

### Step 2: Add to Main Application

```python
# main.py (add after line 237)
# Add performance tracking middleware
try:
    from middleware.performance_tracking import performance_middleware
    app.add_middleware(BaseHTTPMiddleware, dispatch=performance_middleware)
    logger.info("✅ Performance tracking middleware enabled")
except ImportError as e:
    logger.warning(f"⚠️ Performance tracking middleware not available: {e}")
```

### Step 3: Create SLO Monitoring Endpoint

```python
# api/v1/slo.py
import logging
from fastapi import APIRouter, Depends
from datetime import datetime
from monitoring.observability import performance_tracker, metrics_collector
from security.jwt_auth import require_admin, TokenData

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/slo", tags=["slo-monitoring"])


@router.get("/status")
async def get_slo_status(current_user: TokenData = Depends(require_admin)):
    """
    Get current SLO compliance status for all endpoints.

    Returns:
        dict: SLO compliance status with violations and metrics
    """
    stats = performance_tracker.get_all_stats()

    slo_status = {
        "timestamp": datetime.now().isoformat(),
        "overall_compliant": True,
        "violations": [],
        "endpoints": {},
        "summary": {
            "total_endpoints": 0,
            "compliant_endpoints": 0,
            "violated_endpoints": 0,
            "p95_violations": 0,
            "error_rate_violations": 0
        }
    }

    for endpoint, endpoint_stats in stats.items():
        if endpoint_stats.get("requests", 0) < 10:
            # Skip endpoints with insufficient data
            continue

        slo_status["summary"]["total_endpoints"] += 1

        latency = endpoint_stats.get("latency_ms", {})
        p95 = latency.get("p95", 0)
        p99 = latency.get("p99", 0)
        error_rate = endpoint_stats.get("error_rate", 0)

        # Check P95 compliance
        p95_compliant = p95 < 200
        # Check P99 compliance
        p99_compliant = p99 < 500
        # Check error rate compliance
        error_rate_compliant = error_rate < 0.5

        endpoint_compliant = p95_compliant and p99_compliant and error_rate_compliant

        if endpoint_compliant:
            slo_status["summary"]["compliant_endpoints"] += 1
        else:
            slo_status["summary"]["violated_endpoints"] += 1
            slo_status["overall_compliant"] = False

        # Track violations
        if not p95_compliant:
            slo_status["summary"]["p95_violations"] += 1
            slo_status["violations"].append({
                "type": "p95_latency",
                "endpoint": endpoint,
                "current_value": round(p95, 2),
                "threshold": 200,
                "severity": "HIGH" if p95 > 300 else "MEDIUM"
            })

        if not error_rate_compliant:
            slo_status["summary"]["error_rate_violations"] += 1
            slo_status["violations"].append({
                "type": "error_rate",
                "endpoint": endpoint,
                "current_value": round(error_rate, 2),
                "threshold": 0.5,
                "severity": "CRITICAL" if error_rate > 1.0 else "HIGH"
            })

        # Store endpoint metrics
        slo_status["endpoints"][endpoint] = {
            "requests": endpoint_stats["requests"],
            "errors": endpoint_stats["errors"],
            "error_rate_percent": round(error_rate, 2),
            "latency_ms": {
                "p50": round(latency.get("p50", 0), 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2),
                "mean": round(latency.get("mean", 0), 2),
                "min": round(latency.get("min", 0), 2),
                "max": round(latency.get("max", 0), 2)
            },
            "slo_compliance": {
                "p95_compliant": p95_compliant,
                "p99_compliant": p99_compliant,
                "error_rate_compliant": error_rate_compliant,
                "overall_compliant": endpoint_compliant
            }
        }

    return slo_status


@router.get("/endpoint/{endpoint_path:path}")
async def get_endpoint_slo(
    endpoint_path: str,
    current_user: TokenData = Depends(require_admin)
):
    """
    Get SLO metrics for a specific endpoint.

    Args:
        endpoint_path: API endpoint path (e.g., 'api/v1/health')

    Returns:
        dict: Detailed SLO metrics for the endpoint
    """
    endpoint = f"/{endpoint_path}"
    stats = performance_tracker.get_endpoint_stats(endpoint)

    if not stats or stats.get("requests", 0) == 0:
        return {
            "endpoint": endpoint,
            "status": "no_data",
            "message": "Insufficient data for this endpoint"
        }

    latency = stats.get("latency_ms", {})
    p95 = latency.get("p95", 0)
    error_rate = stats.get("error_rate", 0)

    return {
        "endpoint": endpoint,
        "timestamp": datetime.now().isoformat(),
        "requests": stats["requests"],
        "errors": stats["errors"],
        "error_rate_percent": round(error_rate, 2),
        "latency_ms": {
            "min": round(latency.get("min", 0), 2),
            "p50": round(latency.get("p50", 0), 2),
            "p95": round(p95, 2),
            "p99": round(latency.get("p99", 0), 2),
            "max": round(latency.get("max", 0), 2),
            "mean": round(latency.get("mean", 0), 2)
        },
        "slo_compliance": {
            "p95_target_ms": 200,
            "p95_compliant": p95 < 200,
            "p95_margin_ms": round(200 - p95, 2),
            "error_rate_target_percent": 0.5,
            "error_rate_compliant": error_rate < 0.5,
            "overall_compliant": p95 < 200 and error_rate < 0.5
        }
    }


logger.info("✅ SLO monitoring API endpoints registered")
```

### Step 4: Register SLO Router

```python
# main.py (add to router registration section around line 500)
try:
    from api.v1.slo import router as slo_router
    app.include_router(slo_router, prefix="/api/v1/slo", tags=["v1-slo"])
    logger.info("✅ SLO monitoring router registered")
except ImportError as e:
    logger.warning(f"⚠️ SLO router not available: {e}")
```

---

## Phase 2: Caching Layer (Week 2)

### Step 1: Create Caching Decorator

```python
# utils/caching.py
import json
import hashlib
from functools import wraps
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

try:
    from ml.redis_cache import RedisCache
    import os

    redis_cache = RedisCache(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        default_ttl=3600
    )
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("Redis cache not available - using in-memory fallback")

# In-memory fallback cache
_memory_cache = {}


def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """
    Cache function result in Redis (or memory fallback).

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key

    Example:
        @cache_result(ttl=3600, key_prefix="products")
        async def get_products():
            return await db.fetch_all("SELECT * FROM products")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_data = {
                "function": func.__name__,
                "args": str(args),
                "kwargs": str(sorted(kwargs.items()))
            }
            key_hash = hashlib.md5(
                json.dumps(key_data, sort_keys=True).encode()
            ).hexdigest()
            cache_key = f"{key_prefix}:{func.__name__}:{key_hash}"

            # Try to get from cache
            if CACHE_AVAILABLE:
                try:
                    cached_value = await redis_cache.get(cache_key)
                    if cached_value is not None:
                        logger.debug(f"Cache HIT: {cache_key}")
                        return cached_value
                except Exception as e:
                    logger.warning(f"Cache get failed: {e}")
            else:
                # In-memory fallback
                if cache_key in _memory_cache:
                    logger.debug(f"Memory cache HIT: {cache_key}")
                    return _memory_cache[cache_key]

            logger.debug(f"Cache MISS: {cache_key}")

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            if CACHE_AVAILABLE:
                try:
                    await redis_cache.set(cache_key, result, ttl=ttl)
                    logger.debug(f"Cached result: {cache_key} (TTL: {ttl}s)")
                except Exception as e:
                    logger.warning(f"Cache set failed: {e}")
            else:
                # In-memory fallback (basic, no TTL)
                _memory_cache[cache_key] = result
                logger.debug(f"Memory cached: {cache_key}")

            return result

        return wrapper
    return decorator


async def invalidate_cache(pattern: str):
    """
    Invalidate cache keys matching pattern.

    Args:
        pattern: Cache key pattern (e.g., "products:*")
    """
    if CACHE_AVAILABLE:
        try:
            await redis_cache.delete_pattern(pattern)
            logger.info(f"Invalidated cache pattern: {pattern}")
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
    else:
        # Clear memory cache
        keys_to_delete = [k for k in _memory_cache.keys() if k.startswith(pattern.replace("*", ""))]
        for key in keys_to_delete:
            del _memory_cache[key]
        logger.info(f"Invalidated memory cache: {len(keys_to_delete)} keys")
```

### Step 2: Apply Caching to Expensive Operations

```python
# Example: Cache product listings
# api/v1/ecommerce.py (or wherever product endpoints are)

from utils.caching import cache_result, invalidate_cache

@router.get("/products")
@cache_result(ttl=3600, key_prefix="products")  # Cache for 1 hour
async def get_products(
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get product listings (cached)."""
    # ... database query ...
    return products


@router.post("/products")
async def create_product(product_data: dict):
    """Create product and invalidate cache."""
    # Create product
    new_product = await db.insert_product(product_data)

    # Invalidate cache
    await invalidate_cache("products:*")

    return new_product
```

### Step 3: Cache AI Model Results

```python
# Example: Cache AI styling recommendations
# agent/modules/backend/fashion_agent.py

from utils.caching import cache_result

class FashionAgent:
    @cache_result(ttl=7200, key_prefix="ai_styling")  # Cache for 2 hours
    async def get_styling_recommendations(self, user_id: int, product_id: int):
        """
        Get AI styling recommendations (expensive operation).

        This operation is expensive (AI inference takes 500-2000ms).
        Caching reduces subsequent requests to < 10ms.
        """
        # Expensive AI operation
        recommendations = await self.ai_engine.generate_recommendations(
            user_id=user_id,
            product_id=product_id
        )

        return recommendations
```

---

## Phase 3: Database Optimization (Week 3)

### Step 1: Add Slow Query Logging

```python
# database/query_monitor.py
import time
import logging
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)

SLOW_QUERY_THRESHOLD_MS = 100  # Log queries slower than 100ms


def log_query_time(threshold_ms: int = SLOW_QUERY_THRESHOLD_MS):
    """
    Decorator to log slow database queries.

    Args:
        threshold_ms: Threshold in milliseconds for slow query logging

    Example:
        @log_query_time(threshold_ms=100)
        async def get_user_orders(user_id: int):
            return await db.fetch_all(query, {"user_id": user_id})
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                if duration_ms > threshold_ms:
                    logger.warning(
                        f"SLOW QUERY: {func.__name__} took {duration_ms:.2f}ms",
                        extra={
                            "query_time_ms": duration_ms,
                            "threshold_ms": threshold_ms,
                            "function": func.__name__,
                            "module": func.__module__,
                            "slow_query": True
                        }
                    )
                else:
                    logger.debug(f"Query: {func.__name__} - {duration_ms:.2f}ms")

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"QUERY FAILED: {func.__name__} failed after {duration_ms:.2f}ms",
                    extra={
                        "query_time_ms": duration_ms,
                        "function": func.__name__,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise

        return wrapper
    return decorator


# Usage example:
from database.query_monitor import log_query_time

@log_query_time(threshold_ms=100)
async def get_user_with_orders(user_id: int):
    """Get user with all orders (monitored query)."""
    query = """
    SELECT u.*, o.*
    FROM users u
    LEFT JOIN orders o ON o.user_id = u.id
    WHERE u.id = :user_id
    """
    return await db.fetch_all(query, {"user_id": user_id})
```

### Step 2: Fix N+1 Queries

```python
# Example: Optimize agent task loading

# ❌ BAD: N+1 query problem
async def get_agents_with_tasks_BAD():
    """This creates N+1 queries - DO NOT USE."""
    agents = await db.fetch_all("SELECT * FROM agents")

    for agent in agents:
        # This runs a separate query for EACH agent (N queries)
        agent.tasks = await db.fetch_all(
            "SELECT * FROM tasks WHERE agent_id = :id",
            {"id": agent.id}
        )

    return agents


# ✅ GOOD: Single query with JOIN
@log_query_time(threshold_ms=100)
async def get_agents_with_tasks_GOOD():
    """Optimized single query - USE THIS."""
    query = """
    SELECT
        a.id as agent_id,
        a.name as agent_name,
        a.status as agent_status,
        t.id as task_id,
        t.title as task_title,
        t.status as task_status
    FROM agents a
    LEFT JOIN tasks t ON t.agent_id = a.id
    ORDER BY a.id, t.created_at DESC
    """

    results = await db.fetch_all(query)

    # Group by agent
    agents = {}
    for row in results:
        agent_id = row["agent_id"]

        if agent_id not in agents:
            agents[agent_id] = {
                "id": agent_id,
                "name": row["agent_name"],
                "status": row["agent_status"],
                "tasks": []
            }

        if row["task_id"]:
            agents[agent_id]["tasks"].append({
                "id": row["task_id"],
                "title": row["task_title"],
                "status": row["task_status"]
            })

    return list(agents.values())
```

### Step 3: Add Database Indexes

```sql
-- migrations/add_performance_indexes.sql

-- Index for common user queries
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- Index for order queries
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);

-- Composite index for common order queries
CREATE INDEX IF NOT EXISTS idx_orders_user_status
ON orders(user_id, status, created_at DESC);

-- Index for product searches
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_products_name_gin
ON products USING GIN (to_tsvector('english', name));

-- Agent-specific indexes
CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_agent_logs_agent_id ON agent_logs(agent_id);

-- Analyze tables after adding indexes
ANALYZE users;
ANALYZE orders;
ANALYZE products;
ANALYZE tasks;
ANALYZE agent_logs;
```

---

## Phase 4: Update Alert Thresholds (Week 1)

### Fix Alert Rules to Match Truth Protocol

```python
# monitoring/enterprise_metrics.py
# Update _initialize_alert_rules() method

def _initialize_alert_rules(self):
    """Initialize default alert rules - Truth Protocol compliant."""
    default_rules = [
        # P95 Latency Alert (Truth Protocol: < 200ms)
        AlertRule(
            name="p95_latency_violation",
            metric_name="http_request_duration_seconds",
            condition="> 0.200",  # 200ms = 0.200s
            threshold=0.200,
            severity=AlertSeverity.HIGH,
            duration=120,
            description="P95 latency exceeds 200ms threshold (Truth Protocol Rule #12)",
            runbook_url="https://docs.devskyy.com/runbooks/p95-latency"
        ),

        # P99 Latency Alert (Truth Protocol: < 500ms)
        AlertRule(
            name="p99_latency_violation",
            metric_name="http_request_duration_seconds",
            condition="> 0.500",  # 500ms = 0.500s
            threshold=0.500,
            severity=AlertSeverity.CRITICAL,
            duration=60,
            description="P99 latency exceeds 500ms threshold (Truth Protocol Rule #12)"
        ),

        # Error Rate Alert (Truth Protocol: < 0.5%)
        AlertRule(
            name="high_error_rate",
            metric_name="http_requests_total",
            condition="> 0.005",  # 0.5% = 0.005
            threshold=0.005,
            severity=AlertSeverity.CRITICAL,
            duration=60,
            description="Error rate exceeds 0.5% threshold (Truth Protocol Rule #12)"
        ),

        # CPU Usage Alert (Truth Protocol: < 70%)
        AlertRule(
            name="high_cpu",
            metric_name="cpu_usage_percent",
            condition="> 70",  # Changed from 80
            threshold=70,
            severity=AlertSeverity.MEDIUM,
            duration=300,
            description="CPU usage exceeds 70% threshold (Truth Protocol Rule #12)"
        ),

        # Memory Usage Alert (Truth Protocol: < 80%)
        AlertRule(
            name="low_memory",
            metric_name="memory_usage_bytes",
            condition="> 0.80",  # Changed from 0.90
            threshold=0.80,
            severity=AlertSeverity.HIGH,
            duration=300,
            description="Memory usage exceeds 80% threshold (Truth Protocol Rule #12)"
        ),

        # Additional alerts...
        AlertRule(
            name="ai_model_failures",
            metric_name="ai_model_requests_total",
            condition="> 0.1",
            threshold=0.1,
            severity=AlertSeverity.HIGH,
            duration=180,
            description="AI model failure rate exceeds 10%"
        ),

        AlertRule(
            name="security_events",
            metric_name="security_events_total",
            condition="> 10",
            threshold=10,
            severity=AlertSeverity.CRITICAL,
            duration=60,
            description="High number of security events detected"
        )
    ]

    for rule in default_rules:
        self.add_alert_rule(rule)
```

---

## Testing Your Implementation

### Step 1: Local Performance Test

```python
# scripts/test_performance.py
import asyncio
import httpx
import statistics
import time
from datetime import datetime

async def benchmark_endpoint(url: str, requests: int = 1000):
    """Benchmark API endpoint and validate SLO."""
    print(f"\nBenchmarking: {url}")
    print(f"Requests: {requests}\n")

    latencies = []
    errors = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(requests):
            try:
                start = time.time()
                response = await client.get(url)
                latency_ms = (time.time() - start) * 1000
                latencies.append(latency_ms)

                if response.status_code >= 400:
                    errors += 1

                if (i + 1) % 100 == 0:
                    print(f"Progress: {i + 1}/{requests} requests")

            except Exception as e:
                errors += 1
                print(f"Error: {e}")

    # Calculate percentiles
    sorted_latencies = sorted(latencies)
    count = len(sorted_latencies)

    results = {
        "timestamp": datetime.now().isoformat(),
        "total_requests": requests,
        "successful_requests": count,
        "failed_requests": errors,
        "error_rate_percent": (errors / requests) * 100,
        "latency_ms": {
            "min": round(min(latencies), 2),
            "p50": round(sorted_latencies[int(count * 0.50)], 2),
            "p75": round(sorted_latencies[int(count * 0.75)], 2),
            "p90": round(sorted_latencies[int(count * 0.90)], 2),
            "p95": round(sorted_latencies[int(count * 0.95)], 2),
            "p99": round(sorted_latencies[int(count * 0.99)], 2),
            "max": round(max(latencies), 2),
            "mean": round(statistics.mean(latencies), 2)
        }
    }

    # Print results
    print("\n" + "="*60)
    print("PERFORMANCE TEST RESULTS")
    print("="*60)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Total Requests: {results['total_requests']}")
    print(f"Successful: {results['successful_requests']}")
    print(f"Failed: {results['failed_requests']}")
    print(f"Error Rate: {results['error_rate_percent']:.2f}%")
    print(f"\nLatency (milliseconds):")
    print(f"  Min:  {results['latency_ms']['min']}ms")
    print(f"  P50:  {results['latency_ms']['p50']}ms")
    print(f"  P75:  {results['latency_ms']['p75']}ms")
    print(f"  P90:  {results['latency_ms']['p90']}ms")
    print(f"  P95:  {results['latency_ms']['p95']}ms ← Truth Protocol SLO")
    print(f"  P99:  {results['latency_ms']['p99']}ms")
    print(f"  Max:  {results['latency_ms']['max']}ms")
    print(f"  Mean: {results['latency_ms']['mean']}ms")

    # Validate SLO
    print("\n" + "="*60)
    print("TRUTH PROTOCOL SLO VALIDATION")
    print("="*60)

    p95_pass = results['latency_ms']['p95'] < 200
    p99_pass = results['latency_ms']['p99'] < 500
    error_rate_pass = results['error_rate_percent'] < 0.5

    print(f"P95 < 200ms:     {'✅ PASS' if p95_pass else '❌ FAIL'}")
    print(f"P99 < 500ms:     {'✅ PASS' if p99_pass else '❌ FAIL'}")
    print(f"Error Rate < 0.5%: {'✅ PASS' if error_rate_pass else '❌ FAIL'}")

    all_pass = p95_pass and p99_pass and error_rate_pass
    print("\n" + "="*60)
    if all_pass:
        print("OVERALL: ✅ ALL SLOs MET")
        print("="*60)
        return 0
    else:
        print("OVERALL: ❌ SLO VIOLATIONS DETECTED")
        print("="*60)
        return 1

async def main():
    """Run performance tests against local server."""
    base_url = "http://localhost:8000"

    print("DevSkyy Performance Test Suite")
    print("Truth Protocol Rule #12 Compliance Validation\n")

    # Test health endpoint
    exit_code = await benchmark_endpoint(f"{base_url}/health", requests=1000)

    # Test API status endpoint
    # await benchmark_endpoint(f"{base_url}/status", requests=500)

    return exit_code

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
```

### Step 2: Run the Test

```bash
# Terminal 1: Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Terminal 2: Run performance test
python scripts/test_performance.py
```

### Step 3: Check SLO Status

```bash
# Get SLO compliance status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/slo/status | jq

# Get specific endpoint metrics
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/slo/endpoint/health | jq
```

---

## Quick Wins Checklist

### Immediate (< 1 day)

- [ ] Add performance tracking middleware
- [ ] Create SLO monitoring endpoint
- [ ] Fix alert thresholds (CPU 70%, Memory 80%)
- [ ] Run baseline performance test

### Week 1

- [ ] Implement caching decorator
- [ ] Cache top 10 most expensive operations
- [ ] Add slow query logging
- [ ] Set up SLO dashboard

### Week 2

- [ ] Optimize N+1 queries
- [ ] Add database indexes
- [ ] Increase connection pool size (production)
- [ ] Implement cache invalidation strategy

### Week 3

- [ ] Convert blocking I/O to async
- [ ] Add memory profiling
- [ ] Optimize AI model caching
- [ ] Set up Grafana dashboards

---

## Success Metrics

After implementing these changes, you should see:

**Performance Improvements:**
- 40-60% reduction in P95 latency (caching)
- 80%+ cache hit rate
- 50% reduction in database query time
- 99.9%+ availability

**Monitoring Improvements:**
- Real-time P95/P99 tracking
- SLO compliance dashboard
- Automatic alerting on violations
- Historical performance trends

**Developer Experience:**
- Faster local development
- Performance regression detection
- Better debugging tools
- Clear performance budgets

---

## Support & Resources

**Documentation:**
- Truth Protocol: /home/user/DevSkyy/CLAUDE.md
- Performance Testing: /home/user/DevSkyy/.github/workflows/performance.yml
- Monitoring: /home/user/DevSkyy/monitoring/

**Tools:**
- Autocannon: `npm install -g autocannon`
- Locust: `pip install locust`
- Performance test: `python scripts/test_performance.py`

**Endpoints:**
- Health: `GET /health`
- Status: `GET /status`
- Metrics: `GET /metrics`
- SLO Status: `GET /api/v1/slo/status`
- Performance: `GET /api/v1/monitoring/performance`

---

**Implementation Guide Version:** 1.0
**Last Updated:** 2025-11-15
**Maintainer:** DevSkyy Performance Team
