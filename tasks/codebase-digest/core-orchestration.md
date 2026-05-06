# DevSkyy — Core / Database / Security / Orchestration Digest

Generated: 2026-05-05
Scope: 51 core/ + 8 database/ + 32 security/ + 32 orchestration/ source files (123 total)

---

## 1. Core Foundation (`core/`)

### Architecture Pattern
Hexagonal (Ports & Adapters). `core/` is the innermost ring — zero external dependencies by rule. Outer layers import from `core/`; `core/` imports nothing from `security/`, `database/`, `orchestration/`, or `agents/`. This boundary is enforced by convention and partially by `mypy.ini` (`namespace_packages = False`).

**Known violation:** `core/runtime/input_validator.py` imports `SecurityValidator` from `security.input_validation`. This is an inward dependency from core into security — a documented architectural leak, not an oversight.

### Key Modules

| Module | Exports | Role |
|--------|---------|------|
| `core/auth/types.py` | `UserRole`, `ROLE_HIERARCHY` | 6 roles mapped to ints (SUPER_ADMIN=100 → GUEST=0) |
| `core/auth/role_hierarchy.py` | `has_permission()`, `can_assign_role()` | Numeric comparison for RBAC |
| `core/caching/multi_tier_cache.py` | `MultiTierCache` | L1 TTLCache (in-process) + L2 Redis |
| `core/redis_cache.py` | `RedisLLMCache` | LLM-specific cache with Prometheus metrics |
| `core/performance.py` | `HierarchicalCache` | Third cache using `diskcache` for L3 |
| `core/events.py` | `EventBus`, `EventRecord`, `EventStore` | Pub/sub bus + append-only SQLite event store |
| `core/bus/command_bus.py` | `CommandBus` | Write path: validate → execute → emit event |
| `core/bus/query_bus.py` | `QueryBus` | Read path: dispatch to registered handlers |
| `core/llm/ports.py` | `ILLMProvider`, `ILLMRouter`, `IProviderFactory` | Protocol/ABC interfaces for LLM layer |
| `core/registry/tool_registry.py` | `ToolRegistry` (singleton, 2159L) | 37 built-in tools; exports to OpenAI/Anthropic/MCP formats |
| `core/runtime/input_validator.py` | `InputValidator` | Pydantic + `SecurityValidator` (architectural leak) |
| `core/container.py` | `DependencyContainer` | Service locator / DI container |

### Three-Cache Redundancy (Gotcha)
Three independent caching implementations exist in `core/` alone:
1. `multi_tier_cache.py` — general-purpose L1 TTLCache + L2 Redis
2. `redis_cache.py` — LLM-specific with Prometheus hit/miss counters
3. `performance.py` — `HierarchicalCache` adds disk (diskcache) as L3

All three are active. No consolidation plan is documented. New code landing in `core/` that needs caching should read all three to pick the appropriate one rather than creating a fourth.

### CQRS + Event Sourcing
- `CommandBus`: validates command schema (Pydantic), calls handler, emits domain event
- `QueryBus`: dispatches to projection handlers only (read-side)
- `EventStore._persist()`: write-only; `EventRecord` rows are never updated or deleted; state rebuilt by replaying by `aggregate_id + timestamp`

### Tool Registry
`core/registry/tool_registry.py` (2159 lines) is a singleton. 37 built-in tools registered at import time. Supports Anthropic Advanced Tool Use fields: `defer_loading`, `allowed_callers`, `input_examples`. Multi-format export for OpenAI function calling, Anthropic tool use, and MCP. Any new MCP tool must register here.

---

## 2. Database Layer (`database/`)

No Alembic migrations directory exists. Schema management is done via `Base.metadata.create_all()` at application startup (`DatabaseManager.initialize()`). The 8-file database layer is deliberately thin.

### Models in `database/db.py`

| Table | Key Fields | Notes |
|-------|-----------|-------|
| `users` | email (unique), username (unique), hashed_password, role, failed_login_attempts, locked_until | Composite index on (email, is_active) |
| `products` | sku (unique), name, price, category, collection, variants_json, images_json | JSON columns for variants/images/SEO |
| `orders` | order_number (unique), user_id FK, status, total, currency | Composite indexes on (user_id, status) and created_at |
| `order_items` | order_id FK, product_id FK, quantity, unit_price, variant_json | Join table with variant snapshot |
| `audit_logs` | timestamp, user_id, action, resource_type, resource_id, details_json, ip_address | Composite index on (timestamp, action) |
| `agent_tasks` | agent_name, action, status, parameters_json, result_json, error, started_at, completed_at | Background task tracking |
| `event_store` | event_id (PK), event_type, aggregate_id, aggregate_type, data_json, version, correlation_id | Append-only; NEVER update/delete |

