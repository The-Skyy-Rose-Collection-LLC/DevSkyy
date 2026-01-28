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
**DevSkyy**: `agent_orchestrator` `rag_query` `brand_context` `product_search` `wordpress_sync` `3d_generate` `analytics_query` `health_check`
**External**: Figma, Notion, HuggingFace, Vercel, WordPress.com, Stripe, Cloudflare

## Codebase
`main_enterprise.py` (FastAPI) | `devskyy_mcp.py` (MCP) | `agents/` (6 SuperAgents) | `llm/` (6 providers) | `security/` (AES-256-GCM, JWT) | `tests/` (1200+)

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

**v1.2.0** | SkyyRose LLC | Production Hardening
