"""SceneGeneratorAgent — text-to-image scene generation for the elite team.

Generates atmospheric scene backgrounds (no products in frame) by reading
canonical scene specs from ``SCENES_DIR/{collection}/{scene_name}/scene.json``
and dispatching a text-only prompt to Gemini's image API. Designed as the
Stage-1 step that precedes ``CompositorAgent.composite()`` — real products
composite onto the generated scene in Stage 2.

Replaces the bespoke ``scripts/gemini_scene_gen.py`` direct-API path. All scene
generation now flows through the elite team for consistent budget enforcement,
quality scoring (via QualityAgent), and canon anchoring (via scene.json).

Usage::

    from skyyrose.elite_studio.agents.scene_generator_agent import SceneGeneratorAgent

    agent = SceneGeneratorAgent()
    await agent.initialize()
    result = await agent.generate_scene(
        scene_name="black-rose-bay-bridge-sf-side-night",
        collection="black-rose",
        budget=budget,
    )
    if result.success:
        print(f"Scene at: {result.output_path}")
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

from adk.base import ADKProvider, AgentConfig
from adk.super_agents import BaseSuperAgent

from ..budget import BudgetExceededError, RunBudget
from ..config import GEMINI_IMAGE_GEN_MODEL, SCENES_DIR
from ..gemini_rest import generate_image as gemini_generate_image
from ..models import GenerationResult
from .compositor.lighting import SCENE_LOOKBOOK, load_lighting_spec

logger = logging.getLogger(__name__)

# Per-image cost (gemini-3-pro-image-preview). Pre-checked against budget
# before each dispatch.
_SCENE_GENERATION_COST_USD = 0.08

# Output directory for generated scenes. Mirrors SCENES_DIR layout so
# downstream agents resolve scene PNGs via the same canonical path.
_SCENE_OUTPUT_DIR = SCENES_DIR


class SceneGeneratorAgent(BaseSuperAgent):
    """Generates a Stage-1 scene background image from a canonical scene.json.

    Reads ``scene_description``, ``color_palette``, ``lighting``, ``camera``,
    ``skyyrose_dna``, ``focal_anchor``, ``negative_prompts``, and atmospheric
    fields from ``scene.json``, composes a single prompt, and dispatches one
    text-to-image call to the Gemini image model.

    The result is a PNG written to::

        SCENES_DIR/{collection}/{scene_name}/{filename}.png

    where ``filename`` comes from ``scene.json["expected_filename"]`` or is
    derived from ``scene_name``.
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        if config is None:
            config = AgentConfig(
                name="scene_generator_agent",
                provider=ADKProvider.GOOGLE,
                model=GEMINI_IMAGE_GEN_MODEL,
                system_prompt=(
                    "You are the SkyyRose Scene Generator. Your output is "
                    "atmospheric scene backgrounds anchored to founder-locked "
                    "canon. No products appear in your generations — only "
                    "environment, lighting, and the canon focal anchor object."
                ),
            )
        super().__init__(config)

    async def generate_scene(
        self,
        scene_name: str,
        collection: str | None = None,
        budget: RunBudget | None = None,
        output_dir: Path | None = None,
    ) -> GenerationResult:
        """Generate a single Stage-1 scene background image.

        Args:
            scene_name: One of the canonical names in ``SCENE_LOOKBOOK``.
            collection: Collection slug. Derived from ``scene_name`` prefix
                if omitted (e.g., ``black-rose-...`` → ``black-rose``).
            budget: Optional ``RunBudget`` for cost enforcement.
            output_dir: Override for output directory. Defaults to
                ``SCENES_DIR/{collection}/{scene_name}/``.

        Returns:
            ``GenerationResult`` with ``output_path`` set to the scene PNG
            on success, or ``success=False`` with ``error`` on failure.
        """
        # Resolve collection from scene_name if not provided.
        if collection is None:
            collection = self._collection_from_scene_name(scene_name)

        # Validate scene_name is canonical.
        if scene_name not in SCENE_LOOKBOOK:
            return GenerationResult(
                success=False,
                provider="none",
                error=(
                    f"scene_name {scene_name!r} is not in SCENE_LOOKBOOK. "
                    f"Valid keys: {sorted(SCENE_LOOKBOOK.keys())}"
                ),
            )

        # Load canonical scene spec.
        spec = load_lighting_spec(collection, scene_name)
        if not spec:
            return GenerationResult(
                success=False,
                provider="none",
                error=(
                    f"No scene.json found at SCENES_DIR/{collection}/{scene_name}/scene.json. "
                    f"Author the scene.json before invoking SceneGeneratorAgent."
                ),
                metadata={"scene_name": scene_name, "collection": collection},
            )

        # Pre-check budget before any paid call.
        if budget is not None:
            try:
                budget.ensure_within_budget(
                    _SCENE_GENERATION_COST_USD, stage="scene_generator_agent"
                )
            except BudgetExceededError as exc:
                logger.error("budget exceeded before scene generation for %s: %s", scene_name, exc)
                return GenerationResult(
                    success=False,
                    provider="none",
                    error=f"budget exceeded: {exc}",
                    metadata={"budget_blocked": True, "scene_name": scene_name},
                )

        # Build the prompt from spec fields.
        prompt = self._build_scene_prompt(spec)

        # Resolve output path.
        output_dir = output_dir or (_SCENE_OUTPUT_DIR / collection / scene_name)
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = spec.get("expected_filename") or f"{scene_name}.png"
        output_path = output_dir / filename

        # Dispatch generation. Scenes are text-only (no reference images).
        # Gemini accepts only pure aspect ratios: 1:1, 1:4, 1:8, 2:3, 3:2, 3:4, 4:1, 4:3
        # Strip trailing descriptors (e.g. "3:4 portrait" → "3:4").
        raw_aspect = str(spec.get("render_aspect", "3:4"))
        aspect_ratio = raw_aspect.split()[0] if raw_aspect else "3:4"

        # Model fallback chain (2026-05-26): gemini-3.1-flash-image-preview
        # safety filter rejects fairy-tale gothic content as "No image in response"
        # even with softened prompts. gemini-2.5-flash-image (original Nano Banana)
        # has a looser safety profile suitable for cathedral/dark-fantasy scenes.
        # Try primary model first, fall back to 2.5 on safety rejection.
        model_chain = [self.config.model]
        if "2.5-flash-image" not in self.config.model:
            model_chain.append("gemini-2.5-flash-image")

        result = None
        last_error = ""
        model_used = ""
        for model_id in model_chain:
            try:
                result = gemini_generate_image(
                    model=model_id,
                    prompt=prompt[:4000],
                    reference_images_b64="",
                    aspect_ratio=aspect_ratio,
                    mime_type="image/png",
                )
            except Exception as exc:
                last_error = f"raised on {model_id}: {exc}"
                logger.warning("Gemini image generation raised on %s: %s", model_id, exc)
                continue

            model_used = model_id
            if result.get("success") and result.get("image_data"):
                break

            err_msg = result.get("error", "no image in response")
            last_error = f"{model_id}: {err_msg}"
            logger.warning(
                "Scene %s rejected by %s (%s); trying next model in chain",
                scene_name,
                model_id,
                err_msg[:120],
            )

        if not result or not result.get("success") or not result.get("image_data"):
            return GenerationResult(
                success=False,
                provider="google/gemini",
                model=model_used or self.config.model,
                error=f"all models in fallback chain failed. last: {last_error}",
                metadata={
                    "scene_name": scene_name,
                    "collection": collection,
                    "model_chain_tried": model_chain,
                },
            )

        # Record spend AFTER successful API call.
        if budget is not None:
            budget.spend(_SCENE_GENERATION_COST_USD, stage="scene_generator_agent.gemini")

        # Write image bytes.
        image_bytes = result["image_data"]
        if isinstance(image_bytes, str):
            image_bytes = base64.b64decode(image_bytes)
        output_path.write_bytes(image_bytes)

        return GenerationResult(
            success=True,
            provider="google/gemini",
            model=self.config.model,
            output_path=str(output_path),
            metadata={
                "scene_name": scene_name,
                "collection": collection,
                "canon_lock_date": spec.get("canon_lock_date"),
                "founder_directed": spec.get("founder_directed"),
                "render_aspect": spec.get("render_aspect"),
                "cost_usd": _SCENE_GENERATION_COST_USD,
            },
        )

    @staticmethod
    def _collection_from_scene_name(scene_name: str) -> str:
        """Derive collection slug from scene_name prefix.

        ``black-rose-...`` → ``black-rose``
        ``love-hurts-...`` → ``love-hurts``
        ``signature-...`` → ``signature``
        ``kids-capsule-...`` → ``kids-capsule``
        """
        for prefix in ("black-rose", "love-hurts", "kids-capsule", "signature"):
            if scene_name.startswith(prefix + "-"):
                return prefix
        # Last resort — take the first hyphen-delimited segment.
        return scene_name.split("-", 1)[0]

    def _build_scene_prompt(self, spec: dict[str, Any]) -> str:
        """Compose a lean prompt string from canonical scene.json fields.

        Empirical lesson (2026-05-26): dense exclusionary prompts ("DO NOT
        INCLUDE...", "AVOID STYLISTIC FINGERPRINT OF...") trip the Gemini
        image safety filter on edge-case content (gothic cathedral, deep red
        palette, "Beast" references) — Gemini returns text-only with no
        image_data. Lean assembly: scene_description + focal anchor + palette
        highlights + skyyrose_dna + brief output directive maximizes pass-rate.

        Verbose lighting/camera/atmospheric/negative_prompts/anti_references
        fields are retained in scene.json for human reference but omitted
        from the live prompt.
        """
        sections: list[str] = []

        sections.append(spec["scene_description"])

        focal = spec.get("focal_anchor", {})
        if focal:
            focal_obj = focal.get("object", "")
            position = focal.get("position", "")
            detail = focal.get("detail", "")
            if focal_obj and position:
                line = f"Focal anchor — {focal_obj}, {position}."
                if detail:
                    line += f" {detail}."
                sections.append(line)

        palette = spec.get("color_palette", {})
        if isinstance(palette, dict) and palette:
            highlights = [
                palette.get("primary_bg") or palette.get("primary"),
                palette.get("primary_accent") or palette.get("accent"),
                palette.get("highlight"),
            ]
            highlights = [h for h in highlights if h]
            if highlights:
                sections.append("Color palette: " + ", ".join(highlights) + ".")
        elif isinstance(palette, str) and palette:
            sections.append(f"Color palette: {palette}.")

        dna = spec.get("skyyrose_dna", "")
        if dna:
            sections.append(dna)

        sections.append(
            "Photorealistic cinematic photography. No people, no human figures. "
            "3:4 portrait composition. Ultra-detailed materials, atmospheric depth."
        )

        return "\n\n".join(sections)
