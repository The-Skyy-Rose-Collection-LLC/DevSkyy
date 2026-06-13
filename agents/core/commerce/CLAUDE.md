# agents/core/commerce/ — Commerce domain CoreAgent

`CommerceCoreAgent` — all revenue-generating operations: products, orders, pricing, inventory, WooCommerce sync. Extends `CoreAgent` (`core_type = CoreAgentType.COMMERCE`). Three native sub-agents + two SDK sub-agents registered at init.

## Key files

- `agent.py` — `CommerceCoreAgent(CoreAgent)`: registers `ProductOpsSubAgent`, `WordPressAssetsSubAgent`, `WordPressBridgeSubAgent` plus SDK agents `SDKCatalogManagerAgent` and `SDKPriceOptimizerAgent`. All ALIASES from `ProductOpsSubAgent.ALIASES` are registered under the same instance.
- `sub_agents/product_ops.py` — `ProductOpsSubAgent`: consolidated CRUD + pricing + inventory + order ops. `ALIASES = ("product_manager", "pricing_engine", "inventory_tracker", "order_processor")`.
- `sub_agents/wordpress_assets.py` — `WordPressAssetsSubAgent`: WordPress media library management, image attachment sync, asset URL resolution.
- `sub_agents/wordpress_bridge.py` — `WordPressBridgeSubAgent`: WooCommerce product push, attribute sync, variant mapping. Wraps `agents/wordpress_bridge/agent.py` — does NOT call WC REST directly.

## Conventions

- WooCommerce REST writes require STOP AND SHOW — enforced by `WordPressBridgeSubAgent` which delegates to `WordPressBridgeAgent` (the MCP-backed agent with the gate).
- Keyword routing in `execute()`: `"product"/"inventory"/"order"/"price"` → `ProductOpsSubAgent`, `"media"/"asset"/"image"` → `WordPressAssetsSubAgent`, `"publish"/"sync"/"woocommerce"` → `WordPressBridgeSubAgent`.
- SDK catalog agents require file-system access — they use `SDKSubAgent` (tool-use enabled). Regular sub-agents are LLM-only.
- `ProductOpsSubAgent.ALIASES` ensures backward-compatible routing when callers use old sub-agent names like `"inventory_tracker"`.

## Don't

- Don't route Klaviyo email/SMS through commerce — that's `MarketingCoreAgent`.
- Don't bypass `WordPressBridgeSubAgent` to call WC REST endpoints directly — all WC writes must flow through the gated `WordPressBridgeAgent`.
- Don't add order fulfillment logic to `product_ops.py` — fulfillment is `OperationsAgent` territory.

## Related

- `agents/core/base.py` — `CoreAgent`, `CoreAgentType`, circuit breaker
- `agents/wordpress_bridge/agent.py` — MCP-backed WP/WC agent delegated to by `WordPressBridgeSubAgent`
- `agents/claude_sdk/domain_agents/commerce.py` — `SDKCatalogManagerAgent`, `SDKPriceOptimizerAgent`
- `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` — canonical product catalog
