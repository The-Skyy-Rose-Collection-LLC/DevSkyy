# mcp_servers/ — MCP server implementations (12 Python files)

Exposes DevSkyy capabilities to MCP clients (Claude.ai, Claude Code, other MCP-aware tools).

## Servers

- `agent_bridge_server.py` — exposes the 6 SuperAgents as MCP tools
- `catalog_generator.py` — generates catalog data for external consumption
- `openai_server.py` — OpenAI-compatible bridge (function-calling clients)
- `rag_server.py` — RAG retrieval over the brand corpus
- `woocommerce_mcp.py` — WooCommerce REST bridge (products, orders, inventory)
- `orchestrator.py` — meta-server that manages the others
- `process_manager.py`, `server_manager.py` — runtime lifecycle (start/stop/health)
- `playwright_client.py`, `serena_client.py`, `context7_client.py` — clients to other MCP servers we consume

## Config

- `mcp_orchestrator.json` — declares which servers to start, ports, and dependencies
- `requirements.txt` — Python deps specific to MCP servers (kept separate from the main pyproject)

## Conventions

- Each server file starts with a module docstring naming its tools and the agents/services it bridges.
- Tool names in MCP responses follow `mcp__devskyy__<verb>_<noun>` (snake_case verbs).
- Servers are FastMCP-based unless there's a specific protocol-version reason to use the lower-level SDK.

## Don't

- Don't add a new server without registering it in `mcp_orchestrator.json`.
- Don't expose internal services directly — wrap them in agent or service-layer calls so the MCP surface stays semantic.

## Related

- Tools used: `mcp_tools/`
- Top-level entrypoint: `devskyy_mcp.py` (root)
- Config served from: `fastmcp.config.json`


<claude-mem-context>

</claude-mem-context>