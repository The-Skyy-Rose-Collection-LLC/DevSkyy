# DevSkyy - Claude Code Configuration

> **Principal Engineer Instructions for Production-Grade Enterprise AI Platform**

## 🌟 Global Rules

**Mission**: 100% production-quality code — no hacks, no stubs, no TODOs. Real integration tests only.

**Core Behaviors**:
- Full ownership: complete tasks without premature exits
- Proactive: ask focused questions only when blocked
- Engineering cycle: understand → design → implement → test → document
- Propose better alternatives when user's approach is suboptimal
- Code quality check after EVERY file
- **MANDATORY**: Context7 for library docs, Serena for codebase navigation

---

## 🧠 Tool Calling Workflow (MANDATORY)

**4-Phase Sequence for ALL coding tasks:**

**Phases**:
1. **Research** (Context7 BEFORE code): resolve-library-id → query-docs → analyze patterns
2. **Navigate** (Serena only): find_symbol / read_file / search_for_pattern / get_symbols_overview
3. **Implement** (Serena only): replace_content (prefer regex mode) / create_text_file (rare)
4. **Validate** (Serena): think_about_collected_information → execute_shell_command → think_about_whether_you_are_done

**Anti-Patterns**: ❌ Code before Context7 ❌ Read/Write instead of Serena ❌ Skip reflection steps

---

## 🎯 Mission & Rules

**Mission**: DevSkyy B+ (52/100) → A+ (90+/100) via security, API versioning, GDPR, deployment readiness. Zero stubs/TODOs.

**Absolute Rules**:
1. **Priority**: Correctness > Elegance > Performance (no magic, explicit behavior)
2. **No Deletions**: Refactor YES, remove capabilities NO (agents/MCP/RAG/3D/security/WordPress)
3. **Truthful**: README/version/license = reality; production = tests + CI
4. **Deterministic**: All agent actions traceable/validated/testable
5. **Explicit Contracts**: Pydantic validation, typed outputs, classified errors, documented side effects
6. **Interface Changes**: Update ALL call sites + tests + docs

---

## 🏗️ Repository Structure

**Quick Reference** (full details in `docs/architecture/DEVSKYY_MASTER_PLAN.md`):

```
├── 🎯 Core: main_enterprise.py (FastAPI), devskyy_mcp.py (MCP server)
├── 🤖 agents/: 54 agents (6 super, 48 specialized) + base_super_agent.py (17 techniques)
├── 🧠 llm/: 6 providers + router + round_table + ab_testing + tournament
├── 🎭 orchestration/: llm_orchestrator + tool_registry + prompt_engineering + vector_store
├── ⚙️  runtime/tools.py: ToolSpec, ToolRegistry, ToolCallContext
├── 🔌 adk/: PydanticAI, Google ADK, CrewAI, AutoGen, Agno adapters
├── 🔒 security/: AES-256-GCM, JWT, PII, rate limiting, SSRF, audit, zero-trust
├── 🌐 api/: index, agents, gdpr, webhooks, versioning
├── 🛠️ mcp/: openai, agent_bridge, rag, woocommerce servers
├── 📝 wordpress/: REST API client + AR viewer
├── ✅ tests/: 1,063 tests (9 skipped, documented)
├── 🎨 frontend/: Next.js 15 dashboard
├── 💎 src/collections/: 5 Three.js experiences
└── 📚 docs/: Architecture, API, security runbooks
```

---

## 🏛️ Architecture

### Super Agents
6 agents (Commerce, Creative, Marketing, Support, Operations, Analytics) + `base_super_agent.py` (17 prompt techniques, auto-selection, LLM Round Table)

### LLM Layer
6 providers (OpenAI, Anthropic, Google, Mistral, Cohere, Groq) → router (task-based) → round_table (competition) → ab_testing (significance) → tournament (consensus)

### Key Patterns
- **Tool Execution**: `runtime/tools.py` registry → `await agent.use_tool(name, params)`
- **LLM Round Table**: All 6 parallel → score → top 2 A/B test → winner (PostgreSQL)
- **Prompt Technique**: Auto-select (reasoning→CoT, classification→few-shot, creative→ToT, search→ReAct, qa→RAG)
- **Database**: Neon PostgreSQL (serverless), Chroma/Pinecone (vectors), Redis (cache)
- **Deployment**: Vercel (serverless) + Docker (traditional)
- **Brand DNA**: SkyyRose context injected (`{"name": "SkyyRose", "colors": {"primary": "#B76E79"}, "style": ["luxury", "sophisticated"]}`)

