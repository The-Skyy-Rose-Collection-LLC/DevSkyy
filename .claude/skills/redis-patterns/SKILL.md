---
name: redis-patterns
description: Redis data structure patterns, caching strategies, distributed locks, rate limiting, pub/sub, and connection management for production applications. Use when adding or debugging caching, a distributed lock, a rate limiter, session/token storage, or a Streams/Pub-Sub flow against the devskyy Redis. Do NOT use for durable relational data or transactional integrity (postgres-patterns — Redis is not a system of record), for schema/versioned state (database-migrations), or for the container's health/networking (docker-patterns).
origin: ECC
---

# Redis Patterns

Quick reference for Redis best practices across common backend use cases.

## How It Works

Redis is an in-memory data structure store that supports strings, hashes, lists, sets, sorted sets, streams, and more. Individual Redis commands are atomic on a single instance; multi-step workflows require Lua scripts, MULTI/EXEC transactions, or explicit synchronization to stay atomic. Data is optionally persisted via RDB snapshots or AOF logs. Clients communicate over TCP using the RESP protocol; connection pools are essential to avoid per-request handshake overhead.

All primary examples use `redis.asyncio` — the async-native client bundled with redis-py ≥ 4.2. Use it for any FastAPI / asyncio application. A short sync note is included at the end of Connection Management for scripts and CLI utilities.

## When to use

- Adding caching to an application
- Implementing rate limiting or throttling
- Building distributed locks or coordination
- Setting up session or token storage
- Using Pub/Sub or Redis Streams for messaging
- Configuring Redis in production (pooling, eviction, clustering)

**When NOT to use:**

- Data that must survive a flush or a node loss → Postgres. Redis here runs `maxmemory-policy
  noeviction` with `maxmemory 0` (verified below): unbounded, and nothing evicts to make room.
- Schema/versioned state → `database-migrations`. Relational modelling and indexes →
  `postgres-patterns`.
- "Redis container won't start / can't connect from the app" → `docker-patterns` first; this skill
  assumes a reachable, authenticated client.
- Any `FLUSHALL`/`FLUSHDB` against a shared instance — irreversible, STOP-AND-SHOW.

## Inputs

**Absent input = STOP. A cache key written to the wrong instance is invisible until it corrupts something.**

1. **A reachable, authenticated client.** This instance requires auth: a bare `redis-cli ping`
   returns `NOAUTH Authentication required.` (observed 2026-07-28 `[repro]`). Use
   `REDISCLI_AUTH="$REDIS_PASSWORD"` (env, not argv). No password → stop; do not disable auth.
2. **The target instance and DB index.** Cache, queue, and rate-limit state should not share a
   logical DB by accident. Confirm with `INFO server` / `dbsize` before writing.
3. **A TTL decision for every key you create.** There is no eviction fallback here (see the
   `maxmemory-policy` check) — a key without a TTL is a permanent memory leak. If the TTL is
   genuinely unbounded, that key belongs in Postgres.
4. **For any lock: an owner token and a TTL that exceeds the worst-case job duration.** A lock
   released by a different holder is a correctness bug, which is why release must be the
   compare-and-delete Lua script, never a bare `DEL`.

## Procedure

1. Confirm connectivity and identity (Verification check 1) before writing any code.
2. Pick the structure from the cheat sheet by access pattern, then design the key name
   (`namespace:resource:id`) and its TTL together — never the key alone.
3. Implement with `redis.asyncio` (the sync client blocks the FastAPI event loop) and a module-level
   pool created once at startup; wire teardown through the lifespan handler.
4. Make every multi-step sequence atomic: pipeline with `transaction=True` for grouped writes, or a
   Lua script when a read must gate a write (sliding-window limiter, lock release).
5. Set the TTL in the same call that writes the value (`setex`, or `hset` + `expire` inside one
   pipeline) — a crash between write and expire is exactly how untracked keys are born.
6. Verify TTL coverage and lock semantics against the real instance (Verification checks 2-3).
7. On failure paths, confirm the app degrades to the source of truth rather than serving stale or
   erroring: a cache outage must not be an application outage.

## Verification

Each check names its command and pass condition. A command that returns an auth error or connects
to the wrong instance is a dead gate, not a pass (bug-230). Results below are `[repro]` against the
local dev container — they are not claims about any production Redis.

