# core/caching/ — Multi-Tier Cache

**L1 (in-process TTLCache) → L2 (Redis) → none.** L3 (CDN) reserved for future static-asset use.

## Public Surface (`core/caching/__init__.py`)

- `MultiTierCache` — class, instantiate per use-case or via global `get_cache()`
- `cached(ttl, key_prefix)` — async decorator, each decorated fn gets its own isolated `MultiTierCache(l1_max_size=500)`

## Behavior (`multi_tier_cache.py`)

| Method | Behavior |
|--------|----------|
| `get(key)` | L1 lookup → on miss, L2 lookup → **promote L2 hit to L1** → return / None |
| `set(key, value, ttl=300)` | Write L1 sync + L2 async (does not block caller) |
| `invalidate(key)` | Remove from L1 + L2 |
| `invalidate_pattern("product:*")` | L1 prefix-match + Redis `SCAN` with `MATCH` |
| `get_stats()` | hit/miss counters per tier, L1 size, hit-rate % |

## Hard Rules

- **Redis is optional** — `_ensure_redis()` fails open (`logger.debug`, returns `False`). L1 always works
- TTLs in seconds. Default 300s (5 min). Use shorter (30-60s) for hot-path data, longer (1h+) for static
- Cache key: namespaced strings (`"product:br-001"`, `"user:42:profile"`). No raw IDs
- **`@cached` collisions:** key derived from `func.__name__ + sha256(args+kwargs)[:32]` — 128-bit hash, negligible birthday risk
- Redis URL: `REDIS_URL` env var, default `redis://localhost:6379/0`
- Async-only — every method is `async`. No sync wrappers

## Consumers

- `api/graphql/resolvers/*` — `@cached(ttl=300)` on read resolvers
- `services/*` — long-lived `MultiTierCache` instances for ML model warmup
- `agents/*` — short-TTL caching of expensive LLM responses

## Legacy Cache (do not extend)

- `core/redis_cache.py` is the pre-multi-tier LLM response cache. New code uses `core.caching` instead


