# DevSkyy API Layer — Comprehensive Digest

Generated: 2026-05-05  
Coverage: 79 Python files across `api/`, `api/v1/`, `api/v1/analytics/`, `api/v1/portal/`, `api/v2/`, `api/graphql/`, `api/graphql/dataloaders/`, `api/graphql/resolvers/`

---

## 1. Architecture Overview

The API layer has **two distinct FastAPI entry points** mounted differently:

| Entry Point | Purpose | Location |
|---|---|---|
| `api/index.py` | Vercel serverless function | Deployed to Vercel, mounts a subset of routers |
| `main_enterprise.py` | Full enterprise app | Docker/uvicorn, mounts all routers |

**Versioning:** A `VersionMiddleware` (`api/versioning.py`) intercepts every request. Priority order: URL (`/v1/`, `/v2/`) → `X-API-Version` header → `api-version` query param. Sunset versions return HTTP 410; unsupported versions return HTTP 400. The `@versioned` decorator marks individual handlers.

**Module mount tree (abbreviated):**
```
main_enterprise.py
├── /api          ← root-level routers (gateway, graphql, webhooks, gdpr, agents, etc.)
├── /api/v1       ← 30+ v1 routers
│   ├── analytics/ (business, dashboard, alerts, alert_configs, ml_pipelines, health)
│   └── portal/   (billing, subscriptions, team, usage)
└── /api/v2       ← 5 v2 routers (assets, characters, creative, health, webhooks)
```

**GraphQL:** Strawberry schema mounted at `/graphql`. GraphiQL disabled in production via `DisableIntrospection` extension. Per-request context includes `ProductDataLoader` + correlation ID. Schema exposes `product(sku)` and `products(collection, limit, offset)` queries only; limit clamped 1–100.

---

## 2. Route Table

### Root-level `api/`

| Method | Path | Module | Auth | Notes |
|---|---|---|---|---|
| ALL | `/gateway/*` | gateway.py | None (API key on proxied service) | Longest-prefix route matching; circuit breaker; rate limiter; SSRF block |
| POST | `/webhooks/register` | webhooks.py | get_current_user | HMAC-SHA256 signing; SSRF validated at register |
| POST | `/webhooks/{id}/deliver` | webhooks.py | get_current_user | 5 retries exp backoff; 60/min per endpoint |
| ALL | `/graphql` | graphql_server.py | None (per-resolver) | Strawberry; GraphiQL disabled prod |
| POST | `/gdpr/export` | gdpr.py | get_current_user | Article 15; AES-256-GCM encrypted export |
| POST | `/gdpr/delete` | gdpr.py | get_current_user | Article 17; accepts "CONFIRM_DELETE" or sha256 code |
| GET | `/gdpr/consent` | gdpr.py | get_current_user | Article 13 |
| GET | `/gdpr/processing` | gdpr.py | get_current_user | Article 30 |
| POST | `/agents/{type}/execute` | agents.py | get_current_user | 27 agents; avatar-stylist requires confirm_fashn_cost |
| POST | `/virtual_tryon/fashn` | virtual_tryon.py | **NONE** | $0.075/image; **no auth** |
| POST | `/virtual_tryon/idm` | virtual_tryon.py | **NONE** | Free; **no auth** |
| POST | `/virtual_tryon/round_table` | virtual_tryon.py | **NONE** | **No auth** |
| ALL | `/ar_sessions/*` | ar_sessions.py | **NONE** | **No auth**; hardcoded SAMPLE_AR_PRODUCTS |
| ALL | `/3d/*` | ai_3d_endpoints.py | get_current_user | 95% fidelity threshold; in-memory JobStore |
| ALL | `/dashboard/*` | dashboard.py | get_current_user | 6 SuperAgents lazy via AgentRegistry |
| ALL | `/brand/*` | brand.py | None | Thin wrapper over orchestration.brand_context |
| ALL | `/admin/*` | admin_dashboard.py | admin role | Two in-memory stores; lazy imports |
| POST | `/sync` | sync_endpoints.py | get_current_user | Delegates to CatalogSyncEngine |
| ALL | `/tasks/*` | tasks.py | get_current_user | deque maxlen=1000; WebSocket broadcast |
| ALL | `/round_table/*` | round_table.py | get_current_user | Singleton LLMRoundTable |
| ALL | `/tools` | tools.py | get_current_user | Aggregates tools from all agents |
| ALL | `/visual/*` | visual.py | get_current_user | Real-ESRGAN or PIL Lanczos fallback |
| ALL | `/ws/{channel}` | websocket.py | **NONE** | **No auth**; 5 typed channels |
| ALL | `/elementor_3d/*` | elementor_3d.py | DEVELOPER role | list/get/delete are stub TODOs |