### Connection Pool Strategy
- SQLite in-memory → `StaticPool` (single connection alive)
- SQLite file → `NullPool` (multiple processes)
- PostgreSQL → `QueuePool` (pool_size=10, max_overflow=20, pool_recycle=1800s)

### Multi-Tenant Models (`database/models/`)
`Tenant` + `TenantUser` models in `database/models/tenant.py` and `tenant_user.py`. `TenantMiddleware` (in `security/`) resolves tenant from `X-Tenant-ID` header (HMAC-validated) or JWT `tenant_id` claim.

### Query Optimizer
`database/query_optimizer.py` — `QueryOptimizer.optimize_product_query()` adds `selectinload(Product.order_items)` to prevent N+1. `explain_query()` runs `EXPLAIN ANALYZE` on PostgreSQL only (no-op on SQLite).

### Seed Scripts
- `database/seed_admin.py` — creates default admin user on first boot
- `database/seed_catalog.py` — loads `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` into the `products` table

---

## 3. Security Layer (`security/`, 32 files)

### Auth Subsystem

**`security/jwt_oauth2_auth.py`**
- `UserRole` enum + `ROLE_HIERARCHY` dict — **duplicated** from `core/auth/types.py` (gotcha; the security copy is the one actually used at runtime for JWT claims)
- `TokenFamily` tracking: refresh tokens carry a `family_id` claim; `revoke_family()` invalidates all tokens on a device by marking the family ID in Redis
- Access tokens: 15-minute TTL. Refresh tokens: 7-day TTL, rotation on every use
- Token blacklist stored in Redis with per-token TTL; fallback to in-memory set when Redis unavailable

**`security/advanced_auth.py`**
- `AdvancedAuthManager`: TOTP / SMS / EMAIL MFA paths
- Device fingerprinting: SHA-256 of first 16 chars from `UA + IP + Accept-Language + Timezone`
- Risk scoring 0–100; brute-force lockout after 5 failures in 30-minute window
- `SecuritySession(BaseModel)`: `is_mfa_verified`, `risk_score`, `is_expired()`, `update_activity()`
- Global singleton: `advanced_auth = AdvancedAuthManager()`

### Encryption Subsystem

**`security/aes256_gcm_encryption.py`**
- Format: `version:iv_b64:ciphertext_b64` (all base64), 96-bit IV, 128-bit auth tag
- Key derivation: 600K PBKDF2-SHA256 iterations (OWASP 2023)
- `FieldEncryption`: per-field AAD context binding (prevents ciphertext transplanting between fields)
- 20 `SENSITIVE_FIELDS` constants declared at module level
- `needs_rehash()` checks PBKDF2 iteration count for migration

**`security/password_hashing.py`**
- Primary: Argon2id (64MB memory, 2 iterations, OWASP 2023)
- Legacy fallback: BCrypt for existing hashes
- `needs_rehash()` detects BCrypt hashes and migrates on next login

**`security/key_management.py`**
- Key rotation with versioned keys (`v1`, `v2`, …); ciphertext headers carry version so old keys decrypt old data
- `KeyRotationScheduler`: background thread, configurable interval

### Secrets Manager (`security/secrets_manager.py`)
Three backends, auto-detected at runtime:
1. **AWS Secrets Manager** — detected via `AWS_REGION` env var; boto3 paginator for list; 30-day recovery window on delete
2. **HashiCorp Vault** — detected via `VAULT_ADDR`; hvac KV v2; path format `mount/path` or `path` (defaults to `secret` mount)
3. **LocalEncryptedBackend** — Fernet; `0o700` dir permissions, `0o600` file permissions; fallback when neither cloud backend is configured

`SecretRotationScheduler`: background daemon thread; glob pattern matching via `fnmatch`; `RotationPolicy(interval_days, notify_days_before)`; `RotationEvent` history; thread-safe with `threading.Lock`.

Convenience functions: `get_secrets_manager()`, `get_secret(key)`, `set_secret(key, value)`.

### Input Security

