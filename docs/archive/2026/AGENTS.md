> SUPERSEDED 2026-07-10/11 — fonts now per SOT.md → typography.json (Archivo / Hanken Grotesk / Anton / Cinzel + bespoke collection name-scripts; zero-CDN self-hosted woff2). Font/CDN references below are historical.

# DevSkyy Agent Architecture

> 54 Specialized Agents | 6 Super Agents | Production-Grade Orchestration

---

## 🎯 AGENT MANDATE

```
⚠️  Every agent action MUST be: traced, validated, tested, idempotent
⚠️  NO placeholder returns ("simulated", "TODO", stubs)
⚠️  ALL tools called through ToolRegistry
⚠️  Correlation IDs propagated through entire chain
```

---

## 🏗️ WORKFLOW (Mandatory)

```
PLAN → RETRIEVE → EXECUTE → VALIDATE → EMIT
```

```python
class BaseAgent:
    async def execute_task(self, task: AgentTask, context: AgentContext) -> AgentResult:
        plan = await self.plan(task, context)           # 1. PLAN
        data = await self.retrieve(plan, context)       # 2. RETRIEVE (RAG-ready)
        results = await self.execute_tools(plan.tool_calls, data)  # 3. EXECUTE
        validated = await self.validate(results, plan.expected_schema)  # 4. VALIDATE
        return self.emit(validated, context)            # 5. EMIT
```

---

## 🤖 SUPER AGENTS (6)

| Agent | Domain | Tools | Priority |
|-------|--------|-------|----------|
| **CommerceAgent** | Products, inventory, pricing | `product_search`, `order_management` | 🔴 HIGH |
| **CreativeAgent** | 3D generation, visuals | `3d_generate`, `brand_context` | 🔴 HIGH |
| **MarketingAgent** | Campaigns, SEO, social | `analytics_query`, `rag_query` | 🟡 MED |
| **SupportAgent** | Customer interactions | `rag_query`, `order_management` | 🟡 MED |
| **OperationsAgent** | WordPress, infrastructure | `wordpress_sync`, `cache_ops` | 🔴 HIGH |
| **AnalyticsAgent** | ML predictions, insights | `analytics_query`, `llm_route` | 🟡 MED |

---

## 🛠️ TOOL REGISTRATION

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

---

## 📊 17 TECHNIQUES

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

---

## 🎨 FASHION DOMAIN RULES

```python
class FashionRules:
    PDP_IMAGE_HIERARCHY = ["hero", "detail", "lifestyle", "flat_lay"]
    COLLECTION_GRID = {"columns": 4, "aspect_ratio": "3:4"}
    TYPOGRAPHY = {"h1": "Playfair Display 700", "body": "Inter 400"}
    LUXURY_SPACING = {"section": "120px", "element": "24px"}
```

---

## ⚡ PATTERNS

### ✅ CORRECT
```python
class CommerceAgent(BaseAgent):
    async def create_product(self, data: ProductCreate, *, correlation_id: str | None = None) -> ProductResponse:
        correlation_id = correlation_id or generate_correlation_id()
        result = await self.registry.execute(
            "create_product", data.model_dump(),
            context=ToolCallContext(correlation_id=correlation_id, permissions=["wordpress:write"])
        )
        return ProductResponse.model_validate(result)
```

### ❌ WRONG
```python
async def create_product(self, data):
    response = await self.wc_client.post("/products", data)  # Direct API!
    return response  # Unvalidated!
```

---

## 🧪 TESTING

```python
@pytest.mark.asyncio
async def test_commerce_agent_creates_product(commerce_agent, mock_registry):
    data = ProductCreate(name="Test", sku="TEST-001", price=Decimal("99.99"))
    result = await commerce_agent.create_product(data)
    assert result.success is True
    mock_registry.execute.assert_called_once()
```

---

## 📁 STRUCTURE

```
agents/
├── __init__.py
├── base_super_agent.py    # BaseAgent workflow
├── commerce.py            # Products, inventory
├── creative.py            # 3D, visuals
├── marketing.py           # Campaigns, SEO
├── support.py             # Customer service
├── operations.py          # WordPress, infra
├── analytics.py           # ML, insights
└── CLAUDE.md              # This file
```

---

**v5.1.0** | 54 Agents | Production-Ready | 2026-01-17
