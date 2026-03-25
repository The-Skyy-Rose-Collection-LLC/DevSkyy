"""
Operations Core Agent
======================

Domain: Deploy, security, health, code quality.
Sub-agents: Deployment Manager, Security Monitor, Health Checker, Coding Doctor.

Wraps the existing OperationsAgent with CoreAgent base.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgent, CoreAgentType

logger = logging.getLogger(__name__)


class OperationsCoreAgent(CoreAgent):
    """
    Operations Core Agent — deploy, security, health, code quality.

    Delegates to sub-agents:
    - deployment_manager: CI/CD, rollback, health check post-deploy
    - security_monitor: Vulnerability scanning, dependency updates, compliance
    - health_checker: Uptime monitoring, auto-restart, alerting
    - coding_doctor: Lint, type check, code smell detection, auto-fix
    """

    core_type = CoreAgentType.OPERATIONS
    name = "operations_core"
    description = "Deployment, security, health monitoring, code quality"

    def __init__(self, *, correlation_id: str | None = None, **kwargs: Any) -> None:
        super().__init__(correlation_id=correlation_id, **kwargs)
        self._legacy_agent: Any = None
        self._register_sub_agents()

    def _register_sub_agents(self) -> None:
        """Auto-register consolidated sub-agents with aliases."""
        try:
            from agents.core.operations.sub_agents.deploy_health import (
                DeployHealthSubAgent,
            )

            agent = DeployHealthSubAgent()
            self.register_sub_agent("deploy_health", agent)
            for alias in DeployHealthSubAgent.ALIASES:
                self.register_sub_agent(alias, agent)
        except ImportError:
            logger.debug("[%s] DeployHealthSubAgent unavailable", self.name)

        try:
            from agents.core.operations.sub_agents.security_monitor import (
                SecurityMonitorSubAgent,
            )

            self.register_sub_agent("security_monitor", SecurityMonitorSubAgent())
        except ImportError:
            logger.debug("[%s] SecurityMonitorSubAgent unavailable", self.name)

        try:
            from agents.core.operations.sub_agents.coding_doctor import (
                CodingDoctorSubAgent,
            )

            self.register_sub_agent("coding_doctor", CodingDoctorSubAgent())
        except ImportError:
            logger.debug("[%s] CodingDoctorSubAgent unavailable", self.name)

        # SDK-powered agents (tool-use enabled)
        try:
            from agents.claude_sdk.domain_agents.operations import (
                SDKCodeDoctorAgent,
                SDKDeployRunnerAgent,
                SDKSecurityScannerAgent,
            )

            self.register_sub_agent("sdk_deploy_runner", SDKDeployRunnerAgent())
            self.register_sub_agent("sdk_code_doctor", SDKCodeDoctorAgent())
            self.register_sub_agent("sdk_security_scanner", SDKSecurityScannerAgent())
        except ImportError:
            logger.debug("[%s] SDK operations agents unavailable", self.name)

    def _get_legacy_agent(self) -> Any:
        if self._legacy_agent is None:
            try:
                from adk.base import AgentConfig
                from agents.operations_agent import OperationsAgent

                config = AgentConfig(name="operations", description="Operations")
                self._legacy_agent = OperationsAgent(config)
            except ImportError:
                logger.warning("[%s] Legacy OperationsAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        task_lower = task.lower()
        # Prefer SDK agents (tool-use) when "run", "execute", "fix",
        # "scan", or "check" indicate action is needed, not just advice.
        needs_action = any(
            kw in task_lower for kw in ["run", "execute", "fix", "scan", "check", "patch"]
        )

        if any(kw in task_lower for kw in ["deploy", "rollback", "release", "ci", "cd"]):
            if needs_action and "sdk_deploy_runner" in self._sub_agents:
                return await self.delegate("sdk_deploy_runner", task, **kwargs)
            if "deployment_manager" in self._sub_agents:
                return await self.delegate("deployment_manager", task, **kwargs)

        if any(kw in task_lower for kw in ["security", "vulnerability", "cve", "audit"]):
            if needs_action and "sdk_security_scanner" in self._sub_agents:
                return await self.delegate("sdk_security_scanner", task, **kwargs)
            if "security_monitor" in self._sub_agents:
                return await self.delegate("security_monitor", task, **kwargs)

        if any(kw in task_lower for kw in ["health", "uptime", "monitor", "status"]):
            if needs_action and "sdk_deploy_runner" in self._sub_agents:
                return await self.delegate("sdk_deploy_runner", task, **kwargs)
            if "health_checker" in self._sub_agents:
                return await self.delegate("health_checker", task, **kwargs)

        if any(kw in task_lower for kw in ["lint", "type", "code", "quality", "fix"]):
            if needs_action and "sdk_code_doctor" in self._sub_agents:
                return await self.delegate("sdk_code_doctor", task, **kwargs)
            if "coding_doctor" in self._sub_agents:
                return await self.delegate("coding_doctor", task, **kwargs)

        legacy = self._get_legacy_agent()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}

        return {"success": False, "error": f"No handler for operations task: {task[:100]}"}


__all__ = ["OperationsCoreAgent"]
