"""
nodes package — convenience re-exports.

Internal modules: _shared, layer1, layer2, ghost_mannequin.
Callers should import from ``skyyrose.elite_studio.graph.nodes`` (the shim),
not from these sub-modules directly.
"""

from ._shared import _invoke_adk_render_engine, _record_cost, run_sync
from .ghost_mannequin import (
    _COLLAR_KEYWORDS,
    _is_collar_garment,
    ghost_mannequin_composite_node,
    preflight_node,
    three_d_node,
)
from .layer1 import (
    CompositorAgent,
    GeneratorAgent,
    HumanReviewGate,
    QualityAgent,
    QualityClassifier,
    TryOnAgent,
    VisionAgent,
    _find_garment_image,
    compositor_node,
    finalize_node,
    generator_node,
    human_review_node,
    quality_node,
    tryon_node,
    vision_node,
)
from .layer2 import (
    ColorCorrectionAgent,
    color_correction_node,
    prompt_enrichment_node,
    safety_node,
    upscaling_node,
    variant_node,
)

__all__ = [
    # Shared infrastructure
    "run_sync",
    "_record_cost",
    "_invoke_adk_render_engine",
    # Layer 1 nodes
    "vision_node",
    "generator_node",
    "quality_node",
    "human_review_node",
    "compositor_node",
    "tryon_node",
    "finalize_node",
    # Layer 2 nodes
    "prompt_enrichment_node",
    "upscaling_node",
    "color_correction_node",
    "safety_node",
    "variant_node",
    # Ghost mannequin nodes
    "three_d_node",
    "preflight_node",
    "ghost_mannequin_composite_node",
    # Private helpers (re-exported so test patches resolve)
    "_is_collar_garment",
    "_COLLAR_KEYWORDS",
    "_find_garment_image",
    # Agent classes (re-exported so test patches resolve)
    "VisionAgent",
    "GeneratorAgent",
    "QualityAgent",
    "QualityClassifier",
    "CompositorAgent",
    "TryOnAgent",
    "HumanReviewGate",
    "ColorCorrectionAgent",
]