**`security/input_validation.py`** — `SecurityValidator`
- `MAX_STRING_LENGTH = 10000`, `MAX_ARRAY_LENGTH = 1000`, `MAX_NESTING_DEPTH = 10`
- SQL injection: regex pattern scan + `sqlparse` tokenization
- XSS: `bleach` sanitization + HTML entity checks
- Path traversal: blocks `../`, `..\\`, absolute paths to sensitive dirs
- Command injection: blocks shell metacharacters

**`security/ssrf_protection.py`** — `SSRFProtection`
- Blocked by default: `localhost`, `127.0.0.1`, `::1`, `169.254.169.254`, `fd00:ec2::254`, `metadata.google.internal`, `metadata.azure.com`
- Allowed protocols: `{http, https}`; allowed ports: `{80, 443}` (configurable)
- Max redirects: 3; timeout: 10s

**`security/file_upload_security.py`**
- Allowlist of MIME types; magic-byte validation (not just extension)
- Max file size configurable; virus scan hook (pluggable)

### Monitoring Subsystem

**`security/audit_log.py`** — `AuditLogger`
- `AuditLogEntry.calculate_hash()`: `json.dumps(asdict(entry), sort_keys=True, default=str)` → SHA-256
- `verify_chain()`: traverses all in-memory entries, validates each hash
- Append-only `_audit_entries: list[AuditLogEntry]`
- **Bug**: `log_data_access()` maps `"read"` action to `AuditEventType.DATA_CREATED` — copy-paste error; `"read"` should map to `DATA_READ`
- 25+ `AuditEventType` values across auth/authorization/data/security/API/config categories

**`security/prometheus_exporter.py`**
- Custom `devskyy_registry = CollectorRegistry()` (not default Prometheus registry — avoids conflicts with other exporters)
- 8 metrics: `security_events_total`, `threat_score` (Gauge), `api_request_duration_seconds`, `auth_events_total`, `input_validation_failures_total`, `active_sessions`, `rate_limit_events_total`, `db_query_duration_seconds`

**`security/alerting.py`**
- `AlertDeduplicator`: content hash + 5-minute time window prevents spam
- `AlertingConfig`: severity thresholds per channel — Slack ≥ MEDIUM, Email ≥ HIGH, PagerDuty ≥ CRITICAL

### Rate Limiting (`security/rate_limiting.py`)
- `TokenBucket(capacity, refill_rate)`: time-based refill
- `SlidingWindowCounter(window_size, max_requests)`: sliding list of timestamps
- `AdvancedRateLimiter`: endpoint-specific rules (e.g., `/api/v1/auth/login` = 10 rpm)
- IP whitelist: `127.0.0.1`, `::1`
- Auto-blacklist when requests exceed 2× burst limit (DDoS detection)
- `RATE_LIMIT_TIERS`: free (10 rpm) / starter (100 rpm) / pro (500 rpm) / enterprise (2000 rpm)

### Middleware (`security/security_middleware.py`)
`SecurityMiddleware(BaseHTTPMiddleware)` — 7-step dispatch:
1. Rate limit check
2. Security validation (request structure)
3. Authentication (JWT extraction)
4. Input validation (payload scan)
5. CSRF check
6. `call_next` (pass to application)
7. Add 10 security response headers (`X-Content-Type-Options`, `Strict-Transport-Security`, `Cross-Origin-Opener-Policy`, etc.)

CSP: per-request nonce via `secrets.token_hex(16)`. Note: `CSPMiddleware` in `security/csp_middleware.py` also generates per-request nonces independently — two nonce sources if both are mounted (potential header duplication).

### MFA (`security/mfa.py`)
- `MFAManager`: raises `RuntimeError` if `pyotp` not installed
- `setup_totp()` returns `MFASetupData(secret, qr_code_uri, backup_codes)`
- Backup code format: `XXXX-XXXX` (8 hex chars split by dash)
- `verify_backup_code()` tracks `used_codes: set[str]` to prevent reuse
- `MFASession`: TTL-based; tracks `verification_method`

### PII Protection (`security/pii_protection.py`)
- 14 PII types; 5 sensitivity classifications (PUBLIC → TOP_SECRET)
- `PIIDetectionRule`: field_patterns (field name regex) + value_patterns (value regex)
- Imports `FieldEncryption` from `.aes256_gcm_encryption` for encryption-at-rest