```bash
docker exec devskyy-redis sh -c 'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli ping; \
  REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli dbsize; \
  REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli info memory | grep -E "used_memory_human|maxmemory_human"'
```
**PASS:** `PONG`, plus a `dbsize` and memory figure you can compare against later. Observed
2026-07-28: `PONG`, `dbsize 0`, `used_memory_human:1.23M`, `maxmemory_human:0B` `[repro]`.
`maxmemory 0` = no cap, so TTLs are the *only* thing bounding memory on this instance.

```bash
docker exec devskyy-redis sh -c 'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli config get maxmemory-policy'
```
**PASS:** you have read the value and your key design matches it. Observed 2026-07-28:
`noeviction` `[repro]` — under a memory cap this instance would **error on writes** rather than
evict, so "the cache will just evict old keys" is false here. Any pattern in this skill that
assumes `allkeys-lru` must be adjusted or the policy changed deliberately.

```bash
docker exec devskyy-redis sh -c '
  REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli set lock:demo tok-1 PX 5000 NX
  REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli set lock:demo tok-2 PX 5000 NX
  REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli pttl lock:demo
  REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli del lock:demo'
```
**PASS:** first `SET` returns `OK`, the second returns **empty** (nil — contended, correctly
refused), `pttl` is a positive number ≤ 5000, and `del` returns `1`. Observed 2026-07-28:
`OK`, ``(empty)``, `4985`, `1` `[repro]`. If the second `SET` also returns `OK`, `NX` is not being
applied and your lock grants concurrent holders.

```bash
docker exec devskyy-redis sh -c 'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli --scan --count 1000 \
  | while read -r k; do t=$(REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli ttl "$k"); \
    [ "$t" = "-1" ] && echo "NO-TTL $k"; done'
```
**PASS:** no `NO-TTL` lines. Every key that is not a deliberate, documented long-lived structure must
carry a TTL — with `noeviction` and no `maxmemory`, a TTL-less key never leaves. `[repro]`

Prove the lock check can fail (rule 3): drop the `NX` flag from the second `SET` and re-run — it
must return `OK`, showing the check distinguishes "lock held" from "lock free" — then restore it.

Attribute before claiming a leak is yours (rule 4): snapshot `dbsize` and the TTL-less key list
before and after your change, and compare against the pristine tree's code via
`git archive HEAD core/ | tar -x -C <scratch>`. Never `git stash` — the stack is shared across
worktrees.

## Worked example

Real session against the dev container, 2026-07-28:

```bash
docker exec devskyy-redis redis-cli ping
docker exec devskyy-redis sh -c 'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli ping'
docker exec devskyy-redis sh -c '
  REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli set lock:skill-demo:wp-ops tok-1 PX 5000 NX
  REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli set lock:skill-demo:wp-ops tok-2 PX 5000 NX
  REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli pttl lock:skill-demo:wp-ops
  REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli del lock:skill-demo:wp-ops'
```

Observed `[repro]`:

```
NOAUTH Authentication required.
PONG
OK

4985
1
```

Three facts fall out. The first line is auth *working* — an agent that reads `NOAUTH` as "Redis is
down" will go fix a container that is healthy. The blank line after `OK` is the second `SET NX`
returning nil: the lock was already held, so acquisition was correctly refused — that empty line is
the entire safety property, and a harness that only checks "did the command run" would miss it.
`pttl 4985` confirms the 5000ms expiry is armed, which is what stops a crashed holder from wedging
the resource forever.

Paired with `maxmemory-policy noeviction` and `maxmemory 0B` on this instance, the operative rule
for any new key here is the TTL: nothing evicts, nothing is capped, so
`core/redis_cache.py:191`'s `await self._client.setex(key, ttl, json.dumps(response))` — TTL passed
in the same call as the value, defaulting from `LLM_CACHE_TTL` at `core/redis_cache.py:60` `[repo]`
— is the pattern to copy, not a bare `set` followed by a hopeful `expire`.

## Data Structure Cheat Sheet

