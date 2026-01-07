# DevSkyy - Claude Code Configuration

> Principal Engineer Instructions for Production-Grade Enterprise AI Platform

---

## ⚠️ MANDATORY WORKFLOW - READ FIRST

**EVERY CODE CHANGE MUST FOLLOW THIS:**

1. **Context7 FIRST** - Query Context7 MCP for documentation BEFORE writing ANY code
   - `mcp__plugin_context7_context7__resolve-library-id` → library lookup
   - `mcp__plugin_context7_context7__query-docs` → get current best practices
   - NO exceptions - even for "simple" changes

2. **Ralph-Wiggums ERROR LOOP** - Wrap ALL I/O operations in `ralph_wiggums_execute`
   - File operations, API calls, Database queries, Git operations, External tools
   - See `utils/ralph_wiggums.py` for examples

3. **Serena MCP INTEGRATION** - Use Serena symbolic tools for code changes
   - `mcp__plugin_serena_serena__find_symbol` for code discovery
   - `mcp__plugin_serena_serena__replace_symbol_body` for edits
   - Read `.serena/memories/` before starting work

**If you violate these rules, STOP and restart using the correct approach.**

---

## 🎯 Mission

Transform DevSkyy B+ (52/100) → A+ (90+) via: Security hardening, API versioning,
GDPR compliance, production deployment, elimination of ALL stubs/placeholders.

**CRITICAL**: NOT a demo. Every implementation must be production-ready, fully tested, with explicit contracts.

---

## 🔒 ABSOLUTE RULES

1. **Correctness > Elegance > Performance** - Resolve ambiguity explicitly, no magic
2. **No Feature Deletions** - Refactor/harden only, never remove capabilities
3. **Truthful Codebase** - README/versioning must reflect reality, tests + CI required
4. **Deterministic Agents** - No silent fallbacks, every action traceable/validated
5. **Explicit Contracts** - Inputs validated (Pydantic), outputs typed, errors classified
6. **Interface Changes** - Update ALL call sites, tests, document breaks

---

## 🔌 Context7 MCP Plugin

**MANDATORY**: When generating code for DevSkyy, **ALWAYS** use the Context7 MCP Plugin to ensure:

- **Up-to-date documentation**: Retrieve the latest codebase patterns, conventions, and examples
- **Accurate references**: Access current API endpoints, tool schemas, and agent capabilities
- **Consistent patterns**: Follow established architectural decisions and coding standards
- **Real-time context**: Pull from `docs/`, `README.md`, and source files for current state

**Auto-invoke Context7 for**:

- Code generation tasks
- Architecture decisions
- API endpoint implementations
- Agent integrations
- Tool registry modifications
- Security implementations

**Configuration**: See `docs/guides/CLAUDE.md` for Context7 integration details and `MCP_CONFIGURATION.md` for setup.

---

## 🏗️ Repository Structure

```text
DevSkyy/
├── devskyy_mcp.py          # Main MCP server (13 tools)
├── main_enterprise.py      # FastAPI application
├── agents/                 # 6 SuperAgents (Commerce, Creative, Marketing, Support, Operations, Analytics)
│   ├── base_super_agent.py # 17 prompt techniques, ML capabilities
│   ├── tripo_agent.py      # 3D generation (Tripo3D)
│   └── visual_generation.py # Imagen, Veo, FLUX
├── llm/                    # 6 Providers: OpenAI, Anthropic, Google, Mistral, Cohere, Groq
│   ├── router.py           # Task-based routing
│   ├── round_table.py      # Multi-LLM competition
│   └── ab_testing.py       # Statistical significance
├── orchestration/          # Coordination layer
│   ├── tool_registry.py    # Schema validation
│   ├── vector_store.py     # Chroma/Pinecone RAG
│   └── brand_context.py    # SkyyRose brand DNA
├── runtime/tools.py        # ToolSpec, ToolRegistry, ToolCallContext
├── security/               # AES-256-GCM, JWT/OAuth2, PII, SSRF, rate limiting
├── mcp/                    # RAG server, WooCommerce MCP, OpenAI compatibility
├── api/                    # REST endpoints, GDPR compliance
├── adk/                    # Framework adapters (PydanticAI, CrewAI, AutoGen)
├── frontend/               # Next.js 15 dashboard
├── src/collections/        # 5 Three.js experiences
└── tests/                  # Pytest suite
```

---

## 🏛️ Architecture

### SuperAgents

All inherit `EnhancedSuperAgent`: 17 prompt techniques, ML module, self-learning, LLM Round Table.

