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

import asyncio
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


import uuid
from typing import Any

from .state import EliteStudioState, extract_production_result
from ..models import (
    CompositorResult,
    EnrichedPrompt,
    GenerationResult,
    QualityVerification,
    SynthesizedVision,
    TryOnResult,
)

logger = logging.getLogger(__name__)


def run_sync(coro):
    """Helper to run a coroutine from a synchronous node."""
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            # In a running loop, we should ideally use a thread or just run it.
            # But LangGraph sync nodes are usually run in a way that allows run_until_complete?
            # For now, if loop is running, we might be in trouble if we block it.
            # However, for simplicity in this factory setting:
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


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
    result = run_sync(agent.analyze(state["sku"], state["view"]))
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

    result = run_sync(agent.generate(
        sku=state["sku"],
        view=state["view"],
        generation_spec=vision.unified_spec,
    ))
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
        quality_result = run_sync(llm_agent.verify(
            image_path=gen.output_path,
            expected_spec=vision.unified_spec,
        ))

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
                    comp_result = run_sync(agent.composite(
                        sku=state["sku"],
                        image_path=gen.output_path,
                        scene_name=scene_name,
                        collection=collection,
                    ))
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
    result = run_sync(agent.execute_tryon(
        garment_image_path=garment_path,
        model_image_path=gen.output_path,
        category=category,
    ))

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

    result = run_sync(agent.enrich(
        sku=state["sku"],
        vision_spec=spec,
        style=state.get("style", "flat_lay")
    ))
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

    result = run_sync(agent.upscale(image_path=image_path))
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

    result = run_sync(agent.correct(image_path=image_path))
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

    results = run_sync(agent.generate_variants(
        sku=state["sku"],
        base_image_path=base_path,
        variant_specs=variants,
    ))
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["variants"] = round(elapsed, 2)

    return {
        "variant_results": results,
        "stage_timings": timings,
    }


def three_d_node(state: EliteStudioState) -> dict:
    """Legendary 3D generation node.
    
    Generates a 3D .glb replica and renders front/back/ghost shots.
    Updates the state with the 3D-rendered paths.
    """
    import asyncio
    from ..agents.three_d_agent import ThreeDAgent
    from ..agents.vision_agent import _reference_path

    sku = state["sku"]
    style = state.get("style", "flat_lay")
    
    # We need a reference image (techflat or real photo)
    ref_path = state.get("reference_path") or _reference_path(sku)
    
    # Get the spec from the vision stage or catalog
    spec = ""
    if state.get("enriched_prompt"):
        spec = state["enriched_prompt"].enriched_spec
    elif state.get("vision_result"):
        spec = state["vision_result"].unified_spec
        
    agent = ThreeDAgent()
    
    # Run the async generation
    try:
        # Check if we are already in an event loop (e.g. if called via ainvoke)
        loop = asyncio.get_running_loop()
        # This is tricky in a sync node. Since this node is synchronous in the graph 
        # (func, not afunc), we might need to run it in a thread or just use run_until_complete 
        # if the loop isn't running yet.
        # But for CLI 'invoke', there is usually no loop.
        replica_result = loop.run_until_complete(
            agent.generate_replica(sku, ref_path, spec)
        )
    except RuntimeError:
        # No loop running, use asyncio.run
        replica_result = asyncio.run(agent.generate_replica(sku, ref_path, spec))
    
    if not replica_result["success"]:
        return {
            "status": "error",
            "error": replica_result.get("error", "3D Generation failed"),
            "failed_step": "3d_generation"
        }
    
    # Map the renders to the state paths
    renders = replica_result["renders"]
    
    # Convert to standard GenerationResult for compatibility
    gen_result = agent.generate_result_bridge(replica_result, state["view"])
    
    return {
        "generation_result": gen_result,
        "ghost_mannequin_front_path": renders.get("front", ""),
        "ghost_mannequin_back_path": renders.get("back", ""),
        "3d_model_path": replica_result["glb_path"],
        "3d_fidelity_score": replica_result["fidelity_score"]
    }


# ---------------------------------------------------------------------------
# Phase B2 ghost-mannequin nodes
# ---------------------------------------------------------------------------

_COLLAR_KEYWORDS = {"hoodie", "jacket", "crewneck", "bomber", "windbreaker", "sherpa"}


def _is_collar_garment(sku: str) -> bool:
    """Return True for garments that need neck-in composite."""
    try:
        from ..catalog import Catalog

        cat = Catalog.load()
        name = cat.require(sku).name.lower()
        return any(kw in name for kw in _COLLAR_KEYWORDS)
    except Exception:
        return False


