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

Layer 6 additions to GraphConfig:
- enable_tryon: insert virtual try-on node after compositor/finalize routing
- tryon_category: garment category passed to FASHN API
"""

from __future__ import annotations

from dataclasses import dataclass, field

from langgraph.graph import END, StateGraph

from .edges import (
    COLOR_CORRECTION,
    COMPOSITOR,
    FINALIZE,
    GENERATOR,
    GHOST_MANNEQUIN_COMPOSITE,
    HUMAN_REVIEW,
    PREFLIGHT,
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
    ghost_mannequin_composite_node,
    human_review_node,
    preflight_node,
    prompt_enrichment_node,
    quality_node,
    safety_node,
    three_d_node,
    tryon_node,
    upscaling_node,
    variant_node,
    vision_node,
)
from .state import EliteStudioState

# Node name constants (mirror edges.py for graph construction)
_VISION = "vision"
_PREFLIGHT = PREFLIGHT
_GENERATOR = GENERATOR
_QUALITY = QUALITY
_THREE_D = "three_d"
_COMPOSITOR = COMPOSITOR
_GHOST_MANNEQUIN_COMPOSITE = GHOST_MANNEQUIN_COMPOSITE
_FINALIZE = FINALIZE
_PROMPT_ENRICHMENT = PROMPT_ENRICHMENT
_SAFETY = SAFETY
_UPSCALING = UPSCALING
_COLOR_CORRECTION = COLOR_CORRECTION
_VARIANTS = VARIANTS
_HUMAN_REVIEW = HUMAN_REVIEW
_TRYON = "tryon"


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

    Layer 6 fields:
        enable_tryon: When True, a virtual try-on node is inserted after
            quality (additive — errors never fail the main job). Defaults
            to False.
        tryon_category: Garment category for FASHN API. Defaults to
            "upper_body".
    """

    max_retries: int = 2
    enable_compositor: bool = False

    # Layer 2 optional stages
    enable_prompt_enrichment: bool = True  # on by default (pure enrichment, no cost)
    enable_safety: bool = True  # on by default
    enable_upscaling: bool = False  # off by default (costs $)
    enable_color_correction: bool = False  # off by default
    enable_variants: bool = False  # off by default
    variant_specs: list[str] = field(default_factory=list)

    # Layer 4 optional stages
    enable_human_review: bool = False
    review_confidence_threshold: float = 0.6
    enable_visual_regression: bool = False

    # Layer 6 fields:
    enable_tryon: bool = False
    tryon_category: str = "upper_body"

    # Phase B2 ghost-mannequin fields
    enable_ghost_mannequin_preflight: bool = False
    enable_ghost_mannequin_composite: bool = False

    # Phase 16 3D Activation
    enable_3d: bool = False

    # Extension hook (reserved for future layers)

    extra_nodes: list[str] = field(default_factory=list)


