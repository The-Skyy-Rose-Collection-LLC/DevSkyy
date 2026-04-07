"""
Graph builder — assembles the Elite Studio StateGraph.

Call ``build_graph()`` once to get a compiled, reusable graph. The
returned object is thread-safe and can be invoked concurrently.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from langgraph.graph import END, StateGraph

from .edges import (
    COMPOSITOR,
    FINALIZE,
    GENERATOR,
    QUALITY,
    after_compositor,
    after_generation,
    after_quality,
    after_vision,
)
from .nodes import (
    compositor_node,
    finalize_node,
    generator_node,
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


@dataclass(frozen=True)
class GraphConfig:
    """Configuration for the Elite Studio graph.

    All fields have sensible defaults so callers only need to specify
    what differs from the standard pipeline.
    """

    max_retries: int = 2
    enable_compositor: bool = False
    # Future layers will add: enable_upscaling, enable_safety, etc.
    extra_nodes: list[str] = field(default_factory=list)


def build_graph(config: GraphConfig | None = None) -> object:
    """Build and compile the Elite Studio StateGraph.

    Returns a ``CompiledGraph`` that can be invoked with
    ``graph.invoke(state_dict)``.

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
