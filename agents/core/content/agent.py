"""
Content Core Agent
===================

Domain: All written content — pages, products, blogs, SEO.
Sub-agents: Collection Content, SEO Content, Copywriter.

Wraps the existing SkyyRoseContentAgent with CoreAgent base.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgent, CoreAgentType

logger = logging.getLogger(__name__)


class ContentCoreAgent(CoreAgent):
    """
    Content Core Agent — manages all written content.

    Delegates to sub-agents:
    - collection_content: Collection page sections, product descriptions
    - seo_content: Meta tags, structured data, keyword optimization
    - copywriter: Brand voice copy, marketing copy, blog posts
    """

    core_type = CoreAgentType.CONTENT
    name = "content_core"
    description = "All written content: pages, products, blogs, SEO copy"

    def __init__(self, *, correlation_id: str | None = None, **kwargs: Any) -> None:
        super().__init__(correlation_id=correlation_id, **kwargs)
        self._legacy_agent: Any = None
        self._register_sub_agents()

    def _register_sub_agents(self) -> None:
        """Auto-register consolidated sub-agents with aliases."""
        try:
            from agents.core.content.sub_agents.collection_content import (
                CollectionContentSubAgent,
            )

            self.register_sub_agent("collection_content", CollectionContentSubAgent())
        except ImportError:
            logger.debug("[%s] CollectionContentSubAgent unavailable", self.name)

        try:
            from agents.core.content.sub_agents.seo_copywriter import (
                SeoCopywriterSubAgent,
            )

            agent = SeoCopywriterSubAgent()
            self.register_sub_agent("seo_copywriter", agent)
            for alias in SeoCopywriterSubAgent.ALIASES:
                self.register_sub_agent(alias, agent)
        except ImportError:
            logger.debug("[%s] SeoCopywriterSubAgent unavailable", self.name)

    def _get_legacy_agent(self) -> Any:
        if self._legacy_agent is None:
            try:
                from agents.skyyrose_content_agent import SkyyRoseContentAgent
                from adk.base import AgentConfig

                config = AgentConfig(name="content", description="Content operations")
                self._legacy_agent = SkyyRoseContentAgent(config)
            except ImportError:
                logger.warning("[%s] Legacy SkyyRoseContentAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["collection", "section", "hero"]):
            if "collection_content" in self._sub_agents:
                return await self.delegate("collection_content", task, **kwargs)

        if any(kw in task_lower for kw in ["seo", "meta", "keyword", "ranking"]):
            if "seo_content" in self._sub_agents:
                return await self.delegate("seo_content", task, **kwargs)

        if any(kw in task_lower for kw in ["copy", "blog", "post", "write"]):
            if "copywriter" in self._sub_agents:
                return await self.delegate("copywriter", task, **kwargs)

        # Fallback to legacy
        legacy = self._get_legacy_agent()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}

        return {"success": False, "error": f"No handler for content task: {task[:100]}"}


__all__ = ["ContentCoreAgent"]