### Zero Trust / mTLS (`security/zero_trust_config.py`, `security/mtls_handler.py`)
- `ZeroTrustConfig`, `ServiceIdentity`, `SelfSignedCA`, `VaultCA`
- TLS 1.3 minimum; cert compatibility helpers for `cryptography < 42.0`

### `security/__init__.py`
Exports all of `aes256_gcm_encryption` + key symbols from `jwt_oauth2_auth` + `secrets_manager`. The remaining 29 security files must be imported directly — they are not re-exported.

---

## 4. Orchestration Layer (`orchestration/`, 32 files)

### RAG Pipeline

The full RAG stack is self-contained within `orchestration/`:

```
Query
  └─ [optional] AdvancedQueryRewriter (query_rewriter.py)
       ├─ ZERO_SHOT / FEW_SHOT / SUB_QUERIES / STEP_BACK / HYDE
       ├─ Uses claude-haiku-4-5-20251001 (cost-optimized)
       ├─ 24h Redis cache for rewritten queries
       └─ Bypass: queries < 20 chars skip rewriting
  └─ EmbeddingEngine (embedding_engine.py)
       ├─ EmbeddingCache: async OrderedDict LRU, 1024 entries, asyncio.Lock
       ├─ SHA-256 key (first 32 chars), hit/miss counters
       └─ Backends: SentenceTransformers (local default) / OpenAI / Cohere
  └─ BaseVectorStore (vector_store.py)
       ├─ ChromaDB (default, local — adequate for 33-SKU catalog)
       ├─ Pinecone (cloud — swap via VectorStoreConfig one-liner)
       └─ VectorSearchCache: 256-entry LRU, 5-min TTL, 64-dim rounded key
  └─ [optional] Reranker (reranker.py)
       ├─ Cohere Rerank API (cross-encoder)
       ├─ RerankingCache: 512-entry LRU, 30-min TTL
       └─ Claimed 20-40% relevance improvement + $20-50/month savings
  └─ RAGContextConfig (rag_context_manager.py)
       └─ top_k=5, similarity_threshold=0.5, use_query_rewriting=False, use_reranking=False
```

**`orchestration/catalog_retriever.py`** — thin wrapper that indexes `branding_spec + description + name` per SKU for semantic queries. Returns `CatalogMatch` (sku, name, collection, score, branding_spec, description) and `CatalogAnswer` (natural-language answer with `[SKU]` citation markers).

**`orchestration/docs_context.py`** — module-level singleton; double-checked locking (`asyncio.Lock`); initializes `DocumentIngestionPipeline` against `devskyy_docs` ChromaDB collection on first call; all agents share one connection.

**`orchestration/auto_ingestion.py`** — `AutoDocumentIngestion` scans `docs/`, `README.md`, `CLAUDE.md`, `.claude/` for `.md/.txt/.rst/.html/.pdf`; incremental (skip already-indexed by SHA-256 hash); chunk_size=1000, chunk_overlap=200.

### LLM Routing

**`orchestration/llm_registry.py`** — 18 model definitions across 6 providers; `ModelCapability` enum with 20 capability tags; pricing and token limits per model. Used by `llm_orchestrator.py` for routing decisions.

**`orchestration/llm_orchestrator.py`** — `TaskType` StrEnum with 20+ types including `THREE_D_GENERATION`, `IMAGE_GENERATION`, `VIDEO_GENERATION`, `REAL_TIME`, `STREAMING`. `RoutingStrategy`: QUALITY / BALANCED / COST / SPEED / SPECIFIC.

**`orchestration/llm_clients.py`** — 6 provider clients using official async SDKs:
- OpenAI: `AsyncOpenAI`
- Anthropic: `AsyncAnthropic`
- Google: `google.genai`
- Mistral: `Mistral` (mistralai SDK)
- Cohere: `cohere`
- Groq: `AsyncGroq`
API keys loaded from `config.py` (which reads `.env.hf`); fallback to `os.getenv()` for standalone use. All clients implement abstract `BaseLLMClient` with `complete()` and `stream()`. `tenacity` retry decorator on all calls.

**`orchestration/domain_router.py`** — `DomainRouter` routes by file path regex patterns or task hint keywords. Domain-to-provider matrix:

