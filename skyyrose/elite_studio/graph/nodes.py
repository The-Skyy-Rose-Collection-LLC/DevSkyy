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
from ..agents.vision_agent import VisionAgent
from .state import EliteStudioState

logger = logging.getLogger(__name__)

# Approximate token estimates per node call (used for cost tracking).
# These are conservative estimates; real token counts are not yet surfaced
# by the agent layer. Replace with actual counts when agents expose usage.
_VISION_TOKENS_ESTIMATE = 2_000     # dual-provider: Gemini + OpenAI
_GENERATION_TOKENS_ESTIMATE = 1_500  # Gemini image generation prompt
_QC_TOKENS_ESTIMATE = 1_000         # Claude Sonnet QC call
_COMPOSITOR_TOKENS_ESTIMATE = 800    # Gemini QA gate


def _record_cost(job_id: str | None, provider: str, tokens: int) -> None:
    """Record estimated API cost for a node call. No-ops if job_id is None."""
    if not job_id:
        return
    try:
        from ..queue.cost_tracker import CostTracker, PRICING_PER_1K
        from ..config import COST_TRACKING_ENABLED

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

    job_id: str | None = state.get("job_id")  # type: ignore[assignment]
    _record_cost(job_id, "anthropic", _QC_TOKENS_ESTIMATE)

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

    if comp_result and comp_result.success:
        job_id: str | None = state.get("job_id")  # type: ignore[assignment]
        _record_cost(job_id, "gemini", _COMPOSITOR_TOKENS_ESTIMATE)

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
