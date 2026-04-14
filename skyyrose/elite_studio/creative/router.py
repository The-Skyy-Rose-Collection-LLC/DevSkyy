"""
Creative Operations Hub LangGraph router.

Builds the unified StateGraph for all 14 creative intents.

"Luxury Grows from Concrete."
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from .edges import (
    ENTRY,
    PRODUCT_RENDER,
    THREE_D_MODEL,
    SOCIAL_PACK,
    PRODUCT_COPY,
    CHARACTER,
    SCENE_COMPOSITE,
    DESIGN_IDEATION,
    COLLECTION_PLAN,
    FINALIZE,
    after_any,
    after_render,
    route_intent,
)
from .nodes import (
    character_node,
    collection_plan_node,
    design_ideation_node,
    entry_node,
    finalize_node,
    product_copy_node,
    product_render_node,
    scene_composite_node,
    social_pack_node,
    three_d_model_node,
)
from .state import CreativeOperationState


def build_creative_graph():  # type: ignore[return]
    """Build and compile the unified creative operations graph.

    Topology:
        entry
          → route_intent (conditional)
            → product_render → [after_render: social_pack | finalize]
            → three_d_model  → finalize
            → social_pack    → finalize
            → product_copy   → finalize
            → character      → finalize
            → scene_composite → finalize
            → design_ideation → finalize
            → collection_plan → finalize
          → finalize → END

    Returns:
        Compiled LangGraph StateGraph ready for invocation.
    """
    graph = StateGraph(CreativeOperationState)

    # Register all nodes
    graph.add_node(ENTRY, entry_node)
    graph.add_node(PRODUCT_RENDER, product_render_node)
    graph.add_node(THREE_D_MODEL, three_d_model_node)
    graph.add_node(SOCIAL_PACK, social_pack_node)
    graph.add_node(PRODUCT_COPY, product_copy_node)
    graph.add_node(CHARACTER, character_node)
    graph.add_node(SCENE_COMPOSITE, scene_composite_node)
    graph.add_node(DESIGN_IDEATION, design_ideation_node)
    graph.add_node(COLLECTION_PLAN, collection_plan_node)
    graph.add_node(FINALIZE, finalize_node)

    # Entry point
    graph.set_entry_point(ENTRY)

    # entry → route_intent (conditional dispatch to all specialized nodes)
    graph.add_conditional_edges(
        ENTRY,
        route_intent,
        {
            PRODUCT_RENDER: PRODUCT_RENDER,
            THREE_D_MODEL: THREE_D_MODEL,
            SOCIAL_PACK: SOCIAL_PACK,
            PRODUCT_COPY: PRODUCT_COPY,
            CHARACTER: CHARACTER,
            SCENE_COMPOSITE: SCENE_COMPOSITE,
            DESIGN_IDEATION: DESIGN_IDEATION,
            COLLECTION_PLAN: COLLECTION_PLAN,
            FINALIZE: FINALIZE,
        },
    )

    # product_render can chain to social_pack (full_product_launch) or finalize
    graph.add_conditional_edges(
        PRODUCT_RENDER,
        after_render,
        {SOCIAL_PACK: SOCIAL_PACK, FINALIZE: FINALIZE},
    )

    # All other nodes go directly to finalize
    for node in (THREE_D_MODEL, SOCIAL_PACK, PRODUCT_COPY, CHARACTER,
                 SCENE_COMPOSITE, DESIGN_IDEATION, COLLECTION_PLAN):
        graph.add_conditional_edges(node, after_any, {FINALIZE: FINALIZE})

    # Terminal edge
    graph.add_edge(FINALIZE, END)

    return graph.compile()


# Module-level singleton — compiled once, reused across all requests
_CREATIVE_GRAPH = None


def get_creative_graph():
    """Return the cached compiled graph, building it on first call."""
    global _CREATIVE_GRAPH
    if _CREATIVE_GRAPH is None:
        _CREATIVE_GRAPH = build_creative_graph()
    return _CREATIVE_GRAPH