| Domain | Primary | Fallback |
|--------|---------|---------|
| CODE_GENERATION | Claude (claude-sonnet-4) | GPT-4o |
| WEB_DESIGN | Gemini (gemini-2.0-flash) | Claude |
| PRODUCT_CONTENT | GPT-4o | Claude |
| FAST_INFERENCE | Groq (llama-3.3-70b) | Mistral |
| RAG_SEARCH | Cohere (command-r-08-2024) | Claude |
| THREE_D_GENERATION | Claude | GPT-4o |
| MEDIA_GENERATION | Gemini | GPT-4o |

**`orchestration/feedback_tracker.py`** — `FeedbackTracker` writes `ResponseMetric` records to SQLite (`data/feedback.db`); tracks per-provider acceptance rate, avg quality score, avg latency, total cost. `BrandLearningLoop` reads these signals.

**`orchestration/prompt_engineering.py`** — 17 prompting techniques as `PromptTechnique` StrEnum (CoT, ToT, ReAct, HyDE, Constitutional, COSTARD, etc.); `PromptChain` executor; `EnsemblePrompt` for multi-technique fusion. Academic citations inline.

### Brand Learning Loop

**`orchestration/brand_learning.py`** — `BrandLearningLoop`: OBSERVE → EXTRACT → LEARN → ADAPT → EMIT closed loop. Subscribes to `core.events.event_bus`; reads from `FeedbackTracker`; updates `SKYYROSE_BRAND` dict in `brand_context.py`; persists to `data/brand_learning.db` (SQLite). `InsightConfidence`: LOW (<5 signals) / MEDIUM (5–20) / HIGH (20+) / VERIFIED (human-confirmed).

**`orchestration/brand_context.py`** — `SKYYROSE_BRAND` dict (brand DNA: colors, tone, typography, tagline); `BrandContextInjector` inserts brand system prompt into all LLM calls; `compile_catalog_digest()` serializes product catalog to ≤7500 chars (≈2000 tokens budget). `CatalogSummary` and `load_catalog_context()` load from canonical CSV.

**`orchestration/brand_integration.py`** — `wire_brand_learning()` — call once at app startup to connect `BrandLearningLoop` to event bus + `FeedbackTracker`. Called from `main_enterprise.py`.

### 3D Pipeline

**`orchestration/threed_round_table.py`** (1482 lines) — `ThreeDRoundTable` production tournament.

**Circuit Breaker**: `CircuitBreakerState` (CLOSED/OPEN/HALF_OPEN). 5 failures → OPEN; auto-transitions OPEN → HALF_OPEN after `recovery_timeout`; 2 successes in HALF_OPEN → CLOSED.

**Retry**: exponential backoff with jitter: `delay = min(base * exp^attempt, max_delay) + uniform(-jitter_range, +jitter_range)`.

**Providers & timeouts**:
| Provider | Timeout | Notes |
|----------|---------|-------|
| HUNYUAN3D_2 | 180s | Best quality (geo=95, tex=95) |
| TRIPO3D | 300s | External API; lazy-loaded `TripoAssetAgent` |
| ANIGEN | 240s | Image-to-3D only; rigged GLB output |
| INSTANTMESH | 120s | geo=85, tex=85 |
| TRIPOSR | 90s | geo=88 |
| LGM | 90s | geo=80, tex=80 |
| SHAP_E | 60s | geo=70 |
| POINT_E | 45s | geo=60, lowest quality |

**Competition flow**:
1. Filter unhealthy providers (open circuit breakers)
2. `asyncio.gather()` all active providers in parallel (semaphore: concurrent_limit=4)
3. `_enhance_quality()` on each successful response — **currently a stub** (sets metadata flags only; no actual trimesh/pymeshlab processing; `enhancement_bonus` score is a no-op signal until implemented)
4. `_score_response()` — 7 weighted components: geometry(0.24) + texture(0.20) + CLIP alignment×100×(0.20) + polycount(0.12) + speed(0.08) + web_readiness(0.08) + format(0.08) + enhancement_bonus
5. `_rank_entries()` — sorted descending by total score
6. A/B test between top 2: `confidence = min(score_diff / 20, 1.0)` — pure score math, no LLM judge
7. `RoundTableResult.to_dict()` for DB persistence; truncates prompt to 500 chars

**CLIP alignment** (`_maybe_score_alignment()`): looks for `thumbnail_url` / `preview_url` / `rendered_image` / `preview_path` in response metadata; calls `skyyrose.elite_studio.quality.clip_alignment.score_alignment(prompt, img)`; silently returns 0.0 on any failure (CLIP unavailable, network error, no preview).

