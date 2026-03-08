"""
Deployment & Health Sub-Agent (Consolidated)
================================================

Consolidates: deployment_manager, health_checker.
Wraps agents/operations_agent.py into the new hierarchy.

Parent: Operations Core Agent
Capabilities: Deployment orchestration, health monitoring, uptime checks.
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


class DeployHealthSubAgent(SubAgent):
    """Deployment orchestration and health monitoring."""

    name = "deploy_health"
    parent_type = CoreAgentType.OPERATIONS
    description = "Deployment management, health checks, uptime monitoring"
    capabilities = [
        # deployment_manager
        "deploy",
        "rollback",
        "blue_green",
        "canary_release",
        # health_checker
        "health_check",
        "uptime_monitor",
        "endpoint_probe",
        "resource_usage",
    ]

    ALIASES = ("deployment_manager", "health_checker")

    system_prompt = (
        "You are the Deployment & Health specialist for DevSkyy. "
        "Stack: FastAPI on Vercel (serverless), WordPress on shared hosting, "
        "Next.js frontend on Vercel. You plan deployments (blue-green, canary), "
        "monitor health endpoints, check uptime, and manage rollbacks. "
        "Return deployment checklists and health reports."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["DeployHealthSubAgent"]
