"""
Graph builder — assembles the Elite Studio StateGraph.

Call ``build_graph()`` once to get a compiled, reusable graph. The
returned object is thread-safe and can be invoked concurrently.

Layer 2 optional stages (all disabled by default unless noted):
  - prompt_enrichment  (on by default — pure rule-based, no cost)
  - safety             (on by default — blocks flagged content)
  - upscaling          (off — costs $ via Replicate)
  - color_correction   (off)
  - variants           (off)

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
    COLOR_CORRECTION,
    FINALIZE,
    GENERATOR,
    HUMAN_REVIEW,
    PROMPT_ENRICHMENT,
    QUALITY,
    SAFETY,
    UPSCALING,
    VARIANTS,
    after_compositor,
    after_generation,
    after_human_review,
    after_quality,
    after_quality_v2,
    after_safety,
    after_vision,
)
from .nodes import (
    color_correction_node,
    compositor_node,
    finalize_node,
    generator_node,
    human_review_node,
    prompt_enrichment_node,
    quality_node,
<<<<<<< HEAD
    safety_node,
    upscaling_node,
    variant_node,
=======
    tryon_node,
>>>>>>> elite/layer-6-virtual-tryon
    vision_node,
)
from .state import EliteStudioState

# Node name constants (mirror edges.py for graph construction)
_VISION = "vision"
_GENERATOR = GENERATOR
_QUALITY = QUALITY
_COMPOSITOR = COMPOSITOR
_FINALIZE = FINALIZE
<<<<<<< HEAD
_PROMPT_ENRICHMENT = PROMPT_ENRICHMENT
_SAFETY = SAFETY
_UPSCALING = UPSCALING
_COLOR_CORRECTION = COLOR_CORRECTION
_VARIANTS = VARIANTS
_HUMAN_REVIEW = HUMAN_REVIEW
=======
_TRYON = "tryon"
>>>>>>> elite/layer-6-virtual-tryon


@dataclass(frozen=True)
class GraphConfig:
    """Configuration for the Elite Studio graph.

    All fields have sensible defaults so callers only need to specify
    what differs from the standard pipeline.

    Layer 2 flags:
        enable_prompt_enrichment: Insert rule-based enrichment between vision
            and generator. On by default (free, no external calls).
        enable_safety: Insert safety check between generator and quality.
            On by default (blocks inappropriate content before QC cost).
        enable_upscaling: Insert Real-ESRGAN upscaling after quality gate.
            Off by default (costs Replicate credits).
        enable_color_correction: Insert PIL color correction after upscaling.
            Off by default.
        enable_variants: Generate alternate angle/colorway variants after QC.
            Off by default.
        variant_specs: List of variant names to generate when enable_variants
            is True (e.g., ['back_view', 'side_view']).

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
<<<<<<< HEAD

    # Layer 2 optional stages
    enable_prompt_enrichment: bool = True  # on by default (pure enrichment, no cost)
    enable_safety: bool = True  # on by default
    enable_upscaling: bool = False  # off by default (costs $)
    enable_color_correction: bool = False  # off by default
    enable_variants: bool = False  # off by default
    variant_specs: list[str] = field(default_factory=list)

    # Layer 4 quality gates
    enable_human_review: bool = False
    review_confidence_threshold: float = 0.6
    enable_visual_regression: bool = False

    # Extension hook (reserved for future layers)
=======
    enable_tryon: bool = False
    tryon_category: str = "upper_body"
>>>>>>> elite/layer-6-virtual-tryon
    extra_nodes: list[str] = field(default_factory=list)


def build_graph(config: GraphConfig | None = None) -> object:
    """Build and compile the Elite Studio StateGraph.

    Returns a ``CompiledGraph`` that can be invoked with
    ``graph.invoke(state_dict)``.

<<<<<<< HEAD
    Topology (Layers 1-4):

        vision
          → [prompt_enrichment?]
          → generator
          → [safety?]              # routes to END if flagged
          → quality                # dual-layer: ML classifier + Claude Sonnet
          → [human_review?]        # pauses for human approval if confidence low
          → [retry?]               → generator
          → [upscaling?]
          → [color_correction?]
          → [variants?]
          → [compositor?]
          → finalize
          → END
=======
    When ``enable_tryon=True``, a sequential tryon node is inserted after
    quality (alongside compositor routing). The tryon node is additive:
    errors never fail the main job.
>>>>>>> elite/layer-6-virtual-tryon

    Args:
        config: Optional graph configuration. Uses defaults if None.

    Returns:
        A compiled LangGraph ``StateGraph`` ready for invocation.
    """
    if config is None:
        config = GraphConfig()

    graph = StateGraph(EliteStudioState)

<<<<<<< HEAD
    # --- Register core nodes (always present) ---
=======
    # --- Register core nodes ---
>>>>>>> elite/layer-6-virtual-tryon
    graph.add_node(_VISION, vision_node)
    graph.add_node(_GENERATOR, generator_node)
    graph.add_node(_QUALITY, quality_node)
    graph.add_node(_COMPOSITOR, compositor_node)
    graph.add_node(_FINALIZE, finalize_node)

