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
        try:
            result = gemini_generate_image(
                model=self.config.model,
                prompt=prompt[:4000],
                reference_images_b64="",
                aspect_ratio=spec.get("render_aspect", "3:4"),
                mime_type="image/png",
            )
        except Exception as exc:
            logger.exception("Gemini image generation raised for %s", scene_name)
            return GenerationResult(
                success=False,
                provider="google/gemini",
                error=f"generation raised: {exc}",
                metadata={"scene_name": scene_name, "collection": collection},
            )

        if not result.get("success"):
            err = result.get("error", "unknown gemini failure")
            return GenerationResult(
                success=False,
                provider="google/gemini",
                model=self.config.model,
                error=err,
                metadata={"scene_name": scene_name, "collection": collection},
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
        """Compose a single prompt string from canonical scene.json fields.

        Sections appended in priority order: scene_description, focal_anchor,
        color_palette, lighting, camera, atmospheric, skyyrose_dna, then
        negative_prompts. Reference brands and anti-references appended last
        as style anchors.
        """
        sections: list[str] = []

        sections.append(spec["scene_description"])

        focal = spec.get("focal_anchor", {})
        if focal:
            sections.append(
                f"FOCAL ANCHOR: {focal.get('object', '')}. "
                f"Position: {focal.get('position', '')}. "
                f"Detail: {focal.get('detail', '')}. "
                f"Rationale: {focal.get('rationale', '')}"
            )

        palette = spec.get("color_palette", {})
        if isinstance(palette, dict) and palette:
            palette_str = "; ".join(f"{k}: {v}" for k, v in palette.items())
            sections.append(f"COLOR PALETTE — {palette_str}")
        elif isinstance(palette, str) and palette:
            sections.append(f"COLOR PALETTE — {palette}")

        lighting = spec.get("lighting", {})
        if lighting:
            lighting_str = "; ".join(f"{k}: {v}" for k, v in lighting.items())
            sections.append(f"LIGHTING — {lighting_str}")

        camera = spec.get("camera", {})
        if camera:
            camera_str = "; ".join(
                f"{k}: {v if not isinstance(v, list) else ', '.join(v)}" for k, v in camera.items()
            )
            sections.append(f"CAMERA — {camera_str}")

        atmospheric = spec.get("atmospheric", {})
        if atmospheric:
            atm_str = "; ".join(f"{k}: {v}" for k, v in atmospheric.items())
            sections.append(f"ATMOSPHERIC — {atm_str}")

        dna = spec.get("skyyrose_dna", "")
        if dna:
            sections.append(f"SKYYROSE DNA — {dna}")

        negatives = spec.get("negative_prompts", [])
        if negatives:
            sections.append("DO NOT INCLUDE: " + "; ".join(negatives))

        refs = spec.get("reference_brands", [])
        if refs:
            sections.append("STYLE REFERENCES: " + ", ".join(refs))

        anti = spec.get("anti_references", [])
        if anti:
            sections.append("AVOID STYLISTIC FINGERPRINT OF: " + ", ".join(anti))

        sections.append(
            "OUTPUT: Photorealistic cinematic image. "
            "NO products, NO people, NO text overlays. "
            "Only the environment and the named focal anchor object. "
            "Ultra-detailed materials, dramatic lighting per spec, "
            "strong atmospheric depth. "
            f"Render aspect: {spec.get('render_aspect', '3:4 portrait')}."
        )

        return "\n\n".join(sections)
