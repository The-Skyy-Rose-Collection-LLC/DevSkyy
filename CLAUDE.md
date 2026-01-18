# DevSkyy — Claude Config

> Enterprise AI | SkyyRose Luxury Fashion | 54 Agents | **pytest AFTER EVERY CHANGE**

---

## ⚡ PROTOCOL

```
1. CONTEXT7    → resolve-library-id → get-library-docs (BEFORE library code)
2. SKILLS      → view /mnt/skills/*/SKILL.md (before complex tasks)
3. NAVIGATE    → view/bash (understand first, NO code)
4. IMPLEMENT   → str_replace (targeted) | create_file (new only)
5. TEST        → pytest -v (MANDATORY after EVERY file touch)
6. FORMAT      → isort . && ruff check --fix && black .
```

---

## 🔧 TOOLS

### Core
| Tool | Use |
|------|-----|
| `Context7:resolve-library-id` → `get-library-docs` | ALWAYS first for any library |
| `view` | Read files/dirs |
| `str_replace` | Edit files (prefer over rewrites) |
| `create_file` | New files only |
| `bash_tool` | pytest, format, git |
| `web_search` / `web_fetch` | Current docs, APIs |

### DevSkyy MCP (`devskyy_mcp.py`)
`agent_orchestrator` `rag_query` `rag_ingest` `brand_context` `product_search` `order_management` `wordpress_sync` `3d_generate` `analytics_query` `cache_ops` `health_check` `tool_catalog` `llm_route`

### External MCP Integrations
| Service | Key Tools |
|---------|-----------|
| **Figma** | `get_design_context` `get_screenshot` `get_metadata` `get_code_connect_map` |
| **Notion** | `notion-search` `notion-fetch` `notion-create-pages` `notion-update-page` `notion-create-database` |
| **HuggingFace** | `model_search` `dataset_search` `paper_search` `hf_jobs` `hub_repo_details` `hf_doc_search` |
| **Vercel** | `deploy_to_vercel` `list_deployments` `get_deployment_build_logs` `search_vercel_documentation` |
| **WordPress.com** | `wpcom-mcp-posts-search` `wpcom-mcp-post-get` `wpcom-mcp-site-settings` `wpcom-mcp-site-statistics` |
| **Google Drive** | `google_drive_search` `google_drive_fetch` |
| **Desktop Commander** | `read_file` `write_file` `edit_block` `start_process` `start_search` `list_directory` |
| **Stripe** | Payment integrations |
| **Cloudflare** | Edge deployments |

---

## 📂 SKILLS (Read BEFORE Complex Tasks)

| Task | Skill |
|------|-------|
| Word docs | `/mnt/skills/public/docx/SKILL.md` |
| Spreadsheets | `/mnt/skills/public/xlsx/SKILL.md` |
| Presentations | `/mnt/skills/public/pptx/SKILL.md` |
| PDFs | `/mnt/skills/public/pdf/SKILL.md` |
| Frontend/UI | `/mnt/skills/public/frontend-design/SKILL.md` |
| **SkyyRose brand** | `/mnt/skills/user/skyyrose-brand-dna/SKILL.md` |
| **WordPress/WooCommerce** | `/mnt/skills/user/wordpress-woocommerce-automation/SKILL.md` |
| **Agent building** | `/mnt/skills/user/devskyy-agent-builder/SKILL.md` |
| **MCP debugging** | `/mnt/skills/user/mcp-server-debugger/SKILL.md` |
| **RAG optimization** | `/mnt/skills/user/rag-query-rewriter/SKILL.md` |
| **Production checks** | `/mnt/skills/user/production-readiness-checker/SKILL.md` |
| Conversation analysis | `/mnt/skills/user/conversation-reflection/SKILL.md` |

---

## 📁 CODEBASE

```
main_enterprise.py        # FastAPI (47+ endpoints)
devskyy_mcp.py            # MCP server (13 tools)
runtime/tools.py          # ToolSpec, ToolRegistry, ToolCallContext
agents/                   # 6 SuperAgents + base (17 techniques)
  base_super_agent.py     # plan→retrieve→execute→validate→emit
llm/                      # 6 providers, router, round_table, ab_testing
orchestration/            # tool_registry, vector_store, brand_context
security/                 # AES-256-GCM, JWT, audit_log
services/elementor/       # BrandKit theme builder
services/three_d/         # Tripo3D, FASHN (95% fidelity)
api/v1/                   # REST, gdpr, webhooks
tests/                    # 1200+ tests
```

---

## 💻 COMMANDS

