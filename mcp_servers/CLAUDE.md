# mcp_servers/ — MCP server implementations (18 Python files)

Exposes DevSkyy capabilities to MCP clients (Claude Desktop, Claude Code, ChatGPT, custom agents). Each server is a FastMCP process bridging an internal domain (agents, RAG, WooCommerce, OpenAI-compat) to the MCP protocol.

## Surface

| Server | File | What it exposes |
|--------|------|-----------------|
| **Agent Bridge** | `agent_bridge_server.py` (59k) | All 6 SuperAgents as MCP tools: commerce_* (15), creative_* (10), marketing_* (12), support_* (8), operations_* (17), analytics_* (10) + orchestration tools (Round Table, Router, Learning) |
| **WooCommerce** | `woocommerce_mcp.py` (36k) | WooCommerce REST bridge: products, orders, inventory, media |
| **OpenAI Compat** | `openai_server.py` (27k) | Function-calling clients can call DevSkyy as if it were OpenAI |
| **RAG** | `rag_server.py` (15k) | Retrieval over brand corpus (catalog, dossiers, brand docs) |
| **Catalog Generator** | `catalog_generator.py` (20k) | Generates catalog data for external consumption |
| **Orchestrator** | `orchestrator.py` (15k) | Meta-server managing the others |
| **Process Manager** | `process_manager.py` (17k) | Runtime lifecycle: start/stop/restart of server processes |
| **Server Manager** | `server_manager.py` (10k) | Health check + supervision wrapper |
| **WordPress.com** | `wordpress-com/` (subdir) | WordPress.com-specific MCP server (subdir bundle) |

### Clients to other MCP servers

These are **clients** that consume external MCP servers from inside DevSkyy:

| Client | File | Talks to |
|--------|------|----------|
| `Context7Client` | `context7_client.py` | Context7 docs server (library docs lookup) |
| `PlaywrightClient` | `playwright_client.py` | Playwright MCP (browser automation) |
| `SerenaClient` | `serena_client.py` | Serena MCP (code-aware editing) |

## Backend selection (`MCP_BACKEND` env var)

`mcp_tools/server.py` and most servers honor:

- `MCP_BACKEND=devskyy` (default) → `DEVSKYY_API_URL` (default `http://localhost:8000`)
- `MCP_BACKEND=critical-fuchsia-ape` → `CRITICAL_FUCHSIA_APE_URL` (FastMCP-hosted endpoint)

Switch at process start; not runtime-configurable.

## Config

- **`mcp_orchestrator.json`** — declares which servers to start, ports, dependencies. Single source of truth for `process_manager.py` startup.
- **`requirements.txt`** — Python deps specific to MCP servers (kept separate from root `pyproject.toml` so MCP processes can install minimally).
- **`.env.example`** — required env vars: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `WORDPRESS_URL`, `WOOCOMMERCE_KEY`, `WOOCOMMERCE_SECRET`, `DEVSKYY_API_KEY`, etc.
- **Root entry point** — `devskyy_mcp.py` (not in this dir) is the canonical FastMCP entry; declared in `fastmcp.config.json`.

## Agent Bridge Server — canonical pattern

```
MCP Client (Claude Desktop, etc.)
    │
    ▼
agent_bridge_server.py  (FastMCP "devskyy-agents")
    │
    ├── commerce_*    (CommerceAgent — 15 tools)
    ├── creative_*    (CreativeAgent — 10 tools)
    ├── marketing_*   (MarketingAgent — 12 tools)
    ├── support_*     (SupportAgent — 8 tools)
    ├── operations_*  (OperationsAgent — 17 tools)
    ├── analytics_*   (AnalyticsAgent — 10 tools)
    └── orchestration_*  (Round Table, Router, Self-Learning)
```

Claude Desktop config:

```json
{
  "mcpServers": {
    "devskyy-agents": {
      "command": "python",
      "args": ["/path/to/mcp_servers/agent_bridge_server.py"],
      "env": {
        "OPENAI_API_KEY": "...",
        "ANTHROPIC_API_KEY": "..."
      }
    }
  }
}
```

## Conventions

- **Each server file starts with a module docstring** naming its tools and which agents/services it bridges. Don't merge multiple domains into one server — split by domain.
- **Tool names follow `mcp__devskyy__<verb>_<noun>`** (snake_case verbs) when exposed to MCP clients. FastMCP synthesizes the prefix; functions decorated with `@mcp.tool()` use `<verb>_<noun>` form.
- **FastMCP-based** unless there's a specific protocol-version reason to use the lower-level SDK. FastMCP handles tool discovery, schema validation (Pydantic), and SSE/stdio transport.
- **Async tool functions.** All `@mcp.tool()` handlers are `async def`. Use `asyncio.to_thread` for sync vendor SDKs.
- **Configure logging early.** `configure_logging(json_output=True)` from `utils.logging_utils` — JSON output for downstream log aggregation. Stdlib `print()` corrupts MCP stdio transport.
- **Response size cap:** `CHARACTER_LIMIT = 25000` (from `mcp_tools/server.py`). MCP clients chunk above this; tools that return long content should paginate or summarize.
- **PTC caller marker:** `code_execution_20250825` — when a tool is invoked from inside a code execution container (vs. direct Claude tool call), surface this in `CallerInfo` for tracing.

## Don't

- Don't add a new server without registering it in `mcp_orchestrator.json`. Process manager won't start an unknown server.
- Don't expose internal services directly. **Wrap them in agent or service-layer calls** so the MCP surface stays semantic (e.g. `support_resolve_ticket` not `support_call_zendesk_api`).
- Don't write to stdout from tool handlers (corrupts stdio transport). Use the configured structured logger.
- Don't share state between tool invocations via module globals. Each MCP call may be a fresh process; persist via `services/storage/`.
- Don't return secrets in tool responses. Sanitize before returning. `mcp_tools/security.py` provides redaction helpers.

## Related

- Tools defined in: `mcp_tools/`
- Top-level entrypoint: `devskyy_mcp.py` (root)
- Config served from: `fastmcp.config.json` (root)
- Settings → `mcp_orchestrator.json` (this dir)
- Per-Claude-Code config: top-level `mcpServers` key in `.claude.json` (Claude Code only reads top-level — rename-prefixed keys are silently ignored)

## Recent learnings

- Agent Bridge exposes **6 SuperAgents** = 72 tools total. When the SuperAgent count changes, update the docstring header in `agent_bridge_server.py` so MCP clients see accurate categorization.
- Claude Code's MCP discovery only reads `mcpServers` from the top of `settings.json`. Don't nest under a sub-key.
- `MCP_BACKEND=critical-fuchsia-ape` is the FastMCP-hosted production endpoint. Set `CRITICAL_FUCHSIA_APE_KEY` in addition to URL.
