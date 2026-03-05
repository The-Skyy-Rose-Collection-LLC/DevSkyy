"""
Imagery & 3D Core Agent
=========================

Domain: All visual asset generation — photos, VTON, 3D models.
Sub-agents: Gemini Image Gen, Fashn VTON, Tripo 3D, Meshy 3D, HF Spaces.

Merges skyyrose_imagery_agent.py + skyyrose_product_agent.py into one core.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgent, CoreAgentType

logger = logging.getLogger(__name__)


class ImageryCoreAgent(CoreAgent):
    """
    Imagery & 3D Core Agent — all visual asset generation.

    Delegates to sub-agents:
    - gemini_image: AI image generation via Google Gemini
    - fashn_vton: Virtual try-on (FASHN → WeShopAI → IDM-VTON failover)
    - tripo_3d: 3D model generation via Tripo3D API
    - meshy_3d: 3D model generation via Meshy (fallback to Tripo)
    - hf_spaces: HuggingFace Spaces orchestration and quota management

    Self-healing:
    - Provider failover: if Tripo is down → route to Meshy
    - Quality gate: auto-retry with different params if output quality < threshold
    - Quota management: track API limits across all providers
    """

    core_type = CoreAgentType.IMAGERY
    name = "imagery_core"
    description = "Visual asset generation: photos, VTON, 3D models"

    def __init__(self, *, correlation_id: str | None = None, **kwargs: Any) -> None:
        super().__init__(correlation_id=correlation_id, **kwargs)
        self._legacy_imagery: Any = None
        self._legacy_product: Any = None
        self._register_sub_agents()

    def _register_sub_agents(self) -> None:
        """Auto-register all imagery sub-agents."""
        sub_agents = {
            "gemini_image": ("agents.core.imagery.sub_agents.gemini_image", "GeminiImageSubAgent"),
            "fashn_vton": ("agents.core.imagery.sub_agents.fashn_vton", "FashnVtonSubAgent"),
            "tripo_3d": ("agents.core.imagery.sub_agents.tripo_3d", "Tripo3dSubAgent"),
            "meshy_3d": ("agents.core.imagery.sub_agents.meshy_3d", "Meshy3dSubAgent"),
            "hf_spaces": ("agents.core.imagery.sub_agents.hf_spaces", "HfSpacesSubAgent"),
        }
        for name, (module_path, class_name) in sub_agents.items():
            try:
                import importlib

                mod = importlib.import_module(module_path)
                cls = getattr(mod, class_name)
                self.register_sub_agent(name, cls())
            except (ImportError, AttributeError):
                logger.debug("[%s] %s unavailable", self.name, class_name)

    def _get_legacy_imagery(self) -> Any:
        if self._legacy_imagery is None:
            try:
                from agents.skyyrose_imagery_agent import SkyyRoseImageryAgent
                from adk.base import AgentConfig

                config = AgentConfig(name="imagery", description="Imagery operations")
                self._legacy_imagery = SkyyRoseImageryAgent(config)
            except ImportError:
                logger.warning("[%s] Legacy SkyyRoseImageryAgent unavailable", self.name)
        return self._legacy_imagery

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        task_lower = task.lower()

        # 3D model generation
        if any(kw in task_lower for kw in ["3d", "model", "glb", "mesh"]):
            # Try Tripo first, fall back to Meshy
            if "tripo_3d" in self._sub_agents:
                try:
                    return await self.delegate("tripo_3d", task, **kwargs)
                except Exception:
                    if "meshy_3d" in self._sub_agents:
                        return await self.delegate("meshy_3d", task, **kwargs)

        # Virtual try-on
        if any(kw in task_lower for kw in ["vton", "try-on", "try on", "virtual"]):
            if "fashn_vton" in self._sub_agents:
                return await self.delegate("fashn_vton", task, **kwargs)

        # HuggingFace Spaces
        if any(kw in task_lower for kw in ["huggingface", "hf", "space"]):
            if "hf_spaces" in self._sub_agents:
                return await self.delegate("hf_spaces", task, **kwargs)

        # Image generation (default)
        if "gemini_image" in self._sub_agents:
            return await self.delegate("gemini_image", task, **kwargs)

        # Fallback to legacy imagery agent
        legacy = self._get_legacy_imagery()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}

        return {"success": False, "error": f"No handler for imagery task: {task[:100]}"}

    async def _apply_fix(self, diagnosis: Any) -> Any:
        """
        Imagery-specific healing: provider failover.

        If one 3D provider is down, automatically route to the alternative.
        """
        from agents.core.base import FailureCategory, HealResult

        if diagnosis.failure_category == FailureCategory.PROVIDER_DOWN:
            # Attempt failover between 3D providers
            for provider_name in ["tripo_3d", "meshy_3d", "gemini_image"]:
                sub = self._sub_agents.get(provider_name)
                if sub and hasattr(sub, "circuit_breaker_allows"):
                    if sub.circuit_breaker_allows():
                        return HealResult(
                            success=True,
                            message=f"Failover to {provider_name}",
                            changes=[f"Switched provider to {provider_name}"],
                        )

        return await super()._apply_fix(diagnosis)


__all__ = ["ImageryCoreAgent"]
