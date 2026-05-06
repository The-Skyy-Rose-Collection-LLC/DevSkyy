"""Tool 3: Route to the best image-gen engine.

F3 finding (load-bearing): engine routing is the dominant signal —
br-001 swung 88 → 30 between gemini-pro and flux-pro. Vision-driven
routing is stochastic because Gemini-vision keywords drive
`route_product()`. The fix: catalog `engine_override` lets us pin
the empirically-verified winner per SKU.

Routing precedence:
    1. Catalog `engine_override` (deterministic, F3-verified per SKU)
    2. `route_product()` vision-driven heuristic (existing logic)

State writes:
    engine, model_id, estimated_cost_usd, override_applied (bool)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.render_pipeline.tools._paths import ensure_repo_paths

ensure_repo_paths()

if TYPE_CHECKING:
    from google.adk.tools.tool_context import ToolContext

# Cost table mirrors nano_banana.router.COST_TABLE — copied verbatim
# rather than imported because the override path doesn't go through
# route_product(), so we still need the cost data here.
_COST_TABLE = {
    "gemini-pro": 0.04,  # NB Pro (gemini-3-pro-image-preview)
    "gemini-flash": 0.04,  # NB Pro everywhere — luxury default (Option A 2026-05-06)
    "gpt-image": 0.08,
    "flux-pro": 0.075,  # Updated 2026-05-05 from observed costs in multi-SKU validator
    "flux-kontext": 0.04,
}


def _model_id_for(engine: str) -> str:
    """Map engine slug → SDK model ID. NB Pro for both gemini engines (luxury)."""
    from llm.model_ids import NANO_BANANA_PRO_MODEL, OPENAI_IMAGE_15_MODEL

    return {
        "gemini-pro": NANO_BANANA_PRO_MODEL,
        "gemini-flash": NANO_BANANA_PRO_MODEL,  # NB Pro everywhere (Option A)
        "gpt-image": OPENAI_IMAGE_15_MODEL,
        "flux-pro": "fal-ai/flux-pro/v1.1",
        "flux-kontext": "fal-ai/flux-pro/kontext",
    }.get(engine, NANO_BANANA_PRO_MODEL)


def route_engine_fn(sku: str, view: str, tool_context: ToolContext) -> dict:
    """Pick the engine. Override → vision-driven fallthrough.

    Args:
        sku: Catalog SKU.
        view: 'front' | 'back' | 'branding'.
        tool_context: ADK-injected.

    Returns dict with engine, model_id, reason, estimated_cost_usd,
    override_applied. State is written for downstream `generate_image_fn`
    and `qa_tournament_fn` (the latter reads engine for learning recorder).
    """
    from nano_banana.catalog import load_catalog
    from nano_banana.router import route_product
    from nano_banana.spec_builder import build_dna_from_sku

    catalog = load_catalog()
    row = catalog.get(sku, {})
    engine_override = row.get("engine_override", "")

    if engine_override:
        engine = engine_override
        model_id = _model_id_for(engine)
        cost = _COST_TABLE.get(engine, 0.05)
        reason = f"catalog engine_override (F3-pinned: {engine})"
        tool_context.state["engine"] = engine
        tool_context.state["model_id"] = model_id
        tool_context.state["estimated_cost_usd"] = cost
        return {
            "engine": engine,
            "model_id": model_id,
            "reason": reason,
            "estimated_cost_usd": cost,
            "override_applied": True,
        }

    # Vision-driven fallthrough — load DNA, call route_product
    dna = build_dna_from_sku(sku)
    product = {**dna.catalog, "sku": sku}
    decisions = route_product(product, dna, view)
    if not decisions:
        return {"error": f"router returned no decisions for {sku}/{view}"}

    primary = decisions[0]
    tool_context.state["engine"] = primary.engine
    tool_context.state["model_id"] = primary.model_id
    tool_context.state["estimated_cost_usd"] = primary.estimated_cost
    return {
        "engine": primary.engine,
        "model_id": primary.model_id,
        "reason": primary.reason,
        "estimated_cost_usd": primary.estimated_cost,
        "override_applied": False,
    }
