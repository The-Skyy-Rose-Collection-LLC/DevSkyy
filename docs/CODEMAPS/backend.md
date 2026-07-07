# Backend Codemap

<!-- Generated: 2026-07-06 | Files scanned: api/ ~60, core/ ~55, security/ 30, llm/ ~30, orchestration/ 33, database/ 10, services/ ~55 | Token estimate: ~950 -->

**Entry points:** `main_enterprise.py` (primary FastAPI app), `api/index.py` (serverless/Vercel mirror — a separate, smaller app), `devskyy_mcp.py` (MCP tool server).

## Dependency flow

`core` → `security`, `database`, `llm` → `orchestration`, `services` → `agents` → `api` (diagram in [architecture.md](architecture.md)).

## api/ — route surface

| Layer | Location | Content |
|---|---|---|
| Top-level | `api/*.py` (25 files) | admin_dashboard, agents, brand, dashboard, round_table, tasks, tools, three_d, visual, ar_sessions, elementor_3d, gdpr, virtual_tryon, webhooks, websocket(+_integration), versioning, sync_endpoints, gateway, ai_3d_endpoints |
| v1 | `api/v1/` (30 modules, aggregated in `api/v1/__init__.py`) | catalog, commerce, assets, media, ml, monitoring, orchestration, approval, autonomous, brand_assets, claude_sdk, code, competitors, descriptions, hf_spaces, marketing, social_media, sync, training_status, wordpress(+`_agent`/`_theme`/`_integration`), elite_studio(+webhooks), rag_anything, pipeline, feature_flags; subpackages `analytics/`, `clothing_3d/`, `portal/` |
| v2 | `api/v2/` (5 modules) | assets, characters, creative, health, webhooks — newer, parallel surface, no v1 equivalent yet |
| GraphQL | `api/graphql/` (schema.py, types.py, resolvers/, dataloaders/) | mounted at `/graphql` via `api/graphql_server.py:graphql_router` |

`main_enterprise.py` imports the `api.v1` aggregator plus several direct `api.v1.<module>` imports (elite_studio, rag_anything, wordpress_integration, feature_flags, pipeline, portal) plus `graphql_router`. `api/index.py` is a **separate, smaller** FastAPI app for Vercel serverless — it mounts only 7 routers (dashboard, tasks, round_table, brand, tools, three_d, visual). The two entry points are not the same app and can drift.

## core/ — foundation (zero outer deps)

Subpackages: `auth/`(7) `caching/`(3) `cqrs/`(4) `errors/`(4) `events/`(6) `feature_flags/`(3) `llm/`(5, provider-agnostic interfaces) `middleware/`(4) `registry/`(5) `repositories/`(3) `runtime/`(6) `services/`(4) `telemetry/`(4). Root-level: `performance.py`, `redis_cache.py`, `structured_logging.py`, `task_status_store.py`, `token_tracker.py`, `product_spec.py`.

## security/ — 30 modules

Encryption: `aes256_gcm_encryption.py`. Auth: `jwt_oauth2_auth.py`, `advanced_auth.py`, `mfa.py`. Network: `ssrf_protection.py`, `mtls_handler.py`, `rate_limiting.py`. Governance: `zero_trust_config.py`, `audit_log.py`, `pii_protection.py`, `secrets_manager.py`, `key_management.py`, `certificate_authority.py`. Scanning: `vulnerability_scanner.py`(+`_remediation.py`), `dependency_scanner.py`, `code_analysis.py`. Ops: `security_monitoring.py`, `alerting.py`, `prometheus_exporter.py`, `security_webhooks.py`, `hardening_scripts.py`.

## llm/ — 11 provider adapters (not 6 — see [dependencies.md](dependencies.md))

`llm/providers/`: anthropic, openai, google, mistral, cohere, groq, deepseek, replicate, stability, vertex_imagen, litellm_provider. Routing chain: `router.py` → `task_classifier.py` → `tournament.py` (provider selection) → `round_table.py` (multi-provider consensus) → `verification.py`.

## database/

`database/db.py` (session/engine), `database/models/` (`tenant.py`, `tenant_user.py`), `seed_admin.py`, `seed_catalog.py`, `query_optimizer.py`. Migrations in `alembic/versions/`: `001_baseline_schema`, `002_add_brand_assets`, `003_add_analytics_tables` (details in [data.md](data.md)).

## orchestration/ — 33 modules

RAG/retrieval: `catalog_retriever.py`, `vector_store.py`, `reranker.py`, `embedding_engine.py`, `query_rewriter.py`(+`_integration`), `enterprise_index.py`, `rag_context_manager.py`. Brand: `brand_context.py`, `brand_integration.py`, `brand_learning.py`. Ingestion: `document_ingestion.py`, `auto_ingestion.py`, `docs_context.py`. LLM glue: `llm_clients.py`, `llm_registry.py`, `model_config.py`, `prompt_engineering.py`. 3D: `threed_round_table.py`, `huggingface_3d_client.py`. Sync/tasks: `sync_pipeline.py`, `tasks.py`, `asset_pipeline.py`.

## agents/ — 218 Python files

`agents/base_super_agent/agent.py:65` — `EnhancedSuperAgent` (17 prompt techniques, foundation class). `agents/core/` — 8-domain CoreAgent hierarchy (analytics, commerce, content, creative, imagery, marketing, operations, web_builder), each with a `sub_agents/` package. `agents/claude_sdk/domain_agents/` — 15 SDK-native domain agents. `agents/elite_web_builder/` — full-stack theme-building agency (`director.py` + 10+ specialist agents). `agents/render_pipeline/` — Google ADK agent for SkyyRose SKU renders (9-tool pipeline).

## services/ — business logic

`analytics/`, `competitive/`, `forecasting/`(demand), `lifecycle/`(retention), `ml/`(gemini_client, `enhancement/`, `prompts/`, `schemas/`), `notifications/`, `personalization/`(recommender), `risk/`(fraud), `storage/`(r2_client, version_manager), `three_d/`(provider_factory, `trellis/`). Root: `ai_image_enhancement.py`, `approval_queue_manager.py`, `image_deduplication.py`, `image_ingestion.py`, `rag_anything_service.py`.

## Testing

`pytest tests/ -v` (unit + `tests/integration/`); `make test-cov` for coverage; `isort . && ruff check --fix && black .` before commit.
