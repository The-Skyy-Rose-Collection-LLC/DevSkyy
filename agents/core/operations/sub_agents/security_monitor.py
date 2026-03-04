"""
Security Monitor Sub-Agent
============================

Wraps agents/security_ops_agent.py into the new hierarchy.

Parent: Operations Core Agent
Capabilities: Vulnerability scanning, dependency updates, compliance reporting.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent

logger = logging.getLogger(__name__)


class SecurityMonitorSubAgent(SubAgent):
    """Security monitoring — vulnerability scanning, auto-remediation."""

    name = "security_monitor"
    parent_type = CoreAgentType.OPERATIONS
    description = "Vulnerability scanning, dependency updates, compliance"
    capabilities = [
        "scan_vulnerabilities",
        "update_dependencies",
        "compliance_report",
        "auto_patch",
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._legacy_agent: Any = None

    def _get_legacy(self) -> Any:
        if self._legacy_agent is None:
            try:
                from agents.security_ops_agent import SecurityOpsAgent

                self._legacy_agent = SecurityOpsAgent()
            except ImportError:
                logger.warning("[%s] Legacy SecurityOpsAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        legacy = self._get_legacy()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}
        return {"success": False, "error": "SecurityOpsAgent not available"}


__all__ = ["SecurityMonitorSubAgent"]
