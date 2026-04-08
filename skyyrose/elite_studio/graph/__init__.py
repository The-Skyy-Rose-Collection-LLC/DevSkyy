"""
Elite Studio graph package — LangGraph-based pipeline engine.

Public API:

    from skyyrose.elite_studio.graph import build_graph, GraphConfig
    from skyyrose.elite_studio.graph import run_single, run_batch
    from skyyrose.elite_studio.graph import EliteStudioState, create_initial_state
"""

from .builder import GraphConfig, build_graph
from .edges import (
    COLOR_CORRECTION,
    COMPOSITOR,
    FINALIZE,
    GENERATOR,
    PROMPT_ENRICHMENT,
    QUALITY,
    SAFETY,
    UPSCALING,
    VARIANTS,
    after_safety,
)
from .nodes import (
    color_correction_node,
    prompt_enrichment_node,
    safety_node,
    upscaling_node,
    variant_node,
)
from .runner import run_batch, run_single
from .state import EliteStudioState, create_initial_state, extract_production_result

__all__ = [
    # Builder
    "GraphConfig",
    "build_graph",
    # Runner
    "run_single",
    "run_batch",
    # State
    "EliteStudioState",
    "create_initial_state",
    "extract_production_result",
    # Layer 2 nodes
    "prompt_enrichment_node",
    "safety_node",
    "upscaling_node",
    "color_correction_node",
    "variant_node",
    # Layer 2 edge functions
    "after_safety",
    # Layer 2 node name constants
    "PROMPT_ENRICHMENT",
    "SAFETY",
    "UPSCALING",
    "COLOR_CORRECTION",
    "VARIANTS",
    # Core node name constants
    "GENERATOR",
    "QUALITY",
    "COMPOSITOR",
    "FINALIZE",
]