**`orchestration/huggingface_3d_client.py`** — `HuggingFace3DClient` (async `aiohttp` + Gradio Client); models: HUNYUAN3D_2, TRIPOSR, INSTANTMESH, LGM, SHAP_E_TEXT, POINT_E; Gradio Spaces: `stabilityai/TripoSR`, `TencentARC/InstantMesh`, `tencent/Hunyuan3D-2`. `HuggingFace3DConfig.from_env()` reads `HF_TOKEN`.

**`orchestration/asset_pipeline.py`** — `ProductAssetPipeline`: Tripo3D + FASHN + WP upload in one orchestrated flow. Batch processing: 5 concurrent (`asyncio.Semaphore(5)`). Redis cache: 7-day TTL on 3D models (`devskyy:asset_pipeline:` prefix). WebSocket progress callbacks. Prometheus metrics via optional `prometheus_client` import. Retry queue with exponential backoff. Imports: `FashnTryOnAgent`, `MeshyAgent`, `TripoAssetAgent`, `WordPressAssetAgent`, `HuggingFace3DClient`.

**`orchestration/sync_pipeline.py`** — Round Table results → HuggingFace dataset export → WordPress media sync. Security guards: `MAX_JSON_FILE_SIZE = 10MB`, `MAX_SYNC_ITEMS = 1000`, `API_TIMEOUT_SECONDS = 30`. Reads from `assets/ai-enhanced-images/ROUND_TABLE_ELITE_RESULTS.json`; sync state persisted to `data/sync_state.json`.

### LangGraph Integration

**`orchestration/langgraph_integration.py`** — thin adapter; previously a parallel reimplementation. Now simply re-exports `StateGraph`, `END`, `START`, `add_messages` from real `langgraph`. Keeps local: `WorkflowState(BaseModel)`, `WorkflowStatus`, `NodeType`, `EdgeType`. Canonical usage: `skyyrose/elite_studio/creative/router.py`.

### Supporting Modules

**`orchestration/semantic_analyzer.py`** — `SemanticCodeAnalyzer`: AST-based Python analysis; `CodePatternType` enum covers 15 design patterns and anti-patterns (GOD_CLASS, LONG_METHOD, DEAD_CODE, CIRCULAR_DEPENDENCY, etc.); `CodeSymbol` dataclass captures name, type, file_path, line_number, docstring, parameters, decorators, cyclomatic complexity.

**`orchestration/enterprise_index.py`** — `EnterpriseCodeIndex`: multi-provider code search (GitHub Enterprise, GitLab, Sourcegraph, Bitbucket); `CodeSearchResult` + `RepositoryContext`; async `httpx` client. Used by SuperAgents to find existing implementations before writing new code.

**`orchestration/scout_harvester.py`** — competitor ad creative ingestion; sources: Meta Ad Library, Google Ads Transparency Center, internal teardowns. Default mode: fixture-driven (`tests/fixtures/competitor_ads/*.json`). Live scraping gated behind `SCOUT_LIVE_SCRAPE=1`; raises `NotImplementedError` until official-API harvester PR ships.

**`orchestration/agent_counter.py`** — `count_active_agents()`: dynamic discovery by counting `@mcp.tool` decorators in `devskyy_mcp.py` + scanning `agent_sdk/super_agents/*_agent.py`. Returns `{mcp_tools, super_agents, legacy_agents, total, active}`. Canonical count: 21 MCP tools + 6 SuperAgents = 27 total.

---

## 5. Cross-Cutting Patterns

### Async + Semaphore Concurrency
Every long-running pipeline uses `asyncio.Semaphore` to bound parallelism: `ThreeDRoundTable` (4), `ProductAssetPipeline` (5), `DocumentIngestionPipeline` (5 via `MAX_PARALLEL_INGESTION`). All public `process_*()` / `compete_*()` entry points are `async def`.

### Structlog vs stdlib Logging
Inconsistent: `orchestration/` newer files use `structlog.get_logger(__name__)` (structured JSON); older files use `logging.getLogger(__name__)` (stdlib). FastAPI `api/` layer uses stdlib. Both coexist — no consolidation.

