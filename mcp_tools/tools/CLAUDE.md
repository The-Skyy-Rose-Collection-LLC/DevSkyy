# mcp_tools/tools/ — Per-domain MCP tool modules (15 files)

Each file groups `@mcp.tool()` handlers for one domain. Importing the parent package (`mcp_tools/`) loads all modules here and side-effect-registers every handler against the FastMCP instance.

## Domain map

| File | Domain | `AgentCategory` |
|------|--------|----------------|
| `advanced.py` | Multi-step / chained workflows | `ADVANCED` |
| `claude_sdk.py` | Claude Agent SDK passthrough | `AI_INTELLIGENCE` |
| `cli_anything.py` | Arbitrary CLI execution (gated) | `INFRASTRUCTURE` |
| `ecommerce.py` | Product / order / inventory / pricing | `ECOMMERCE` |
| `infrastructure.py` | System monitoring, code scanning, self-healing | `INFRASTRUCTURE` |
| `lora_generation.py` | LoRA inference for image gen | `AI_INTELLIGENCE` |
| `lora_training.py` | LoRA training jobs (long-running) | `AI_INTELLIGENCE` |
| `marketing.py` | SEO, campaigns, content generation | `MARKETING` |
| `ml.py` | Trend prediction, segmentation, forecasting, sentiment | `AI_INTELLIGENCE` |
| `monitoring.py` | Platform health metrics | `INFRASTRUCTURE` |
| `resources.py` | MCP resources (read-only data sources) | n/a — resources, not tools |
| `threed.py` | Tripo AI text/image → 3D | `INTEGRATION` |
| `virtual_tryon.py` | FASHN virtual try-on flows | `INTEGRATION` |
| `wordpress.py` | WordPress / WooCommerce admin + media | `INTEGRATION` |

## Authoring a new tool module

```python
# mcp_tools/tools/foo.py
from mcp_tools.server import mcp
from mcp_tools.types import BaseAgentInput, ResponseFormat
from pydantic import Field

class FooInput(BaseAgentInput):
    target_sku: str = Field(..., description="SKU to operate on")
    dry_run: bool = Field(default=True, description="Preview only — do not mutate")

@mcp.tool()
async def foo_analyze_product(input: FooInput) -> str:
    """Analyze a product. Returns markdown or JSON based on response_format."""
    # 1. Validate input (Pydantic already did the heavy lifting)
    # 2. Call services/ — never DB directly
    # 3. Render response per input.response_format
    return ...
```

After saving, the next import of `mcp_tools` will register the handler. **No manual registry step.**

## Module-level rules

- **Tool names: `<verb>_<noun>` snake_case** — `analyze_product`, not `ProductAnalyzer.analyze`.
- **Mutations gated** — destructive ops require `confirm: bool = False` field. Tool refuses execution unless `confirm=True` AND the parent agent has surfaced the plan to the user.
- **Long-running ops** — return a job ID + status polling URL, not the final result. Use `lora_training.py` pattern: enqueue → return job handle → expose `lora_get_job_status` for polling.
- **Resources vs tools** — `resources.py` registers `@mcp.resource()` handlers (read-only, addressed by URI). Tools are `@mcp.tool()` (invokable, may mutate). Don't conflate.
- **Logging** — every handler should `logger.info(...)` invocation + outcome with correlation ID for agent → tool → service tracing.

## Don't

- Don't add tools that wrap a single service method 1:1. Inline-call the service from the agent instead. Tools earn their existence by composing OR by exposing an agent-shaped abstraction.
- Don't import from sibling tool files (`tools/marketing.py` importing `tools/ecommerce.py`). Shared logic goes into `services/` or `mcp_tools/api_client.py`.
- Don't catch and swallow exceptions silently. Map to `LLMError` / domain-specific exceptions; let FastMCP serialize the error response.
- Don't shell out without sanitization. `cli_anything.py` is the only place arbitrary CLI execution lives — anywhere else, the parent agent must have already validated the command.

## Related

- Parent package: `mcp_tools/` (registration entry point)
- Server config: `mcp_tools/server.py` (`mcp` FastMCP instance)
- Types: `mcp_tools/types.py` (`BaseAgentInput`, enums)
- Security: `mcp_tools/security.py` (redaction, auth gates)
- HTTP backend: `mcp_tools/api_client.py` → `DEVSKYY_API_URL`
- Underlying services: `services/`, `agents/`


