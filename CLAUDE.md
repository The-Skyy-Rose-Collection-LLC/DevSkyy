# DevSkyy — Claude Config

> Enterprise AI | SkyyRose Luxury Fashion | 54 Agents | **Self-Correcting System**

---

## Protocol (Do This Every Time)

1. **Context7** → `resolve-library-id` → `query-docs` (BEFORE library code)
2. **Serena** → Codebase navigation and symbol lookup
3. **Navigate** → Read first, understand, NO code until clear
4. **Implement** → `Edit` tool (targeted) | `Write` (new only)
5. **Test** → `pytest -v` (MANDATORY after EVERY file touch)
6. **Format** → `isort . && ruff check --fix && black .`
7. **Learn** → After any correction, update this CLAUDE.md ⭐

---

## Verification Commands (Run After Changes)

```bash
# Python
pytest -v && mypy . --ignore-missing-imports && ruff check

# JavaScript
npm test && npm run type-check && npm run lint

# WordPress
wp theme list && curl -I https://skyyrose.co | grep -i content-security-policy

# Full System
pytest -v && npm test && curl http://localhost:8000/health
```

---

## Learnings (Updated Weekly When Claude Makes Mistakes) ⭐

### WordPress

- ❌ **Mistake**: Using `/wp-json/` for WordPress.com API
  - ✅ **Correct**: Use `index.php?rest_route=` instead (WordPress.com requirement)

- ❌ **Mistake**: Assuming page purpose from name
  - ✅ **Correct**: ALWAYS read `wordpress-theme/skyyrose-flagship/PAGES-DOCUMENTATION.md` first

- ❌ **Mistake**: Thinking immersive pages = product catalog
  - ✅ **Correct**: Immersive = 3D storytelling (NOT shopping), Catalog = product grids (FOR shopping)

- ❌ **Mistake**: Editing WordPress files without Serena
  - ✅ **Correct**: Use Serena MCP tools for all WordPress file operations

- ❌ **Mistake**: Referencing skyyrose-2025 theme
  - ✅ **Correct**: Only `skyyrose-flagship` exists (production theme)

### Testing

- ❌ **Mistake**: Skipping tests "just this once"
  - ✅ **Correct**: `pytest -v` after EVERY file touch, no exceptions

- ❌ **Mistake**: Coverage <80%
  - ✅ **Correct**: 90%+ coverage required (use `pytest --cov`)

- ❌ **Mistake**: Writing implementation before tests
  - ✅ **Correct**: TDD workflow: RED (write failing test) → GREEN (minimal impl) → IMPROVE (refactor)

### Security

- ❌ **Mistake**: Passing `str(exc)` to gRPC `context.set_details()` or HTTP error responses
  - ✅ **Correct**: Always return generic messages to clients (`"Internal server error"`). Log detailed exceptions server-side only. SQLAlchemy errors expose connection strings and schema names.

- ❌ **Mistake**: Allowing arbitrary backend URLs in API gateway `register_route()`
  - ✅ **Correct**: Validate backend URLs against an allowlist of internal service hostnames/schemes. Block `169.254.x.x` (cloud metadata), `file://`, `gopher://`. Normalize paths with `posixpath.normpath()` to prevent `/../` traversal.

- ❌ **Mistake**: Using unbounded `dict` or `set` for per-client tracking (rate limiters, dedup windows, analytics)
  - ✅ **Correct**: Always cap in-memory tracking with LRU eviction (`OrderedDict.popitem(last=False)`) or `max_size` guards. An attacker sending unique keys can exhaust memory in minutes.

- ❌ **Mistake**: Using `set.pop()` for bounded dedup windows (non-deterministic eviction)
  - ✅ **Correct**: Use `OrderedDict` with `popitem(last=False)` for FIFO eviction — ensures the oldest event IDs are evicted first, preventing recent-ID replay attacks.

- ❌ **Mistake**: Using `load_from_dict(**settings)` without whitelisting keys from external config
  - ✅ **Correct**: Whitelist allowed keys before unpacking: `filtered = {k: v for k, v in settings.items() if k in _ALLOWED_KEYS}`. Unknown keys from files/APIs could inject unexpected constructor arguments.

### Architecture

- ❌ **Mistake**: Circular dependencies (api imports core, core imports api)
  - ✅ **Correct**: One-way flow only: `core → adk → security → agents → api`

- ❌ **Mistake**: Using `base_legacy.py` or `operations_legacy.py`
  - ✅ **Correct**: Use `adk/base_super_agent.py` (17 techniques, ADK-based)

- ❌ **Mistake**: Importing from outer layers into inner layers
  - ✅ **Correct**: Inner layers (core, adk) have ZERO dependencies on outer layers

