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

from ..agents.color_correction_agent import ColorCorrectionAgent
from ..agents.compositor_agent import CompositorAgent
from ..agents.generator_agent import GeneratorAgent
from ..agents.prompt_enrichment_agent import PromptEnrichmentAgent
from ..agents.quality_agent import QualityAgent
from ..agents.safety_agent import SafetyAgent
from ..agents.tryon_agent import TryOnAgent, _find_garment_image
from ..agents.upscaling_agent import UpscalingAgent
from ..agents.variant_agent import VariantAgent
from ..agents.vision_agent import VisionAgent
from ..quality.human_review import HumanReviewGate
from ..quality.ml_classifier import QualityClassifier
from .state import EliteStudioState

logger = logging.getLogger(__name__)

# Lazy import guard so nodes remain testable without prometheus_client installed.
try:
    from monitoring.elite_studio_metrics import record_stage_duration as _record_stage_duration
except ImportError:  # pragma: no cover

    def _record_stage_duration(stage: str, duration_s: float) -> None:  # type: ignore[misc]
        pass


# Approximate token estimates per node call (used for cost tracking).
_VISION_TOKENS_ESTIMATE = 2_000  # dual-provider: Gemini + OpenAI
_GENERATION_TOKENS_ESTIMATE = 1_500  # Gemini image generation prompt
_QC_TOKENS_ESTIMATE = 1_000  # Claude Sonnet QC call
_COMPOSITOR_TOKENS_ESTIMATE = 800  # Gemini QA gate

# Classifier confidence threshold — below this the LLM QC runs as well
_CLASSIFIER_CONFIDENCE_THRESHOLD = 0.8

# Classifier confidence threshold — below this the LLM QC runs as well
_CLASSIFIER_CONFIDENCE_THRESHOLD = 0.8


def _record_cost(job_id: str | None, provider: str, tokens: int) -> None:
    """Record estimated API cost for a node call. No-ops if job_id is None."""
    if not job_id:
        return
    try:
        from ..config import COST_TRACKING_ENABLED
        from ..queue.cost_tracker import PRICING_PER_1K, CostTracker

        if not COST_TRACKING_ENABLED:
            return
        cost_usd = PRICING_PER_1K.get(provider, 0.0) * tokens / 1000
        CostTracker().record(job_id=job_id, provider=provider, tokens=tokens, cost_usd=cost_usd)
    except Exception as exc:
        logger.debug("Cost tracking skipped: %s", exc)