| Use Case | Structure | Example Key |
|----------|-----------|-------------|
| Simple cache | String | `product:123` |
| User session | Hash | `session:abc` |
| Leaderboard | Sorted Set | `scores:weekly` |
| Unique visitors | Set | `visitors:2024-01-01` |
| Activity feed | List | `feed:user:456` |
| Event stream | Stream | `events:orders` |
| Counters / rate limits | String (INCR) | `ratelimit:user:123` |
| Bloom filter / HLL | HyperLogLog | `hll:pageviews` |

## Core Patterns

### Cache-Aside (Lazy Loading)

```python
import json
import redis.asyncio as redis

# Module-level pool — create once at app startup, reuse everywhere.
pool = redis.ConnectionPool.from_url(
    "redis://localhost:6379/0",
    decode_responses=True,
    max_connections=20,
)
r = redis.Redis(connection_pool=pool)

async def get_product(product_id: int) -> dict:
    cache_key = f"product:{product_id}"
    cached = await r.get(cache_key)

    if cached:
        return json.loads(cached)

    product = await db.fetchrow("SELECT * FROM products WHERE id = $1", product_id)
    await r.setex(cache_key, 3600, json.dumps(product))  # TTL: 1 hour
    return product
```

**FastAPI lifespan wiring** — close the pool cleanly on shutdown:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as redis

pool: redis.ConnectionPool | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = redis.ConnectionPool.from_url(
        "redis://localhost:6379/0",
        decode_responses=True,
        max_connections=20,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    app.state.redis = redis.Redis(connection_pool=pool)
    yield
    await pool.aclose()

app = FastAPI(lifespan=lifespan)
```

### Write-Through Cache

```python
async def update_product(product_id: int, data: dict) -> None:
    # Write to DB first
    await db.execute("UPDATE products SET ... WHERE id = $1", product_id)

    # Immediately update cache
    cache_key = f"product:{product_id}"
    await r.setex(cache_key, 3600, json.dumps(data))
```

### Cache Invalidation

```python
# Tag-based invalidation — group related keys under a set
async def cache_product(product_id: int, category_id: int, data: dict) -> None:
    key = f"product:{product_id}"
    tag = f"tag:category:{category_id}"
    async with r.pipeline(transaction=True) as pipe:
        await pipe.setex(key, 3600, json.dumps(data))
        await pipe.sadd(tag, key)
        await pipe.expire(tag, 3600)
        await pipe.execute()

async def invalidate_category(category_id: int) -> None:
    tag = f"tag:category:{category_id}"
    keys = await r.smembers(tag)
    if keys:
        await r.delete(*keys)
    await r.delete(tag)
```

### Session Storage

```python
import time
import uuid

async def create_session(user_id: int, ttl: int = 86400) -> str:
    session_id = str(uuid.uuid4())
    key = f"session:{session_id}"
    async with r.pipeline(transaction=True) as pipe:
        await pipe.hset(key, mapping={
            "user_id": user_id,
            "created_at": int(time.time()),
        })
        await pipe.expire(key, ttl)
        await pipe.execute()
    return session_id

async def get_session(session_id: str) -> dict | None:
    data = await r.hgetall(f"session:{session_id}")
    return data if data else None

async def delete_session(session_id: str) -> None:
    await r.delete(f"session:{session_id}")
```

## Rate Limiting

### Fixed Window (Simple)

```python
async def is_rate_limited(user_id: int, limit: int = 100, window: int = 60) -> bool:
    key = f"ratelimit:{user_id}:{int(time.time()) // window}"
    async with r.pipeline(transaction=True) as pipe:
        await pipe.incr(key)
        await pipe.expire(key, window)
        count, _ = await pipe.execute()
    return count > limit
```

### Sliding Window (Lua — Atomic)

```lua
-- sliding_window.lua
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)

if count < limit then
    -- Use unique member (now + sequence) to avoid collisions within the same millisecond
    local seq_key = key .. ':seq'
    local seq = redis.call('INCR', seq_key)
    redis.call('EXPIRE', seq_key, math.ceil(window / 1000))
    redis.call('ZADD', key, now, now .. '-' .. seq)
    redis.call('EXPIRE', key, math.ceil(window / 1000))
    return 1
end
return 0
```

```python
sliding_window = r.register_script(open('sliding_window.lua').read())

