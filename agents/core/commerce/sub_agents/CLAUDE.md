<claude-mem-context>

</claude-mem-context>

# agents/core/commerce/sub_agents/ — Commerce sub-agents

Three sub-agents registered by `CommerceCoreAgent`. All extend `SubAgent` with `parent_type = CoreAgentType.COMMERCE`.

## Key files

- `product_ops.py` — `ProductOpsSubAgent`: the heavy lifter. Consolidates `product_manager`, `pricing_engine`, `inventory_tracker`, `order_processor` into one agent. Capabilities: `create_product`, `update_product`, `delete_product`, `list_products`, `set_price`, `bulk_pricing`, `discount_rules`, `stock_check`, `reorder_alert`, `inventory_sync`, `process_order`, `order_status`, `refund`. `ALIASES = ("product_manager", "pricing_engine", "inventory_tracker", "order_processor")`.
- `wordpress_assets.py` — `WordPressAssetsSubAgent`: WordPress media library sync. Handles image attachment creation, alt-text injection, URL resolution, and duplicate-detection before upload. No ALIASES — callers use `"wordpress_assets"` directly.
- `wordpress_bridge.py` — `WordPressBridgeSubAgent`: pushes product data to WooCommerce. Delegates to `agents/wordpress_bridge/agent.py` (the MCP-backed agent) — does NOT make WC REST calls itself. STOP AND SHOW gate lives in the delegate, not here.

## Conventions

- All three classes set `parent_type = CoreAgentType.COMMERCE` — this routes escalations back to `CommerceCoreAgent`.
- `ProductOpsSubAgent.ALIASES` is used by the parent at registration time: `for alias in ProductOpsSubAgent.ALIASES: self.register_sub_agent(alias, agent)`. Do not change ALIASES without updating callers.
- `WordPressAssetsSubAgent` must validate image dimensions before calling WP media upload — uses `PIL` internally to check min 800×800px for product images.
- `WordPressBridgeSubAgent` sets `permission_mode="acceptEdits"` when delegating — only switch to `bypassPermissions` for pure reads.

## Don't

- Don't add WC REST endpoint calls to `wordpress_bridge.py` — all WC API traffic goes through `agents/wordpress_bridge/agent.py`.
- Don't merge `wordpress_assets.py` and `wordpress_bridge.py` — assets (media library) and bridge (product sync) are separate WP domains.
- Don't raise raw `RuntimeError` — use `agents/errors.py` exception classes.

## Related

- `agents/core/commerce/agent.py` — parent that registers these sub-agents
- `agents/wordpress_bridge/agent.py` — MCP-backed WC agent delegated to by `wordpress_bridge.py`
- `agents/core/base.py` — `SubAgent` base class with `_apply_fix()` self-healing hook