- ❌ **Mistake**: Placing DataLoaders in `core/dataloaders/` (violates zero-dep rule)
  - ✅ **Correct**: DataLoaders go in `api/graphql/dataloaders/` — they import `aiodataloader` + `database.db`, neither is stdlib/pydantic

- ❌ **Mistake**: Using `strawberry.argument(default=...)` to set GraphQL argument defaults
  - ✅ **Correct**: Use Python default values directly: `limit: int = 20`. `strawberry.argument()` only accepts `description`, `name`, `deprecation_reason`

- ❌ **Mistake**: Using `GraphQLTestClient` from `strawberry.test`
  - ✅ **Correct**: Use `schema.execute(query, context_value={...})` directly for unit testing GraphQL resolvers

### GraphQL / DataLoader

- **Schema:** `api/graphql/schema.py` — Strawberry schema with `Query.product(sku)` + `Query.products(collection, limit, offset)`
- **Types:** `api/graphql/types.py` — `ProductType` with `from_db()` factory (handles `images_json` deserialization)
- **DataLoader:** `api/graphql/dataloaders/product_loader.py` — batches SKU lookups, request-scoped cache
- **Router:** `api/graphql_server.py` — mounts at `/graphql`, injects `ProductDataLoader` per request in context
- **Resolver:** `api/graphql/resolvers/product_resolver.py` — `get_products_from_db()` decorated with `@cached(ttl=300)`

### Multi-Tier Cache

- **Location:** `core/caching/multi_tier_cache.py` — `MultiTierCache` + `@cached` decorator
- **L1:** `cachetools.TTLCache` (in-memory, per-process, microseconds)
- **L2:** Redis async client (shared across processes, milliseconds)
- **Promotion:** L2 hit → automatically written back to L1
- **Decorator:** `@cached(ttl=300, key_prefix="...")` — hashes args for cache key, per-function isolated cache instance

### Mocking Pattern (Critical)

- ❌ **Mistake**: Patching `module.ClassName` when `ClassName` is imported inside a function body
  - ✅ **Correct**: Always import dependencies at **module level** so `patch("module.ClassName")` works. Local imports (`from x import Y` inside a function) bypass the patch and re-import the real class.
  - **Files where this was fixed**: `core/cqrs/command_bus.py` (EventStore), `grpc_server/product_service.py` (DatabaseManager)

### Event Sourcing / CQRS

- **Event Store:** `core/events/event_store.py` — `Event` (immutable, deep-copy data), `EventStore.append()`, `EventStore.replay()`
- **Event Bus:** `core/events/event_bus.py` — singleton `event_bus`, handler errors logged/swallowed
- **Event Handlers:** `core/events/event_handlers.py` — `ProductEventHandler` with idempotent upsert pattern
- **Command Bus:** `core/cqrs/command_bus.py` — `Command` dataclass + `CommandBus.execute()` routes to handlers
- **Query Bus:** `core/cqrs/query_bus.py` — `Query` dataclass + `QueryBus.execute()` for read side
- **EventRecord DB model:** `database/db.py` — `event_store` table with composite index on `(aggregate_id, timestamp)`

### gRPC

- **Proto:** `grpc_server/proto/product.proto` — `ProductService` with GetProduct, ListProducts, CreateProduct, UpdateProductPrice
- **Servicer:** `grpc_server/product_service.py` — `ProductServicer` (grpcio optional, degrades gracefully)
- **Testing:** Call servicer methods directly with mock request/context objects — no real gRPC server needed

### API Gateway

- **Location:** `gateway/api_gateway.py` — `CircuitBreaker`, `RateLimiter` (token bucket), `APIGateway`
- **Circuit states:** CLOSED → OPEN (at failure_threshold) → HALF_OPEN (after recovery_timeout) → CLOSED
- **Routing:** longest-prefix matching; each route has its own independent circuit breaker

### Analytics

- **Location:** `analytics/stream_processor.py` — `StreamProcessor`, `AnalyticsState`
- **Kafka optional:** confluent_kafka import fails gracefully with warning
- **Idempotency:** event_id dedup window (10k events) prevents double-counting at-least-once Kafka delivery

### Feature Flags

- **Location:** `core/feature_flags/flag_manager.py` — `FeatureFlag`, `FlagManager`, singleton `flag_manager`
- **Evaluation order:** not-found→False, kill-switch→False, disabled_for_users→False, enabled_for_users→True, 100%→True, 0%→False, hash-bucket
- **Consistent hashing:** `SHA256(flag_name:user_id)[:8] % 100` — same user always in same bucket (sticky A/B)

### GraphQL + Cache Integration Tests