def preflight_node(state: EliteStudioState) -> dict:
    """Dual-vision pre-flight: verify reference image matches CSV spec.

    Only runs for ghost_mannequin style — flat_lay skips (returns empty dict).
    """
    if state.get("style", "flat_lay") != "ghost_mannequin":
        return {}

    sku = state["sku"]

    try:
        from ..catalog import Catalog

        cat = Catalog.load()
        product = cat.require(sku)
        expected_garment = product.name
        
        # Use catalog-defined source image if available, else fallback to rigid SKU lookup
        source_img = product.source_files[0] if product.source_files else ""
        if source_img:
            # Source images live in wordpress-theme/skyyrose-flagship/assets/images/products/
            ref_path = str(__import__("skyyrose.elite_studio.agents.vision_agent", fromlist=["_PRODUCTS_DIR"])._PRODUCTS_DIR / source_img)
        else:
            ref_path = state.get("reference_path") or __import__(
                "skyyrose.elite_studio.agents.vision_agent", fromlist=["_reference_path"]
            )._reference_path(sku)
            
    except Exception as exc:
        return {
            "status": "error",
            "error": f"Preflight catalog load failed: {exc}",
            "failed_step": "preflight",
        }

    from ..agents.vision_agent import DualVisionGate

    gate = DualVisionGate()
    result = run_sync(gate.verify_reference(
        image_path=ref_path,
        sku=sku,
        expected_garment=expected_garment,
    ))

    if not result.passed:
        logger.warning("[Preflight] BLOCKED %s: %s", sku, result.blocking_reason)
        return {
            "preflight_result": result,
            "status": "error",
            "error": f"Preflight blocked: {result.blocking_reason}",
            "failed_step": "preflight",
        }

    return {"preflight_result": result}


def ghost_mannequin_composite_node(state: EliteStudioState) -> dict:
    """Neck-in composite for collar garments (hoodies, jackets, crewnecks).

    For collar garments: crops the top 20% of the back render and pastes
    it behind the front render's neckline area to create the hollow-man effect.
    For non-collar garments: saves the front render as-is (no neck-in).
    """
    import time

    from PIL import Image

    from ..models import GhostMannequinCompositeResult

    start = time.monotonic()
    sku = state["sku"]
    front_path = state.get("ghost_mannequin_front_path", "")
    back_path = state.get("ghost_mannequin_back_path", "")

    if not front_path:
        gen = state.get("generation_result")
        front_path = gen.output_path if gen and gen.success else ""

    if not front_path:
        return {
            "ghost_mannequin_composite_result": GhostMannequinCompositeResult(
                success=False, error="No front render available for composite"
            )
        }

    collar = _is_collar_garment(sku)
    out_dir = __import__("pathlib").Path(front_path).parent
    out_path = str(out_dir / f"{sku}-front-ghost-composite.webp")

    if not collar or not back_path or not __import__("pathlib").Path(back_path).exists():
        # Non-collar or no back render: pass front through unchanged
        __import__("shutil").copy2(front_path, out_path)
        timings = dict(state.get("stage_timings", {}))
        timings["ghost_composite"] = round(time.monotonic() - start, 2)
        return {
            "ghost_mannequin_composite_result": GhostMannequinCompositeResult(
                success=True,
                output_path=out_path,
                front_path=front_path,
                back_path=back_path,
                neck_in_applied=False,
            ),
            "stage_timings": timings,
        }

    # Neck-in composite: paste top 20% of back render behind front render neckline
    try:
        front_img = Image.open(front_path).convert("RGBA")
        back_img = Image.open(back_path).convert("RGBA").resize(front_img.size)

        w, h = front_img.size
        neck_fraction = 0.20
        neck_strip = back_img.crop((0, 0, w, int(h * neck_fraction)))

        composite = Image.new("RGBA", front_img.size, (255, 255, 255, 255))
        composite.paste(neck_strip, (0, 0))
        composite = Image.alpha_composite(composite, front_img)
        composite.convert("RGB").save(out_path, "WEBP", quality=92)
    except Exception as exc:
        return {
            "ghost_mannequin_composite_result": GhostMannequinCompositeResult(
                success=False, error=f"Composite failed: {exc}"
            )
        }

    timings = dict(state.get("stage_timings", {}))
    timings["ghost_composite"] = round(time.monotonic() - start, 2)
    return {
        "ghost_mannequin_composite_result": GhostMannequinCompositeResult(
            success=True,
            output_path=out_path,
            front_path=front_path,
            back_path=back_path,
            neck_in_applied=True,
        ),
        "stage_timings": timings,
    }
