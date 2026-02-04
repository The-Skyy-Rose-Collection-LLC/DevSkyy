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

## WordPress Theme Documentation (REQUIRED READING)
**IMPORTANT**: All agents MUST read these files before working on WordPress site:

| File | Purpose | When to Read |
|------|---------|--------------|
| `PAGES-DOCUMENTATION.md` | Complete page reference (static, interactive, catalog) | Before modifying ANY page templates |
| `THEME-AUDIT.md` | Security audit, file verification, hardening patterns | Before deployment or security changes |
| `SECURITY_HARDENING_COMPLETE.md` | OWASP compliance, defensive patterns | Before adding new features |
| `CONTEXT7_VERIFICATION.md` | WordPress best practices verification | Before writing WordPress code |

**Key Distinction (CRITICAL)**:
- **Immersive Pages** (`template-collection.php`): 3D storytelling, NOT shopping
- **Catalog Pages** (`page-collection-*.php`): Product grids, FOR shopping
- ALWAYS check documentation before assuming page purpose

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
wordpress-theme/          # SkyyRose WordPress theme (108 new packages)
├── skyyrose-2025/        # Main theme directory
│   ├── template-collection.php  # Collection pages (immersive)
│   ├── elementor-widgets/       # Custom widgets (3D, pre-order)
│   └── inc/                     # Theme functions
frontend/
├── components/3d/        # LuxuryProductViewer (React Three Fiber)
└── lib/animations/       # luxury-transitions.ts (Framer Motion)
services/
└── ai_image_enhancement.py  # AI image processing (FLUX, SD3, RemBG)
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
- **WordPress Theme**: Use Serena for all WordPress file operations
- **Context7**: ALWAYS query WordPress/Elementor/WooCommerce docs BEFORE coding
- **Collection Pages**:
  - IMMERSIVE (3D): BLACK ROSE (gothic cathedral), LOVE HURTS (romantic castle), SIGNATURE (Oakland/SF tour)
  - CATALOG (products): page-collection-black-rose.php, page-collection-love-hurts.php, page-collection-signature.php
- **Immersive**: React Three Fiber + Framer Motion + luxury animations (#B76E79 rose gold)
- **Ralph Loop**: Use for complex multi-step immersive page builds
- **WordPress Docs**: ALWAYS read `wordpress-theme/skyyrose-2025/PAGES-DOCUMENTATION.md` before modifying pages
- **Security**: ALWAYS read `wordpress-theme/skyyrose-2025/THEME-AUDIT.md` before deployment changes

## Health
`/health` `/health/ready` `/health/live` `/metrics` (Prometheus)

## Dependencies
**Single Source**: `pyproject.toml` + `package.json` (108 new packages installed)

### Python
- **Core**: FastAPI, Pydantic, SQLAlchemy, PyJWT, Sentry
- **ML**: torch, transformers, diffusers, chromadb, llama-index
- **Worker**: celery, kombu, flower
- **Deploy**: gunicorn, uvicorn
- **MCP**: 13 MCP tools + 6 LLM providers
- **AI Image**: fal-client, stability-sdk, rembg, clip-interrogator

### JavaScript/TypeScript (39 new packages)
- **3D**: @react-three/fiber, @react-three/drei, postprocessing, three
- **Animation**: framer-motion, react-spring, gsap, lottie-web
- **Image**: sharp, pica, blurhash, @vercel/og
- **WordPress**: @wordpress/scripts (31.4.0), @wordpress/block-editor, @wordpress/components
- **WooCommerce**: @woocommerce/components, @woocommerce/data
- **Elementor**: swiper, aos, isotope-layout, typed.js

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

**Phase 5 Active** (v3.0.0 - WordPress Enhancement):
- ✅ 108 packages installed (39 JS/TS + 69 WordPress)
- ✅ LuxuryProductViewer component (React Three Fiber)
- ✅ Luxury animations library (Framer Motion)
- ✅ AI image enhancement (FLUX, SD3, RemBG)
- 🔄 Immersive collection pages (Ralph Loop in progress)
- 🔄 WooCommerce integration with 3D viewers
- 🔄 Pre-order forms with checkout

**v3.0.0** | SkyyRose LLC | Immersive WordPress Experience
