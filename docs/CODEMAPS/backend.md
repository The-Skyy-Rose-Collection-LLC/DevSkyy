# Backend Codemap

**Last Updated:** 2026-02-19
**Source of Truth:** `main_enterprise.py`, `devskyy_mcp.py`, Python modules

## Structure

```
DevSkyy/                           # Backend (Python 3.11+)
|-- main_enterprise.py             # FastAPI entry point (47+ endpoints)
|-- devskyy_mcp.py                 # MCP server (13 tools, 54 agents)
|
|-- core/                          # Foundation Layer (ZERO outer dependencies)
|   |-- __init__.py
|   |-- auth/                      # Auth types, models, interfaces
|   |-- registry/                  # Service registry (dependency injection)
|   |-- runtime/                   # Tool registry, input validation
|   |-- repositories/              # Repository interfaces
|   |-- agents/                    # Agent base interfaces
|   |-- llm/                       # LLM provider interfaces
|   |-- services/                  # Service interfaces
|   |-- performance.py             # Performance monitoring
|   |-- redis_cache.py             # Redis caching layer
|   |-- structured_logging.py      # Structured logging
|   |-- task_status_store.py       # Task status tracking
|   |-- token_tracker.py           # Token usage tracking
|   `-- CLAUDE.md                  # Core module instructions
|
|-- security/                      # Security Layer (depends on: core)
|   |-- __init__.py
|   |-- aes256_gcm_encryption.py   # AES-256-GCM encryption (NIST SP 800-38D)
|   |-- jwt_oauth2_auth.py         # JWT + OAuth2 authentication
|   |-- advanced_auth.py           # MFA, session management
|   |-- mfa.py                     # Multi-factor authentication
|   |-- rate_limiting.py           # Request rate limiting
|   |-- audit_log.py               # Security audit logging
|   |-- api_security.py            # API security middleware
|   |-- csp_middleware.py          # Content Security Policy
|   |-- input_validation.py        # Input sanitization
|   |-- pii_protection.py          # PII detection and masking
|   |-- secrets_manager.py         # Secrets management
|   |-- key_management.py          # Encryption key lifecycle
|   |-- certificate_authority.py   # Certificate management
|   |-- mtls_handler.py            # Mutual TLS
|   |-- ssrf_protection.py         # SSRF prevention
|   |-- file_upload.py             # File upload validation
|   |-- zero_trust_config.py       # Zero-trust architecture config
|   |-- security_middleware.py     # Security middleware chain
|   |-- security_monitoring.py     # Real-time security monitoring
|   |-- security_testing.py        # Security test utilities
|   |-- vulnerability_scanner.py   # Vulnerability detection
|   |-- vulnerability_remediation.py  # Auto-remediation
|   |-- dependency_scanner.py      # Dependency vulnerability scanning
|   |-- code_analysis.py           # Static code analysis
|   |-- prometheus_exporter.py     # Metrics export
|   |-- alerting.py                # Security alerting
|   |-- hardening_scripts.py       # System hardening
|   |-- infrastructure_security.py # Infrastructure config
|   |-- requirements_hardening.py  # Dependency pinning
|   |-- security_webhooks.py       # Security event webhooks
|   |-- structured_logging.py      # Security-specific logging
|   `-- CLAUDE.md                  # Security module instructions
|
|-- llm/                           # LLM Provider Layer (depends on: core)
|   |-- __init__.py
|   |-- router.py                  # Multi-provider routing
|   |-- unified_llm_client.py      # Unified client interface
|   |-- base.py                    # Provider base class
|   |-- round_table.py             # Tournament consensus mechanism
|   |-- round_table_metrics.py     # Round table performance metrics
|   |-- tournament.py              # Tournament-style provider selection
|   |-- classification.py          # Task classification
|   |-- task_classifier.py         # Task type classifier
|   |-- creative_judge.py          # Creative output evaluation
|   |-- evaluation_metrics.py      # Response quality metrics
|   |-- ab_testing.py              # A/B testing framework
|   |-- adaptive_learning.py       # Provider preference learning
|   |-- statistics.py              # Statistical analysis
|   |-- verification.py            # Response verification
|   |-- exceptions.py              # LLM-specific exceptions
|   |-- providers/                 # Provider implementations
|   |   |-- openai_provider.py     # OpenAI (GPT-4, etc.)
|   |   |-- anthropic_provider.py  # Anthropic (Claude)
|   |   |-- google_provider.py     # Google (Gemini)
|   |   |-- mistral_provider.py    # Mistral AI
|   |   |-- cohere_provider.py     # Cohere
|   |   `-- groq_provider.py       # Groq
|   `-- CLAUDE.md                  # LLM module instructions
|
|-- agents/                        # Agent Layer (depends on: core, llm, security)
|   |-- __init__.py
|   |-- base_super_agent.py        # EnhancedSuperAgent (17 prompt techniques)
|   |-- enhanced_base.py           # Enhanced agent base
|   |-- base_legacy.py             # Legacy base (DEPRECATED)
|   |-- operations_legacy.py       # Legacy operations (DEPRECATED)
|   |-- models.py                  # Agent data models
|   |-- errors.py                  # Agent-specific exceptions
|   |-- multimodal_capabilities.py # Multimodal agent support
|   |-- analytics_agent.py         # Analytics and reporting
|   |-- coding_doctor_agent.py     # Code analysis and fixing
|   |-- coding_doctor_toolkits.py  # Code analysis tools
|   |-- collection_content_agent.py  # Collection content management
|   |-- commerce_agent.py          # E-commerce operations
|   |-- creative_agent.py          # Creative content generation
|   |-- fashn_agent.py             # FASHN virtual try-on
|   |-- marketing_agent.py         # Marketing automation
|   |-- operations_agent.py        # Operations management
|   `-- CLAUDE.md                  # Agent module instructions
|
|-- api/                           # API Layer (depends on: all inner layers)
|   |-- __init__.py
|   |-- index.py                   # API router registration
|   |-- v1/                        # Versioned REST API routes
|   |-- admin_dashboard.py         # Admin dashboard endpoints
|   |-- dashboard.py               # Dashboard API
|   |-- agents.py                  # Agent invocation endpoints
|   |-- brand.py                   # Brand context endpoints
|   |-- elementor_3d.py            # Elementor 3D integration
|   |-- gdpr.py                    # GDPR compliance endpoints
|   |-- round_table.py             # Round table API
|   |-- sync_endpoints.py          # Data sync endpoints
|   |-- tasks.py                   # Task management
|   |-- three_d.py                 # 3D generation endpoints
|   |-- tools.py                   # Tool catalog endpoints
|   |-- versioning.py              # API versioning
|   |-- virtual_tryon.py           # Virtual try-on endpoints
|   |-- visual.py                  # Visual generation endpoints
|   |-- webhooks.py                # Webhook handlers (Stripe, WooCommerce)
|   |-- websocket.py               # WebSocket endpoints
|   |-- websocket_integration.py   # WebSocket integration layer
|   |-- ar_sessions.py             # AR session management
|   |-- image-processing/          # Image processing endpoints
|   `-- CLAUDE.md                  # API module instructions
|
|-- services/                      # Business Logic Layer
|   |-- __init__.py
|   |-- ai_image_enhancement.py    # AI image processing (FLUX, SD3, RemBG)
|   |-- approval_queue_manager.py  # Content approval workflow
|   |-- analytics/                 # Analytics services
|   |-- competitive/               # Competitive intelligence
|   |-- ml/                        # Machine learning services
|   |-- notifications/             # Notification services
|   |-- storage/                   # File storage services
|   `-- three_d/                   # 3D generation services (Tripo3D, etc.)
```

## Key Modules

| Module | Purpose | Location |
|--------|---------|----------|
| `main_enterprise.py` | FastAPI app with 47+ endpoints | Root |
| `devskyy_mcp.py` | MCP server exposing 54 agents as tools | Root |
| `base_super_agent.py` | SuperAgent with 17 prompt techniques (CoT, ReAct, ToT) | `agents/` |
| `unified_llm_client.py` | Unified interface to 6 LLM providers | `llm/` |
| `round_table.py` | Tournament consensus across LLM providers | `llm/` |
| `aes256_gcm_encryption.py` | NIST-compliant AES-256-GCM encryption | `security/` |
| `jwt_oauth2_auth.py` | JWT + OAuth2 authentication | `security/` |
| `zero_trust_config.py` | Zero-trust architecture configuration | `security/` |
| `ai_image_enhancement.py` | FLUX/SD3/RemBG image pipeline | `services/` |
| `redis_cache.py` | Redis caching with TTL management | `core/` |

## Data Flow

1. **API Request Flow**: HTTP request -> FastAPI middleware (CORS, rate limiting, CSP) -> JWT/OAuth2 authentication -> API route handler -> Service layer -> Agent invocation (if needed) -> LLM provider (via router) -> Response validation -> JSON response.

2. **Agent Execution Flow**: API triggers agent -> `EnhancedSuperAgent._plan()` creates execution plan -> `_retrieve()` gathers context (RAG, brand DNA) -> `_execute_step()` runs each plan step via LLM -> `_validate()` checks output quality -> `_emit()` returns structured result.

3. **MCP Tool Flow**: External AI system connects via MCP protocol -> `devskyy_mcp.py` receives tool invocation -> Maps to internal agent/service -> Executes with correlation_id tracking -> Returns structured result.

4. **LLM Routing Flow**: Request arrives at `router.py` -> `task_classifier.py` determines task type -> `tournament.py` selects optimal provider -> Provider executes -> `verification.py` checks response quality -> If tournament mode, `round_table.py` aggregates multi-provider consensus.

## Health Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /health` | Overall system health | `{"status": "healthy", "version": "3.1.0"}` |
| `GET /health/ready` | Readiness probe (DB, services) | `{"ready": true}` |
| `GET /health/live` | Liveness probe (process alive) | `{"alive": true}` |
| `GET /metrics` | Prometheus metrics | Prometheus text format |

