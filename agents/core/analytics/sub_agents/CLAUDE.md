# agents/core/analytics/sub_agents/ — Analytics sub-agents

Three sub-agents registered by `AnalyticsCoreAgent`. All extend `SubAgent` with `parent_type = CoreAgentType.ANALYTICS`.

## Key files

- `analytics_ops.py` — `AnalyticsOpsSubAgent`: the primary data agent. Consolidates `data_analyst`, `trend_predictor`, `conversion_tracker`. 11 capabilities: `query_data`, `aggregate`, `visualize`, `export_report`, `forecast`, `seasonality`, `anomaly_detect`, `funnel_analysis`, `attribution`, `cohort_analysis`, `revenue_tracking`. `ALIASES = ("data_analyst", "trend_predictor", "conversion_tracker")`.
- `algorithm_agent.py` — `AlgorithmSubAgent`: algorithmic intelligence layer. 7 capabilities: recommendation engine, dynamic pricing, trend scoring, inventory optimization, content ranking, brand affinity scoring, A/B test analysis. Has `ALIASES` tuple — check before adding routing names. Integrates with the Brand Learning Loop via `orchestration/brand_learning.py`.
- `brand_intel_agent.py` — `BrandIntelAgent`: competitive intelligence. 7 capabilities: competitor profiling (SWOT), price gap analysis, style trend mapping, opportunity detection, threat assessment, strategic briefings, comparative scoring. Has `ALIASES` tuple — check before adding routing names. Data source: `services/competitive/` (`CompetitorAnalysisService`).

## Conventions

- All three classes set `parent_type = CoreAgentType.ANALYTICS` — escalations route back to `AnalyticsCoreAgent`.
- `ALIASES` on each class are registered by the parent at init time. Do not change ALIASES without checking `AnalyticsCoreAgent._register_sub_agents()` for dependent callers.
- `AlgorithmSubAgent` owns the Prophet (`fbprophet`) model lifecycle — all forecasting calls go through it, not through `analytics_ops.py`.
- `BrandIntelAgent` emits `competitive_intel` signals to `orchestration/brand_learning.py` — these signals feed brand strategy loops; don't strip or suppress them.
- Sub-agents return markdown tables + recommendations. Callers must not strip the markdown structure — it carries the table schema.

## Don't

- Don't call Prophet directly from `analytics_ops.py` — route through `AlgorithmSubAgent`.
- Don't add WooCommerce or Klaviyo reads to these files — data access goes through `WordPressAIBridge` (`agents/core/shared/wp_ai_bridge.py`).
- Don't merge `algorithm_agent.py` into `analytics_ops.py` — algorithmic model lifecycle and raw analytics are separate concerns.

## Related

- `agents/core/analytics/agent.py` — parent that registers all three sub-agents and their ALIASES
- `agents/core/shared/wp_ai_bridge.py` — data source for WP/WC metrics
- `services/competitive/` — `CompetitorAnalysisService` consumed by `BrandIntelAgent`
- `orchestration/brand_learning.py` — receives signals from `AlgorithmSubAgent` and `BrandIntelAgent`
