# DevSkyy MCP Servers

> MCP 1.0 compliant, tool-first | 12 files

## Architecture
```
mcp_servers/
├── devskyy_mcp.py          # Main server (13 tools)
├── config.py               # Configuration
└── tools/                  # Tool implementations
```

## Tools (13 Total)
| Tool | Category | Description |
|------|----------|-------------|
| agent_orchestrator | Agents | Invoke SuperAgents |
| rag_query | Knowledge | Query RAG pipeline |
| rag_ingest | Knowledge | Ingest documents |
| brand_context | Brand | SkyyRose DNA |
| product_search | Commerce | Search products |
| order_management | Commerce | Manage orders |
| wordpress_sync | Integration | Sync to WordPress |
| 3d_generate | Visual | Generate 3D models |
| analytics_query | Analytics | Query metrics |
| cache_ops | Ops | Cache management |
| health_check | Ops | System health |
| tool_catalog | Meta | List available tools |
| llm_route | LLM | Route LLM requests |

## Pattern
```python
@server.tool()
async def rag_query(query: str, top_k: int = 5) -> dict:
    context = await rag_manager.get_context(query=query, top_k=top_k)
    return context.model_dump()
```

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
- **Skill**: `mcp-health` for diagnostics

**"MCP is the future. We're building it today."**