---

## 🌍 Environment & Secrets

**Setup**: `cp .env.example .env` then configure

**Critical Variables**:
```bash
# Security (REQUIRED)
JWT_SECRET_KEY=     # python -c "import secrets; print(secrets.token_urlsafe(64))"
ENCRYPTION_MASTER_KEY=  # python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
DATABASE_URL=postgresql+asyncpg://user:pass@host/devskyy  # Use PostgreSQL in prod  # pragma: allowlist secret

# LLM (≥1 required): OPENAI, ANTHROPIC, GOOGLE_AI, MISTRAL, COHERE, GROQ
# 3D/Visual: TRIPO_API_KEY, FASHN_API_KEY
# WordPress: WORDPRESS_URL, WORDPRESS_APP_PASSWORD, WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET
# Cache: REDIS_URL=redis://localhost:6379/0
```

**Secrets Management**: Local (`.env`), Prod (AWS Secrets Manager/Vercel), never hardcode, rotate 90d, audit access

---

## 🛠️ Commands

**Dev**: `pip install -e .` → `isort . && ruff check . --fix && black .` → `mypy .` → `pytest -v` → `pip-audit && bandit -r .`
**Test**: `pytest --cov=. --cov-report=html` / `pytest tests/test_agents.py::test_tool_runtime -v` / `pytest -m "not slow"`
**MCP**: `python devskyy_mcp.py [--mcp-debug]` / `python -c "from devskyy_mcp import mcp; print(mcp.list_tools())"`
**TypeScript**: `npm run build/dev/test/lint/lint:fix/type-check/security:audit`
**3D Demos**: `npm run demo:{black-rose,signature,love-hurts,showroom,runway}`
**Makefile**: `make {help,dev,lint-all,format-all,test-all,ci,clean,docker-build}`

---

## 📋 Code Style

**Python**: Type hints everywhere, Pydantic > dicts, no mutable defaults, async/await for I/O, Google-style docstrings

**Patterns**:
```python
# ✅ Good: Explicit error taxonomy
class DevSkyError(Exception): pass
class ToolExecutionError(DevSkyError):
    def __init__(self, tool_name: str, reason: str):
        super().__init__(f"Tool {tool_name} failed: {reason}")

# ❌ Bad: Generic exceptions, placeholder strings, mutable defaults
raise Exception("error")  # ❌
return "Agent execution simulated"  # ❌
def foo(items: list = []): pass  # ❌
```

---

## 🔍 Testing

**TDD**: Tests FIRST → confirm fail → implement → iterate → commit separately

**Pattern**: Fixtures + async tests + ToolRegistry validation (see `tests/test_agents.py`)

---

## 🎨 WordPress & 🤖 Agents

**WordPress Pattern**: BrandKit abstraction (`BrandKit.from_yaml`) → PageSpec → generate → validate → import → assign
**Agent Pattern**: Plan → Retrieve (RAG) → Execute (ToolRegistry) → Validate (schema) → Emit (structured)
**Tool Runtime**: ToolRegistry + ToolSpec + ToolCallContext (`runtime/tools.py`)
**Tool Classification**:
- **Categories**: CONTENT, COMMERCE, MEDIA, COMMUNICATION, ANALYTICS, INTEGRATION, SYSTEM, AI, OPERATIONS, SECURITY
- **Severity**: READ_ONLY, LOW, MEDIUM, HIGH, DESTRUCTIVE
```

---

## 🔐 Security & 📦 3D Pipeline

**Crypto**: AES-256-GCM supports str/bytes/dict (JSON stable serialization) → `encrypt()` / `decrypt()` / `decrypt_bytes()`
**GDPR**: `/api/v1/gdpr/{export,delete,retention-policy}` (Articles 15, 17, 13)
**3D Pipeline**: `generate(prompt, retries=3, idempotency_key)` → validate (polycount/texture) → WP upload → WooCommerce attach
```

---

## 🚀 Deployment

**Production URLs**: Frontend (`app.devskyy.app`), API (`api.devskyy.app`), Docs (`api.devskyy.app/docs`)

