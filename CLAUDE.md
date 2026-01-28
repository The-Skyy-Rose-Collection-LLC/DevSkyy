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
**DevSkyy** (`devskyy_mcp.py`): `multi_agent_workflow` `manage_products` `dynamic_pricing` `generate_wordpress_theme` `generate_3d_from_description` `generate_3d_from_image` `virtual_tryon` `lora_generate` `product_caption` `marketing_campaign` `system_monitoring` `health_check` `list_agents` `scan_code` `fix_code` `self_healing`

| Service | Key Tools |
|---------|-----------|
| **Figma** | `get_design_context` `get_screenshot` `get_metadata` `get_code_connect_map` |
| **Notion** | `notion-search` `notion-fetch` `notion-create-pages` `notion-update-page` |
| **HuggingFace** | `model_search` `dataset_search` `paper_search` `hf_doc_search` |
| **WordPress.com** | `wpcom-mcp-posts-search` `wpcom-mcp-post-get` `wpcom-mcp-site-settings` |
| **Vercel** | `deploy_to_vercel` `list_deployments` `get_deployment_build_logs` |

## Codebase
```
main_enterprise.py        # FastAPI (47+ endpoints)
devskyy_mcp.py            # MCP server (27 tools)
agents/                   # SuperAgents + base
llm/                      # 6 providers, router, round_table
security/                 # AES-256-GCM, JWT, audit_log
api/v1/                   # REST, gdpr, webhooks
tests/                    # 1200+ tests
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

**v1.2.0** | SkyyRose LLC | Production Hardening