def vision_node(state: EliteStudioState) -> dict:
    """Analyze product images via dual-provider vision (Gemini + OpenAI)."""
    start = time.monotonic()
    agent = VisionAgent()
    result = agent.analyze(state["sku"], state["view"])
    elapsed = time.monotonic() - start

    job_id: str | None = state.get("job_id")  # type: ignore[assignment]
    _record_cost(job_id, "gemini", _VISION_TOKENS_ESTIMATE // 2)
    _record_cost(job_id, "openai", _VISION_TOKENS_ESTIMATE // 2)

    timings = dict(state.get("stage_timings", {}))
    timings["vision"] = round(elapsed, 2)
    _record_stage_duration("vision", elapsed)

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

    job_id: str | None = state.get("job_id")  # type: ignore[assignment]
    _record_cost(job_id, "gemini", _GENERATION_TOKENS_ESTIMATE)

    timings = dict(state.get("stage_timings", {}))
    timings["generation"] = round(elapsed, 2)
    _record_stage_duration("generation", elapsed)

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

    job_id: str | None = state.get("job_id")  # type: ignore[assignment]
    _record_cost(job_id, "anthropic", _QC_TOKENS_ESTIMATE)

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
    _record_stage_duration("quality", elapsed)

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

    if comp_result and comp_result.success:
        job_id: str | None = state.get("job_id")  # type: ignore[assignment]
        _record_cost(job_id, "gemini", _COMPOSITOR_TOKENS_ESTIMATE)

    timings = dict(state.get("stage_timings", {}))
    timings["compositing"] = round(elapsed, 2)
    _record_stage_duration("compositing", elapsed)

    return {
        "compositor_result": comp_result,
        "stage_timings": timings,
    }


def tryon_node(state: EliteStudioState) -> dict:
    """Run virtual try-on in parallel with compositor (additive — never fails the job).

    Skips silently when:
    - generation_result is absent or unsuccessful
    - no garment image can be found for the SKU
    """
    start = time.monotonic()
    timings = dict(state.get("stage_timings", {}))

    gen = state.get("generation_result")
    if not gen or not gen.success:
        logger.debug("tryon_node: skipping — no successful generation result")
        timings["tryon"] = round(time.monotonic() - start, 2)
        return {"tryon_result": None, "stage_timings": timings}

    sku = state["sku"]
    garment_path = _find_garment_image(sku)
    if not garment_path:
        logger.debug("tryon_node: skipping — no garment image found for %s", sku)
        timings["tryon"] = round(time.monotonic() - start, 2)
        return {"tryon_result": None, "stage_timings": timings}

    category = state.get("tryon_category", "upper_body")
    agent = TryOnAgent()
    result = agent.try_on(
        sku=sku,
        garment_image_path=garment_path,
        model_image_path=gen.output_path,
        category=category,
    )

    timings["tryon"] = round(time.monotonic() - start, 2)
    return {"tryon_result": result, "stage_timings": timings}


def finalize_node(state: EliteStudioState) -> dict:
    """Set final status based on accumulated results."""
    # If status is already "error", keep it
    if state.get("status") == "error":
        return {}

    return {
        "status": "success",
    }


# ---------------------------------------------------------------------------
# Layer 2 nodes — optional pipeline stages
# ---------------------------------------------------------------------------


def prompt_enrichment_node(state: EliteStudioState) -> dict:
    """Enrich vision spec with brand/collection DNA and style modifiers."""
    start = time.monotonic()
    agent = PromptEnrichmentAgent()

    vision = state.get("vision_result")
    spec = vision.unified_spec if vision and vision.success else ""

    result = agent.enrich(sku=state["sku"], vision_spec=spec)
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["prompt_enrichment"] = round(elapsed, 2)

    update: dict = {
        "enriched_prompt": result,
        "stage_timings": timings,
    }

    # When enrichment succeeds, propagate the enriched spec back into the
    # vision_result's unified_spec so downstream nodes use it.
    if result.success and vision and result.enriched_spec:
        from ..models import SynthesizedVision

        enriched_vision = SynthesizedVision(
            success=vision.success,
            unified_spec=result.enriched_spec,
            providers_used=vision.providers_used,
            individual_results=vision.individual_results,
            error=vision.error,
        )
        update["vision_result"] = enriched_vision

    return update


def upscaling_node(state: EliteStudioState) -> dict:
    """Upscale the current output image via Real-ESRGAN or PIL LANCZOS."""
    start = time.monotonic()
    agent = UpscalingAgent()

    # Use upscaled path if already upscaled, else generation output
    gen = state.get("generation_result")
    image_path = gen.output_path if gen and gen.success else ""

    if not image_path:
        elapsed = time.monotonic() - start
        timings = dict(state.get("stage_timings", {}))
        timings["upscaling"] = round(elapsed, 2)
        return {
            "upscale_result": None,
            "stage_timings": timings,
        }

    result = agent.upscale(image_path=image_path)
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["upscaling"] = round(elapsed, 2)

    return {
        "upscale_result": result,
        "stage_timings": timings,
    }


def color_correction_node(state: EliteStudioState) -> dict:
    """Apply brand-palette color corrections to the current image."""
    start = time.monotonic()
    agent = ColorCorrectionAgent()

    # Prefer upscaled output if available, else generation output
    upscale = state.get("upscale_result")
    gen = state.get("generation_result")

    if upscale and upscale.success and upscale.output_path:
        image_path = upscale.output_path
    elif gen and gen.success and gen.output_path:
        image_path = gen.output_path
    else:
        elapsed = time.monotonic() - start
        timings = dict(state.get("stage_timings", {}))
        timings["color_correction"] = round(elapsed, 2)
        return {
            "color_result": None,
            "stage_timings": timings,
        }

    result = agent.correct(image_path=image_path)
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["color_correction"] = round(elapsed, 2)

    return {
        "color_result": result,
        "stage_timings": timings,
    }


def safety_node(state: EliteStudioState) -> dict:
    """Check generated image for content safety violations."""
    start = time.monotonic()
    agent = SafetyAgent()

    gen = state.get("generation_result")
    image_path = gen.output_path if gen and gen.success else ""

    if not image_path:
        elapsed = time.monotonic() - start
        timings = dict(state.get("stage_timings", {}))
        timings["safety"] = round(elapsed, 2)
        return {
            "safety_result": None,
            "stage_timings": timings,
        }

    result = agent.check(image_path=image_path)
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["safety"] = round(elapsed, 2)

    update: dict = {
        "safety_result": result,
        "stage_timings": timings,
    }

    # If flagged, mark pipeline as error — routing edge will send to END
    if result.success and result.flagged:
        update["status"] = "error"
        update["failed_step"] = "safety_filter"
        update["error"] = f"Safety filter triggered: {', '.join(result.categories)}"

    return update


def variant_node(state: EliteStudioState) -> dict:
    """Generate image variants (alternate angles/colorways)."""
    start = time.monotonic()
    agent = VariantAgent()

    gen = state.get("generation_result")
    vision = state.get("vision_result")

    base_path = gen.output_path if gen and gen.success else ""
    spec = vision.unified_spec if vision and vision.success else ""

    # Variant names come from state (set via GraphConfig at invocation time)
    variants: list[str] = state.get("variant_specs", [])  # type: ignore[assignment]

    if not variants or not base_path:
        elapsed = time.monotonic() - start
        timings = dict(state.get("stage_timings", {}))
        timings["variants"] = round(elapsed, 2)
        return {
            "variant_results": [],
            "stage_timings": timings,
        }

    results = agent.generate_variants(
        sku=state["sku"],
        base_image_path=base_path,
        spec=spec,
        variants=variants,
    )
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["variants"] = round(elapsed, 2)

    return {
        "variant_results": results,
        "stage_timings": timings,
    }
