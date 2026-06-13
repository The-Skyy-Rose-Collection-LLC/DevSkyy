# agents/core/shared/ — Shared cross-domain infrastructure

Shared sub-agents and utilities consumed by multiple domain CoreAgents. Not owned by any single domain.

## Key files

- `wp_ai_bridge.py` — `WordPressAIBridge(SubAgent)`: bridges AI provider calls through the WordPress AI REST API. `parent_type = CoreAgentType.ORCHESTRATOR` — escalations go to the orchestrator layer, not to any single domain. Five capabilities: `text_generation`, `image_generation`, `function_calling`, `provider_status`, `model_discovery`.

## WordPressAIBridge conventions

- REST endpoints: `POST /wp-ai/v1/ai/prompt` (text/image generation), `GET /wp-ai/v1/ai/providers/models` (provider discovery).
- Provider routing: `TEXT_PRIORITY = ["anthropic", "openai", "google"]`, `IMAGE_PRIORITY = ["openai", "google"]`. Provider name → backend mapping: `"claude"` → `"anthropic"`, `"gpt4"` → `"openai"`, `"gemini"` → `"google"`.
- Uses `httpx` async client — all calls are non-blocking; do NOT wrap in `asyncio.run()` inside an existing event loop.
- Authentication goes through `WP_AI_API_KEY` env var — never hardcoded. Bridge reads it at init time.
- `"provider_status"` capability polls provider health before dispatching — callers should check status if they need guaranteed provider availability.

## Don't

- Don't use `WordPressAIBridge` for WooCommerce REST writes — it routes AI completions only, not product/order mutations.
- Don't add domain-specific post-processing logic here — transform outputs in the caller (the domain CoreAgent or sub-agent), not in the bridge.
- Don't instantiate `WordPressAIBridge` with a `parent_type` other than `CoreAgentType.ORCHESTRATOR` — the escalation chain is intentional.

## Related

- `agents/core/base.py` — `SubAgent` base class, `CoreAgentType.ORCHESTRATOR`
- `agents/core/orchestrator.py` — `CoreOrchestrator` that receives escalations from this bridge
- WordPress AI plugin — exposes `/wp-ai/v1/ai/` REST namespace on skyyrose.co (not in this repo)
