"""
Graph node functions — thin wrappers around existing agents.

Each node reads from EliteStudioState, calls the corresponding agent,
and returns an updated state dict. LangGraph merges the returned dict
into the shared state automatically.

Agent instances are created once via module-level factories and reused
across invocations. Nodes are intentionally synchronous — the agents
themselves are synchronous (REST calls with retry).

Layer 4 additions:
- quality_node now runs ML classifier first; falls back to Claude Sonnet
  only when classifier confidence is below threshold.
- human_review_node submits to HumanReviewGate and polls for decision.
"""

from __future__ import annotations

import logging
import time

from ..agents.compositor_agent import CompositorAgent
from ..agents.generator_agent import GeneratorAgent
from ..agents.quality_agent import QualityAgent
from ..agents.vision_agent import VisionAgent
from ..quality.human_review import HumanReviewGate
from ..quality.ml_classifier import QualityClassifier
from .state import EliteStudioState

logger = logging.getLogger(__name__)

# Classifier confidence threshold — below this the LLM QC runs as well
_CLASSIFIER_CONFIDENCE_THRESHOLD = 0.8


def vision_node(state: EliteStudioState) -> dict:
    """Analyze product images via dual-provider vision (Gemini + OpenAI)."""
    start = time.monotonic()
    agent = VisionAgent()
    result = agent.analyze(state["sku"], state["view"])
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["vision"] = round(elapsed, 2)

    if not result.success:
        return {
            "vision_result": result,
            "status": "error",
            "error": result.error,
            "failed_step": "vision",
            "stage_timings": timings,
        }

    return {
        "vision_result": result,
        "stage_timings": timings,
    }


def generator_node(state: EliteStudioState) -> dict:
    """Generate fashion model image from vision specification."""
    start = time.monotonic()
    agent = GeneratorAgent()

    vision = state.get("vision_result")
    if not vision or not vision.success:
        return {
            "status": "error",
            "error": "No vision result available for generation",
            "failed_step": "generation",
        }

    result = agent.generate(
        sku=state["sku"],
        view=state["view"],
        generation_spec=vision.unified_spec,
    )
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["generation"] = round(elapsed, 2)

    if not result.success:
        return {
            "generation_result": result,
            "status": "error",
            "error": result.error,
            "failed_step": "generation",
            "stage_timings": timings,
        }

    return {
        "generation_result": result,
        "stage_timings": timings,
    }


def quality_node(state: EliteStudioState) -> dict:
    """Dual-QC: ML classifier first, Claude Sonnet fallback on low confidence.

    Decision logic:
    1. Run QualityClassifier (CLIP) — fast, no LLM cost.
    2. If classifier.confidence >= 0.8: use classifier decision, skip LLM.
    3. If classifier.confidence < 0.8: run QualityAgent (Claude Sonnet) as well.
    4. Return both classifier_result and quality_result in state.
    """
    start = time.monotonic()

    gen = state.get("generation_result")
    vision = state.get("vision_result")
    if not gen or not gen.success or not vision:
        return {
            "status": "error",
            "error": "No generated image available for QC",
            "failed_step": "quality",
        }

    # --- Stage 1: ML classifier ---
    classifier = QualityClassifier()
    classifier_result = classifier.predict(gen.output_path)
    logger.info(
        "[QC] classifier: sku=%s score=%.3f confidence=%.3f label=%s",
        state["sku"],
        classifier_result.score,
        classifier_result.confidence,
        classifier_result.label,
    )

    timings = dict(state.get("stage_timings", {}))

    # --- Stage 2: LLM QC (only when classifier is uncertain) ---
    quality_result = None
    if classifier_result.confidence >= _CLASSIFIER_CONFIDENCE_THRESHOLD:
        logger.info(
            "[QC] High-confidence classifier result — skipping LLM QC (confidence=%.3f)",
            classifier_result.confidence,
        )
        # Synthesise a QualityVerification from classifier result alone
        from ..models import QualityVerification

        passed = classifier_result.score >= 0.7
        quality_result = QualityVerification(
            success=True,
            provider="clip",
            model="openai/clip-vit-base-patch32",
            overall_status="pass" if passed else "fail",
            recommendation="approve" if passed else "regenerate",
            details={
                "classifier_score": classifier_result.score,
                "classifier_confidence": classifier_result.confidence,
                "classifier_label": classifier_result.label,
                "source": "ml_classifier",
            },
        )
    else:
        logger.info(
            "[QC] Low classifier confidence (%.3f) — running Claude Sonnet QC",
            classifier_result.confidence,
        )
        llm_agent = QualityAgent()
        quality_result = llm_agent.verify(
            image_path=gen.output_path,
            expected_spec=vision.unified_spec,
        )

    elapsed = time.monotonic() - start
    timings["quality"] = round(elapsed, 2)

    return {
        "quality_result": quality_result,
        "classifier_result": classifier_result,
        "stage_timings": timings,
    }