def build_graph(config: GraphConfig | None = None) -> object:
    """Build and compile the Elite Studio StateGraph.

    Returns a ``CompiledGraph`` that can be invoked with
    ``graph.invoke(state_dict)``.

    Topology (Layer 1 + Layer 2 optional nodes + Layer 4 quality system
              + Layer 6 virtual try-on):

        vision
          → [prompt_enrichment?]
          → generator
          → [safety?]          # routes to END if flagged
          → quality            # dual-QC: ML classifier + optional LLM fallback
          → [human_review?]    # pauses for human approval when confidence low
          → [retry?]           → generator
          → [upscaling?]
          → [color_correction?]
          → [variants?]        # parallel branch, joins at finalize
          → [compositor?]
          → [tryon?]           # virtual try-on, additive (errors skipped)
          → finalize
          → END

    When ``config.enable_human_review`` is True the graph uses the Layer 4
    ``after_quality_v2`` edge function which can route to the
    ``human_review`` node. Otherwise the original ``after_quality`` edge
    is used for backwards compatibility.

    When ``enable_tryon=True``, a sequential tryon node is inserted after
    quality (alongside compositor routing). The tryon node is additive:
    errors never fail the main job.

    Args:
        config: Optional graph configuration. Uses defaults if None.

    Returns:
        A compiled LangGraph ``StateGraph`` ready for invocation.
    """
    if config is None:
        config = GraphConfig()

    graph = StateGraph(EliteStudioState)

    # --- Register core nodes (always present) ---
    graph.add_node(_VISION, vision_node)
    if not config.enable_3d:
        graph.add_node(_GENERATOR, generator_node)
    graph.add_node(_QUALITY, quality_node)
    graph.add_node(_COMPOSITOR, compositor_node)
    graph.add_node(_FINALIZE, finalize_node)
    graph.add_node(_HUMAN_REVIEW, human_review_node)

    # --- Register optional Layer 2 nodes ---
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

    # --- Register optional Phase B2 ghost-mannequin nodes ---
    if config.enable_ghost_mannequin_preflight:
        graph.add_node(_PREFLIGHT, preflight_node)

    if config.enable_ghost_mannequin_composite:
        graph.add_node(_GHOST_MANNEQUIN_COMPOSITE, ghost_mannequin_composite_node)

    if config.enable_3d:
        graph.add_node(_THREE_D, three_d_node)

    # --- Register optional Layer 6 tryon node ---
    if config.enable_tryon:
        graph.add_node(_TRYON, tryon_node)

    # --- Entry point ---
    graph.set_entry_point(_VISION)

    # Determine what vision routes to
    _active_generator = _THREE_D if config.enable_3d else _GENERATOR
    _post_vision = _active_generator
    if config.enable_prompt_enrichment:
        _post_vision = _PROMPT_ENRICHMENT
    if config.enable_ghost_mannequin_preflight:
        _post_vision = _PREFLIGHT

    # --- vision → [preflight?] → [prompt_enrichment?] → generator ---
    graph.add_conditional_edges(
        _VISION,
        after_vision,
        {_GENERATOR: _post_vision, END: END},
    )

    if config.enable_ghost_mannequin_preflight:
        _post_preflight = _active_generator
        if config.enable_prompt_enrichment:
            _post_preflight = _PROMPT_ENRICHMENT
        graph.add_edge(_PREFLIGHT, _post_preflight)

    if config.enable_prompt_enrichment:
        graph.add_edge(_PROMPT_ENRICHMENT, _active_generator)

    # --- generator → [safety?] → quality ---
    if config.enable_safety:
        graph.add_conditional_edges(
            _active_generator,
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
            _active_generator,
            after_generation,
            {_QUALITY: _QUALITY, END: END},
        )

    # --- quality → [human_review?] → [retry?] → post-processing chain ---
    # Determine what quality/human_review routes to on "proceed"
    _post_quality = _build_post_quality_target(config)

    if config.enable_human_review:
        graph.add_conditional_edges(
            _QUALITY,
            after_quality_v2,
            {
                _GENERATOR: _active_generator,
                _HUMAN_REVIEW: _HUMAN_REVIEW,
                _COMPOSITOR: _post_quality,
                _FINALIZE: _post_quality,
            },
        )
        graph.add_conditional_edges(
            _HUMAN_REVIEW,
            after_human_review,
            {_GENERATOR: _active_generator, _COMPOSITOR: _post_quality, _FINALIZE: _post_quality},
        )
    else:
        graph.add_conditional_edges(
            _QUALITY,
            after_quality,
            {_GENERATOR: _active_generator, _COMPOSITOR: _post_quality, _FINALIZE: _post_quality},
        )

    graph.add_conditional_edges(
        _COMPOSITOR,
        after_compositor,
        {_FINALIZE: _FINALIZE},
    )

    # --- Post-quality chain: upscaling → color_correction → variants → compositor → finalize ---
    _wire_post_quality_chain(graph, config)

    # --- Terminal edge ---
    graph.add_edge(_FINALIZE, END)

    return graph.compile()


def _build_post_quality_target(config: GraphConfig) -> str:
    """Return the first node in the post-quality processing chain."""
    if config.enable_tryon:
        return _TRYON
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
    # Build the ordered chain of optional post-quality nodes
    chain: list[str] = []
    if config.enable_upscaling:
        chain.append(_UPSCALING)
    if config.enable_color_correction:
        chain.append(_COLOR_CORRECTION)
    if config.enable_variants:
        chain.append(_VARIANTS)
    if config.enable_compositor:
        chain.append(_COMPOSITOR)
    if config.enable_ghost_mannequin_composite:
        chain.append(_GHOST_MANNEQUIN_COMPOSITE)
    if config.enable_tryon:
        chain.append(_TRYON)

    if not chain:
        # No optional nodes — quality already routes to FINALIZE directly
        return

    # Wire sequential edges between optional nodes
    for i in range(len(chain) - 1):
        graph.add_edge(chain[i], chain[i + 1])

    # Last optional node → finalize
    graph.add_edge(chain[-1], _FINALIZE)
