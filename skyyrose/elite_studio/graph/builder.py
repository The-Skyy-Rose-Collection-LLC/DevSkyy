"""
Graph builder — assembles the Elite Studio StateGraph.

Call ``build_graph()`` once to get a compiled, reusable graph. The
returned object is thread-safe and can be invoked concurrently.

Layer 4 additions to GraphConfig:
- enable_human_review: pause at quality for human approval on uncertain images
- review_confidence_threshold: classifier confidence below which human review triggers
- enable_visual_regression: run SSIM comparison against golden references
"""

from __future__ import annotations

from dataclasses import dataclass, field

from langgraph.graph import END, StateGraph

from .edges import (
    COMPOSITOR,
    FINALIZE,
    GENERATOR,
    HUMAN_REVIEW,
    QUALITY,
    after_compositor,
    after_generation,
    after_human_review,
    after_quality,
    after_quality_v2,
    after_vision,
)
from .nodes import (
    compositor_node,
    finalize_node,
    generator_node,
    human_review_node,
    quality_node,
    vision_node,
)
from .state import EliteStudioState

# Node name constants (mirror edges.py for graph construction)
_VISION = "vision"
_GENERATOR = GENERATOR
_QUALITY = QUALITY
_COMPOSITOR = COMPOSITOR
_FINALIZE = FINALIZE
_HUMAN_REVIEW = HUMAN_REVIEW


@dataclass(frozen=True)
class GraphConfig:
    """Configuration for the Elite Studio graph.

    All fields have sensible defaults so callers only need to specify
    what differs from the standard pipeline.

    Layer 4 fields:
        enable_human_review: When True, uncertain images are paused for
            human approval before continuing. Defaults to False.
        review_confidence_threshold: Classifier confidence below which
            human review is triggered. Only used when enable_human_review
            is True. Defaults to 0.6.
        enable_visual_regression: When True, generated images are compared
            against golden references using SSIM. Defaults to False.
    """

    max_retries: int = 2
    enable_compositor: bool = False
    enable_human_review: bool = False
    review_confidence_threshold: float = 0.6
    enable_visual_regression: bool = False
    extra_nodes: list[str] = field(default_factory=list)


def build_graph(config: GraphConfig | None = None) -> object:
    """Build and compile the Elite Studio StateGraph.

    Returns a ``CompiledGraph`` that can be invoked with
    ``graph.invoke(state_dict)``.

    When ``config.enable_human_review`` is True the graph uses the Layer 4
    ``after_quality_v2`` edge function which can route to the
    ``human_review`` node. Otherwise the original ``after_quality`` edge
    is used for backwards compatibility.

    Args:
        config: Optional graph configuration. Uses defaults if None.

    Returns:
        A compiled LangGraph ``StateGraph`` ready for invocation.
    """
    if config is None:
        config = GraphConfig()

    graph = StateGraph(EliteStudioState)

    # --- Register nodes ---
    graph.add_node(_VISION, vision_node)
    graph.add_node(_GENERATOR, generator_node)
    graph.add_node(_QUALITY, quality_node)
    graph.add_node(_COMPOSITOR, compositor_node)
    graph.add_node(_FINALIZE, finalize_node)
    graph.add_node(_HUMAN_REVIEW, human_review_node)

    # --- Entry point ---
    graph.set_entry_point(_VISION)

    # --- Conditional edges ---
    graph.add_conditional_edges(
        _VISION,
        after_vision,
        {_GENERATOR: _GENERATOR, END: END},
    )
    graph.add_conditional_edges(
        _GENERATOR,
        after_generation,
        {_QUALITY: _QUALITY, END: END},
    )

    # Layer 4: use v2 edge when human review is enabled
    if config.enable_human_review:
        graph.add_conditional_edges(
            _QUALITY,
            after_quality_v2,
            {
                _GENERATOR: _GENERATOR,
                _HUMAN_REVIEW: _HUMAN_REVIEW,
                _COMPOSITOR: _COMPOSITOR,
                _FINALIZE: _FINALIZE,
            },
        )
        graph.add_conditional_edges(
            _HUMAN_REVIEW,
            after_human_review,
            {_GENERATOR: _GENERATOR, _COMPOSITOR: _COMPOSITOR, _FINALIZE: _FINALIZE},
        )
    else:
        graph.add_conditional_edges(
            _QUALITY,
            after_quality,
            {_GENERATOR: _GENERATOR, _COMPOSITOR: _COMPOSITOR, _FINALIZE: _FINALIZE},
        )

    graph.add_conditional_edges(
        _COMPOSITOR,
        after_compositor,
        {_FINALIZE: _FINALIZE},
    )

    # --- Terminal edge ---
    graph.add_edge(_FINALIZE, END)

    return graph.compile()
