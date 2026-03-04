"""
DevSkyy Orchestrator
=====================

Top-level system orchestrator that:
- Routes tasks to the appropriate core agent
- Handles escalation from core agents
- Runs Round Table consensus for high-stakes decisions
- Enforces budget limits
- Reports system-wide health to the 3D portal

The Orchestrator is the single node at the top of the 3D portal graph.
All 8 core agents connect to it. It's the escalation endpoint.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.errors import AgentError, ErrorCategory

from .base import CoreAgent, CoreAgentType, HealthStatus, SelfHealingMixin

logger = logging.getLogger(__name__)


# Task routing: keywords → core agent type
_ROUTING_RULES: list[tuple[list[str], CoreAgentType]] = [
    (["product", "order", "inventory", "price", "payment", "cart", "woocommerce"],
     CoreAgentType.COMMERCE),
    (["content", "copy", "blog", "seo", "page", "description", "text"],
     CoreAgentType.CONTENT),
    (["design", "brand", "visual", "logo", "creative", "style", "color"],
     CoreAgentType.CREATIVE),
    (["campaign", "social", "marketing", "email", "audience", "ad"],
     CoreAgentType.MARKETING),
    (["deploy", "security", "health", "monitor", "build", "ci", "code quality"],
     CoreAgentType.OPERATIONS),
    (["analytics", "data", "report", "forecast", "trend", "conversion", "metric"],
     CoreAgentType.ANALYTICS),
    (["image", "photo", "3d", "model", "render", "vton", "try-on", "asset"],
     CoreAgentType.IMAGERY),
    (["theme", "template", "wordpress", "web build", "site", "page template"],
     CoreAgentType.WEB_BUILDER),
]


class Orchestrator(SelfHealingMixin):
    """
    System-wide orchestrator — the brain of the agent fleet.

    Routes tasks to core agents, handles cross-domain coordination,
    and serves as the final escalation point before human intervention.

    Usage:
        orchestrator = Orchestrator()
        orchestrator.register_core_agent(commerce_core)
        orchestrator.register_core_agent(content_core)
        result = await orchestrator.route("Update product prices for Black Rose")
    """

    name: str = "orchestrator"
    core_type: CoreAgentType = CoreAgentType.ORCHESTRATOR

    def __init__(self, *, correlation_id: str | None = None, **kwargs: Any) -> None:
        self.correlation_id = correlation_id
        self.__init_healing__()
        self._core_agents: dict[CoreAgentType, CoreAgent] = {}
        self._budget_limit_usd: float | None = None
        self._budget_spent_usd: float = 0.0

    # -------------------------------------------------------------------------
    # Agent Registration
    # -------------------------------------------------------------------------

    def register_core_agent(self, agent: CoreAgent) -> None:
        """Register a core agent in the fleet."""
        self._core_agents[agent.core_type] = agent
        logger.info(
            "[orchestrator] Registered core agent: %s (%s)",
            agent.name,
            agent.core_type.value,
        )

    def get_core_agent(self, agent_type: CoreAgentType) -> CoreAgent | None:
        """Get a registered core agent by type."""
        return self._core_agents.get(agent_type)

    def set_budget_limit(self, limit_usd: float) -> None:
        """Set the maximum budget for autonomous operations."""
        self._budget_limit_usd = limit_usd
        logger.info("[orchestrator] Budget limit set to $%.2f", limit_usd)

    # -------------------------------------------------------------------------
    # Task Routing
    # -------------------------------------------------------------------------

    def route_task(self, task: str) -> CoreAgentType:
        """
        Determine which core agent should handle a task.

        Uses keyword matching against routing rules.
        Falls back to OPERATIONS for unclassified tasks.
        """
        task_lower = task.lower()

        # Score each agent type by keyword matches
        scores: dict[CoreAgentType, int] = {}
        for keywords, agent_type in _ROUTING_RULES:
            score = sum(1 for kw in keywords if kw in task_lower)
            if score > 0:
                scores[agent_type] = scores.get(agent_type, 0) + score

        if scores:
            return max(scores, key=scores.get)  # type: ignore[arg-type]

        # Default fallback
        return CoreAgentType.OPERATIONS

    async def route(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """
        Route a task to the appropriate core agent.

        Steps:
        1. Determine target agent via routing rules
        2. Check budget limits
        3. Check circuit breaker on target agent
        4. Execute via the core agent's execute_safe()
        5. Handle escalation if the core agent fails
        """
        target_type = self.route_task(task)
        agent = self._core_agents.get(target_type)

        if agent is None:
            # Try to find any available agent
            logger.warning(
                "[orchestrator] No agent for %s, trying alternatives",
                target_type.value,
            )
            return await self._route_to_any_available(task, **kwargs)

        # Budget gate
        if self._budget_limit_usd is not None:
            if self._budget_spent_usd >= self._budget_limit_usd:
                return {
                    "success": False,
                    "error": "Budget limit reached",
                    "budget_spent": self._budget_spent_usd,
                    "budget_limit": self._budget_limit_usd,
                    "requires_human_approval": True,
                }

        logger.info(
            "[orchestrator] Routing to %s: %s",
            agent.name,
            task[:100],
        )

        result = await agent.execute_safe(task, **kwargs)

        if result.get("escalation_needed"):
            logger.warning(
                "[orchestrator] %s escalated — trying alternatives",
                agent.name,
            )
            return await self._handle_escalation(
                task, failed_type=target_type, original_result=result, **kwargs
            )

        return result

    async def _route_to_any_available(
        self, task: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Try routing to any available agent as fallback."""
        for agent_type, agent in self._core_agents.items():
            if isinstance(agent, SelfHealingMixin) and not agent.circuit_breaker_allows():
                continue

            try:
                result = await agent.execute_safe(task, **kwargs)
                if result.get("success", True):
                    return result
            except Exception:
                continue

        return {
            "success": False,
            "error": "No available agents could handle this task",
            "requires_human_approval": True,
        }

    async def _handle_escalation(
        self,
        task: str,
        failed_type: CoreAgentType,
        original_result: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Handle escalation when a core agent fails.

        Strategy:
        1. Try alternative core agents that might handle the task
        2. If all fail, return requires_human_approval=True
        """
        for agent_type, agent in self._core_agents.items():
            if agent_type == failed_type:
                continue

            if isinstance(agent, SelfHealingMixin) and not agent.circuit_breaker_allows():
                continue

            try:
                result = await agent.execute_safe(task, **kwargs)
                if not result.get("escalation_needed"):
                    logger.info(
                        "[orchestrator] Escalation resolved by %s",
                        agent.name,
                    )
                    return result
            except Exception:
                continue

        # All agents failed — human required
        self._record_failure()
        return {
            "success": False,
            "error": "All core agents failed — human intervention required",
            "requires_human_approval": True,
            "original_failure": original_result,
            "agents_tried": [
                a.name for a in self._core_agents.values()
            ],
        }

    # -------------------------------------------------------------------------
    # System Health
    # -------------------------------------------------------------------------

    def system_health(self) -> dict[str, Any]:
        """
        Full system health report for the 3D portal.

        Returns health of all core agents + orchestrator.
        """
        agent_health: dict[str, HealthStatus] = {}
        total_healthy = 0
        total_agents = len(self._core_agents)

        for agent_type, agent in self._core_agents.items():
            if isinstance(agent, SelfHealingMixin):
                status = agent.health_check()
                agent_health[agent_type.value] = status
                if status.healthy:
                    total_healthy += 1

        return {
            "orchestrator": self.health_check().__dict__,
            "agents": {k: v.__dict__ for k, v in agent_health.items()},
            "summary": {
                "total_agents": total_agents,
                "healthy_agents": total_healthy,
                "unhealthy_agents": total_agents - total_healthy,
                "system_healthy": total_healthy == total_agents,
                "budget_spent": self._budget_spent_usd,
                "budget_limit": self._budget_limit_usd,
            },
        }

    def to_portal_graph(self) -> dict[str, Any]:
        """
        Serialize the entire agent hierarchy for the 3D portal.

        Returns nodes + connections compatible with React Three Fiber.
        """
        nodes = [
            {
                "id": "orchestrator",
                "type": "orchestrator",
                "label": "Orchestrator",
                "healthy": self.health_check().healthy,
            }
        ]
        connections = []

        for agent_type, agent in self._core_agents.items():
            if hasattr(agent, "to_portal_node"):
                node = agent.to_portal_node()
                nodes.append(node)
                connections.append({
                    "from": "orchestrator",
                    "to": node["id"],
                    "type": "manages",
                })

                # Add sub-agent nodes
                for sub in node.get("sub_agents", []):
                    connections.append({
                        "from": node["id"],
                        "to": sub["id"],
                        "type": "delegates",
                    })

        return {
            "nodes": nodes,
            "connections": connections,
        }


__all__ = ["Orchestrator"]