### Retry Strategy
Two retry patterns in use:
1. **`tenacity`** — `@retry(stop=stop_after_attempt(3), wait=wait_exponential())` in `llm_clients.py`
2. **Manual loop** — `ThreeDRoundTable._generate_with_resilience()` custom loop with `RetryConfig.get_delay(attempt)` (exp backoff + jitter); circuit breaker integrated

### SQLite for Everything Internal
- `data/brand_learning.db` — brand learning signals
- `data/feedback.db` — LLM response quality metrics
- `devskyy.db` — main application DB (users, products, orders, events)

All internal state stores are SQLite. Redis is only used for: JWT blacklist, rate limiting counters, LLM response cache (optional), RAG query rewrite cache (optional), 3D model cache (7-day TTL).

### Prometheus
Two registries: the default Prometheus registry (used by `prometheus_client` itself) and `security/prometheus_exporter.py`'s custom `devskyy_registry`. Security metrics route to the custom registry to avoid conflicts. If both are exposed on the same `/metrics` endpoint there would be a merge step.

---

## 6. Key Interfaces and Entry Points

### How a Request Flows (Example: Product Description Generation)

```
API request → SecurityMiddleware (7-step)
            → DomainRouter.detect_domain(file_path="product")
            → TaskDomain.PRODUCT_CONTENT → GPT-4o primary
            → BrandContextInjector.inject() → system prompt with brand DNA + catalog digest
            → LLMClient.complete() → tenacity retry
            → FeedbackTracker.record() → SQLite
            → BrandLearningLoop.observe() → signal accumulation
```

### How a 3D Model is Generated

```
API → ProductAssetPipeline.process_product()
    → Redis cache check (devskyy:asset_pipeline:{hash})
    → ThreeDRoundTable.compete_image_to_3d()
        → circuit breaker filter
        → asyncio.gather() [HUNYUAN3D_2, TRIPOSR, INSTANTMESH, LGM, ANIGEN, TRIPO3D]
        → _enhance_quality() [stub]
        → _score_response() [7 weighted metrics]
        → _rank_entries()
        → _run_ab_test() [top 2 by score]
        → winner selected
    → Redis cache write (7-day TTL)
    → FashnTryOnAgent.generate_tryon()
    → WordPressAssetAgent.upload()
    → WebSocket progress callback
```

### How RAG Context is Retrieved

```
Agent calls get_docs_context("query")
  → docs_context._ensure_ready() [singleton init, double-checked lock]
  → DocumentIngestionPipeline.search(query)
      → EmbeddingEngine.embed(query) [LRU cache check]
      → VectorStore.search() [VectorSearchCache check]
      → [optional] Reranker.rerank() [RerankingCache check]
      → returns list[{"text": ..., "source": ...}]
```

---

## 7. Duplicate / Conflicting Definitions

| Symbol | Location 1 | Location 2 | Impact |
|--------|-----------|-----------|--------|
| `UserRole` enum | `core/auth/types.py` | `security/jwt_oauth2_auth.py` | JWT claims use security copy; RBAC logic uses core copy — could diverge if one is updated |
| `ROLE_HIERARCHY` dict | `core/auth/role_hierarchy.py` | `security/jwt_oauth2_auth.py` | Same risk as above |
| Cache implementations | `core/multi_tier_cache.py` | `core/redis_cache.py` | `core/performance.py` | Three overlapping abstractions, no consolidation |
| Prometheus registry | Default registry | `devskyy_registry` in `security/prometheus_exporter.py` | Could produce duplicate metrics if both are exposed |
| CSP nonce generation | `security/security_middleware.py` | `security/csp_middleware.py` | Two independent nonces per request if both middlewares are mounted |

---

## 8. Known Bugs and Stubs

| ID | File | Issue |
|----|------|-------|
| bug-001 | `security/audit_log.py:log_data_access()` | Maps `"read"` action to `AuditEventType.DATA_CREATED` — should be `DATA_READ` |
| bug-002 | `orchestration/threed_round_table.py:_enhance_quality()` | Documented stub — sets metadata flags only; no actual mesh/texture processing; `enhancement_bonus` score is phantom signal |
| arch-001 | `core/runtime/input_validator.py` | Imports `SecurityValidator` from `security.input_validation` — violates core/ zero-external-dep rule |
| arch-002 | `security/jwt_oauth2_auth.py` | Duplicates `UserRole` + `ROLE_HIERARCHY` from `core/auth/` — two sources of truth for roles |
| arch-003 | `orchestration/threed_round_table.py:_run_ab_test()` | "A/B test" is pure score math (`confidence = score_diff / 20`), not a real A/B test — naming is misleading |