### `api/v1/`

| Method | Path | Module | Auth | Notes |
|---|---|---|---|---|
| POST/GET | `/v1/catalog/search` | catalog.py | None | Voyage+Pinecone semantic search |
| POST/GET | `/v1/catalog/answer` | catalog.py | **NONE** | **Unauthenticated LLM call ~$0.002/req** |
| GET | `/v1/catalog/answer/stream` | catalog.py | None | SSE streaming variant |
| GET | `/v1/catalog/cache/clear` | catalog.py | None | Admin helper; no auth check |
| POST/GET | `/v1/commerce/products/bulk` | commerce.py | get_current_user | Max 100 products; >50 → background task |
| POST | `/v1/commerce/pricing` | commerce.py | get_current_user | **Returns mock data (TODO comment)** |
| ALL | `/v1/wordpress/sync` | wordpress.py | None | No auth; creates WP posts |
| ALL | `/v1/wordpress/status` | wordpress.py | None | No auth |
| POST | `/v1/wordpress/products/sync` | wordpress_integration.py | Depends(get_settings) | HMAC-verified; ORM write on product.updated |
| POST | `/v1/wordpress/webhooks/order-*` | wordpress_integration.py | HMAC verify dep | Writes EventRecord to DB |
| GET | `/v1/wordpress/health` | wordpress_integration.py | get_settings | Tests live WooCommerce connection |
| POST | `/v1/agent/execute` | wordpress_agent.py | None | SSE streaming; WordPress Bridge Agent |
| POST | `/v1/agent/webhooks/dispatch` | wordpress_agent.py | None | Formats WC webhook as agent prompt |
| GET | `/v1/wordpress/theme/config` | wordpress_theme.py | admin role | Returns hardcoded config (v3.2.0 — incorrect, real is v1.0.0) |
| POST | `/v1/wordpress/theme/deploy` | wordpress_theme.py | admin role | **TODO stub — always returns failure** |
| POST/GET | `/v1/woocommerce/webhooks/order` | woocommerce_webhooks.py | HMAC verify dep | Thin layer over wordpress_integration |
| POST/GET | `/v1/woocommerce/webhooks/product` | woocommerce_webhooks.py | HMAC verify dep | Thin layer over wordpress_integration |
| POST | `/v1/assets` | assets.py | get_current_user | 50MB limit; AssetVersionManager |
| POST | `/v1/approval/approve` | approval.py | get_current_user | ApprovalQueueManager |
| POST/GET | `/v1/brand_assets/*` | brand_assets.py | get_current_user | Bulk up to 100; Cloudflare R2 |
| POST/GET | `/v1/ai/image-enhancement/*` | ai_image_enhancement.py | get_current_user | Blurhash is placeholder; luxury filter wired |
| POST | `/v1/elite_studio/*` | elite_studio.py | X-API-Key ("dev mode" fallback) | Redis result store; 3 queue functions |
| ALL | `/v1/hf_spaces/*` | hf_spaces.py | None | HF_USERNAME hardcoded as "damBruh"; Prometheus metrics |
| ALL | `/v1/claude_sdk/*` | claude_sdk.py | None | Lazy imports; 503 if SDK not installed |
| ALL | `/v1/training/*` | training_status.py | get_current_user | Job ID pattern `^[a-zA-Z0-9_-]{1,128}$` |
| ALL | `/v1/monitoring/*` | monitoring.py | get_current_user | Agent directory + system metrics |
| ALL | `/v1/orchestration/*` | orchestration.py | get_current_user | Pre-built enterprise workflows |
| ALL | `/v1/marketing/*` | marketing.py | get_current_user | A/B testing flag; campaigns |
| ALL | `/v1/ml/*` | ml.py | get_current_user | 5 model types; Redis-backed task store |
| ALL | `/v1/media/*` | media.py | get_current_user | text-to-3D; SSRF on URL fields |
| ALL | `/v1/social_media/*` | social_media.py | get_current_user | Delegates to SocialMediaAgent |
| ALL | `/v1/sync/*` | sync.py | **NONE** | **No auth**; Prometheus metrics |
| ALL | `/v1/descriptions/*` | descriptions.py | get_current_user | SSRF protection on image URLs |
| ALL | `/v1/competitors/*` | competitors.py | strategy/marketing roles | In-memory `_competitors` dict |
| ALL | `/v1/code/*` | code.py | get_current_user | Code scanning/fixing |
| ALL | `/v1/flags/*` | feature_flags.py | None (list), get_current_user (write) | **Double-prefix bug: `/api/v1/flags` hardcoded** |
| POST/GET | `/v1/rag/*` | rag_anything.py | get_current_user | EntitlementChecker + UsageMetering |
| ALL | `/v1/pipeline/*` | pipeline.py | get_current_user | In-memory `_jobs`/`_results`; stub responses |
| ALL | `/v1/analytics/business/*` | analytics/business.py | get_current_user | SQLAlchemy ORM; DAILY only (others unimplemented) |
| ALL | `/v1/analytics/dashboard/*` | analytics/dashboard.py | role-based | ADMIN/DEV → all 4 sections; health/ML = mock |
| ALL | `/v1/analytics/alerts/*` | analytics/alerts.py | get_current_user | Raw `text()` SQL; MockConfig in loop |
| ALL | `/v1/analytics/alert_configs/*` | analytics/alert_configs.py | get_current_user | CRUD; threshold/anomaly/rate conditions |
| ALL | `/v1/analytics/ml_pipelines/*` | analytics/ml_pipelines.py | get_current_user | Tripo, Replicate, HF, Gemini, OpenAI |
| GET | `/v1/analytics/health/*` | analytics/health.py | get_current_user | Prometheus: active_sessions, cache_hit_rate |
| ALL | `/v1/billing/*` | portal/billing.py | get_current_user | Stripe portal session + invoice list |
| ALL | `/v1/subscriptions/*` | portal/subscriptions.py | get_current_user | 3 tiers: starter/pro/enterprise; Stripe |
| ALL | `/v1/team/*` | portal/team.py | get_current_user | In-memory `_team_store`; owner protect |
| ALL | `/v1/usage/*` | portal/usage.py | get_current_user | UsageMetering Redis; 6-month history |

