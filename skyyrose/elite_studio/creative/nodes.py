"""
Creative Operations Hub node functions.

Each node reads from CreativeOperationState, executes a specific creative
intent, and returns an updated state dict. All external calls are wrapped
in try/except — nodes never raise.

"Luxury Grows from Concrete."
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


def entry_node(state: dict) -> dict:
    """Validate intent, build FashionContext, optionally enhance prompt.

    Sets fashion_context in state for downstream nodes to use.
    Returns error state if intent is unrecognized.
    """
    start = time.monotonic()
    intent = state.get("intent", "")
    sku = state.get("sku", "")
    params = state.get("params", {})

    try:
        from .state import CreativeIntent

        valid_intents = {e.value for e in CreativeIntent}
        if intent not in valid_intents:
            return {
                "status": "error",
                "error": f"Unknown intent: {intent!r}. Valid intents: {sorted(valid_intents)}",
                "stage_timings": {
                    **state.get("stage_timings", {}),
                    "entry": time.monotonic() - start,
                },
            }

        # Build FashionContext if we have enough info
        fashion_context: dict | None = None
        if sku or params.get("garment_type") or params.get("collection"):
            try:
                from skyyrose.elite_studio.fashion.context import FashionContextBuilder

                builder = FashionContextBuilder()
                if sku:
                    ctx = builder.build_from_product_catalog(sku)
                else:
                    ctx = builder.build(
                        garment_type=params.get("garment_type", ""),
                        collection=params.get("collection", ""),
                        season=params.get("season", "FW26"),
                    )
                fashion_context = {
                    "garment_type": ctx.garment_type,
                    "fabric": ctx.fabric,
                    "collection_dna": ctx.collection_dna,
                    "season": ctx.season,
                    "photography_style": ctx.photography_style,
                    "color_palette": list(ctx.color_palette),
                    "styling_notes": ctx.styling_notes,
                    "size_range": ctx.size_range,
                    "rendering_spec": ctx.rendering_spec,
                    "trend_alignment": list(ctx.trend_alignment),
                }
            except Exception as exc:
                logger.warning("FashionContext build failed (non-fatal): %s", exc)

        elapsed = time.monotonic() - start
        return {
            "fashion_context": fashion_context,
            "stage_timings": {**state.get("stage_timings", {}), "entry": elapsed},
        }

    except Exception as exc:
        logger.exception("entry_node failed: %s", exc)
        return {
            "status": "error",
            "error": f"entry_node failed: {exc}",
            "stage_timings": {**state.get("stage_timings", {}), "entry": time.monotonic() - start},
        }


def product_render_node(state: dict) -> dict:
    """Run the LangGraph Elite Studio pipeline for a single SKU render."""
    start = time.monotonic()
    sku = state.get("sku", "")
    params = state.get("params", {})
    view = params.get("view", "front")

    try:
        from skyyrose.elite_studio.graph.builder import GraphConfig
        from skyyrose.elite_studio.graph.runner import run_single

        config = GraphConfig(
            enable_compositor=params.get("enable_compositor", False),
            enable_tryon=params.get("enable_tryon", False),
        )
        result = run_single(sku=sku, view=view, config=config)
        render_result = {
            "success": result.status == "success",
            "sku": result.sku,
            "view": result.view,
            "status": result.status,
            "output_path": result.output_path,
            "error": result.error,
        }
        elapsed = time.monotonic() - start
        return {
            "render_result": render_result,
            "stage_timings": {**state.get("stage_timings", {}), "product_render": elapsed},
        }

    except Exception as exc:
        logger.exception("product_render_node failed: %s", exc)
        elapsed = time.monotonic() - start
        return {
            "render_result": {"success": False, "error": str(exc)},
            "status": "error",
            "error": f"product_render failed: {exc}",
            "stage_timings": {**state.get("stage_timings", {}), "product_render": elapsed},
        }


def three_d_model_node(state: dict) -> dict:
    """Generate a 3D model from the product render via ThreeDGenerationPipeline."""
    import asyncio

    start = time.monotonic()
    params = state.get("params", {})
    image_path = params.get("image_path", "")

    try:
        from ai_3d.generation_pipeline import ThreeDGenerationPipeline

        pipeline = ThreeDGenerationPipeline()
        result = asyncio.run(
            pipeline.generate_from_image(
                image_path=image_path,
                prompt=params.get("prompt", ""),
            )
        )
        model_result = {
            "success": result.success,
            "model_path": getattr(result, "model_path", ""),
            "error": getattr(result, "error", ""),
        }
        elapsed = time.monotonic() - start
        return {
            "model_3d_result": model_result,
            "stage_timings": {**state.get("stage_timings", {}), "three_d_model": elapsed},
        }

    except Exception as exc:
        logger.exception("three_d_model_node failed: %s", exc)
        elapsed = time.monotonic() - start
        return {
            "model_3d_result": {"success": False, "error": str(exc)},
            "status": "error",
            "error": f"3d_model failed: {exc}",
            "stage_timings": {**state.get("stage_timings", {}), "three_d_model": elapsed},
        }


def social_pack_node(state: dict) -> dict:
    """Generate a multi-platform social media campaign via SocialMediaAgent."""
    start = time.monotonic()
    params = state.get("params", {})
    fashion_context = state.get("fashion_context") or {}
    collection = params.get("collection", "") or _extract_collection(fashion_context)

    try:
        from agents.social_media_agent import SocialMediaAgent

        agent = SocialMediaAgent()
        campaign = agent.generate_campaign(
            collection=collection,
            campaign_name=params.get("campaign_name", "Collection Drop"),
            max_products=params.get("max_products", 5),
            platforms=params.get("platforms"),
        )
        social_result = {
            "success": True,
            "campaign_name": campaign.name,
            "collection": campaign.collection,
            "post_count": len(campaign.posts) if hasattr(campaign, "posts") else 0,
        }
        elapsed = time.monotonic() - start
        return {
            "social_result": social_result,
            "stage_timings": {**state.get("stage_timings", {}), "social_pack": elapsed},
        }

    except Exception as exc:
        logger.exception("social_pack_node failed: %s", exc)
        elapsed = time.monotonic() - start
        return {
            "social_result": {"success": False, "error": str(exc)},
            "status": "error",
            "error": f"social_pack failed: {exc}",
            "stage_timings": {**state.get("stage_timings", {}), "social_pack": elapsed},
        }


def product_copy_node(state: dict) -> dict:
    """Generate SEO-optimized product copy using LLM."""
    start = time.monotonic()
    params = state.get("params", {})
    sku = state.get("sku", "")
    fashion_context = state.get("fashion_context") or {}

    try:
        garment_type = params.get("garment_type") or fashion_context.get("garment_type", "product")
        collection = params.get("collection") or _extract_collection(fashion_context)
        product_name = params.get("product_name", f"SkyyRose {garment_type.title()}")
        price = params.get("price", 0)

        collection_display = collection.replace("-", " ").title() if collection else "SkyyRose"
        dna = fashion_context.get("collection_dna", "Luxury Grows from Concrete.")
        _ = fashion_context.get("color_palette", [])

        short_description = (
            f"Elevate your look with the {product_name}. "
            f"{collection_display} collection — {dna.split('.')[0] if dna else 'luxury streetwear'}. "
            f"'Luxury Grows from Concrete.' "
        )

        long_description = (
            f"The {product_name} is the cornerstone of SkyyRose's {collection_display} collection. "
            f"Crafted with premium {fashion_context.get('fabric', 'materials')}, "
            f"this piece embodies the SkyyRose ethos: luxury grown from Oakland's concrete foundations. "
            f"{dna} "
            f"Available in sizes {fashion_context.get('size_range', 'S–3XL')}. "
            f"{'Pre-order now — limited edition.' if params.get('is_preorder') else 'Shop now.'}"
        )

        meta_title = f"{product_name} — SkyyRose {collection_display} | Luxury Streetwear"
        meta_description = (
            f"Shop the {product_name} from SkyyRose's {collection_display} collection. "
            f"Premium luxury streetwear from Oakland. "
            f"{'Pre-order available.' if params.get('is_preorder') else 'Free shipping on orders $100+.'}"
        )

        keywords = [
            "SkyyRose",
            "luxury streetwear",
            f"{collection_display} collection",
            garment_type,
            "Oakland fashion",
            "premium streetwear",
            "Luxury Grows from Concrete",
        ]
        if sku:
            keywords.append(sku)

        copy_result = {
            "success": True,
            "sku": sku,
            "product_name": product_name,
            "short_description": short_description.strip(),
            "long_description": long_description.strip(),
            "meta_title": meta_title[:70],
            "meta_description": meta_description[:160],
            "keywords": keywords,
            "price": price,
        }
        elapsed = time.monotonic() - start
        return {
            "copy_result": copy_result,
            "stage_timings": {**state.get("stage_timings", {}), "product_copy": elapsed},
        }

    except Exception as exc:
        logger.exception("product_copy_node failed: %s", exc)
        elapsed = time.monotonic() - start
        return {
            "copy_result": {"success": False, "error": str(exc)},
            "status": "error",
            "error": f"product_copy failed: {exc}",
            "stage_timings": {**state.get("stage_timings", {}), "product_copy": elapsed},
        }


def character_node(state: dict) -> dict:
    """Generate a character sheet via CharacterCreationAgent."""
    start = time.monotonic()
    params = state.get("params", {})

    try:
        from skyyrose.elite_studio.character.agent import CharacterCreationAgent
        from skyyrose.elite_studio.character.models import CharacterSpec

        agent = CharacterCreationAgent()

        # Use Rosie (canonical mascot) if no custom spec provided
        if not params.get("character_name"):
            sheet = agent.create_skyyrose_rosie()
        else:
            spec = CharacterSpec(
                name=params.get("character_name", "Custom Character"),
                style=params.get("style", "realistic"),
                body_description=params.get("body_description", ""),
                face_features=params.get("face_features", ""),
                outfit_base=params.get("outfit_base", "SkyyRose hoodie and joggers"),
                brand_elements=tuple(params.get("brand_elements", ["SkyyRose rose motif"])),
                reference_paths=tuple(params.get("reference_paths", [])),
            )
            sheet = agent.create_sheet(spec)

        character_result = {
            "success": sheet.success,
            "character_name": sheet.spec.name,
            "front_view_prompt": sheet.front_view_prompt,
            "side_view_prompt": sheet.side_view_prompt,
            "back_view_prompt": sheet.back_view_prompt,
            "expression_grid_prompt": sheet.expression_grid_prompt,
            "sprite_description": sheet.sprite_description,
            "error": sheet.error,
        }
        elapsed = time.monotonic() - start
        return {
            "character_result": character_result,
            "stage_timings": {**state.get("stage_timings", {}), "character": elapsed},
        }

    except Exception as exc:
        logger.exception("character_node failed: %s", exc)
        elapsed = time.monotonic() - start
        return {
            "character_result": {"success": False, "error": str(exc)},
            "status": "error",
            "error": f"character_sheet failed: {exc}",
            "stage_timings": {**state.get("stage_timings", {}), "character": elapsed},
        }


def scene_composite_node(state: dict) -> dict:
    """Run scene compositing via CompositorAgent."""
    start = time.monotonic()
    params = state.get("params", {})
    sku = state.get("sku", "")

    try:
        from skyyrose.elite_studio.agents.compositor_agent import CompositorAgent

        agent = CompositorAgent()
        result = agent.composite(
            sku=sku,
            scene_image_path=params.get("scene_image_path", ""),
            model_image_path=params.get("model_image_path", ""),
            collection=params.get("collection", ""),
            scene_name=params.get("scene_name", ""),
        )
        composite_result = {
            "success": result.success,
            "output_path": result.output_path,
            "qa_status": result.qa_status,
            "collection": result.collection,
            "error": result.error,
        }
        elapsed = time.monotonic() - start
        return {
            "composite_result": composite_result,
            "stage_timings": {**state.get("stage_timings", {}), "scene_composite": elapsed},
        }

    except Exception as exc:
        logger.exception("scene_composite_node failed: %s", exc)
        elapsed = time.monotonic() - start
        return {
            "composite_result": {"success": False, "error": str(exc)},
            "status": "error",
            "error": f"scene_composite failed: {exc}",
            "stage_timings": {**state.get("stage_timings", {}), "scene_composite": elapsed},
        }


def design_ideation_node(state: dict) -> dict:
    """Generate design concepts via DesignIdeationAgent."""
    start = time.monotonic()
    params = state.get("params", {})
    fashion_context = state.get("fashion_context") or {}

    try:
        from skyyrose.elite_studio.fashion.design.ideation import DesignBrief, DesignIdeationAgent

        agent = DesignIdeationAgent()
        brief = DesignBrief(
            collection=params.get("collection") or _extract_collection(fashion_context),
            garment_type=params.get("garment_type")
            or fashion_context.get("garment_type", "hoodie"),
            season=params.get("season", "FW26"),
            target_price_usd=float(params.get("target_price_usd", 65.0)),
            design_intent=params.get("design_intent", "Premium SkyyRose luxury streetwear"),
            colorway_preference=params.get("colorway_preference", ""),
            reference_tags=tuple(params.get("reference_tags", [])),
        )
        concept = agent.generate_concept(brief)
        design_result = {
            "success": True,
            "concept_id": concept.concept_id,
            "concept_name": concept.concept_name,
            "headline_description": concept.headline_description,
            "full_description": concept.full_description,
            "colorway_hex": list(concept.colorway_hex),
            "key_design_elements": list(concept.key_design_elements),
            "fabric_specification": concept.fabric_specification,
            "generation_prompt": concept.generation_prompt,
        }
        elapsed = time.monotonic() - start
        return {
            "design_result": design_result,
            "stage_timings": {**state.get("stage_timings", {}), "design_ideation": elapsed},
        }

    except Exception as exc:
        logger.exception("design_ideation_node failed: %s", exc)
        elapsed = time.monotonic() - start
        return {
            "design_result": {"success": False, "error": str(exc)},
            "status": "error",
            "error": f"design_ideation failed: {exc}",
            "stage_timings": {**state.get("stage_timings", {}), "design_ideation": elapsed},
        }


def collection_plan_node(state: dict) -> dict:
    """Generate a collection plan via CollectionPlanner."""
    start = time.monotonic()
    params = state.get("params", {})
    fashion_context = state.get("fashion_context") or {}

    try:
        from skyyrose.elite_studio.fashion.design.collection_planner import CollectionPlanner

        planner = CollectionPlanner()
        collection = (
            params.get("collection") or _extract_collection(fashion_context) or "black-rose"
        )
        plan = planner.plan_collection(
            collection=collection,
            season=params.get("season", "FW26"),
            theme=params.get("theme", "Luxury Grows from Concrete."),
            target_skus_count=int(params.get("target_skus_count", 8)),
        )
        collection_plan_result = {
            "success": True,
            "plan_id": plan.plan_id,
            "collection": plan.collection,
            "season": plan.season,
            "theme": plan.theme,
            "product_categories": list(plan.product_categories),
            "hero_pieces": list(plan.hero_pieces),
            "colorway_strategy": plan.colorway_strategy,
            "pricing_strategy": plan.pricing_strategy,
            "trend_hooks": list(plan.trend_hooks),
            "launch_sequence": list(plan.launch_sequence),
            "editorial_direction": plan.editorial_direction,
        }
        elapsed = time.monotonic() - start
        return {
            "collection_plan_result": collection_plan_result,
            "stage_timings": {**state.get("stage_timings", {}), "collection_plan": elapsed},
        }

    except Exception as exc:
        logger.exception("collection_plan_node failed: %s", exc)
        elapsed = time.monotonic() - start
        return {
            "collection_plan_result": {"success": False, "error": str(exc)},
            "status": "error",
            "error": f"collection_plan failed: {exc}",
            "stage_timings": {**state.get("stage_timings", {}), "collection_plan": elapsed},
        }


def finalize_node(state: dict) -> dict:
    """Set final status and log stage timings."""
    if state.get("status") == "error":
        return {}  # preserve error state as-is

    return {"status": "success"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_collection(fashion_context: dict) -> str:
    """Extract collection slug from fashion context data."""
    dna = fashion_context.get("collection_dna", "")
    if "Black Rose" in dna:
        return "black-rose"
    if "Love Hurts" in dna:
        return "love-hurts"
    if "Signature" in dna:
        return "signature"
    if "Kids Capsule" in dna:
        return "kids-capsule"
    return ""