async def allow_request(user_id: int) -> bool:
    key = f"ratelimit:sliding:{user_id}"
    now = int(time.time() * 1000)
    result = await sliding_window(keys=[key], args=[now, 60000, 100])
    return bool(result)
```

## Distributed Locks

### Distributed Lock (Single Node — SET NX PX)

```python
import uuid

async def acquire_lock(resource: str, ttl_ms: int = 5000) -> str | None:
    lock_key = f"lock:{resource}"
    token = str(uuid.uuid4())
    acquired = await r.set(lock_key, token, px=ttl_ms, nx=True)
    return token if acquired else None

async def release_lock(resource: str, token: str) -> bool:
    release_script = """
    if redis.call('get', KEYS[1]) == ARGV[1] then
        return redis.call('del', KEYS[1])
    else
        return 0
    end
    """
    result = await r.eval(release_script, 1, f"lock:{resource}", token)
    return bool(result)

# Usage
token = await acquire_lock("order:payment:123")
if token:
    try:
        await process_payment()
    finally:
        await release_lock("order:payment:123", token)
```

> For multi-node setups use the `redlock-py` library which implements the full Redlock algorithm.

## Pub/Sub & Streams

### Pub/Sub (Fire-and-Forget)

```python
import asyncio
import redis.asyncio as redis

# Publisher
async def publish_event(channel: str, payload: dict) -> None:
    await r.publish(channel, json.dumps(payload))

# Subscriber — run as a background task (e.g., via asyncio.create_task)
async def subscribe_events(channel: str) -> None:
    async with r.pubsub() as pubsub:
        await pubsub.subscribe(channel)
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message is not None:
                await handle(json.loads(message["data"]))
```

### Redis Streams (Durable Queue)

```python
# Producer
async def emit(stream: str, event: dict) -> None:
    await r.xadd(stream, event, maxlen=10000)  # Cap stream length

# One-time consumer group setup (idempotent)
async def ensure_consumer_group(stream: str, group: str) -> None:
    try:
        await r.xgroup_create(stream, group, id="0", mkstream=True)
    except Exception:
        pass  # Group already exists

# Consumer — runs in an asyncio task or worker
async def consume(stream: str, group: str, consumer: str) -> None:
    while True:
        messages = await r.xreadgroup(
            group, consumer, {stream: ">"}, count=10, block=2000
        )
        for _, entries in (messages or []):
            for msg_id, data in entries:
                await process(data)
                await r.xack(stream, group, msg_id)
```

> Prefer **Streams** over Pub/Sub when you need delivery guarantees, consumer groups, or replay.

## Key Design

### Naming Conventions

```
# Pattern: resource:id:field
user:123:profile
order:456:status
cache:product:789

# Pattern: namespace:resource:id
myapp:session:abc123
myapp:ratelimit:user:123

# Pattern: resource:date (time-bound keys)
stats:pageviews:2024-01-01
```

### TTL Strategy

| Data Type | Suggested TTL |
|-----------|--------------|
| User session | 24h (`86400`) |
| API response cache | 5–15 min |
| Rate limit window | Match window size |
| Short-lived tokens | 5–10 min |
| Leaderboard | 1h–24h |
| Static/reference data | 1h–1 week |

Always set a TTL. Keys without TTL accumulate indefinitely and cause memory pressure.

## Connection Management

### Async Connection Pool (FastAPI / asyncio — default)

```python
import redis.asyncio as redis

pool = redis.ConnectionPool.from_url(
    "redis://localhost:6379/0",
    decode_responses=True,
    max_connections=20,
    socket_connect_timeout=2,
    socket_timeout=2,
)
r = redis.Redis(connection_pool=pool)

# Shared pool across multiple client handles (e.g., separate read/write clients)
r_read = redis.Redis(connection_pool=pool)
r_write = redis.Redis(connection_pool=pool)

# Shutdown (call from lifespan teardown)
await pool.aclose()
```

### Sync (scripts / CLI only)

For one-off scripts or management CLIs that do not run inside an asyncio event loop:

```python
import redis  # sync client — do NOT use in FastAPI request handlers

pool = redis.ConnectionPool(
    host="localhost", port=6379, db=0,
    max_connections=5, decode_responses=True,
)
r = redis.Redis(connection_pool=pool)
```

### Cluster Mode

```python
from redis.asyncio.cluster import RedisCluster

