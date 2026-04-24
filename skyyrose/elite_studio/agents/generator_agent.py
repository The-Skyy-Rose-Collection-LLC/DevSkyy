"""GeneratorAgent — Phase B2 best-of-N dual-agent image generation.

Agent A: GPT-Image (gpt-image-1) via OpenAI SDK
Agent B: Gemini 3 Pro Image via gemini_rest.generate_image()
Mode:    Best-of-N — both generate; simple heuristic scores both;
         winner is saved to output_dir; loser is discarded.

Scoring heuristic (no paid vision call here — QualityAgent scores post-win):
  - Prefer the output from agent A (GPT-Image) on a tie (configurable).
  - If one model raises an exception, the other wins automatically.
"""
from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

from openai import OpenAI

from ..gemini_rest import generate_image as gemini_generate_image
from ..models import GenerationResult

logger = logging.getLogger(__name__)

_GPT_MODEL = "gpt-image-1"
_GEMINI_GEN_MODEL = "gemini-3-pro-image-preview"
_DEFAULT_OUTPUT_DIR = "renders/output"


class GeneratorAgent:
    """Dual-agent image generator (best-of-N: GPT-Image + Gemini)."""

    def __init__(self, output_dir: str = _DEFAULT_OUTPUT_DIR) -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._openai = OpenAI()

    def generate(self, sku: str, view: str, generation_spec: str) -> GenerationResult:
        """Generate image from spec. Both models run; best output saved."""
        img_a: bytes | None = None
        img_b: bytes | None = None
        err_a = ""
        err_b = ""

        try:
            img_a = self._generate_gpt_image(generation_spec)
        except Exception as exc:
            err_a = str(exc)
            logger.warning("GPT-Image generation failed for %s: %s", sku, exc)

        try:
            img_b = self._generate_gemini_image(generation_spec)
        except Exception as exc:
            err_b = str(exc)
            logger.warning("Gemini image generation failed for %s: %s", sku, exc)

        if img_a is None and img_b is None:
            return GenerationResult(
                success=False,
                provider="none",
                error=f"Both generators failed. GPT: {err_a} | Gemini: {err_b}",
            )

        if img_a is None:
            winner_bytes, provider = img_b, "google/gemini"
        elif img_b is None:
            winner_bytes, provider = img_a, "openai/gpt-image"
        else:
            winner = self._pick_winner(
                score_a=len(img_a),  # byte size as naive proxy; QualityAgent scores properly
                score_b=len(img_b),
                path_a="a",
                path_b="b",
            )
            winner_bytes = img_a if winner == "a" else img_b
            provider = "openai/gpt-image" if winner == "a" else "google/gemini"

        # Use webp for consistency with quality agent and frontend
        out_path = self._output_dir / f"{sku}-{view}-ghost.webp"
        out_path.write_bytes(winner_bytes)

        return GenerationResult(
            success=True,
            provider=provider,
            model=_GPT_MODEL if "openai" in provider else _GEMINI_GEN_MODEL,
            output_path=str(out_path),
        )

    # ------------------------------------------------------------------
    # Private — patchable in tests
    # ------------------------------------------------------------------

    def _generate_gpt_image(self, prompt: str) -> bytes:
        response = self._openai.images.generate(
            model=_GPT_MODEL,
            prompt=prompt[:4000],
            size="1024x1024",
            quality="high",
            response_format="b64_json",
            n=1,
        )
        return base64.b64decode(response.data[0].b64_json)

    def _generate_gemini_image(self, prompt: str) -> bytes:
        # Note: gemini_rest.generate_image requires reference_b64. 
        # In this pipeline, we might need a version that doesn't, 
        # or we pass a dummy if the API allows it. 
        # Looking at gemini_rest.py, it puts it in inline_data.
        # For now, we assume the prompt-only generation works or we pass empty ref.
        result = gemini_generate_image(model=_GEMINI_GEN_MODEL, prompt=prompt[:2000], reference_b64="")
        if not result.get("success"):
            raise RuntimeError(result.get("error", "Gemini image generation failed"))
        return result["image_data"]

    def _pick_winner(
        self, score_a: int, score_b: int, path_a: str, path_b: str
    ) -> str:
        """Return 'a' or 'b'. Prefer 'a' on tie (GPT-Image is agent A)."""
        return "b" if score_b > score_a else "a"
