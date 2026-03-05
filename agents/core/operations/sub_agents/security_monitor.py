"""
Security Monitor Sub-Agent
============================

Wraps agents/security_ops_agent.py into the new hierarchy.

Parent: Operations Core Agent
Capabilities: Vulnerability scanning, dependency updates, compliance reporting.
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


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

    system_prompt = (
        "You are the Security Operations specialist for SkyyRose/DevSkyy. "
        "You scan for vulnerabilities (OWASP Top 10), audit dependencies, "
        "check compliance (PCI-DSS for e-commerce, GDPR for EU customers), "
        "and recommend security patches. Return findings with severity levels "
        "(CRITICAL/HIGH/MEDIUM/LOW) and remediation steps."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["SecurityMonitorSubAgent"]
