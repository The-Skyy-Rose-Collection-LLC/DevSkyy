"""
GeneratorAgent — Phase 16 Legendary Generation Architect.

Promoted to ADK SuperAgent for comprehensive "Back Data" (telemetry) and
high-fidelity best-of-N image generation with RAS support.

Inherits from BaseSuperAgent to leverage standardized enterprise tools
and observability via Google ADK.
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

from openai import OpenAI

from adk.base import ADKProvider, AgentConfig
from adk.super_agents import BaseSuperAgent

from ..gemini_rest import generate_image as gemini_generate_image
from ..models import GenerationResult

logger = logging.getLogger(__name__)

from llm.model_ids import OPENAI_IMAGE_2_MODEL as _GPT_MODEL

from ..config import GEMINI_IMAGE_GEN_MODEL as _GEMINI_GEN_MODEL

_DEFAULT_OUTPUT_DIR = "renders/output"


class GeneratorAgent(BaseSuperAgent):
    """Dual-agent image generator promoted to ADK SuperAgent."""

    def __init__(
        self, output_dir: str = _DEFAULT_OUTPUT_DIR, config: AgentConfig | None = None
    ) -> None:
        if config is None:
            config = AgentConfig(
                name="legendary_generator_architect",
                provider=ADKProvider.GOOGLE,
                model=_GEMINI_GEN_MODEL,
                system_prompt="You are the Legendary Generator Architect for SkyyRose. Your mission is hyper-realistic luxury imagery.",
            )
        super().__init__(config)

        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._openai = None

    async def initialize(self) -> None:
        """Initialize backend and OpenAI client."""
        await super().initialize()
        self._openai = OpenAI()

    async def generate(
        self, sku: str, view: str, generation_spec: str, reference_images: list[str] | None = None
    ) -> GenerationResult:
        """Generate image from spec with full ADK observability."""
        # Capture "Back Data" via ADK run
        adk_prompt = f"GENERATION TASK: SKU={sku}, VIEW={view}, SPEC={generation_spec}"
        logger.info("Running Legendary Generation for %s via ADK...", sku)
        adk_result = await self.execute(adk_prompt)

        img_a: bytes | None = None
        img_b: bytes | None = None
        err_a = ""
        err_b = ""

        try:
            # Agent A: GPT-Image (Legacy fallback)
            img_a = await self._generate_gpt_image(generation_spec)
        except Exception as exc:
            err_a = str(exc)
            logger.warning("GPT-Image generation failed for %s: %s", sku, exc)

        try:
            # Agent B: Gemini Pro Image (Supports Multi-Image RAS)
            img_b = await self._generate_gemini_image(generation_spec, reference_images)
        except Exception as exc:
            err_b = str(exc)
            logger.warning("Gemini image generation failed for %s: %s", sku, exc)

        metadata = adk_result.to_dict() if hasattr(adk_result, "to_dict") else {}

        if img_a is None and img_b is None:
            return GenerationResult(
                success=False,
                provider="none",
                error=f"Both generators failed. GPT: {err_a} | Gemini: {err_b}",
                metadata=metadata,
            )

        if img_a is None:
            winner_bytes, provider = img_b, "google/gemini"
        elif img_b is None:
            winner_bytes, provider = img_a, "openai/gpt-image"
        else:
            winner = self._pick_winner(
                score_a=len(img_a),
                score_b=len(img_b),
                path_a="a",
                path_b="b",
            )
            winner_bytes = img_a if winner == "a" else img_b
            provider = "openai/gpt-image" if winner == "a" else "google/gemini"

        # Use webp for consistency
        out_path = self._output_dir / f"{sku}-{view}-ghost.webp"
        out_path.write_bytes(winner_bytes)

        return GenerationResult(
            success=True,
            provider=provider,
            model=_GPT_MODEL if "openai" in provider else _GEMINI_GEN_MODEL,
            output_path=str(out_path),
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _generate_gpt_image(self, prompt: str) -> bytes:
        response = self._openai.images.generate(
            model=_GPT_MODEL,
            prompt=prompt[:4000],
            size="1024x1024",
            quality="high",
            response_format="b64_json",
            n=1,
        )
        return base64.b64decode(response.data[0].b64_json)

    async def _generate_gemini_image(
        self, prompt: str, reference_paths: list[str] | None = None
    ) -> bytes:
        from ..agents.vision_agent import _load_image_b64

        b64_list = []
        if reference_paths:
            for p in reference_paths:
                if os.path.exists(p):
                    b64_list.append(_load_image_b64(p))

        result = gemini_generate_image(
            model=_GEMINI_GEN_MODEL,
            prompt=prompt[:2000],
            reference_images_b64=b64_list if b64_list else "",
        )
        if not result.get("success"):
            raise RuntimeError(result.get("error", "Gemini image generation failed"))
        return result["image_data"]

    def _pick_winner(self, score_a: int, score_b: int, path_a: str, path_b: str) -> str:
        """Return 'a' or 'b'. Prefer 'a' on tie (GPT-Image is agent A)."""
        return "b" if score_b > score_a else "a"