r = RedisCluster.from_url(
    "redis://redis-1:6379",
    decode_responses=True,
    skip_full_coverage_check=True,
)
```

### Sentinel (High Availability)

```python
from redis.asyncio.sentinel import Sentinel

sentinel = Sentinel(
    [("sentinel-1", 26379), ("sentinel-2", 26379)],
    socket_timeout=0.5,
)
master = sentinel.master_for("mymaster", decode_responses=True)
replica = sentinel.slave_for("mymaster", decode_responses=True)
```

## Eviction Policies

| Policy | Behavior | Best For |
|--------|----------|----------|
| `noeviction` | Error on write when full | Queues / critical data |
| `allkeys-lru` | Evict least recently used | General cache |
| `volatile-lru` | LRU only among keys with TTL | Mixed data store |
| `allkeys-lfu` | Evict least frequently used | Skewed access patterns |
| `volatile-ttl` | Evict soonest-to-expire | Prioritize long-lived data |

Set via `redis.conf`: `maxmemory-policy allkeys-lru`

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Keys with no TTL | Memory grows unbounded | Always set TTL |
| `KEYS *` in production | Blocks the server (O(N)) | Use `SCAN` cursor |
| Storing large blobs (>100KB) | Slow serialization, memory pressure | Store reference + fetch from object store |
| Single Redis for everything | No isolation between cache & queue | Use separate DBs or instances |
| Ignoring connection pool limits | Connection exhaustion under load | Size pool to workload |
| Not handling cache miss stampede | Thundering herd on cold start | Use locks or probabilistic early expiry |
| `FLUSHALL` without thought | Wipes entire instance | Scope deletes by key pattern |
| Using sync `import redis` in FastAPI handlers | Blocks the event loop | Use `redis.asyncio` everywhere in async code |

### Cache Miss Stampede Prevention

```python
import asyncio

_stampede_locks: dict[str, asyncio.Lock] = {}
_locks_mutex = asyncio.Lock()

async def get_with_lock(key: str, fetch_fn, ttl: int = 300):
    cached = await r.get(key)
    if cached:
        return json.loads(cached)

    async with _locks_mutex:
        if key not in _stampede_locks:
            _stampede_locks[key] = asyncio.Lock()
        lock = _stampede_locks[key]

    async with lock:
        cached = await r.get(key)  # Re-check after acquiring lock
        if cached:
            return json.loads(cached)
        value = await fetch_fn()
        await r.setex(key, ttl, json.dumps(value))
        return value
```

> For multi-process deployments, replace the in-process `asyncio.Lock` with `acquire_lock`/`release_lock` from the Distributed Locks section above.

## Examples

**Add caching to a FastAPI endpoint:**
Use cache-aside with `await r.setex(...)` and a 5-minute TTL. Key on the request parameters. Wire the pool via `app.state.redis` in the lifespan context (see FastAPI wiring above).

**Rate-limit an API by user:**
Use fixed-window with `async with r.pipeline(transaction=True)` for low-traffic endpoints; use sliding-window Lua for accurate per-user throttling.

**Coordinate a background job across workers:**
Use `await acquire_lock(...)` with a TTL that exceeds the expected job duration. Always release in a `finally` block.

**Fan-out notifications to multiple subscribers:**
Use Pub/Sub (`async with r.pubsub()`) for fire-and-forget. Switch to Streams if you need guaranteed delivery or replay for late consumers.

## Quick Reference

| Pattern | When to Use |
|---------|-------------|
| Cache-aside | Read-heavy, tolerate slight staleness |
| Write-through | Strong consistency required |
| Distributed lock | Prevent concurrent access to a resource |
| Sliding window rate limit | Accurate per-user throttling |
| Redis Streams | Durable event queue with consumer groups |
| Pub/Sub | Broadcast with no delivery guarantees needed |
| Sorted Set leaderboard | Ranked scoring, pagination |
| HyperLogLog | Approximate unique count at low memory |

## Related

- Skill: `postgres-patterns` — relational data patterns
- Skill: `backend-patterns` — API and service layer patterns
- Skill: `database-migrations` — schema versioning
- Skill: `django-patterns` — Django cache framework integration
- Agent: `database-reviewer` — full database review workflow
