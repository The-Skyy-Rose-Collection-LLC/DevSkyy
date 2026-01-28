---
name: mcp-health
description: MCP server diagnostics and health monitoring.
---

# MCP Health Check

## DevSkyy MCP Servers (4 total)
1. `devskyy_mcp.py` - Main server (13 tools)
2. `mcp/agent_bridge_server.py` - Agent routing
3. `mcp/rag_server.py` - RAG/Knowledge (6 tools)
4. `mcp/woocommerce_mcp.py` - WooCommerce

## Health Status
- 🟢 GREEN: All healthy, production ready
- 🟡 YELLOW: Degraded, some issues
- 🔴 RED: Critical, immediate action

## Key Checks
```bash
pip install mcp fastmcp pydantic    # Core deps
python devskyy_mcp.py --help        # Server test
curl localhost:3000/health          # Health endpoint
```

## Required Environment
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `REDIS_URL`

## MCP Tools Available
- `agent_orchestrator`, `rag_query`, `rag_ingest`
- `brand_context`, `product_search`, `wordpress_sync`
- `3d_generate`, `analytics_query`, `health_check`

## Related Tools
- **MCP**: `health_check` tool for monitoring
- **Skill**: `rag-ingest` for knowledge base
- **Command**: `/mcp-health` for full diagnostics
