# mcp_tools/ — Typed MCP tool definitions

Building blocks for `mcp_servers/`. Each tool is a typed async function decorated with `@mcp.tool()` from FastMCP. Importing `mcp_tools/` triggers side-effect registration of every handler.

## Layout

```
mcp_tools/
├── __init__.py        re-exports `mcp` FastMCP instance + triggers tool registration
├── server.py          FastMCP instance, backend selection, SYSTEM_PROMPT, logger
├── api_client.py      HTTP client used by tools that hit DevSkyy's own API
├── security.py        auth/perm checks + secret redaction for tool calls
├── types.py           shared enums + BaseAgentInput
└── tools/             one concern per file
    ├── advanced.py        — multi-step / chained tools
    ├── claude_sdk.py      — Claude Agent SDK passthrough
    ├── cli_anything.py    — arbitrary CLI execution (gated)
    ├── ecommerce.py       — product + order + inventory
    ├── infrastructure.py  — system monitoring, code scanning, self-healing
    ├── lora_generation.py — LoRA inference
    ├── lora_training.py   — LoRA training jobs
    ├── marketing.py       — SEO, campaigns, content gen
    ├── ml.py              — trend prediction, segmentation, forecasting, pricing, sentiment
    ├── monitoring.py      — platform health, metrics
    ├── resources.py       — MCP resources (read-only data sources)
    ├── threed.py          — Tripo AI text/image to 3D, FASHN virtual try-on
    ├── virtual_tryon.py   — FASHN-specific virtual try-on flows
    └── wordpress.py       — WordPress/WooCommerce admin + media
```

## Registration pattern

`mcp_tools/__init__.py` does a side-effect import:

```python
import mcp_tools.tools   # registers all @mcp.tool() handlers
from mcp_tools.server import mcp   # public API
```

Every file under `tools/` decorates its handlers with `@mcp.tool()` at module load. **All handlers register on first import of `mcp_tools`.** No manual registry — file presence = exposed tool.

## Shared types (`types.py`)

```python
class ResponseFormat(StrEnum):
    MARKDOWN = "markdown"
    JSON = "json"

class AgentCategory(StrEnum):
    INFRASTRUCTURE, AI_INTELLIGENCE, ECOMMERCE, MARKETING,
    CONTENT, INTEGRATION, ADVANCED, FRONTEND

class MLModelType(StrEnum):
    TREND_PREDICTION, CUSTOMER_SEGMENTATION,
    DEMAND_FORECASTING, DYNAMIC_PRICING, SENTIMENT_ANALYSIS

class BaseAgentInput(BaseModel):
    response_format: ResponseFormat = ResponseFormat.MARKDOWN
    # ConfigDict: str_strip_whitespace=True, validate_assignment=True, extra="forbid"
```

Tool input schemas should extend `BaseAgentInput` for free schema-level whitespace stripping and `extra="forbid"` rejection of unknown fields. **Don't define free-form `str` inputs without validation** — use Pydantic models.

## Server config (`server.py`)

- **FastMCP instance:** `mcp = FastMCP("devskyy_mcp_v2")`
- **Backend selection:** `MCP_BACKEND` env var → `devskyy` (default, localhost:8000) or `critical-fuchsia-ape` (FastMCP-hosted)
- **CHARACTER_LIMIT = 25000** — max response size; exceed → truncate or paginate
- **REQUEST_TIMEOUT = 60.0** — API timeout in seconds
- **SYSTEM_PROMPT** — included in MCP `initialize` response; describes agent categories so clients can discover tools by intent
- **PTC_CALLER = "code_execution_20250825"** — distinguishes direct vs code-execution invocation

## Tool authoring checklist

A new tool under `mcp_tools/tools/foo.py`:

1. **Typed signature.** Function parameters use Pydantic models extending `BaseAgentInput`, not loose dicts/strings.
2. **Docstring describes inputs/outputs.** FastMCP uses the docstring to populate tool metadata for MCP clients.
3. **Async.** `async def` even for cheap calls — keeps the event loop unblocked.
4. **Mutations require explicit confirmation.** Add a confirmation flag to the input schema; the parent agent gates approval. Don't perform destructive writes inferring intent from the request alone.
5. **No direct DB writes.** Go through `services/`. Tools are a thin protocol surface, not business logic.
6. **Log invocation with correlation IDs.** Use the configured structured logger so the agent → tool → service stack can be traced.
7. **Sanitize errors.** Don't leak secrets, internal paths, or stack traces in tool responses. `security.py` provides redaction.

## Conventions

- **Tools are pure-ish functions.** Side effects through service-layer clients only; no module-level state.
- **One concern per file.** If `marketing.py` grows past ~600 lines, split (`marketing_seo.py`, `marketing_campaigns.py`, etc.).
- **Tool names follow `<verb>_<noun>` snake_case.** FastMCP prefixes them with the server name when exposed to clients.
- **Response format gated by `BaseAgentInput.response_format`.** Tools should honor MARKDOWN (human-readable) vs JSON (structured).
- **No emoji in tool responses unless explicitly requested.** Per project standard.

## Don't

- Don't define tools that take free-form `str` inputs without validation. Use Pydantic models for any non-trivial input shape.
- Don't add tools that wrap a single existing service method without adding semantic value — inline-call the service instead. Tools must add **agent-shaped abstraction** over raw service calls.
- Don't return >25KB responses without paginating. Hard cap is `CHARACTER_LIMIT` in `server.py`.
- Don't import from `mcp_servers/` here. The dependency direction is `mcp_servers/ → mcp_tools/`, never the reverse.
- Don't bypass `security.py` redaction when returning data from services that may carry secrets (Stripe, OpenAI, internal API keys).

## Related

- Hosted by: `mcp_servers/`
- Backed by: `services/`, `agents/`
- Schemas + base input: `mcp_tools/types.py`
- Auth + redaction: `mcp_tools/security.py`
- HTTP client: `mcp_tools/api_client.py` (talks to DevSkyy API at `DEVSKYY_API_URL`)

## Recent learnings

- Tool count is **15 files** under `tools/` covering 8 `AgentCategory` enum values. When adding a new category, extend `AgentCategory` in `types.py` first.
- `BaseAgentInput` uses `extra="forbid"` — silently drops typoed parameters at the MCP layer. Worth surfacing in error messages to client developers.
- LoRA training and LoRA generation are split (`lora_training.py` + `lora_generation.py`) because training jobs are long-running and need separate timeout / async-queue handling.


<claude-mem-context>

</claude-mem-context>