### `api/v2/`

| Method | Path | Module | Auth | Notes |
|---|---|---|---|---|
| GET/DELETE | `/v2/assets` | assets.py | X-API-Key | Redis-backed; merges v1 legacy result keys |
| POST/GET/PATCH | `/v2/characters` | characters.py | X-API-Key | CharacterCreationAgent; 30-day Redis TTL |
| GET | `/v2/characters/rosie` | characters.py | X-API-Key | Canonical mascot; Redis-cached |
| POST/GET/DELETE | `/v2/creative/operations` | creative.py | X-API-Key | 14 intents; async (enqueue) or sync mode; sorted-set index |
| GET | `/v2/health` | health.py | None | Redis + graph import check; load balancer safe |
| GET | `/v2/usage` | health.py | X-API-Key | Aggregates v2 ops + v1 legacy results |
| POST/GET/DELETE | `/v2/webhooks` | webhooks.py | X-API-Key | Full CRUD; auto-generated secrets; test-fire endpoint |

### `api/graphql/`

| Type | Name | Notes |
|---|---|---|
| Query | `product(sku: String!)` | DataLoader batch; 300s cache |
| Query | `products(collection, limit, offset)` | limit clamped 1–100 |
| DataLoader | `ProductDataLoader` | `SELECT … WHERE sku IN (…)`; max_batch=100; cache=True |
| Type | `ProductType` | `from_db()` static method; maps DB model → GQL |

