"""
EliteStudioState — shared state accumulator for the LangGraph pipeline.

Each node reads from and writes to this TypedDict. LangGraph manages
the state transitions between nodes automatically.
"""

from __future__ import annotations

import uuid
from typing import Any, TypedDict

from ..models import (
    ColorCorrectionResult,
    CompositorResult,
    EnrichedPrompt,
    GenerationResult,
    GhostMannequinCompositeResult,
    PreflightResult,
    QualityVerification,
    SafetyResult,
    SynthesizedVision,
    TryOnResult,
    UpscaleResult,
    VariantResult,
)
from ..quality.human_review import ReviewDecision
from ..quality.ml_classifier import ClassifierResult
from ..quality.visual_regression import RegressionResult


class EliteStudioState(TypedDict, total=False):
    """Shared state flowing through the Elite Studio graph.

    Required fields are set at graph invocation. Optional fields
    are populated by individual nodes as the pipeline progresses.
    """

    # --- Inputs (set at invocation) ---
    sku: str
    view: str
    enable_compositor: bool
    enable_tryon: bool
    tryon_category: str

    # --- Stage results (set by nodes) ---
    vision_result: SynthesizedVision | None
    generation_result: GenerationResult | None
    quality_result: QualityVerification | None
    compositor_result: CompositorResult | None
    tryon_result: TryOnResult | None

    # --- Ghost-mannequin style additions ---
    style: str  # "flat_lay" | "ghost_mannequin" — defaults to "flat_lay"
    preflight_result: PreflightResult | None
    ghost_mannequin_front_path: str
    ghost_mannequin_back_path: str
    ghost_mannequin_composite_result: GhostMannequinCompositeResult | None

    # --- 3D Architecture additions ---
    three_d_model_path: str
    three_d_fidelity_score: float

    # --- Layer 2 stage results (optional — only set when enabled) ---
    enriched_prompt: EnrichedPrompt | None
    upscale_result: UpscaleResult | None
    color_result: ColorCorrectionResult | None
    safety_result: SafetyResult | None
    variant_results: list[VariantResult] | None

    # --- Layer 4 quality results (set by quality_node v2 and human_review_node) ---
    classifier_result: ClassifierResult | None
    human_review_result: ReviewDecision | None
    regression_result: RegressionResult | None

    # --- Control flow ---
    retry_count: int
    max_retries: int
    status: str  # "running", "success", "error"
    error: str
    failed_step: str

    # --- Metadata ---
    workflow_id: str
    stage_timings: dict[str, float]


def create_initial_state(
    sku: str,
    view: str = "front",
    style: str = "flat_lay",
    enable_compositor: bool = False,
    enable_tryon: bool = False,
    tryon_category: str = "upper_body",
    max_retries: int = 2,
) -> EliteStudioState:
    """Create the initial state for a graph invocation."""
    return EliteStudioState(
        sku=sku,
        view=view,
        style=style,
        enable_compositor=enable_compositor,
        enable_tryon=enable_tryon,
        tryon_category=tryon_category,
        vision_result=None,
        generation_result=None,
        quality_result=None,
        compositor_result=None,
        classifier_result=None,
        human_review_result=None,
        regression_result=None,
        tryon_result=None,
        preflight_result=None,
        ghost_mannequin_front_path="",
        ghost_mannequin_back_path="",
        ghost_mannequin_composite_result=None,
        three_d_model_path="",
        three_d_fidelity_score=0.0,
        retry_count=0,
        max_retries=max_retries,
        status="running",
        error="",
        failed_step="",
        workflow_id=str(uuid.uuid4()),
        stage_timings={},
    )


def extract_production_result(state: EliteStudioState) -> Any:
    """Extract a ProductionResult from the final graph state.

    Imported here to avoid circular imports at module level.
    """
    from ..models import ProductionResult

    return ProductionResult(
        sku=state["sku"],
        view=state["view"],
        status=state.get("status", "error"),
        output_path=(
            state["generation_result"].output_path
            if state.get("generation_result") and state["generation_result"].success
            else ""
        ),
        vision=state.get("vision_result"),
        generation=state.get("generation_result"),
        quality=state.get("quality_result"),
        compositing=state.get("compositor_result"),
        tryon=state.get("tryon_result"),
        error=state.get("error", ""),
        step=state.get("failed_step", ""),
    )