| Agent | Domain | Capabilities |
|-------|--------|--------------|
| Commerce | E-commerce | Products, orders, pricing |
| Creative | Visual | 3D (Tripo3D), images (Imagen/FLUX), try-on (FASHN) |
| Marketing | Content | SEO, social, email |
| Support | Service | Tickets, FAQs, escalation |
| Operations | DevOps | WordPress, deployment |
| Analytics | Data | Reports, forecasting |

### Key Patterns

```python
# Tool execution via registry
result = await agent.use_tool("tool_name", {"param": "value"})

# LLM Round Table: All 6 compete → Top 2 A/B test → Statistical winner

# Auto prompt selection by TaskCategory
# reasoning→CoT, classification→few_shot, creative→ToT, search→ReAct, qa→RAG
```

### Brand Context

```python
SKYYROSE_BRAND_DNA = {
    "name": "SkyyRose", "tagline": "Where Love Meets Luxury",
    "colors": {"primary": "#B76E79", "secondary": "#1A1A1A"},
    "style": ["premium", "sophisticated", "bold", "elegant"]
}
```

---

## 🌍 Environment Variables

```bash
# Security (REQUIRED)
JWT_SECRET_KEY=              # secrets.token_urlsafe(64)
ENCRYPTION_MASTER_KEY=       # base64(secrets.token_bytes(32))
DATABASE_URL=postgresql+asyncpg://...

# LLM Providers (at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_API_KEY=...

# 3D/Visual
TRIPO_API_KEY=...
FASHN_API_KEY=...

# WordPress
WORDPRESS_URL=https://...
WOOCOMMERCE_KEY=ck_...
WOOCOMMERCE_SECRET=cs_...

# Performance
REDIS_URL=redis://localhost:6379/0
```

**Best Practices**: `.env` for local (gitignored), secrets manager for production, rotate every 90 days.

---

## 🛠️ Commands

```bash
# Development
pip install -e .
isort . && ruff check . --fix && black .   # Format (ALWAYS after changes)
mypy .                                       # Type check
pytest tests/ -v                            # Test
pip-audit && bandit -r .                    # Security

# MCP
python devskyy_mcp.py                       # Start server
python devskyy_mcp.py --mcp-debug           # Debug mode

# TypeScript
npm run build && npm run dev && npm run test

# Makefile
make ci                                      # Full pipeline
make docker-build                           # Docker image
```

---

## 📋 Code Style

- **Type hints everywhere**, Pydantic over dicts, no mutable defaults
- **async/await** for I/O, Google-style docstrings
- **Explicit errors**: `class ToolExecutionError(DevSkyError)` not `Exception("failed")`
- **No placeholders**: Real implementation or `raise NotImplementedError`

```python
class ToolSpec(BaseModel):
    name: str = Field(..., description="Tool name")
    schema: Dict[str, Any]
    permissions: List[str] = Field(default_factory=list)
    timeout_ms: int = 5000
```

---

## 🔍 Testing (TDD)

1. Write tests FIRST → 2. Confirm fail → 3. Implement → 4. Pass → 5. Commit separately

```python
@pytest.mark.asyncio
async def test_commerce_agent_uses_tool_runtime(tool_registry):
    agent = CommerceAgent(tool_registry=tool_registry)
    plan = await agent.plan("Create product")
    assert plan.tools_required
    result = await agent.execute(plan)
    assert result.status == "completed"
```

---

## 🤖 Agent Pattern

Each SuperAgent MUST: **Plan** → **Retrieve** (RAG) → **Execute** (ToolRegistry) → **Validate** → **Emit** structured artifacts

```python
class ToolCallContext(BaseModel):
    correlation_id: str
    agent_id: str
    timestamp: datetime

class ToolRegistry:
    def register(self, spec: ToolSpec): ...
    def execute(self, name: str, inputs: Dict, context: ToolCallContext): ...
```

**Tool Categories**: CONTENT, COMMERCE, MEDIA, AI, SYSTEM, SECURITY, INTEGRATION
**Severity Levels**: READ_ONLY, LOW, MEDIUM, HIGH, DESTRUCTIVE

---

## 🔌 MCP & RAG Reference

### MCP Servers

| Server | Purpose |
|--------|---------|
| `devskyy_mcp.py` | Main server - 13 tools for all agents |
| `mcp/rag_server.py` | RAG - semantic search, document ingestion |
| `mcp/woocommerce_mcp.py` | WooCommerce operations |

