"""skyyrose.elite_studio.agents — dual-agent imagery pipeline (Phase B2 rebuild pending).

File structure preserved from the pre-scorched-earth layout because these
filenames are the correct architectural home for the rebuilt agents. Every
class is a Phase B1 stub that raises NotImplementedError until Phase B2
lands the LangGraph + dual-agent implementations.

See .claude/plans/well-lets-audit-separately-humming-beacon.md for design.
"""

from __future__ import annotations

from skyyrose.elite_studio.agents.color_correction_agent import ColorCorrectionAgent
from skyyrose.elite_studio.agents.compositor_agent import CompositorAgent
from skyyrose.elite_studio.agents.generator_agent import GeneratorAgent
from skyyrose.elite_studio.agents.prompt_enrichment_agent import PromptEnrichmentAgent
from skyyrose.elite_studio.agents.quality_agent import QualityAgent
from skyyrose.elite_studio.agents.safety_agent import SafetyAgent
from skyyrose.elite_studio.agents.tryon_agent import TryonAgent
from skyyrose.elite_studio.agents.upscaling_agent import UpscalingAgent
from skyyrose.elite_studio.agents.variant_agent import VariantAgent
from skyyrose.elite_studio.agents.vision_agent import DualVisionGate

__all__ = [
    "ColorCorrectionAgent",
    "CompositorAgent",
    "DualVisionGate",
    "GeneratorAgent",
    "PromptEnrichmentAgent",
    "QualityAgent",
    "SafetyAgent",
    "TryonAgent",
    "UpscalingAgent",
    "VariantAgent",
]
