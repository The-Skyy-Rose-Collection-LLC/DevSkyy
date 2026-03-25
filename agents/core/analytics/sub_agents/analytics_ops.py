"""
Analytics Operations Sub-Agent (Consolidated)
================================================

Consolidates: data_analyst, trend_predictor, conversion_tracker.
Wraps agents/analytics_agent.py into the new hierarchy.

Parent: Analytics Core Agent
Capabilities: Data analysis, trend prediction, conversion tracking.
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


class AnalyticsOpsSubAgent(SubAgent):
    """Data analysis, trend prediction, and conversion tracking."""

    name = "analytics_ops"
    parent_type = CoreAgentType.ANALYTICS
    description = "Data analysis, trend forecasting, conversion funnel tracking"
    capabilities = [
        # data_analyst
        "query_data",
        "aggregate",
        "visualize",
        "export_report",
        # trend_predictor
        "forecast",
        "seasonality",
        "anomaly_detect",
        # conversion_tracker
        "funnel_analysis",
        "attribution",
        "cohort_analysis",
        "revenue_tracking",
    ]

    ALIASES = ("data_analyst", "trend_predictor", "conversion_tracker")

    system_prompt = (
        "You are the Analytics specialist for SkyyRose luxury fashion e-commerce. "
        "You analyze sales data, predict trends, track conversion funnels, and "
        "detect anomalies. Metrics: AOV, conversion rate, cart abandonment, LTV, "
        "revenue by collection. Return insights with data visualizations in markdown "
        "tables and actionable recommendations."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["AnalyticsOpsSubAgent"]
