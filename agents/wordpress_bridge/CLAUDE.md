# agents/wordpress_bridge/ — Claude Agent SDK bridge to WordPress/WooCommerce

`WordPressBridgeAgent` — Claude Agent SDK-powered orchestrator that bridges DevSkyy dashboard pipelines to WordPress/WooCommerce. Owns **15 custom MCP tools** for posts, products, media, orders, and theme operations. Uses adaptive thinking for intelligent operation routing.

## Surface (from `__init__.py` — lazy-loaded)

| Symbol | Source | Role |
|--------|--------|------|
| `WordPressBridgeAgent` | `agent.py` | Main SDK-powered agent class |
| `run_agent` | `agent.py` | Convenience runner — instantiate + execute in one call |
| `create_wordpress_tools` | `mcp_server.py` | Builds the FastMCP server exposing all 15 WP tools |
| `SYSTEM_PROMPT` | `prompts.py` | System prompt for the agent — domain instructions + safety gates |

`__init__.py` uses `__getattr__` for lazy imports — symbols only load when accessed (avoids `claude_agent_sdk` import at package-import time).

## Architecture

```python
from agents.wordpress_bridge import WordPressBridgeAgent

agent = WordPressBridgeAgent(
    model="claude-opus-4-6",          # default — adaptive thinking + 20-turn budget
    correlation_id="story_42",
)
result = await agent.execute(
    "Update the Black Rose collection hero image",
    permission_mode="acceptEdits",    # SDK auto-accepts tool calls
)
```

Internally:
1. `agent.get_options()` builds `ClaudeAgentOptions` with all 15 MCP tools wired
2. `ClaudeSDKClient` runs the agent loop (`max_turns=20`)
3. **STOP AND SHOW remains at the DevSkyy layer** — `permission_mode="acceptEdits"` only bypasses SDK's per-call confirmation; production writes still surface for human approval via the dashboard

## Files

```
wordpress_bridge/
├── __init__.py        Lazy __getattr__ — soft-imports for SDK availability
├── agent.py           WordPressBridgeAgent — ClaudeSDKClient orchestration
├── mcp_server.py      create_wordpress_tools() — 15 FastMCP @mcp.tool() handlers
└── prompts.py         SYSTEM_PROMPT — domain instructions + safety contracts
```

## 15 MCP tools (overview — see `mcp_server.py` for exact signatures)

Categories the agent has direct tool access to:

- **Posts / pages** — create, read, update, list, search
- **WooCommerce products** — create, update, delete, list, search by SKU
- **WooCommerce orders** — list, get, update status
- **Media library** — upload, list, attach to product
- **Theme operations** — list templates, read template file, write template file
- **Site config** — read options, update theme settings

Every mutation tool surfaces a confirmation argument at the schema level; the parent layer (dashboard / Director) gates approval before agent dispatch.

## Adaptive thinking

`ClaudeAgentOptions(thinking={"type": "adaptive"})` — the agent decides how deeply to reason per call. Use cases:

- **Trivial reads** (list 10 most recent posts) → fast, ~0 thinking tokens
- **Cross-tool orchestration** (find product → update price → re-attach media) → deeper thinking
- **Ambiguous requests** ("update the hero") → expands thinking to clarify before action

## Conventions

- **Lazy imports** via `__getattr__` in `__init__.py`. Don't move imports to module top — package loads must not require `claude_agent_sdk`.
- **`model="claude-opus-4-6"` default** — Opus for adaptive thinking depth. Sonnet works for narrow tasks; Haiku is too small for multi-tool orchestration.
- **`max_turns=20`** is the safety cap. Long agent loops cost real money and rarely converge to better answers.
- **MCP tool registration in `mcp_server.py` only.** Don't add `@mcp.tool()` handlers anywhere else for WP operations.
- **`SYSTEM_PROMPT` is the source of truth** for agent behavior. Updates here cascade to every invocation.
- **Per `DevSkyy/CLAUDE.md`** — escape output: `esc_html()` / `esc_attr()` / `esc_url()` / `wp_kses_post()`. Use `$wpdb->prepare()` — never string-concat untrusted input.
- **Nonce + capability checks** on all write actions in the underlying PHP. The bridge agent inherits this — it doesn't bypass.

## Don't

- Don't import `ClaudeSDKClient` directly from `claude_agent_sdk` elsewhere in the project. Go through this module so configuration (model, thinking, tools, system_prompt) stays consistent.
- Don't add a 16th MCP tool without justifying it. Each tool widens the agent's reach + cost surface. Prefer composing existing tools where possible.
- Don't run with `permission_mode="bypassPermissions"` against production. The dashboard surfaces a STOP AND SHOW; SDK bypass is for the inner SDK loop only.
- Don't hardcode WordPress URLs / API keys. Read from environment: `WORDPRESS_URL`, `WORDPRESS_USERNAME`, `WORDPRESS_APP_PASSWORD`, `WOOCOMMERCE_KEY`, `WOOCOMMERCE_SECRET`.
- Don't bypass `mcp_server.create_wordpress_tools()` to wire a one-off tool. The tool surface is the contract — additions go through the standard path.

## Related

- WC client used by the tools: `wordpress/products.py` (`WooCommerceProducts`)
- WP/WC config: `.env.wordpress` (gitignored)
- Sister SDK agent path: `agents/claude_sdk/` (broader SDK integration framework)
- Live site: `skyyrose.co` (production WP store)
- Deploy script: `scripts/deploy-theme.sh` (separate from this — handles theme file deploys, not API operations)
- DevSkyy WP rules: `DevSkyy/CLAUDE.md` "WordPress Rules" section

## Recent learnings

- This is one of four major agent sub-systems (cmem #3146, 2026-05-08): elite_web_builder, render_pipeline, visual_generation, wordpress_bridge.
- Claude Agent SDK already extensively integrated (cmem #4087, 2026-05-12) — duplicate version pins exist; check `pyproject.toml` before adding new SDK deps.
- 15 MCP tools is the current surface — composed via `create_wordpress_tools()` factory in `mcp_server.py`.
