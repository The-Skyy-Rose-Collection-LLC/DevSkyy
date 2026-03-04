"""
HuggingFace Spaces Sub-Agent
===============================

Wraps agents/skyyrose_spaces_orchestrator.py into the new hierarchy.

Parent: Imagery Core Agent
Capabilities: HF Spaces orchestration, quota management, health checks.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent

logger = logging.getLogger(__name__)


class HfSpacesSubAgent(SubAgent):
    """HuggingFace Spaces orchestration and quota management."""

    name = "hf_spaces"
    parent_type = CoreAgentType.IMAGERY
    description = "HuggingFace Spaces orchestration, health checks, quota management"
    capabilities = [
        "run_space",
        "check_quota",
        "health_check",
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._legacy_orchestrator: Any = None

    def _get_legacy(self) -> Any:
        if self._legacy_orchestrator is None:
            try:
                from agents.skyyrose_spaces_orchestrator import SpacesOrchestrator

                self._legacy_orchestrator = SpacesOrchestrator()
            except (ImportError, AttributeError):
                logger.warning("[%s] Legacy SpacesOrchestrator unavailable", self.name)
        return self._legacy_orchestrator

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        legacy = self._get_legacy()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}
        return {"success": False, "error": "SpacesOrchestrator not available"}


__all__ = ["HfSpacesSubAgent"]
