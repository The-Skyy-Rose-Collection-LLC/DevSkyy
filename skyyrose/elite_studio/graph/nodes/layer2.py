"""
Layer 2 graph nodes — optional pipeline stages.

prompt_enrichment, upscaling, color_correction, safety, variant.
All disabled by default except prompt_enrichment and safety (see GraphConfig).
"""

from __future__ import annotations

import logging
import time

from ...agents.color_correction_agent import ColorCorrectionAgent
from ...agents.prompt_enrichment_agent import PromptEnrichmentAgent
from ...agents.safety_agent import SafetyAgent
from ...agents.upscaling_agent import UpscalingAgent
from ...agents.variant_agent import VariantAgent
from ..state import EliteStudioState
from ._shared import run_sync

logger = logging.getLogger(__name__)


def prompt_enrichment_node(state: EliteStudioState) -> dict:
    """Enrich vision spec with brand/collection DNA and style modifiers."""
    start = time.monotonic()
    agent = PromptEnrichmentAgent()

    vision = state.get("vision_result")
    spec = vision.unified_spec if vision and vision.success else ""

    # PromptEnrichmentAgent.enrich is synchronous (returns EnrichedPrompt directly).
    # Calling run_sync on a non-awaitable raises TypeError.
    result = agent.enrich(sku=state["sku"], vision_spec=spec, style=state.get("style", "flat_lay"))
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
        from ...models import SynthesizedVision

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

    base_path = gen.output_path if gen and gen.success else ""
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

    results = run_sync(
        agent.generate_variants(
            sku=state["sku"],
            base_image_path=base_path,
            variant_specs=variants,
        )
    )
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["variants"] = round(elapsed, 2)

    return {
        "variant_results": results,
        "stage_timings": timings,
    }