## Environment Variables (from .env.example)

### Application

| Variable | Purpose | Default |
|----------|---------|---------|
| `ENVIRONMENT` | Runtime environment | `development` |
| `DEBUG` | Debug mode (false for security) | `false` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Security (REQUIRED for production)

| Variable | Purpose | Format |
|----------|---------|--------|
| `JWT_SECRET_KEY` | JWT signing key | 64+ char URL-safe string |
| `ENCRYPTION_MASTER_KEY` | AES-256-GCM encryption | Base64-encoded 32-byte key |

### Database

| Variable | Purpose | Format |
|----------|---------|--------|
| `DATABASE_URL` | Database connection | `sqlite+aiosqlite:///./devskyy.db` (dev) or `postgresql+asyncpg://...` (prod) |
| `DB_POOL_SIZE` | Connection pool size | `10` |
| `DB_MAX_OVERFLOW` | Max pool overflow | `20` |
| `DB_POOL_TIMEOUT` | Pool timeout (seconds) | `30` |

### AI/ML APIs

| Variable | Purpose | Format |
|----------|---------|--------|
| `OPENAI_API_KEY` | OpenAI provider | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic provider | `sk-ant-...` |
| `GOOGLE_AI_API_KEY` | Google AI provider | API key string |
| `HF_TOKEN` | HuggingFace token | `hf_...` |