---

## 3. Authentication & Authorization

### Mechanisms in use

| Mechanism | Pattern | Used in |
|---|---|---|
| JWT Bearer | `Depends(get_current_user)` → `TokenPayload` | ~70% of endpoints |
| RBAC | `RoleChecker([UserRole.ADMIN, …])` | admin_dashboard, elementor_3d, analytics/dashboard, wordpress/theme |
| X-API-Key header | `_check_api_key` dependency (env `API_KEY`) | all v2 endpoints; elite_studio v1 |
| HMAC webhook sig | `Depends(verify_webhook)` | wordpress_integration, woocommerce_webhooks |
| `@requires_api_key` | Custom decorator in ai_enhancement | ai_image_enhancement.py |

### Auth gaps (unauthenticated endpoints that should not be)

1. `POST /virtual_tryon/fashn` — costs $0.075/image, no auth
2. `POST /virtual_tryon/idm` and `/round_table` — no auth
3. All `/ar_sessions/*` — session data + WebSocket, no auth
4. All `/ws/{channel}` WebSocket endpoints — no auth
5. `GET|POST /v1/catalog/answer` — invokes Claude, no auth (~$0.002/req)
6. `GET /v1/catalog/cache/clear` — admin action, no auth
7. `POST /v1/wordpress/sync` and `/status` (wordpress.py) — production write, no auth
8. `POST /v1/agent/execute` (wordpress_agent.py) — SSE agent execution, no auth
9. `POST /v1/agent/webhooks/dispatch` — agent invocation, no auth
10. All `/v1/sync/*` endpoints — pipeline orchestration, no auth
11. All `/v1/hf_spaces/*` — Prometheus data exposure, no auth
12. All `/v1/claude_sdk/*` — Claude SDK invocations, no auth

---

## 4. Request/Response Models

All endpoint schemas use Pydantic v2. Key conventions:
- `BaseModel` for both request and response types
- `Field(...)` with descriptions on all fields
- Validators use `@field_validator` with `@classmethod` (Pydantic v2)
- `StrEnum` used for typed path/query parameters (e.g., `JobStatus`, `Provider`, `QualityTier`)
- Response models declared on router decorators (`response_model=...`)
- Background task pattern: endpoint returns queued `{id, status: "queued"}` immediately; `BackgroundTasks` does real work

### Notable model patterns

- `BulkProductRequest`: max 100 products, `action` in {create, update, delete}
- `CreateOperationRequest` (v2): `intent` validated against `CreativeIntent` enum; `priority` 1–10; `async_mode` flag
- `SubscribeRequest` / `UpgradeRequest`: validated `tier` in {starter, pro, enterprise} / {free, starter, pro, enterprise}
- `FidelityBreakdown`: geometry/materials/colors/proportions float scores (pipeline.py)
- `InviteRequest` / `RoleUpdateRequest`: role validated against `_ASSIGNABLE_ROLES` = {admin, member, viewer}; owner role protected

---

## 5. Middleware & Cross-Cutting Concerns

### `VersionMiddleware` (`api/versioning.py`)
Intercepts all requests pre-routing. Version resolution priority: URL path > `X-API-Version` header > `api-version` query param. Unsupported versions → HTTP 400. Sunset versions → HTTP 410 with `Sunset` response header. Applies `@versioned` decorator to individual handlers for fine-grained control.

### Gateway (`api/gateway.py`)
- **Longest-prefix route matching**: registered backends keyed by path prefix
- **CircuitBreaker per backend**: CLOSED → OPEN (after N failures) → HALF_OPEN (probe after timeout). Protects downstream from cascade
- **RateLimiter**: token bucket, `OrderedDict` LRU eviction at 100k client cap
- **SSRF protection** (`SSRFProtection` class): blocks 169.254.x.x, 100.64.x.x (link-local, CGNAT), `file://`, `gopher://` schemes

