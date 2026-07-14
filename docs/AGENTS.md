# DevSkyy Agent Orchestration

> Practical guide (when to use agents) + Architecture reference (how agents work).
> Merged from active workflow doc and v5.1.0 architecture spec.

---

## Part 1 — When to Use Agents

Use agents **proactively** — don't wait to be asked. The rules:

1. **Code just written/modified** → `code-reviewer` (always)
2. **Complex feature request** → `planner` first, then execute
3. **Bug report** → fix it autonomously, then `security-reviewer` if it touched auth/input
4. **Build fails** → `build-error-resolver`
5. **Dead code suspected** → `refactor-cleaner`
6. **Before deploy** → `deploy-and-verify`
7. **After deploy** → screenshot all pages with Chrome DevTools MCP

### Project Agents (`.claude/agents/`)

#### Core Workflow
| Agent | Model | When | What It Does |
|-------|-------|------|-------------|
| `planner` | opus | Before any 3+ step task | Creates step-by-step plan, identifies risks, waits for approval |
| `architect` | opus | Architectural decisions, new systems | Designs system structure, evaluates trade-offs |
| `code-reviewer` | sonnet | After EVERY code change | Reviews quality, security, maintainability — mandatory |
| `security-reviewer` | sonnet | Auth, user input, API endpoints, secrets | Flags OWASP Top 10, injection, XSS, leaked secrets |
| `tdd-guide` | opus | New features, bug fixes | Enforces RED→GREEN→IMPROVE, 85%+ coverage |

#### Build & Deploy
| Agent | Model | When | What It Does |
|-------|-------|------|-------------|
| `build-error-resolver` | sonnet | Build fails, type errors | Minimal diffs to get build green — no architectural edits |
| `deploy-and-verify` | sonnet | Before production deploy | Runs PHP lint → deploy → cache flush → screenshot all pages |
| `e2e-runner` | sonnet | Critical user flows | Playwright E2E tests, screenshots, traces |

#### Cleanup & Docs
| Agent | Model | When | What It Does |
|-------|-------|------|-------------|
| `refactor-cleaner` | sonnet | Dead code, duplicates, bloat | Runs analysis tools, safely removes unused code |
| `wp-code-simplifier` | haiku | After WordPress theme edits | Reviews WP code for dead refs, duplicates, XSS, bloat |
| `doc-updater` | haiku | After significant changes | Updates codemaps, READMEs, docs |

#### Language-Specific
| Agent | Model | When | What It Does |
|-------|-------|------|-------------|
| `python-reviewer` | sonnet | Any Python code change | PEP 8, type hints, security, performance |
| `database-reviewer` | sonnet | SQL, migrations, schemas | Query optimization, schema design, security |

#### Operations
| Agent | Model | When | What It Does |
|-------|-------|------|-------------|
| `loop-operator` | sonnet | Long-running autonomous tasks | Monitors agent loops, intervenes when stalled |

### Parallel Agent Strategy

**ALWAYS run independent agents in parallel.** One message, multiple Agent tool calls.

```
GOOD: 3 agents in parallel
  Agent 1: security-reviewer on auth module
  Agent 2: code-reviewer on API changes
  Agent 3: python-reviewer on ML pipeline

BAD: Sequential when independent
  First agent 1... wait... then agent 2... wait... then agent 3
```

### Agent Selection by Workspace
| Workspace | Primary Agents | Review Agent |
|-----------|---------------|--------------|
| **Python API** (`/`) | planner, tdd-guide, build-error-resolver | python-reviewer |
| **Dashboard** (`frontend/`) | planner, e2e-runner | code-reviewer |
| **WordPress** (`wordpress-theme/`) | deploy-and-verify, wp-code-simplifier | code-reviewer |
| **Database** (`database/`) | planner | database-reviewer |

### WordPress Theme Deploy Pipeline

The standard deploy sequence for SkyyRose:

```
1. planner          → Plan the changes
2. (implement)      → Write the code
3. code-reviewer    → Review changes
4. wp-code-simplifier → WordPress-specific review
5. security-reviewer → If touched auth/input/WC
6. deploy-and-verify → PHP lint + deploy + screenshots
7. (verify)         → Chrome DevTools MCP screenshots
```

### Model Routing
| Complexity | Model | Agents |
|-----------|-------|--------|
| Deep reasoning, architecture | **Opus** | planner, architect, tdd-guide |
| Code work, reviews, builds | **Sonnet** | code-reviewer, security-reviewer, build-error-resolver, e2e-runner |
| Lightweight docs, quick checks | **Haiku** | doc-updater, wp-code-simplifier |

---

## Part 2 — Runtime Agent Architecture

### Agent Mandate

Every agent action MUST be:
- **Traced** — correlation IDs propagated through entire chain
- **Validated** — outputs match expected Pydantic schemas
- **Tested** — unit + integration coverage
- **Idempotent** — same inputs produce same outputs; retries are safe

**Forbidden:** placeholder returns, "simulated" responses, TODO stubs, direct API calls bypassing ToolRegistry.

