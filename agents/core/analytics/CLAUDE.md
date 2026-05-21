<claude-mem-context>

</claude-mem-context>

# agents/core/analytics/ — Analytics domain CoreAgent

`AnalyticsCoreAgent` — data, trends, and conversion intelligence. Extends `CoreAgent` (`core_type = CoreAgentType.ANALYTICS`). Three sub-agents registered at init via `_register_sub_agents()` with ImportError guards.

## Key files

- `agent.py` — `AnalyticsCoreAgent(CoreAgent)`: registers `AnalyticsOpsSubAgent`, `AlgorithmSubAgent`, `BrandIntelAgent` plus all ALIASES. Each sub-agent's ALIASES are registered under the same instance so keyword routing still resolves to the consolidated agent.
- `sub_agents/analytics_ops.py` — `AnalyticsOpsSubAgent`: consolidates `data_analyst`, `trend_predictor`, `conversion_tracker`. Capabilities: `query_data`, `aggregate`, `visualize`, `export_report`, `forecast`, `seasonality`, `anomaly_detect`, `funnel_analysis`, `attribution`, `cohort_analysis`, `revenue_tracking`. `ALIASES = ("data_analyst", "trend_predictor", "conversion_tracker")`.
- `sub_agents/algorithm_agent.py` — `AlgorithmSubAgent`: product scoring, dynamic pricing, A/B testing, recommendation engine. Has its own `ALIASES` tuple.
- `sub_agents/brand_intel_agent.py` — `BrandIntelAgent`: competitive intelligence, SWOT analysis, threat assessment, market gap analysis. Has its own `ALIASES` tuple.

## Conventions

- Always route analytics tasks through `AnalyticsCoreAgent.execute()` — it applies keyword routing to the right sub-agent before falling back to the legacy `AnalyticsAgent`.
- Keyword routing (set in `execute()`) matches: `"forecast"/"trend"` → `trend_predictor` alias, `"funnel"/"conversion"` → `conversion_tracker`, `"competitor"/"swot"` → `brand_intel`, `"pricing"/"score"` → `algorithm`.
- Metrics in scope: AOV, conversion rate, cart abandonment rate, LTV, revenue by collection. Out-of-scope queries escalate to `CoreOrchestrator`.
- Sub-agents return markdown tables + recommendations — callers should not strip the markdown structure.

## Don't

- Don't register new sub-agents directly in `analytics_ops.py` — put new consolidated capabilities in `algorithm_agent.py` or `brand_intel_agent.py` and add their ALIASES to `agent.py`.
- Don't call Prophet (`fbprophet`) directly from sub-agents — route through `AlgorithmSubAgent` which owns the forecasting model lifecycle.
- Don't add Klaviyo or WooCommerce reads here — analytics reads WP data through `WordPressAIBridge` in `agents/core/shared/`.

## Related

- `agents/core/base.py` — `CoreAgent`, `CoreAgentType`, circuit breaker
- `agents/core/shared/wp_ai_bridge.py` — data source for WP/WC metrics
- `agents/analytics_agent.py` — legacy agent wrapped by `_get_legacy_agent()`
- `agents/claude_sdk/domain_agents/` — SDK-powered analyst agents registered by parent
