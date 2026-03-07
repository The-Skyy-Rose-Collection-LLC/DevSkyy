"""
Analytics Core Agent
=====================

Domain: Data, trends, conversion intelligence.
Sub-agents: Data Analyst, Trend Predictor, Conversion Tracker.

Wraps the existing AnalyticsAgent with CoreAgent base.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgent, CoreAgentType

logger = logging.getLogger(__name__)


class AnalyticsCoreAgent(CoreAgent):
    """
    Analytics Core Agent — data, trends, conversion intelligence.

    Delegates to sub-agents:
    - data_analyst: Reports, anomaly detection, data quality checks
    - trend_predictor: Forecasting, model drift detection, seasonal patterns
    - conversion_tracker: Funnel analysis, tracking validation, optimization
    """

    core_type = CoreAgentType.ANALYTICS
    name = "analytics_core"
    description = "Data analytics, trend prediction, conversion intelligence"

    def __init__(self, *, correlation_id: str | None = None, **kwargs: Any) -> None:
        super().__init__(correlation_id=correlation_id, **kwargs)
        self._legacy_agent: Any = None
        self._register_sub_agents()

    def _register_sub_agents(self) -> None:
        """Auto-register consolidated sub-agents with aliases."""
        try:
            from agents.core.analytics.sub_agents.analytics_ops import (
                AnalyticsOpsSubAgent,
            )

            agent = AnalyticsOpsSubAgent()
            self.register_sub_agent("analytics_ops", agent)
            for alias in AnalyticsOpsSubAgent.ALIASES:
                self.register_sub_agent(alias, agent)
        except ImportError:
            logger.debug("[%s] AnalyticsOpsSubAgent unavailable", self.name)

    def _get_legacy_agent(self) -> Any:
        if self._legacy_agent is None:
            try:
                from adk.base import AgentConfig
                from agents.analytics_agent import AnalyticsAgent

                config = AgentConfig(name="analytics", description="Analytics operations")
                self._legacy_agent = AnalyticsAgent(config)
            except ImportError:
                logger.warning("[%s] Legacy AnalyticsAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["report", "data", "query", "anomaly"]):
            if "data_analyst" in self._sub_agents:
                return await self.delegate("data_analyst", task, **kwargs)

        if any(kw in task_lower for kw in ["trend", "forecast", "predict", "season"]):
            if "trend_predictor" in self._sub_agents:
                return await self.delegate("trend_predictor", task, **kwargs)

        if any(kw in task_lower for kw in ["conversion", "funnel", "tracking", "pixel"]):
            if "conversion_tracker" in self._sub_agents:
                return await self.delegate("conversion_tracker", task, **kwargs)

        legacy = self._get_legacy_agent()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}

        return {"success": False, "error": f"No handler for analytics task: {task[:100]}"}


__all__ = ["AnalyticsCoreAgent"]
