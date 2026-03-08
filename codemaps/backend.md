# DevSkyy Backend Codemap

> Freshness: 2026-03-03 | Python 3.12 | FastAPI + gRPC + Event Sourcing

## Core (`core/`)

Zero dependencies on outer layers. Exports types, interfaces, utilities.

| Module | Key Classes | Purpose |
|--------|-------------|---------|
| `auth/types.py` | UserRole, TokenType, Permission, AuthStatus | Auth enums (6 roles, 24 permissions) |
| `auth/models.py` | TokenResponse, AuthResult, UserCreate, UserInDB | Auth Pydantic models |
| `caching/multi_tier_cache.py` | MultiTierCache, @cached | L1 (TTLCache) + L2 (Redis), auto-promotion |
| `cqrs/command_bus.py` | Command, CommandBus | Write-side routing |
| `cqrs/query_bus.py` | Query, QueryBus | Read-side routing |
| `events/event_store.py` | Event, EventStore | Append-only, immutable deep-copy |
| `events/event_bus.py` | EventBus (singleton) | Pub/sub, handler errors swallowed |
| `events/event_handlers.py` | ProductEventHandler | Idempotent upsert pattern |
| `feature_flags/flag_manager.py` | FlagManager, FeatureFlag | Kill-switch, consistent hash rollout |
| `agents/` | IAgent, ISuperAgent | Agent interfaces |
| `services/` | IRAGManager, IMLPipeline | Service interfaces |
| `repositories/` | IRepository, IUserRepository | Repository interfaces |

## Database (`database/`)

| File | Models | Notes |
|------|--------|-------|
| `db.py` | User, Product, Order, OrderItem, AuditLog, AgentTask, EventRecord | SQLAlchemy 2.0 async, TimestampMixin |
| `query_optimizer.py` | QueryOptimizer | Query optimization strategies |

**Indices**: (email, is_active), (category, is_active), (collection), (user_id, status), (aggregate_id, timestamp)

## Security (`security/`) — 32 files

| File | Purpose |
|------|---------|
| `jwt_oauth2_auth.py` | JWT tokens, OAuth2 flows, role checking |
| `aes256_gcm_encryption.py` | AES-256-GCM + HMAC |
| `api_security.py` | CORS, CSP, HTTPS enforcement |
| `rate_limiting.py` | Token bucket per-client |
| `secrets_manager.py` | AWS/Vault/local secret backends |
| `audit_log.py` | Security audit trails |
| `mfa.py` | TOTP multi-factor auth |
| `key_management.py` | Key rotation, derivation |
| `vulnerability_scanner.py` | Dependency scanning |
| `ssrf_protection.py` | SSRF prevention (block 169.254.x.x) |
| `input_validation.py` | Sanitize HTML, prevent SQLi |
| `pii_protection.py` | PII masking |
| `zero_trust_config.py` | Zero-trust model config |

## Orchestration (`orchestration/`) — 27 files

| File | Key Classes | Purpose |
|------|-------------|---------|
| `llm_orchestrator.py` | LLMOrchestrator | Task → strategy → optimal model |
| `llm_registry.py` | LLMRegistry | Central model definitions |
| `llm_clients.py` | Provider clients | OpenAI, Anthropic, Google, Mistral, Groq, Cohere |
| `prompt_engineering.py` | PromptEngineer | 17 techniques (ReAct, CoT, etc.) |
| `rag_context_manager.py` | RAGContextManager | Ingest → chunk → embed → search → rerank |
| `vector_store.py` | VectorStore | ChromaDB, FAISS, Pinecone backends |
| `embedding_engine.py` | EmbeddingEngine | OpenAI, SentenceTransformer |
| `asset_pipeline.py` | ProductAssetPipeline | 3D/TryOn/WordPress generation |
| `brand_context.py` | BrandContext | SkyyRose brand DNA |

## LLM (`llm/`) — 25 files

| File | Key Classes | Purpose |
|------|-------------|---------|
| `unified_llm_client.py` | UnifiedLLMClient | Classify → technique → route → execute |
| `router.py` | LLMRouter | Cost/speed/quality routing |
| `round_table.py` | LLMRoundTable | Multi-provider consensus voting |
| `task_classifier.py` | TaskClassifier | Task type → technique selection |
| `ab_testing.py` | ABTestManager | A/B experiments across providers |
| `providers/` | 7 providers | Anthropic, OpenAI, Google, Mistral, Groq, Cohere, Stability |

## API (`api/`) — 50+ files

| Component | Location | Purpose |
|-----------|----------|---------|
| GraphQL | `graphql/schema.py` | Strawberry: Query.product(), Query.products() |
| DataLoader | `graphql/dataloaders/` | Batch SKU lookups, request-scoped |
| REST v1 | `v1/*.py` | 30+ modules (commerce, agents, wordpress, media, etc.) |
| Webhooks | `webhooks.py` | HMAC-verified dispatch |
| WebSocket | `websocket.py` | Real-time connections |
| Versioning | `versioning.py` | v1/v2/v3 management |

## Agents (`agents/`) — 40+ files

| Agent | Purpose |
|-------|---------|
| `base_super_agent.py` | Base class (17 techniques, ADK-based) |
| `skyyrose_product_agent.py` | Product management, SKU generation |
| `skyyrose_content_agent.py` | Content generation |
| `skyyrose_imagery_agent.py` | Image generation |
| `commerce_agent.py` | Commerce operations |
| `wordpress_bridge/` | WordPress MCP integration |
| `elite_web_builder/` | 8 specialist web builder agents |

## ADK (`adk/`) — 9 files

Integrations: Google ADK, PydanticAI, CrewAI, AutoGen, Agno, LangGraph
- 6 SuperAgents: Commerce, Creative, Marketing, Support, Operations, Analytics
- Workflow pipelines: product launch, content creation, customer journey

## Gateway (`gateway/`)

- `CircuitBreaker` — CLOSED → OPEN (at threshold) → HALF_OPEN → CLOSED
- `RateLimiter` — Token bucket per-client
- `APIGateway` — Longest-prefix routing, per-route breakers, SSRF protection

## Analytics (`analytics/`)

- `StreamProcessor` — Async Kafka consumer (confluent_kafka optional)
- `AnalyticsState` — page_views, product_interest, revenue_by_hour, search_queries
- Event dedup window: 10k events (OrderedDict FIFO)
