# DevSkyy — Claude Config

> Enterprise AI | SkyyRose Luxury Fashion | 54 Agents | **pytest AFTER EVERY CHANGE**

## Protocol
1. **Context7** → `resolve-library-id` → `get-library-docs` (BEFORE library code)
2. **Serena** → Codebase navigation and symbol lookup
3. **Navigate** → Read first, understand, NO code until clear
4. **Implement** → `str_replace` (targeted) | `create_file` (new only)
5. **Test** → `pytest -v` (MANDATORY after EVERY file touch)
6. **Format** → `isort . && ruff check --fix && black .`

## MCP Tools
**DevSkyy** (`devskyy_mcp.py`): `agent_orchestrator` `rag_query` `rag_ingest` `brand_context` `product_search` `order_management` `wordpress_sync` `3d_generate` `analytics_query` `cache_ops` `health_check` `tool_catalog` `llm_route`

| Service | Key Tools |
|---------|-----------|
| **Figma** | `get_design_context` `get_screenshot` `get_metadata` `get_code_connect_map` |
| **Notion** | `notion-search` `notion-fetch` `notion-create-pages` `notion-update-page` |
| **HuggingFace** | `model_search` `dataset_search` `paper_search` `hf_doc_search` |
| **WordPress.com** | `wpcom-mcp-posts-search` `wpcom-mcp-post-get` `wpcom-mcp-site-settings` |
| **Vercel** | `deploy_to_vercel` `list_deployments` `get_deployment_build_logs` |

## Skills (Read BEFORE Complex Tasks)
| Task | Path |
|------|------|
| SkyyRose brand | `/mnt/skills/user/skyyrose-brand-dna/SKILL.md` |
| WordPress/WooCommerce | `/mnt/skills/user/wordpress-woocommerce-automation/SKILL.md` |
| Agent building | `/mnt/skills/user/devskyy-agent-builder/SKILL.md` |
| MCP debugging | `/mnt/skills/user/mcp-server-debugger/SKILL.md` |
| RAG optimization | `/mnt/skills/user/rag-query-rewriter/SKILL.md` |
| Production checks | `/mnt/skills/user/production-readiness-checker/SKILL.md` |

## Codebase
```
main_enterprise.py        # FastAPI (47+ endpoints)
devskyy_mcp.py            # MCP server (13 tools)
core/
├── auth/                 # Auth types, models, interfaces (zero deps)
└── registry/             # Service registry for dependency injection
agents/
├── base_super_agent.py   # Enhanced base (17 techniques, ADK-based)
├── base_legacy.py        # Legacy base classes (deprecated, use ADK)
└── operations_legacy.py  # Legacy operations agent (deprecated)
adk/                      # Agent Development Kit (symlink to sdk/python/adk)
llm/                      # 6 providers, router, round_table
security/                 # AES-256-GCM, JWT, audit_log (uses core.auth)
api/v1/                   # REST, gdpr, webhooks
tests/
├── integration/          # Integration tests (moved from root)
└── ...                   # 1200+ tests
```

## Rules
- Correctness > Elegance > Performance | No deletions, refactor only
- Pydantic in, typed out | Update ALL sites+tests+docs on interface change
- `pytest -v` after EVERY change | 90%+ coverage

## Patterns
```python
class ToolError(DevSkyError):
    def __init__(self, tool: str, reason: str, *, correlation_id: str | None = None): ...
async def process(data: InputModel, *, correlation_id: str | None = None) -> OutputModel: ...
```

## Security
AES-256-GCM encryption | JWT + OAuth2 | GDPR endpoints | Audit logging | `.env` local, AWS Secrets prod

## Brand
SkyyRose: `#B76E79` primary | "Where Love Meets Luxury" | Use `BrandKit.from_config()`

## Gotchas
- **WP.com API**: `index.php?rest_route=` NOT `/wp-json/`
- **3D CDNs**: VERIFY URLs exist | **Correlation IDs**: ALWAYS propagate

## Health
`/health` `/health/ready` `/health/live` `/metrics` (Prometheus)

## Dependencies
**Single Source**: `pyproject.toml` only (use `pip install -e ".[all]"`)
- **Core**: FastAPI, Pydantic, SQLAlchemy, PyJWT, Sentry
- **ML**: torch, transformers, diffusers, chromadb, llama-index
- **Worker**: celery, kombu, flower
- **Deploy**: gunicorn, uvicorn
- **MCP**: 13 MCP tools + 6 LLM providers

## Architecture (NEW - v1.3.1)
**Dependency Flow** (one-way, no cycles):
```
core/ (auth + registry) ← ZERO dependencies on outer layers
    ↓
adk/ (Agent Development Kit)
    ↓
security (implementations)
    ↓
agents (use adk.base, not legacy base.py)
    ↓
api, services
```

**Phase 2 Complete** (v1.3.1):
- ✅ Root cleanup: base.py, operations.py → agents/
- ✅ Test organization: test files → tests/integration/
- ✅ Service registry: core/registry/ for dependency injection
- ✅ Updated imports: agents use base_legacy until ADK migration

**v1.3.1** | SkyyRose LLC | Phase 2: Structural Reorganization
