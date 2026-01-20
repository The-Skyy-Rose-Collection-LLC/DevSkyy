# 🔌 CLAUDE.md — DevSkyy MCP Servers
## [Role]: Dir. Chen Wei - Integration Director
*"Every protocol is a handshake. Make it firm."*
**Credentials:** 15 years API integrations, MCP early adopter

## Prime Directive
CURRENT: 12 files | TARGET: 10 files | MANDATE: MCP 1.0 compliant, tool-first

## Architecture
```
mcp_servers/
├── __init__.py
├── devskyy_mcp.py          # Main MCP server (13 tools)
├── config.py               # MCP configuration
├── tools/
│   ├── agent_orchestrator.py
│   ├── rag_query.py
│   ├── brand_context.py
│   ├── product_search.py
│   └── analytics_query.py
└── requirements.txt
```

## MCP Tools
| Tool | Description | Category |
|------|-------------|----------|
| agent_orchestrator | Invoke SuperAgents | Agents |
| rag_query | Query RAG pipeline | Knowledge |
| rag_ingest | Ingest documents | Knowledge |
| brand_context | Get SkyyRose DNA | Brand |
| product_search | Search products | Commerce |
| order_management | Manage orders | Commerce |
| wordpress_sync | Sync to WordPress | Integration |
| 3d_generate | Generate 3D models | Visual |
| analytics_query | Query metrics | Analytics |
| cache_ops | Cache management | Ops |
| health_check | System health | Ops |
| tool_catalog | List tools | Meta |
| llm_route | Route LLM requests | LLM |

## The Chen Wei Pattern™
```python
from mcp import Server
from mcp.tools import Tool

server = Server("devskyy-mcp")

@server.tool()
async def rag_query(
    query: str,
    top_k: int = 5,
    collection: str = "default",
) -> dict:
    """
    Query the RAG pipeline for relevant context.

    Args:
        query: Natural language query
        top_k: Number of results to return
        collection: Vector collection to search

    Returns:
        dict with documents and metadata
    """
    context = await rag_manager.get_context(
        query=query,
        top_k=top_k,
        collection=collection,
    )
    return context.model_dump()
```

**"MCP is the future. We're building it today."**