def human_review_node(state: EliteStudioState) -> dict:
    """Submit generated image to HumanReviewGate and wait for decision.

    On timeout or queue unavailability, defaults to approve so production
    is never blocked indefinitely.

    The review decision is stored in human_review_result. If the reviewer
    rejects the image, quality_result.recommendation is set to "regenerate"
    so the after_quality_v2 edge can trigger a retry.
    """
    start = time.monotonic()

    gen = state.get("generation_result")
    if not gen or not gen.success:
        return {
            "status": "error",
            "error": "No generated image to submit for human review",
            "failed_step": "human_review",
        }

    gate = HumanReviewGate()
    sku = state["sku"]
    job_id = state.get("workflow_id", sku)

    review_id = gate.submit_for_review(sku=sku, image_path=gen.output_path, job_id=job_id)
    decision = gate.get_decision(review_id)

    logger.info(
        "[HumanReview] sku=%s decision=%s reviewer=%s",
        sku,
        decision.decision,
        decision.reviewer,
    )

    elapsed = time.monotonic() - start
    timings = dict(state.get("stage_timings", {}))
    timings["human_review"] = round(elapsed, 2)

    # If reviewer rejected: override quality recommendation to trigger regeneration
    if decision.decision == "reject":
        existing_qc = state.get("quality_result")
        if existing_qc:
            from ..models import QualityVerification

            updated_qc = QualityVerification(
                success=existing_qc.success,
                provider=existing_qc.provider,
                model=existing_qc.model,
                overall_status="fail",
                recommendation="regenerate",
                details={**existing_qc.details, "human_rejected": True, "notes": decision.notes},
                error=existing_qc.error,
            )
            return {
                "human_review_result": decision,
                "quality_result": updated_qc,
                "stage_timings": timings,
            }

    return {
        "human_review_result": decision,
        "stage_timings": timings,
    }


def compositor_node(state: EliteStudioState) -> dict:
    """Composite generated model into scene backgrounds."""
    start = time.monotonic()

    gen = state.get("generation_result")
    if not gen or not gen.success:
        elapsed = time.monotonic() - start
        timings = dict(state.get("stage_timings", {}))
        timings["compositing"] = round(elapsed, 2)
        return {
            "compositor_result": None,
            "stage_timings": timings,
        }

    agent = CompositorAgent()
    comp_result = None

    try:
        from ..agents.compositor_agent import SCENE_LOOKBOOK
        from ..utils import discover_scene_images

        for scene_name, sku_map in SCENE_LOOKBOOK.items():
            if state["sku"] in sku_map:
                collection = (
                    scene_name.rsplit("-", 2)[0] if scene_name.count("-") > 2 else scene_name
                )
                scenes = discover_scene_images(collection)
                if scenes:
                    comp_result = agent.composite(
                        sku=state["sku"],
                        scene_image_path=str(scenes[0]),
                        model_image_path=gen.output_path,
                        collection=collection,
                        scene_name=scene_name,
                    )
                break
    except Exception:
        pass

    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["compositing"] = round(elapsed, 2)

    return {
        "compositor_result": comp_result,
        "stage_timings": timings,
    }


def finalize_node(state: EliteStudioState) -> dict:
    """Set final status based on accumulated results."""
    # If status is already "error", keep it
    if state.get("status") == "error":
        return {}

    return {
        "status": "success",
    }