```bash
pip install -e ".[dev]"              # Install
pytest -v                            # TEST (AFTER EVERY CHANGE!)
pytest tests/test_X.py -v            # Single module
pytest --cov=. --cov-report=html     # Coverage (>90%)
isort . && ruff check --fix && black . # Format
mypy . --strict                      # Types
pip-audit && bandit -r .             # Security
python devskyy_mcp.py --mcp-debug    # MCP server
uvicorn main_enterprise:app --reload # Dev server
```

---

## 🎯 RULES

| Rule | Action |
|------|--------|
| Correctness > Elegance > Performance | Explicit, no magic |
| No deletions | Refactor only |
| Truthful | README = reality |
| Deterministic agents | Trace all actions |
| Contracts | Pydantic in, typed out |
| Interface change | Update ALL sites+tests+docs |

---

## 📝 PATTERNS

```python
# ✅ GOOD
class DevSkyError(Exception): pass
class ToolError(DevSkyError):
    def __init__(self, tool: str, reason: str, *, correlation_id: str | None = None):
        self.correlation_id = correlation_id
        super().__init__(f"{tool}: {reason}")

async def process(data: InputModel, *, correlation_id: str | None = None) -> OutputModel:
    """Docstring with Args, Returns, Raises."""
    return OutputModel(result=InputModel.model_validate(data).value)

# ❌ BAD
raise Exception("error")           # Generic
return "simulated"                 # Placeholder
def f(x: list = []): pass          # Mutable default
try: ... except: pass              # Bare except
```

---

## 🧪 TESTING (CRITICAL)

```bash
# ⚠️ AFTER EVERY FILE CHANGE:
pytest tests/ -v --tb=short

# Current: Fix these 19 failures
# DB(10) MCP(2) reranker(2) WP(3) API(1) env(1)
```

**Test Pattern:**
```python
@pytest.mark.asyncio
async def test_feature(fixture: Type) -> None:
    """Feature should do X when Y."""
    result = await function(input)
    assert result.success is True
```

---

## 🔐 SECURITY

| Component | Implementation |
|-----------|----------------|
| Crypto | AES-256-GCM: `encrypt(str\|bytes\|dict)` → `decrypt()` |
| Auth | JWT + refresh, OAuth2, TOTP |
| GDPR | `/api/v1/gdpr/{export,delete,retention-policy}` |
| Audit | All changes logged with correlation_id |
| Secrets | `.env` local, AWS Secrets Manager prod |

---

## 🎨 BRAND

```python
SKYYROSE = {"name": "SkyyRose", "tagline": "Where Love Meets Luxury",
            "colors": {"primary": "#B76E79", "secondary": "#1A1A1A"},
            "style": ["luxury", "sophisticated", "bold", "Oakland"]}
```

**BrandKit**: NO hardcoded values. Use `BrandKit.from_config()` for theme generation.

---

## ⚡ TOKEN EFFICIENCY

```bash
# ❌ WASTEFUL              # ✅ EFFICIENT
cat large.py              → head -50 && tail -50
git diff                  → git diff --stat (then targeted)
grep -r "x" .             → grep -r "x" src/ -l
```

**MCP**: `defer_loading=True` for low-frequency tools (saves ~60K tokens)

---

## ⚠️ GOTCHAS

- **WP.com API**: `index.php?rest_route=` NOT `/wp-json/`
- **Themes**: Cannot upload via REST - use admin
- **3D CDNs**: VERIFY URLs exist before implementation
- **Correlation IDs**: ALWAYS propagate through async

---

## ❌→✅

| Don't | Do |
|-------|-----|
| Code before Context7 | Research first |
| Skip pytest | Test EVERY edit |
| Generic exceptions | Typed errors |
| Placeholders | Real code |
| Mutable defaults | `default_factory` |
| Ignore failures | Fix or document |

---

## 📊 HEALTH

`/health` `/health/ready` `/health/live` `/metrics` (Prometheus)

---

## 📚 DOCS

`docs/architecture/DEVSKYY_MASTER_PLAN.md` | `docs/MCP_*.md` | `docs/ZERO_TRUST_ARCHITECTURE.md`

---

## 🎯 SPRINT

1. Fix tests (19→0) 2. Security 3. ToolRuntime 4. Agents 5. MCP 6. 3D 7. Docs

**Done**: pytest✓ | crypto str/bytes/dict✓ | ToolRegistry✓ | Zero TODOs✓

---

**v1.2.0** | damBruh (SkyyRose LLC) | Production Hardening | 2026-01-17
