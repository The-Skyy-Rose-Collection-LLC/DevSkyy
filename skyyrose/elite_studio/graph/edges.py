"""
Conditional edge functions for the Elite Studio graph.

Each function takes the current state and returns the name of the
next node to execute. LangGraph uses these as routing decisions
at conditional branch points.
"""

from __future__ import annotations

from .state import EliteStudioState

# Node name constants
END = "__end__"
GENERATOR = "generator"
QUALITY = "quality"
COMPOSITOR = "compositor"
FINALIZE = "finalize"


def after_vision(state: EliteStudioState) -> str:
    """Route after vision analysis: continue or stop."""
    vision = state.get("vision_result")
    if not vision or not vision.success:
        return END
    return GENERATOR


def after_generation(state: EliteStudioState) -> str:
    """Route after image generation: continue or stop."""
    gen = state.get("generation_result")
    if not gen or not gen.success:
        return END
    return QUALITY


def after_quality(state: EliteStudioState) -> str:
    """Route after QC: retry generation, go to compositor, or finalize.

    Retry conditions:
        - QC recommendation is "regenerate"
        - retry_count < max_retries

    Compositor conditions:
        - enable_compositor is True
        - Generation succeeded
    """
    qc = state.get("quality_result")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    # Check if QC recommends regeneration and we have retries left
    if qc and qc.success and qc.recommendation == "regenerate" and retry_count < max_retries:
        return GENERATOR

    # Check if compositor is enabled
    if state.get("enable_compositor", False):
        return COMPOSITOR

    return FINALIZE


def after_compositor(state: EliteStudioState) -> str:
    """Always finalize after compositing."""
    return FINALIZE
