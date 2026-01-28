# DevSkyy MCP Servers

> MCP 1.0 compliant, tool-first | Multiple servers

## Architecture
```
mcp_servers/
├── rag_server.py           # RAG pipeline (6 tools)
├── agent_bridge_server.py  # Agent bridge
├── openai_server.py        # OpenAI proxy
├── orchestrator.py         # Multi-server orchestration
├── server_manager.py       # Server lifecycle
├── context7_client.py      # Context7 integration
├── serena_client.py        # Serena integration
└── wordpress-com/          # WP.com MCP
```

## RAG Server Tools (`rag_server.py`)
| Tool | Description |
|------|-------------|
| rag_query | Query RAG pipeline |
| rag_ingest | Ingest documents |
| rag_get_context | Get context for query |
| rag_query_rewrite | Rewrite/expand queries |
| rag_list_sources | List ingested sources |
| rag_stats | Pipeline statistics |

## Main MCP Tools (`devskyy_mcp.py` - root)
`multi_agent_workflow` `manage_products` `dynamic_pricing` `generate_wordpress_theme` `generate_3d_from_description` `virtual_tryon` `lora_generate` `product_caption` `marketing_campaign` `system_monitoring` `health_check` `list_agents` `scan_code` `fix_code`

## Pattern
```python
@mcp.tool()
async def rag_query(input: RAGQueryInput) -> str:
    results = await pipeline.search(input.query, top_k=input.top_k)
    return format_response(results, input.response_format)
```

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

**"MCP is the future. We're building it today."**