<<<<<<< HEAD
    # --- Register Layer 2 optional nodes ---
    if config.enable_prompt_enrichment:
        graph.add_node(_PROMPT_ENRICHMENT, prompt_enrichment_node)

    if config.enable_safety:
        graph.add_node(_SAFETY, safety_node)

    if config.enable_upscaling:
        graph.add_node(_UPSCALING, upscaling_node)

    if config.enable_color_correction:
        graph.add_node(_COLOR_CORRECTION, color_correction_node)

    if config.enable_variants:
        graph.add_node(_VARIANTS, variant_node)

    # --- Register Layer 4 optional nodes ---
    if config.enable_human_review:
        graph.add_node(_HUMAN_REVIEW, human_review_node)
=======
    # --- Register optional tryon node ---
    if config.enable_tryon:
        graph.add_node(_TRYON, tryon_node)
>>>>>>> elite/layer-6-virtual-tryon

    # --- Entry point ---
    graph.set_entry_point(_VISION)

<<<<<<< HEAD
    # --- vision → [prompt_enrichment?] → generator ---
    if config.enable_prompt_enrichment:
        graph.add_conditional_edges(
            _VISION,
            after_vision,
            {_GENERATOR: _PROMPT_ENRICHMENT, END: END},
        )
        graph.add_edge(_PROMPT_ENRICHMENT, _GENERATOR)
    else:
        graph.add_conditional_edges(
            _VISION,
            after_vision,
            {_GENERATOR: _GENERATOR, END: END},
        )

    # --- generator → [safety?] → quality ---
    if config.enable_safety:
        graph.add_conditional_edges(
            _GENERATOR,
            after_generation,
            {_QUALITY: _SAFETY, END: END},
        )
        graph.add_conditional_edges(
            _SAFETY,
            after_safety,
            {_QUALITY: _QUALITY, "error_end": END},
        )
    else:
        graph.add_conditional_edges(
            _GENERATOR,
            after_generation,
            {_QUALITY: _QUALITY, END: END},
        )

    # --- quality → [human_review?] → post-processing chain ---
    _post_quality = _build_post_quality_target(config)

    if config.enable_human_review:
        graph.add_conditional_edges(
            _QUALITY,
            after_quality_v2,
            {
                _GENERATOR: _GENERATOR,
                _HUMAN_REVIEW: _HUMAN_REVIEW,
                _COMPOSITOR: _post_quality,
                _FINALIZE: _post_quality,
            },
        )
        graph.add_conditional_edges(
            _HUMAN_REVIEW,
            after_human_review,
            {_GENERATOR: _GENERATOR, _COMPOSITOR: _post_quality, _FINALIZE: _post_quality},
        )
=======
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

    if config.enable_tryon:
        # quality → tryon → (compositor or finalize)
        graph.add_conditional_edges(
            _QUALITY,
            after_quality,
            {_GENERATOR: _GENERATOR, _COMPOSITOR: _COMPOSITOR, _FINALIZE: _TRYON},
        )
        graph.add_conditional_edges(
            _COMPOSITOR,
            after_compositor,
            {_FINALIZE: _TRYON},
        )
        graph.add_edge(_TRYON, _FINALIZE)
>>>>>>> elite/layer-6-virtual-tryon
    else:
        graph.add_conditional_edges(
            _QUALITY,
            after_quality,
<<<<<<< HEAD
            {_GENERATOR: _GENERATOR, _COMPOSITOR: _post_quality, _FINALIZE: _post_quality},
        )

    graph.add_conditional_edges(
        _COMPOSITOR,
        after_compositor,
        {_FINALIZE: _FINALIZE},
    )
=======
            {_GENERATOR: _GENERATOR, _COMPOSITOR: _COMPOSITOR, _FINALIZE: _FINALIZE},
        )
        graph.add_conditional_edges(
            _COMPOSITOR,
            after_compositor,
            {_FINALIZE: _FINALIZE},
        )
>>>>>>> elite/layer-6-virtual-tryon

    # --- Post-quality chain: upscaling → color_correction → variants → compositor → finalize ---
    _wire_post_quality_chain(graph, config)

    # --- Terminal edge ---
    graph.add_edge(_FINALIZE, END)

    return graph.compile()


def _build_post_quality_target(config: GraphConfig) -> str:
    """Return the first node in the post-quality processing chain."""
    if config.enable_upscaling:
        return _UPSCALING
    if config.enable_color_correction:
        return _COLOR_CORRECTION
    if config.enable_variants:
        return _VARIANTS
    if config.enable_compositor:
        return _COMPOSITOR
    return _FINALIZE


def _wire_post_quality_chain(graph: StateGraph, config: GraphConfig) -> None:  # type: ignore[type-arg]
    """Wire the optional post-quality nodes in sequence."""
    chain: list[str] = []
    if config.enable_upscaling:
        chain.append(_UPSCALING)
    if config.enable_color_correction:
        chain.append(_COLOR_CORRECTION)
    if config.enable_variants:
        chain.append(_VARIANTS)
    if config.enable_compositor:
        chain.append(_COMPOSITOR)

    if not chain:
        # No optional nodes — quality already routes to FINALIZE directly
        return

    for i in range(len(chain) - 1):
        graph.add_edge(chain[i], chain[i + 1])

    graph.add_edge(chain[-1], _FINALIZE)
