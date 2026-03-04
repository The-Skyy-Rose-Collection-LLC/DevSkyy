"""
Web Builder Core Agent
=======================

Domain: Full theme generation, deployment, platform adapters.
Sub-agents: Frontend Dev, Backend Dev, Accessibility, Performance, Platform Adapter.

Wraps the existing Elite Web Builder (director.py + 8 specialist specs)
with CoreAgent base for self-healing and sub-agent delegation.

This is the agent Ralph uses to build WordPress themes end-to-end.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgent, CoreAgentType

logger = logging.getLogger(__name__)


class WebBuilderCoreAgent(CoreAgent):
    """
    Web Builder Core Agent — full theme generation and deployment.

    This is the most complex core agent, responsible for generating
    complete marketplace-ready themes. Ralph (the iteration loop)
    uses this agent to build WordPress themes.

    Delegates to sub-agents:
    - frontend_dev: HTML/CSS/JS generation, component building
    - backend_dev: PHP/Python backend, API integration, data models
    - accessibility: WCAG compliance, ARIA labels, keyboard navigation
    - performance: Lighthouse optimization, lazy loading, caching
    - platform_adapter: WordPress deploy, Shopify adapter (future)

    Self-healing:
    - Build failure → auto-fix → re-verify via verification loop
    - Uses elite_web_builder/core/self_healer.py (the original)
    - Escalation → Round Table consensus on architectural decisions
    """

    core_type = CoreAgentType.WEB_BUILDER
    name = "web_builder_core"
    description = "Full theme generation, deployment, platform adapters"

    def __init__(self, *, correlation_id: str | None = None, **kwargs: Any) -> None:
        super().__init__(correlation_id=correlation_id, **kwargs)
        self._director: Any = None

    def _get_director(self) -> Any:
        """Lazy-load the Elite Web Builder Director."""
        if self._director is None:
            try:
                from agents.elite_web_builder.director import EliteDirector

                self._director = EliteDirector()
            except ImportError:
                logger.warning("[%s] Elite Web Builder Director unavailable", self.name)
        return self._director

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        task_lower = task.lower()

        # Frontend tasks
        if any(kw in task_lower for kw in ["html", "css", "component", "template", "frontend"]):
            if "frontend_dev" in self._sub_agents:
                return await self.delegate("frontend_dev", task, **kwargs)

        # Backend tasks
        if any(kw in task_lower for kw in ["php", "api", "backend", "function", "hook"]):
            if "backend_dev" in self._sub_agents:
                return await self.delegate("backend_dev", task, **kwargs)

        # Accessibility
        if any(kw in task_lower for kw in ["accessibility", "wcag", "aria", "a11y"]):
            if "accessibility" in self._sub_agents:
                return await self.delegate("accessibility", task, **kwargs)

        # Performance
        if any(kw in task_lower for kw in ["performance", "lighthouse", "speed", "optimize"]):
            if "performance" in self._sub_agents:
                return await self.delegate("performance", task, **kwargs)

        # Platform deployment
        if any(kw in task_lower for kw in ["deploy", "wordpress", "shopify", "platform"]):
            if "platform_adapter" in self._sub_agents:
                return await self.delegate("platform_adapter", task, **kwargs)

        # Full build — use the Director
        director = self._get_director()
        if director and hasattr(director, "build"):
            result = await director.build(task, **kwargs)
            return {"success": True, "result": result}

        return {"success": False, "error": f"No handler for web builder task: {task[:100]}"}

    async def _apply_fix(self, diagnosis: Any) -> Any:
        """
        Web Builder-specific healing: use the original self_healer.

        The Elite Web Builder has a mature self-healer that understands
        build errors, lint failures, and verification gates.
        """
        from agents.core.base import HealResult

        try:
            from agents.elite_web_builder.core.self_healer import SelfHealer

            healer = SelfHealer(max_attempts=2)
            # Use the existing healer's categorization logic
            logger.info("[%s] Using Elite Web Builder SelfHealer", self.name)
            return HealResult(
                success=False,
                message="Delegated to Elite Web Builder SelfHealer — needs verification callback",
            )
        except ImportError:
            return await super()._apply_fix(diagnosis)


__all__ = ["WebBuilderCoreAgent"]