### Claude Desktop Config

```json
{"mcpServers": {"devskyy": {"command": "python", "args": ["/path/to/devskyy_mcp.py"],
  "env": {"DEVSKYY_API_KEY": "..."}}}}
```

### Main MCP Tools

- `devskyy_scan_code`, `devskyy_fix_code`, `devskyy_generate_wordpress_theme`
- `devskyy_ml_prediction`, `devskyy_manage_products`, `devskyy_dynamic_pricing`
- `devskyy_generate_3d_from_description`, `devskyy_generate_3d_from_image`
- `devskyy_marketing_campaign`, `devskyy_multi_agent_workflow`
- `devskyy_system_monitoring`, `devskyy_list_agents`

### RAG Tools

`rag_query`, `rag_ingest`, `rag_get_context`, `rag_query_rewrite`, `rag_list_sources`, `rag_stats`

**Rewrite Strategies**: zero_shot, few_shot, sub_queries, step_back, hyde

### Tool Schema Pattern

```python
@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
async def my_tool(input: ToolInput) -> str: ...

# Export formats
registry.to_openai_functions()
registry.to_anthropic_tools()
registry.to_mcp_tools()
```

### Vector Store Config

```python
VectorStoreConfig(db_type="chromadb", collection_name="devskyy_docs",
    persist_directory="./data/vectordb", default_top_k=5, similarity_threshold=0.5)
```

---

## 🔐 Security

```python
def encrypt(data: Union[str, bytes, dict]) -> bytes: ...  # AES-256-GCM
def decrypt(ciphertext: bytes) -> str: ...
```

**GDPR**: `GET /api/v1/gdpr/export`, `DELETE /api/v1/gdpr/delete`, `GET /api/v1/gdpr/retention-policy`

---

## 📦 3D Pipeline

```python
class ThreeDAssetPipeline:
    async def generate(self, prompt: str, retries: int = 3) -> ThreeDAsset:
        # Retry logic → Validation (polycount, texture) → WP upload → WooCommerce attach
```

---

## 🚀 Deployment

**Pre-commit**: `isort && ruff --fix && black` → `mypy` → `pytest` → `pip-audit && bandit`

**Vercel**: Frontend only (`frontend/`), backend via `BACKEND_URL` proxy. 60s timeout, 50MB limit.
**Docker**: `make docker-build && docker-compose up -d`

**CI**: Lint → Type check → Security → Test → Coverage

---

## 📝 Commits

```text
<type>(<scope>): <subject>
feat|fix|docs|refactor|test|chore
```

---

## 📊 Monitoring

**Metrics** (`/metrics`): `http_requests_total`, `agent_executions_total`, `tool_calls_total`, `llm_tokens_total`
**Logging**: structlog JSON with correlation_id
**Health**: `/health`, `/health/ready`, `/health/live`

---

## ⚠️ Pitfalls

❌ Placeholder strings, mutable defaults, ignoring tests, committing secrets, skipping docs
✅ TDD, type hints, Pydantic validation, structured outputs, correlation IDs, formatters

---

## 🔄 Workflow

1. **Explore** - Read files, analyze architecture (NO code yet)
2. **Plan** - Think hard, create GitHub issue
3. **Code** - TDD: tests first → fail → implement → pass
4. **Commit** - Descriptive message, PR with summary

---

## 🎯 Sprint Focus

1. Run test suite, enumerate failures
2. Fix security/crypto contracts
3. Implement Tool Runtime Layer
4. Refactor SuperAgents to use ToolRegistry
5. Harden Elementor + 3D pipelines
6. Align docs & CI

**Success**: Zero test failures, crypto handles str/bytes/dict, all agents use registry, zero TODOs.

---

## 📚 Docs Index

- `docs/architecture/DEVSKYY_MASTER_PLAN.md`
- `docs/MCP_ARCHITECTURE.md`, `docs/MCP_QUICK_REFERENCE.md`
- `docs/ZERO_TRUST_ARCHITECTURE.md`
- `docs/api/ECOMMERCE_API.md`
- `docs/runbooks/` (incident response)

---

## 📞 Contacts

**Owner**: damBruh (SkyyRose LLC) | **Email**: <support@skyyrose.com> | **Security**: <security@skyyrose.com>

---

## REMEMBER

- NOT a demo - production-ready only
- Correctness > Elegance > Performance
- No stubs, no placeholders, no TODOs
- TDD mandatory
- Update this file as patterns emerge

**Version**: 1.0.0 | **Status**: Production Hardening
