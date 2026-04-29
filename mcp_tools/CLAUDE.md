# mcp_tools/ — MCP tool definitions (19 Python files)

Building blocks for `mcp_servers/`. Each tool is a typed function exposed via MCP.

## Layout

- `server.py` — server bootstrap with tool registration
- `api_client.py` — HTTP client used by tools that hit DevSkyy's own API
- `security.py` — auth/perm checks for tool calls
- `types.py` — shared type defs
- `tools/` — individual tool modules (one concern per file)

## Conventions

- Tools are typed: function signature with type hints + docstring describing inputs/outputs.
- Tools that perform mutations require an explicit confirmation flag in the schema; let the parent agent gate.
- No direct DB writes from tools — go through `services/`.
- All tools log invocation with correlation IDs for tracing across the agent → tool → service stack.

## Don't

- Don't define tools that take free-form `str` inputs without validation. Use Pydantic models for non-trivial inputs.
- Don't add tools that wrap a single existing service method without adding semantic value. Inline-call instead.

## Related

- Hosted by: `mcp_servers/`
- Backed by: `services/`, `agents/`
