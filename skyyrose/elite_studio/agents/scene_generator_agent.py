"""SceneGeneratorAgent — text-to-image scene generation for the elite team.

Generates atmospheric scene backgrounds (no products in frame) by reading
canonical scene specs from ``SCENES_DIR/{collection}/{scene_name}/scene.json``
and dispatching a text-only prompt to OpenAI gpt-image-2 (the founder-locked
imagery engine, 2026-06-08), with Gemini as a fallback retained until OAI scene
renders are validated. Designed as the Stage-1 step that precedes
``CompositorAgent.composite()`` — real products composite onto the generated
scene in Stage 2.

Replaces the bespoke ``scripts/gemini_scene_gen.py`` direct-API path. All scene
generation now flows through the elite team for consistent budget enforcement,
quality scoring (via QualityAgent), and canon anchoring (via scene.json). The
gpt-image-2 call reuses the hardened root client ``scripts/oai_render/client``.

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

import asyncio
import base64
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from adk.base import ADKProvider, AgentConfig
from adk.super_agents import BaseSuperAgent

from ..budget import BudgetExceededError, RunBudget
from ..config import GEMINI_IMAGE_GEN_MODEL, SCENES_DIR
from ..gemini_rest import generate_image as gemini_generate_image
from ..models import GenerationResult
from .compositor.lighting import SCENE_LOOKBOOK, load_lighting_spec

if TYPE_CHECKING:
    from scripts.oai_render.client import OAIImageClient

logger = logging.getLogger(__name__)

# Per-image cost estimates (USD), ensured against budget BEFORE each paid call
# and recorded only AFTER success. gpt-image-2 "high" text-to-image at
# ~1024x1536 (no reference-image tokens) is cheaper than the edit path; treated
# as a conservative floor for the gate. Gemini is the fallback engine.
_OAI_SCENE_COST_USD = 0.30
_GEMINI_SCENE_COST_USD = 0.08

# Output directory for generated scenes. Mirrors SCENES_DIR layout so
# downstream agents resolve scene PNGs via the same canonical path.
_SCENE_OUTPUT_DIR = SCENES_DIR


class SceneGeneratorAgent(BaseSuperAgent):
    """Generates a Stage-1 scene background image from a canonical scene.json.

    Reads ``scene_description``, ``color_palette``, ``lighting``, ``camera``,
    ``skyyrose_dna``, ``focal_anchor``, ``negative_prompts``, and atmospheric
    fields from ``scene.json``, composes a single prompt, and dispatches one
    text-to-image call to OpenAI gpt-image-2 (Gemini fallback).

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
        # Lazily constructed gpt-image-2 client (validates OPENAI_API_KEY on
        # first use). Kept off __init__ so importing/constructing the agent
        # never requires an OpenAI key.
        self._oai: OAIImageClient | None = None

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

        # Build the prompt from spec fields.
        prompt = self._build_scene_prompt(spec)

        # Resolve output path.
        output_dir = output_dir or (_SCENE_OUTPUT_DIR / collection / scene_name)
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = spec.get("expected_filename") or f"{scene_name}.png"
        output_path = output_dir / filename

        # Target size for gpt-image-2 + the pure aspect token Gemini still needs.
        raw_aspect = str(spec.get("render_aspect", "3:4"))
        size = self._aspect_to_size(raw_aspect)
        aspect_ratio = raw_aspect.split()[0] if raw_aspect.strip() else "3:4"

        image_bytes: bytes | str | None = None
        provider = ""
        model_used = ""
        cost_spent = 0.0
        errors: list[str] = []
        budget_blocked = False

        # Primary engine: OpenAI gpt-image-2 (founder-locked, 2026-06-08).
        try:
            image_bytes, model_used, cost_spent = await self._dispatch_oai(prompt, size, budget)
            provider = "openai/gpt-image-2"
        except BudgetExceededError as exc:
            budget_blocked = True
            errors.append(f"openai/gpt-image-2 budget: {exc}")
            logger.warning("OAI scene budget block for %s: %s", scene_name, exc)
        except Exception as exc:  # noqa: BLE001 — any OAI failure falls back to Gemini
            errors.append(f"openai/gpt-image-2: {exc}")
            logger.warning(
                "OAI scene generation failed for %s: %s — falling back to Gemini",
                scene_name,
                exc,
            )

        # Fallback engine: Gemini, retained until OAI scene renders are validated
        # (the locked policy erases nano-banana/Gemini AFTER validation).
        if image_bytes is None:
            try:
                image_bytes, model_used, cost_spent = await self._dispatch_gemini(
                    prompt, aspect_ratio, scene_name, budget
                )
                provider = "google/gemini"
            except BudgetExceededError as exc:
                budget_blocked = True
                errors.append(f"google/gemini budget: {exc}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"google/gemini: {exc}")

        if image_bytes is None:
            return GenerationResult(
                success=False,
                provider="none",
                model="",
                error="all scene engines failed: " + " | ".join(errors),
                metadata={
                    "scene_name": scene_name,
                    "collection": collection,
                    "budget_blocked": budget_blocked,
                },
            )

        # Write image bytes (Gemini may return a base64 str; OAI returns bytes).
        if isinstance(image_bytes, str):
            image_bytes = base64.b64decode(image_bytes)
        output_path.write_bytes(image_bytes)

        return GenerationResult(
            success=True,
            provider=provider,
            model=model_used,
            output_path=str(output_path),
            metadata={
                "scene_name": scene_name,
                "collection": collection,
                "canon_lock_date": spec.get("canon_lock_date"),
                "founder_directed": spec.get("founder_directed"),
                "render_aspect": spec.get("render_aspect"),
                "size": size if provider.startswith("openai") else None,
                "cost_usd": cost_spent,
            },
        )

    async def _dispatch_oai(
        self, prompt: str, size: str, budget: RunBudget | None
    ) -> tuple[bytes, str, float]:
        """Generate a scene via OpenAI gpt-image-2. Raises on any failure.

        Budget is ensured BEFORE the call and recorded only AFTER success, so a
        failed call never spends. The blocking SDK call runs off the event loop.
        """
        from scripts.oai_render import config as oai_config

        if budget is not None:
            budget.ensure_within_budget(_OAI_SCENE_COST_USD, stage="scene_generator_agent.oai")
        image_bytes = await asyncio.to_thread(
            self._oai_client().generate, prompt=prompt[:4000], size=size, background="opaque"
        )
        if budget is not None:
            budget.spend(_OAI_SCENE_COST_USD, stage="scene_generator_agent.oai")
        return image_bytes, oai_config.MODEL, _OAI_SCENE_COST_USD

    def _oai_client(self) -> OAIImageClient:
        """Lazily construct the gpt-image-2 client (validates OPENAI_API_KEY)."""
        if self._oai is None:
            from scripts.oai_render.client import OAIImageClient

            self._oai = OAIImageClient()
        return self._oai

    async def _dispatch_gemini(
        self, prompt: str, aspect_ratio: str, scene_name: str, budget: RunBudget | None
    ) -> tuple[str | bytes, str, float]:
        """Generate a scene via Gemini (fallback). Raises RuntimeError on failure.

        Model fallback chain (2026-05-26): the primary Gemini image model's
        safety filter rejects gothic/dark-fantasy content as "no image in
        response"; gemini-2.5-flash-image has a looser profile. Try primary,
        then 2.5. Gemini accepts only pure aspect ratios (e.g. "3:4").
        """
        if budget is not None:
            budget.ensure_within_budget(
                _GEMINI_SCENE_COST_USD, stage="scene_generator_agent.gemini"
            )

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
            except Exception as exc:  # noqa: BLE001
                last_error = f"raised on {model_id}: {exc}"
                logger.warning("Gemini image generation raised on %s: %s", model_id, exc)
                continue

            model_used = model_id
            if result.get("success") and result.get("image_data"):
                break

            last_error = f"{model_id}: {result.get('error', 'no image in response')}"
            logger.warning(
                "Scene %s rejected by %s (%s); trying next model in chain",
                scene_name,
                model_id,
                last_error[:120],
            )

        if not result or not result.get("success") or not result.get("image_data"):
            raise RuntimeError(f"all Gemini models failed. last: {last_error}")

        if budget is not None:
            budget.spend(_GEMINI_SCENE_COST_USD, stage="scene_generator_agent.gemini")
        return result["image_data"], model_used, _GEMINI_SCENE_COST_USD

    @staticmethod
    def _aspect_to_size(raw_aspect: str) -> str:
        """Map a scene.json ``render_aspect`` to a gpt-image-2 size string.

        gpt-image-2 accepts arbitrary ``WIDTHxHEIGHT`` with both dims divisible
        by 16 and aspect within 1:3..3:1 (Context7-verified). Targets a 1536
        long edge for quality. Falls back to ``1024x1536`` (portrait) when the
        aspect can't be parsed.

        ``"3:4 portrait"`` → ``"1152x1536"``; ``"1:1"`` → ``"1536x1536"``;
        ``"16:9"`` → ``"1536x864"``.
        """
        token = raw_aspect.strip().split()[0] if raw_aspect and raw_aspect.strip() else ""
        ratio: float | None = None
        if ":" in token:
            w_str, _, h_str = token.partition(":")
            try:
                w, h = float(w_str), float(h_str)
                if w > 0 and h > 0:
                    ratio = w / h
            except ValueError:
                ratio = None
        if ratio is None:
            return "1024x1536"
        ratio = max(1 / 3, min(3.0, ratio))  # clamp to gpt-image-2 allowed band

        long_edge = 1536

        def _round16(value: float) -> int:
            return max(256, int(round(value / 16)) * 16)

        if ratio >= 1.0:  # landscape or square
            width, height = long_edge, _round16(long_edge / ratio)
        else:  # portrait
            width, height = _round16(long_edge * ratio), long_edge
        return f"{width}x{height}"

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