---

## 9. Dependency Graph (Simplified)

```
core/              ← no external imports (except: core/runtime/input_validator.py → security/)
  ↑
security/          ← imports from core/auth/, core/events/
  ↑
database/          ← imports from core/ (Base, TimestampMixin); SQLAlchemy 2.0 async
  ↑
orchestration/     ← imports from core/, security/, llm/, agents/
  ↑
agents/            ← imports from orchestration/, core/, security/
  ↑
api/               ← imports from all layers; entry points
```

`orchestration/` is the integration hub: it pulls from `core/`, `llm/` (the 6-provider LLM layer), and directly from `agents/` (TripoAssetAgent, FashnTryOnAgent, AniGenAgent, WordPressAssetAgent, MeshyAgent). `skyyrose/elite_studio/` is a parallel pipeline that also imports from `orchestration/` (embedding, vector store, langgraph adapter).

---

## 10. Top Architectural Insights and Gotchas

### Top 3 Architectural Insights

1. **Hexagonal architecture with a documented hole.** `core/` is designed as a zero-dependency inner ring using `Protocol` + `ABC` ports for the LLM layer. The design is sound but has one acknowledged violation: `core/runtime/input_validator.py` imports `SecurityValidator` from `security/`. This is documented, not accidental — but it means `core/` cannot be tested in isolation without pulling in the full security stack.

2. **The 3D Round Table is the platform's most complex subsystem.** At 1482 lines, `threed_round_table.py` implements production circuit-breaking, exponential backoff with jitter, 8-provider parallel tournament, 7-metric quality scoring (including CLIP alignment), and A/B testing in a single file. The `_enhance_quality()` stub is a significant gap: the scoring includes an `enhancement_bonus` component that will always be a flat +5 until real trimesh/pymeshlab integration is wired in, making quality scores ~5% optimistic for any provider that succeeds.

3. **Brand learning is a closed loop, not a one-shot injection.** The `BrandLearningLoop` (OBSERVE → EXTRACT → LEARN → ADAPT → EMIT) continuously mutates the `SKYYROSE_BRAND` dict in memory and persists signals to SQLite. Every LLM call goes through `BrandContextInjector`, so the brand DNA evolves with usage. This is architecturally elegant but creates a risk: if the loop learns wrong patterns (e.g., from bad user feedback), it silently degrades every downstream LLM call until `InsightConfidence.VERIFIED` (human-confirmed) signals correct it.

### Top 3 Gotchas

1. **Three caches, no consolidation.** `core/multi_tier_cache.py`, `core/redis_cache.py`, and `core/performance.py` are three independent caching abstractions. `orchestration/` adds two more (VectorSearchCache, RerankingCache) and `threed_round_table.py` does Redis caching via `asset_pipeline.py`. Before adding any cache logic, read all five to understand which layer owns what — and don't create a sixth.

2. **`UserRole` is defined twice; the security copy wins at runtime.** `core/auth/types.py` defines the canonical `UserRole` enum and `ROLE_HIERARCHY`. `security/jwt_oauth2_auth.py` redefines both identically. JWT claims are encoded and decoded using the security copy. RBAC checks in `core/` use the core copy. If either diverges (e.g., adding a new role to one but not the other), JWT tokens will carry role names that core/ cannot resolve. Fix: `security/jwt_oauth2_auth.py` should import from `core/auth/types.py`.

3. **`_enhance_quality()` is a stub with no warning suppression after first call.** The method logs a warning once per process (via `_enhance_quality_stub_warned` class variable), but the `enhancement_bonus` of +5 still accumulates in every quality score. In a production tournament with 6 providers all succeeding, the winner's score will be systematically inflated by 5 points. The `enhancement_bonus` weight is 0 in `ThreeDQualityScores.total` (it's an additive `+` not a weighted component) — so the actual score impact is a flat +5 on `total`, which is capped at 100. This means any provider scoring ≥95 without enhancement gets no benefit, but providers in the 60–95 range get an artificial 5-point boost that doesn't reflect real mesh quality.

---

*Digest written by the learn-codebase agent. 123 source files read. No migrations directory found — schema managed via `Base.metadata.create_all()` at startup. All claims trace to direct file reads in this session.*