### Mandatory Workflow

```
PLAN → RETRIEVE → EXECUTE → VALIDATE → EMIT
```

```python
class BaseAgent:
    async def execute_task(self, task: AgentTask, context: AgentContext) -> AgentResult:
        plan = await self.plan(task, context)                         # 1. PLAN
        data = await self.retrieve(plan, context)                     # 2. RETRIEVE (RAG-ready)
        results = await self.execute_tools(plan.tool_calls, data)     # 3. EXECUTE
        validated = await self.validate(results, plan.expected_schema)  # 4. VALIDATE
        return self.emit(validated, context)                          # 5. EMIT
```

### Super Agents (6)

| Agent | Domain | Tools | Priority |
|-------|--------|-------|----------|
| **CommerceAgent** | Products, inventory, pricing | `product_search`, `order_management` | HIGH |
| **CreativeAgent** | 3D generation, visuals | `3d_generate`, `brand_context` | HIGH |
| **MarketingAgent** | Campaigns, SEO, social | `analytics_query`, `rag_query` | MED |
| **SupportAgent** | Customer interactions | `rag_query`, `order_management` | MED |
| **OperationsAgent** | WordPress, infrastructure | `wordpress_sync`, `cache_ops` | HIGH |
| **AnalyticsAgent** | ML predictions, insights | `analytics_query`, `llm_route` | MED |

### Tool Registration

```python
from devskyy.runtime.tools import tool, ToolSpec, ToolRegistry

@tool(
    name="create_product",
    description="Create WooCommerce product",
    permissions=["wordpress:write"],
    timeout_seconds=30,
    retries=3,
    idempotency_key_fields=["sku"],
    defer_loading=False,  # High-frequency
)
async def create_product(data: ProductCreate) -> ProductResponse:
    ...
```

### 17 Techniques Implemented

| # | Technique | Implementation |
|---|-----------|----------------|
| 1 | Tool Use | ToolRegistry |
| 2 | RAG | Vector store + reranking |
| 3 | Planning | Plan → Execute → Validate |
| 4 | Delegation | `delegate_to_subagent()` |
| 5 | Reflection | Output validation loops |
| 6 | Memory | Context persistence |
| 7 | Multi-model | LLM router |
| 8 | Structured Output | Pydantic schemas |
| 9 | Error Recovery | Typed exceptions |
| 10 | Idempotency | Hash deduplication |
| 11 | Observability | Correlation IDs |
| 12 | Caching | Redis TTL |
| 13 | Rate Limiting | Token bucket |
| 14 | A/B Testing | Experiments |
| 15 | Round Table | Multi-agent consensus |
| 16 | Brand Context | SkyyRose DNA |
| 17 | Fashion Intelligence | Domain rules |

### Fashion Domain Rules

```python
class FashionRules:
    PDP_IMAGE_HIERARCHY = ["hero", "detail", "lifestyle", "flat_lay"]
    COLLECTION_GRID = {"columns": 4, "aspect_ratio": "3:4"}
    TYPOGRAPHY = {"h1": "Archivo 700", "body": "Hanken Grotesk 400"}
    LUXURY_SPACING = {"section": "120px", "element": "24px"}
```

### Code Patterns

**CORRECT — All tools via ToolRegistry, correlation IDs, validated responses:**
```python
class CommerceAgent(BaseAgent):
    async def create_product(
        self, data: ProductCreate, *, correlation_id: str | None = None
    ) -> ProductResponse:
        correlation_id = correlation_id or generate_correlation_id()
        result = await self.registry.execute(
            "create_product", data.model_dump(),
            context=ToolCallContext(
                correlation_id=correlation_id,
                permissions=["wordpress:write"]
            )
        )
        return ProductResponse.model_validate(result)
```

**WRONG — Direct API calls, unvalidated responses:**
```python
async def create_product(self, data):
    response = await self.wc_client.post("/products", data)  # Direct API!
    return response  # Unvalidated!
```

### Testing Pattern

```python
@pytest.mark.asyncio
async def test_commerce_agent_creates_product(commerce_agent, mock_registry):
    data = ProductCreate(name="Test", sku="TEST-001", price=Decimal("99.99"))
    result = await commerce_agent.create_product(data)
    assert result.success is True
    mock_registry.execute.assert_called_once()
```

### File Structure

```
agents/
├── __init__.py
├── base_super_agent/        # BaseAgent workflow (PLAN→RETRIEVE→EXECUTE→VALIDATE→EMIT)
├── claude_sdk/              # Claude Agent SDK domain agents
├── core/                    # Commerce, Creative, Marketing, Support, Operations, Analytics
├── elite_web_builder/       # WordPress page generation
├── llm_roundtable/          # Multi-agent consensus
├── product_generation/      # 3D model + image generation
├── visual_generation/       # Scene composition
├── wordpress_bridge/        # WordPress API integration
└── wordpress_theme_builder/ # Theme PHP generation
```

---

**Last updated:** 2026-04-05 | Merged from active + v5.1.0 architecture docs