**Pre-Commit**: formatters → mypy → pytest → security audit → update docs → no TODOs

**Vercel** (serverless): `vercel.json` (`rootDirectory: "frontend"`, 60s timeout, 50MB max) → `vercel --prod` | **Limitations**: cold starts ~2-3s, stateless (S3/R2)
**Docker** (traditional): `make docker-build` → `docker-compose up -d` → `docker-compose logs -f api`
**CI/CD**: `.github/workflows/ci.yml` (checkout → Python 3.11 → install → lint/type/security/test → codecov)

---

## 📝 Commits & 📊 Monitoring

**Commit Format**: `<type>(<scope>): <subject>` (types: feat/fix/docs/style/refactor/perf/test/chore)

**Prometheus** (`/metrics`): `http_requests_total`, `http_request_duration_seconds`, `agent_executions_total`, `agent_execution_duration_seconds`, `tool_calls_total`, `llm_requests_total`, `llm_tokens_total`, `cache_hits/misses_total`
**Queries**: `rate(http_requests_total[1m])` / `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`

**Logging**: structlog (JSON), levels (DEBUG/INFO/WARNING/ERROR/CRITICAL), correlation IDs
**Security Audit**: `security/audit_log.py` (auth attempts, authz, secrets, GDPR exports, config changes)
**Health**: `/health` (basic), `/health/ready` (DB/Redis), `/health/live` (minimal)

---

## 🎓 Resources & ⚠️ Pitfalls

**Fashion**: PDP vs Collection layouts, image hierarchy (hero→lifestyle→detail), typography (display→heading→body), size algorithms, color psychology
**ML/AI**: Model registry, distributed caching (Redis+memory), SHAP explainability, A/B testing, continuous retraining
**WordPress**: REST auth, MIME types, Shoptimizer 2.9.0, Elementor Pro 3.32.2, WooCommerce variants

**DON'T**: ❌ Placeholders ❌ Mutable defaults ❌ Ignore tests ❌ Hand-wave validation ❌ Premature optimization ❌ Commit secrets ❌ Skip docs
**DO**: ✅ TDD ✅ Type hints ✅ Pydantic validation ✅ Structured objects ✅ Correlation IDs ✅ Update all files ✅ Run formatters

---

## 🔄 Workflow

1. **Explore**: Read files, analyze (NO code yet)
2. **Plan**: Extended thinking on architecture/migration/tests/compatibility → detailed plan
3. **Code**: TDD (tests → fail → implement → pass → commit separately)
4. **Commit**: Descriptive message → PR (summary, breaking changes, testing)

---

## 🎯 Sprint & 💡 Tips

**Priorities** (7d): Test suite → fix security/crypto → packaging → mutable defaults → Tool Runtime → refactor agents/MCP → harden Elementor/3D → docs/CI
**Success**: pytest ✓, crypto str/bytes/dict ✓, Tool Runtime ✓, ToolRegistry ✓, Elementor validation ✓, 3D retry/validation ✓, CI ✓, zero TODOs ✓

**Tips**: Subagents for verification, ESC to redirect, `/clear` between tasks, checklists for complex migrations

---

## 📞 Contacts & 📚 Docs

**Contacts**: damBruh (SkyyRose LLC), support@skyyrose.com, GitHub issues (bugs/features), security@skyyrose.com (private)
**Docs**: `docs/{architecture/DEVSKYY_MASTER_PLAN,MCP_ARCHITECTURE,MCP_CONFIGURATION_GUIDE,MCP_QUICK_REFERENCE,ZERO_TRUST_ARCHITECTURE,LLM_CLIENTS_QUICK_START,api/ECOMMERCE_API,javascript-typescript-sdk,runbooks/,IMPLEMENTATION_PLAN,SECRETS_MIGRATION}.md`

---

**Version**: 1.0.0 | **Status**: Production Hardening | **Last Updated**: 2026-01-07

**Owner**: damBruh (SkyyRose LLC) | **Email**: <support@skyyrose.com> | **Security**: <security@skyyrose.com>

---

## REMEMBER

- NOT a demo - production-ready only
- Correctness > Elegance > Performance
- No stubs, no placeholders, no TODOs
- TDD mandatory
- Update this file as patterns emerge