### WebSocket multi-channel (`api/websocket.py`, `api/websocket_integration.py`)
Five typed channels: `agents`, `round_table`, `tasks`, `3d_pipeline`, `metrics`. Static `WebSocketIntegration` class; `start_metrics_broadcaster()` emits Prometheus placeholder metrics (TODO: wire real counters). `wrap_agent_execution` decorator broadcasts agent lifecycle events.

### GDPR middleware path
GDPR-relevant endpoints additionally pull from `security_ops_agent`. Article 17 delete endpoint accepts either `sha256(user_id + date)` code OR the string literal `"CONFIRM_DELETE"` / `"CONFIRM_DELETE_GDPR_REQUEST"` — a hardcoded backdoor bypass.

---

## 6. External Integrations

| Integration | Where | Pattern |
|---|---|---|
| **Stripe** | portal/billing.py, portal/subscriptions.py | `StripeClient` singleton; portal sessions + invoices |
| **Pinecone** (serverless, us-west-2) | catalog.py | Voyage `voyage-3-large` embeddings → semantic search |
| **Cloudflare R2** | brand_assets.py | `R2Client` / `R2Config` |
| **FASHN API** | virtual_tryon.py, agents.py | $0.075/image; `confirm_fashn_cost=True` guard in agents.py but NOT in virtual_tryon.py |
| **HuggingFace Spaces** | hf_spaces.py | `HF_USERNAME = "damBruh"` hardcoded |
| **Redis** | catalog.py (AnswerCache/LRU), elite_studio.py, v2/*, portal/* | Multi-role: job store, result store, webhook registry, metering, queue |
| **WordPress/WooCommerce REST** | wordpress_integration.py, wordpress.py | `create_wordpress_client()`; HMAC signature verification |
| **Replicate, FAL, Stability, Together, Runway** | ai_image_enhancement.py | Keys from env; passed to `LuxuryImageEnhancer` |
| **3D providers** | three_d.py, pipeline.py | TRELLIS, Tripo, Hunyuan3D, TripoSR, InstantMesh, LGM, SHAP-E, POINT-E, ROUND_TABLE |
| **Elite Studio** | elite_studio.py, v2/creative.py | Redis queue `queue:elite_studio_produce`; result key `elite_studio:result:{id}` |
| **CharacterCreationAgent** | v2/characters.py | `create_sheet()` / `create_skyyrose_rosie()` |
| **Prometheus** | hf_spaces.py, training_status.py, sync.py, analytics/health.py | Custom `devskyy_registry`; Counters, Gauges, Histograms |
| **RAGAnything** | rag_anything.py | `EntitlementChecker` + `UsageMetering`; billing intents "rag-query"/"rag-ingest" |
| **WordPress Bridge Agent** | wordpress_agent.py | SSE streaming via `run_agent()`; `WordPressBridgeAgent` |

---

## 7. Security Findings

### Critical (production risk)

| ID | Finding | File | Impact |
|---|---|---|---|
| SEC-01 | **GDPR delete backdoor** | gdpr.py | Accepts hardcoded strings `"CONFIRM_DELETE"` / `"CONFIRM_DELETE_GDPR_REQUEST"` — any authenticated user can trigger deletion without cryptographic verification |
| SEC-02 | **Virtual try-on no auth** | virtual_tryon.py | FASHN costs $0.075/image; endpoints are unauthenticated — unlimited financial exposure |
| SEC-03 | **Catalog answer unauthenticated LLM** | catalog.py | `POST /v1/catalog/answer` invokes Claude (~$0.002/req) with no auth. File docstring explicitly flags this but it remains unaddressed |
| SEC-04 | **AR sessions no auth** | ar_sessions.py | WebSocket + session state; no authentication on any endpoint |
| SEC-05 | **WebSocket no auth** | websocket.py | 5 broadcast channels expose real-time pipeline data |
| SEC-06 | **Sync endpoints no auth** | sync.py | Can trigger full catalog sync pipeline; no auth |
| SEC-07 | **WordPress sync no auth** | wordpress.py | Production WP write; no auth |

### High

| ID | Finding | File | Impact |
|---|---|---|---|
| SEC-08 | **HF_USERNAME hardcoded** | hf_spaces.py | `HF_USERNAME = "damBruh"` in source; should be env var |
| SEC-09 | **X-API-Key dev-mode fallback** | elite_studio.py, v2/*.py | If `API_KEY` env var not set, all requests pass auth silently |
| SEC-10 | **feature_flags double-prefix** | feature_flags.py | Router prefix hardcodes `/api/v1/flags` — when mounted under the v1 prefix, resolves to `/api/v1/api/v1/flags` (or the hardcoded path shadows the mount point, either way is a bug) |
| SEC-11 | **subscription cancel stub** | portal/subscriptions.py | `DELETE /subscriptions/current` logs intent but never calls Stripe — subscriptions are not actually cancelled |
| SEC-12 | **Team admin bypass in stub** | portal/team.py | `_require_admin()` allows all operations if no store entry exists; in stub mode any user can manage team |

### Medium

| ID | Finding | File | Impact |
|---|---|---|---|
| SEC-13 | **Pricing returns mock data** | commerce.py | Dynamic pricing endpoint returns hardcoded mock; any caller receives fake data |
| SEC-14 | **elementor_3d stubs return 404/empty** | elementor_3d.py | list/get/delete never implemented; silent data loss |
| SEC-15 | **Blurhash is placeholder** | ai_image_enhancement.py | Returns hardcoded string; real blurhash library not called |
| SEC-16 | **pipeline.py generate returns hardcoded URLs** | pipeline.py | `storage.example.com` URLs in production responses |
| SEC-17 | **WordPress theme version wrong** | wordpress_theme.py | Config returns `version: "3.2.0"`; actual is `1.0.0` |

---

## 8. Data Flow Patterns

### Background task pattern (used by: ai_3d_endpoints.py, commerce.py, ml.py, sync.py)
```
POST /endpoint → validate → create in-memory job {id, status: "queued"} → 
BackgroundTasks.add_task(worker_fn) → return job immediately →
[background] worker_fn runs, updates job dict, broadcasts via WebSocket
```

### Round Table pattern (3 levels)
1. **LLM Round Table** (`round_table.py`): routes queries to multiple LLM providers; dedupes results by ID; singleton
2. **3D Round Table** (`three_d.py`): runs multiple 3D providers in parallel; scores by fidelity; picks best
3. **Virtual Try-On Round Table** (`virtual_tryon.py`): FASHN + IDM-VTON in parallel; consensus selection

### v2 Creative pipeline
```
POST /v2/creative/operations (async_mode=True) →
  enqueue_creative_async() → zadd to "queue:elite_studio_produce" priority queue →
  OperationResponse {status: "queued"} returned →
[consumer] processes from queue → writes to "elite_studio:result:{id}" + 
  "elite_studio:v2:operation:{id}" → fires webhook if registered
GET /v2/creative/operations/{id} → reads from v2 key, falls back to v1 legacy key
```

### Webhook delivery (two systems)
1. **`api/webhooks.py`**: Platform-level webhook registry (HMAC-SHA256, 5 retries exp backoff, SSRF-validated endpoints, 60/min per target)
2. **`api/v1/elite_studio_webhooks.py`**: Elite Studio-specific fire-and-forget delivery (httpx async, no retry, `X-SkyyRose-Signature` header, 20 event types). v2/webhooks.py wraps this with full CRUD + test-fire endpoint

### Dual-store reads (v2 backward compat pattern)
v2/assets.py and v2/creative.py both merge native v2 Redis keys with legacy v1 result keys to maintain backward compatibility after the v2 migration.

---

## 9. Known Gaps & TODOs

| Area | Gap | File |
|---|---|---|
| Analytics timeseries | Only DAILY granularity implemented; WEEKLY/MONTHLY/HOURLY return unimplemented paths | analytics/business.py |
| Analytics funnel | Views and add_to_cart use mock multipliers, not real data | analytics/business.py |
| Analytics health/ML | Health and ML dashboard sections return simulated/mock data | analytics/dashboard.py |
| Alerts SQL | Uses raw `text()` SQL while business.py uses ORM — inconsistency; `MockConfig` defined inside a loop | analytics/alerts.py |
| Pricing optimization | `POST /v1/commerce/pricing` returns mock data with TODO comment | commerce.py |
| Elementor 3D | `GET`, `DELETE` endpoints return empty list / 404 (never implemented) | elementor_3d.py |
| WordPress theme deploy | Always returns `{"success": false}` — not implemented | wordpress_theme.py |
| Pipeline fidelity | `/v1/pipeline/fidelity/{id}` has TODO comment; returns hardcoded 98.5 | pipeline.py |
| Pipeline generate | Returns `storage.example.com` URLs — placeholder URLs in production code | pipeline.py |
| Blurhash | Returns hardcoded hash string, not real computation | ai_image_enhancement.py |
| Task cost estimate | Uses `duration_ms / 1000 * 0.001` as placeholder cost formula | tasks.py |
| WebSocket metrics | `start_metrics_broadcaster()` emits placeholder metrics; TODO to wire Prometheus | websocket_integration.py |
| Subscription cancel | DELETE /subscriptions/current never calls Stripe | portal/subscriptions.py |
| Team admin check | `_require_admin()` always allows in stub mode when no store entry | portal/team.py |
| Billing customer resolution | `_resolve_customer_id()` reads from `request.state` — no DB lookup implemented | portal/billing.py |
| In-memory stores needing DB | `_jobs/_results` (pipeline), `_team_store` (team), `_competitors` (competitors), `_competitor_assets` (competitors), AdminAssetStore, AdminDataStore, ARSessionStore | multiple |

---

## 10. In-Memory Store Inventory

All the following are **process-scoped, non-persistent, and lost on restart**. Each should be migrated to Redis or PostgreSQL before production hardening.

| Store | Type | Location | Capacity |
|---|---|---|---|
| `_jobs` | `dict[str, dict]` | pipeline.py | Unbounded |
| `_results` | `dict[str, dict]` | pipeline.py | Unbounded |
| `_competitors` | `dict` | competitors.py | Unbounded |
| `_competitor_assets` | `dict` | competitors.py | Unbounded |
| `_team_store` | `dict[str, list[dict]]` | portal/team.py | Unbounded |
| `AdminAssetStore` | Instance + dict | admin_dashboard.py | Unbounded |
| `AdminDataStore` | Instance + dict | admin_dashboard.py | Unbounded |
| `ARSessionStore` | Instance | ar_sessions.py | Unbounded |
| `TaskStore` (tasks.py) | `asyncio.Lock` + `deque` | tasks.py | maxlen=1000 |
| `_jobs` (ai_3d) | `dict` | ai_3d_endpoints.py | Unbounded |
| `JobStore` (visual) | Instance | visual.py | Unbounded |
| `SyncJobStore` | Instance | sync_endpoints.py | Unbounded |
| `LLMRoundTable` singleton | Module-level | round_table.py | Unbounded result set |
| `AnswerCache` | `OrderedDict` LRU | catalog.py | TTL-based eviction |
| `DashboardCache` | L1 dict + L2 Redis | analytics/dashboard.py | Configurable TTL |

---

## Appendix: Auth Pattern Legend

- **get_current_user**: JWT Bearer → `TokenPayload` (user sub, roles, exp) via `security/jwt_oauth2_auth.py`
- **RoleChecker([roles])**: FastAPI Depends that checks `TokenPayload.roles` against required set; raises HTTP 403
- **X-API-Key**: Header comparison against `os.getenv("API_KEY")`; if env var unset, all pass ("dev mode" — a production footgun)
- **HMAC verify_webhook**: HMAC-SHA256 of raw request body against `WC_WEBHOOK_SECRET`; timing-safe `hmac.compare_digest`
- **get_settings dependency**: Raises HTTP 503 if `WORDPRESS_SITE_URL` not configured; used as implicit gate for WP endpoints
