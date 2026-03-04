"""
Coding Doctor Sub-Agent
========================

Wraps agents/coding_doctor_agent.py into the new hierarchy.

Parent: Operations Core Agent
Capabilities: Lint auto-fix, type error resolution, code smell detection.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent

logger = logging.getLogger(__name__)


class CodingDoctorSubAgent(SubAgent):
    """Code quality — lint fix, type check, code health analysis."""

    name = "coding_doctor"
    parent_type = CoreAgentType.OPERATIONS
    description = "Lint auto-fix, type error resolution, code smell detection"
    capabilities = [
        "lint_fix",
        "type_check",
        "code_review",
        "health_report",
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._legacy_agent: Any = None

    def _get_legacy(self) -> Any:
        if self._legacy_agent is None:
            try:
                from agents.coding_doctor_agent import create_coding_doctor

                self._legacy_agent = create_coding_doctor()
            except ImportError:
                logger.warning("[%s] Legacy CodingDoctorAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        legacy = self._get_legacy()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}
        return {"success": False, "error": "CodingDoctorAgent not available"}


__all__ = ["CodingDoctorSubAgent"]
