# MCP Tools Reference

**Version**: 3.1.0
**Last Updated**: 2026-02-08

Complete reference for all MCP (Model Context Protocol) tools available in the DevSkyy platform.

---

## DevSkyy MCP Server

**Location**: `devskyy_mcp.py`
**Total Tools**: 13

| Tool | Category | Description | Usage |
|------|----------|-------------|-------|
| `agent_orchestrator` | Agents | Invoke SuperAgents with multi-agent consensus | Complex reasoning, round-table discussions |
| `rag_query` | Knowledge | Query RAG pipeline for semantic search | Document retrieval, knowledge lookup |
| `rag_ingest` | Knowledge | Ingest documents into RAG system | Add new documentation, update knowledge base |
| `brand_context` | Brand | Access SkyyRose brand DNA and guidelines | Brand-compliant content, design decisions |
| `product_search` | Commerce | Search products across catalog | Product discovery, inventory queries |
| `order_management` | Commerce | Manage orders (create, update, query) | Order processing, status tracking |
| `wordpress_sync` | Integration | Sync data to WordPress/WooCommerce | Content publishing, product updates |
| `3d_generate` | Visual | Generate 3D models from text/images | Asset creation, product visualization |
| `analytics_query` | Analytics | Query platform metrics and analytics | Performance monitoring, usage stats |
| `cache_ops` | Operations | Cache management (get, set, invalidate) | Performance optimization, data freshness |
| `health_check` | Operations | System health monitoring | Service status, dependency checks |
| `tool_catalog` | Meta | List available tools and capabilities | Tool discovery, capability mapping |
| `llm_route` | LLM | Route requests to appropriate LLM provider | Cost optimization, model selection |

---

## External MCP Servers

### Figma

**Purpose**: Design system integration, mockup extraction

| Tool | Description | Usage |
|------|-------------|-------|
| `get_design_context` | Retrieve design specifications and guidelines | Extract design tokens, spacing rules |
| `get_screenshot` | Capture design screenshots | Visual QA, design documentation |
| `get_metadata` | Get file/node metadata | Component discovery, version tracking |
| `get_code_connect_map` | Map designs to code components | Design-code synchronization |

### Notion

**Purpose**: Documentation, knowledge management

| Tool | Description | Usage |
|------|-------------|-------|
| `notion-search` | Search across Notion workspace | Find documentation, meeting notes |
| `notion-fetch` | Retrieve specific pages/databases | Load detailed content |
| `notion-create-pages` | Create new Notion pages | Document creation, meeting notes |
| `notion-update-page` | Update existing pages | Content updates, status changes |

### HuggingFace

**Purpose**: ML models, datasets, research papers

| Tool | Description | Usage |
|------|-------------|-------|
| `model_search` | Search HuggingFace model hub | Find pre-trained models |
| `dataset_search` | Search HuggingFace datasets | Discover training data |
| `paper_search` | Search ML research papers | Research, literature review |
| `hf_doc_search` | Search HuggingFace documentation | API reference, examples |

### WordPress.com

**Purpose**: WordPress site management

| Tool | Description | Usage |
|------|-------------|-------|
| `wpcom-mcp-posts-search` | Search WordPress posts | Content discovery |
| `wpcom-mcp-post-get` | Get specific post details | Content retrieval |
| `wpcom-mcp-site-settings` | Get/update site settings | Configuration management |

### Vercel

**Purpose**: Deployment, hosting

| Tool | Description | Usage |
|------|-------------|-------|
| `deploy_to_vercel` | Deploy application to Vercel | Production deployments |
| `list_deployments` | List deployment history | Deployment tracking |
| `get_deployment_build_logs` | Retrieve build logs | Debugging build failures |

---

## Tool Usage Patterns

### RAG Query Pattern
```python
# Query knowledge base
context = await rag_query(
    query="How do I deploy to WordPress.com?",
    top_k=5
)
```

### Agent Orchestration Pattern
```python
# Multi-agent consensus
result = await agent_orchestrator(
    task="Analyze sales data and recommend pricing",
    agents=["data_analyst", "pricing_specialist", "market_researcher"]
)
```

### 3D Generation Pattern
```python
# Generate 3D model
model = await 3d_generate(
    prompt="Luxury handbag with rose gold hardware",
    style="photorealistic",
    format="glb"
)
```

### WordPress Sync Pattern
```python
# Sync product to WordPress
await wordpress_sync(
    entity_type="product",
    entity_id="prod_123",
    action="update"
)
```

---

## Tool Discovery

To discover available tools at runtime:

```python
# List all available tools
tools = await tool_catalog()
print(f"Available tools: {tools['count']}")
for tool in tools['tools']:
    print(f"- {tool['name']}: {tool['description']}")
```

---

## MCP Server Configuration

MCP servers are configured in:
- Main config: `mcp_servers/.env`
- Tool-specific config: `mcp_servers/config/`

See [ENV_VARS_REFERENCE.md](ENV_VARS_REFERENCE.md) for complete MCP server environment variables.

---

## Troubleshooting

### Tool Not Available
```bash
# Check MCP server is running
curl http://localhost:8002/health

# List available tools
curl http://localhost:8002/tools
```

### Tool Timeout
```bash
# Increase timeout in config
# mcp_servers/.env
REQUEST_TIMEOUT=120  # 2 minutes
```

### Authentication Errors
```bash
# Verify API keys are set
echo $DEVSKYY_API_KEY
echo $HF_TOKEN
echo $ANTHROPIC_API_KEY
```

---

**See Also**:
- [CONTRIB.md](CONTRIB.md) - Development workflow
- [ENV_VARS_REFERENCE.md](ENV_VARS_REFERENCE.md) - Environment variables
- [RUNBOOK.md](RUNBOOK.md) - Operations guide

**Document Owner**: DevSkyy Platform Team
**Next Review**: When new tools are added
