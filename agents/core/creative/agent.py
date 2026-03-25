"""
Creative Core Agent
====================

Domain: Visual identity, design system, brand enforcement.
Sub-agents: Design System, Brand Guardian, Asset Generator, Quality Checker.

Wraps the existing CreativeAgent with CoreAgent base.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgent, CoreAgentType

logger = logging.getLogger(__name__)


class CreativeCoreAgent(CoreAgent):
    """
    Creative Core Agent — visual identity and brand enforcement.

    Delegates to sub-agents:
    - design_system: CSS variables, design tokens, component consistency
    - brand_guardian: Off-brand detection, color/font violations
    - asset_generator: Generate brand assets with quality gates
    - quality_checker: Cross-browser regression, visual diff
    """

    core_type = CoreAgentType.CREATIVE
    name = "creative_core"
    description = "Visual identity, design system, brand enforcement"

    def __init__(self, *, correlation_id: str | None = None, **kwargs: Any) -> None:
        super().__init__(correlation_id=correlation_id, **kwargs)
        self._legacy_agent: Any = None
        self._register_sub_agents()

    def _register_sub_agents(self) -> None:
        """Auto-register consolidated sub-agents with aliases."""
        try:
            from agents.core.creative.sub_agents.brand_creative import (
                BrandCreativeSubAgent,
            )

            agent = BrandCreativeSubAgent()
            self.register_sub_agent("brand_creative", agent)
            for alias in BrandCreativeSubAgent.ALIASES:
                self.register_sub_agent(alias, agent)
        except ImportError:
            logger.debug("[%s] BrandCreativeSubAgent unavailable", self.name)

    def _get_legacy_agent(self) -> Any:
        if self._legacy_agent is None:
            try:
                from adk.base import AgentConfig
                from agents.creative_agent import CreativeAgent

                config = AgentConfig(name="creative", description="Creative operations")
                self._legacy_agent = CreativeAgent(config)
            except ImportError:
                logger.warning("[%s] Legacy CreativeAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["design system", "css", "token", "variable"]):
            if "design_system" in self._sub_agents:
                return await self.delegate("design_system", task, **kwargs)

        if any(kw in task_lower for kw in ["brand", "off-brand", "color", "font"]):
            if "brand_guardian" in self._sub_agents:
                return await self.delegate("brand_guardian", task, **kwargs)

        if any(kw in task_lower for kw in ["generate", "asset", "create"]):
            if "asset_generator" in self._sub_agents:
                return await self.delegate("asset_generator", task, **kwargs)

        if any(kw in task_lower for kw in ["qa", "quality", "regression", "visual diff"]):
            if "quality_checker" in self._sub_agents:
                return await self.delegate("quality_checker", task, **kwargs)

        legacy = self._get_legacy_agent()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}

        return {"success": False, "error": f"No handler for creative task: {task[:100]}"}


__all__ = ["CreativeCoreAgent"]
