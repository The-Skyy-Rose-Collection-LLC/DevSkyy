"""
Graph node functions — thin wrappers around existing agents.

Each node reads from EliteStudioState, calls the corresponding agent,
and returns an updated state dict. LangGraph merges the returned dict
into the shared state automatically.

Agent instances are created once via module-level factories and reused
across invocations. Nodes are intentionally synchronous — the agents
themselves are synchronous (REST calls with retry).
"""

from __future__ import annotations

import logging
import time

from ..agents.compositor_agent import CompositorAgent
from ..agents.generator_agent import GeneratorAgent
from ..agents.quality_agent import QualityAgent
from ..agents.tryon_agent import TryOnAgent, _find_garment_image
from ..agents.vision_agent import VisionAgent
from .state import EliteStudioState

logger = logging.getLogger(__name__)


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
    """Verify generated image quality via Claude Sonnet."""
    start = time.monotonic()
    agent = QualityAgent()

    gen = state.get("generation_result")
    vision = state.get("vision_result")
    if not gen or not gen.success or not vision:
        return {
            "status": "error",
            "error": "No generated image available for QC",
            "failed_step": "quality",
        }

    result = agent.verify(
        image_path=gen.output_path,
        expected_spec=vision.unified_spec,
    )
    elapsed = time.monotonic() - start

    timings = dict(state.get("stage_timings", {}))
    timings["quality"] = round(elapsed, 2)

    return {
        "quality_result": result,
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