- **Location:** `tests/integration/test_graphql_cache.py` — 10 integration tests across two classes
- **TestGraphQLCacheIntegration:** Mocks only `DatabaseManager`; lets `@cached` + `MultiTierCache` run fully — catches bugs invisible to unit tests
- **TestDataLoaderBatching:** Replaces `loader.batch_load_fn` (not `loader._batch_load_fn` — that bypasses aiodataloader's internal ref) to verify batching
- ❌ **Mistake**: `cache_invalidate` lambda in `@cached` used `hexdigest()[:16]` while the main key used `[:32]` — invalidations silently no-op'd
  - ✅ **Correct**: Both must use the same hash length; fixed in `multi_tier_cache.py:295`
- ❌ **Mistake**: Integration tests placed in `tests/api/` which has encryption-key import errors at collection time
  - ✅ **Correct**: Place in `tests/integration/` to isolate from encryption module issues

### 3D Development

- ❌ **Mistake**: Using CDN URLs without verification
  - ✅ **Correct**: VERIFY URLs exist first (`curl -I <url>`)

- ❌ **Mistake**: Forgetting to propagate correlation_id
  - ✅ **Correct**: ALWAYS accept `correlation_id` as keyword-only arg and propagate

- ❌ **Mistake**: Hardcoding 3D library versions
  - ✅ **Correct**: Three.js v0.160.0, Babylon.js latest (via CDN)

### Google ADK

- ❌ **Mistake**: Using hyphens in `LlmAgent(name=...)`
  - ✅ **Correct**: Agent names must be valid Python identifiers — use underscores: `skyyrose_content_director`

- ❌ **Mistake**: Asking agent to process a whole collection in one turn
  - ✅ **Correct**: Loop product-by-product with `time.sleep(8)` between calls to avoid 429 rate limits

- ❌ **Mistake**: Writing audit prompts without read-only guard
  - ✅ **Correct**: Prepend `"READ-ONLY AUDIT — do NOT call update_product_field()."` to any audit prompt

- ❌ **Mistake**: Loading multiple `.env` files with `override=False` when one has a placeholder key
  - ✅ **Correct**: Load the authoritative keys file LAST with `override=True` so real keys win

- ❌ **Mistake**: Calling `runner.run()` without pre-creating session
  - ✅ **Correct**: Always call `session_svc.create_session_sync()` before `runner.run()`

- ❌ **Mistake**: Installing ADK deps into the image pipeline venv
  - ✅ **Correct**: Use isolated `.venv-agents/` — ADK drags cloud deps that conflict with `numpy==2.3.5`

### Context7

- ❌ **Mistake**: Writing library code before checking docs
  - ✅ **Correct**: ALWAYS `resolve-library-id` → `query-docs` first

- ❌ **Mistake**: Assuming WordPress/Elementor/WooCommerce APIs haven't changed
  - ✅ **Correct**: Query Context7 for up-to-date docs every time

### Code Quality

- ❌ **Mistake**: Mutating objects directly
  - ✅ **Correct**: Immutability always (use spread: `{...obj, newKey}` not `obj.key = val`)

- ❌ **Mistake**: Using `console.log` or debug statements
  - ✅ **Correct**: Remove all debug output before committing

- ❌ **Mistake**: Hardcoding values (API keys, URLs)
  - ✅ **Correct**: Use environment variables (see `docs/ENV_VARS_REFERENCE.md`)

---

## Critical Rules (Never Break These)

- **NO deletions**, refactor only (preserve git history)
- **Context7 BEFORE any library code** (WordPress, Elementor, WooCommerce, Three.js)
- **Serena for WordPress** file operations (NOT direct file access)
- **pytest AFTER EVERY CHANGE** (no exceptions)
- **90%+ coverage** required (use `pytest --cov`)
- **Update CLAUDE.md** after every correction (self-correcting system)

---

## Quick Reference

### Brand & Health
- **Brand**: `#B76E79` (rose gold) | "Where Love Meets Luxury" | `BrandKit.from_config()`
- **Health**: `/health` `/health/ready` `/health/live` `/metrics`

### Collections & Docs
- **Immersive** (3D): Black Rose (cathedral), Love Hurts (castle), Signature (city tour)
- **Catalog** (shopping): `page-collection-{black-rose,love-hurts,signature}.php`
- **Docs**: `docs/` → CONTRIB, RUNBOOK, ENV_VARS_REFERENCE, MCP_TOOLS, DEPENDENCIES, ARCHITECTURE

---

## When Claude Does Something Wrong

**Self-Correcting Protocol** (Boris Cherny's approach):

1. **Fix the issue** (correct the code, tests, docs)
2. **Add to Learnings** (update this file with ❌ Mistake → ✅ Correct)
3. **Commit both** (code fix + CLAUDE.md update together)
4. **Update multiple times weekly** (living document, not static)

This transforms our codebase into a **self-correcting organism** where mistakes become rules.

---

**v3.1.0** | SkyyRose LLC | Self-Correcting AI System