### Integrations

| Variable | Purpose | Format |
|----------|---------|--------|
| `STRIPE_API_KEY` | Stripe payments | `sk_test_...` or `sk_live_...` |
| `STRIPE_PUBLISHABLE_KEY` | Stripe public key | `pk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook verification | `whsec_...` |
| `WORDPRESS_URL` | WordPress site URL | `https://...` |
| `WORDPRESS_APP_PASSWORD` | WordPress auth | `xxxx-xxxx-xxxx-xxxx` |
| `WOOCOMMERCE_KEY` | WooCommerce API key | `ck_...` |
| `WOOCOMMERCE_SECRET` | WooCommerce API secret | `cs_...` |
| `FASHN_API_KEY` | FASHN virtual try-on | API key string |
| `TRIPO_API_KEY` | Tripo3D generation | API key string |
| `KLAVIYO_PRIVATE_KEY` | Klaviyo email marketing | `pk_...` |

### Infrastructure

| Variable | Purpose | Format |
|----------|---------|--------|
| `REDIS_URL` | Redis cache connection | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | Allowed CORS origins | Comma-separated URLs |
| `FRONTEND_URL` | Frontend application URL | `https://app.devskyy.app` |
| `API_URL` | Backend API URL | `https://api.devskyy.app` |
| `SENTRY_DSN` | Sentry error tracking | DSN URL |
| `PROMETHEUS_ENABLED` | Enable Prometheus metrics | `true` / `false` |

### Performance

| Variable | Purpose | Default |
|----------|---------|---------|
| `RATE_LIMIT_REQUESTS` | Max requests per window | `100` |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate limit window | `60` |
| `EMBEDDING_CACHE_SIZE` | Embedding cache entries | `1024` |
| `RESPONSE_CACHE_TTL` | HTTP cache TTL (seconds) | `300` |
| `VECTOR_SEARCH_CACHE_TTL` | Vector search cache (seconds) | `300` |
| `RERANKING_CACHE_TTL` | Reranking cache (seconds) | `1800` |
| `MAX_PARALLEL_INGESTION` | Max parallel file workers | `5` |

## Dependencies (Key External)

| Dependency | Purpose |
|-----------|---------|
| FastAPI + Uvicorn | HTTP server |
| SQLAlchemy + Alembic | Database ORM + migrations |
| Pydantic | Data validation |
| Redis (ioredis) | Caching |
| OpenAI SDK | OpenAI LLM provider |
| Anthropic SDK | Anthropic LLM provider |
| Google GenAI | Google LLM provider |
| Prisma | Database client (TypeScript side) |
| Socket.IO | WebSocket communication |
| Sentry | Error monitoring |

## Testing

```bash
# Python backend tests
pytest -v                          # Run all tests
pytest tests/unit -v               # Unit tests only
pytest tests/integration -v        # Integration tests
pytest --cov=core --cov=agents     # Coverage report

# Full verification
isort . && ruff check --fix && black .   # Format
mypy . --ignore-missing-imports          # Type check
pytest -v                                # Test
```
