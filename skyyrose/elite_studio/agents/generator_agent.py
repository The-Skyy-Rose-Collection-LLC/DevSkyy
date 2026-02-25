"""
Generator Agent — Gemini 3 Pro Image Generation

Generates editorial fashion model images from synthesized product specs.
Uses reference product photos for accuracy.
"""

from __future__ import annotations

from ..config import (
    GENERATION_ASPECT_RATIO,
    GENERATION_MODEL,
    OUTPUT_DIR,
)
from ..models import GenerationResult
from ..retry import is_transient_error, retry_on_transient
from ..utils import get_reference_image_path, image_to_base64


class GeneratorAgent:
    """Image generation agent using Gemini 3 Pro.

    Takes a synthesized product specification and generates a
    professional editorial fashion photograph.
    """

    def generate(
        self,
        sku: str,
        view: str,
        generation_spec: str,
        resolution: str = "4K",
    ) -> GenerationResult:
        """Generate fashion model image from specification.

        Args:
            sku: Product SKU (e.g., 'br-001')
            view: Image view ('front', 'back')
            generation_spec: Detailed specification from vision analysis
            resolution: Target resolution label

        Returns:
            GenerationResult with output path or error.
        """
        image_path = get_reference_image_path(sku, view)
        if not image_path:
            return GenerationResult(
                success=False,
                error=f"No reference image for {sku} {view}",
            )

        ref_b64 = image_to_base64(image_path)
        prompt = self._build_prompt(generation_spec, view, resolution)

        from .. import gemini_rest

        try:
            def _call():
                result = gemini_rest.generate_image(
                    model=GENERATION_MODEL,
                    prompt=prompt,
                    reference_b64=ref_b64,
                    aspect_ratio=GENERATION_ASPECT_RATIO,
                )
                if not result["success"]:
                    raise RuntimeError(result.get("error", "Unknown error"))
                return result["image_data"]

            image_data = retry_on_transient(_call, label="[Generator]")
            return self._save_image(image_data, sku, view)

        except Exception as exc:
            return GenerationResult(
                success=False,
                provider="google",
                model=GENERATION_MODEL,
                error=str(exc),
            )

    def _build_prompt(self, spec: str, view: str, resolution: str) -> str:
        """Build generation prompt from spec."""
        return f"""Generate a professional editorial fashion photograph.

REFERENCE PRODUCT:
{spec}

REQUIREMENTS:
- Professional fashion model wearing this exact product
- Editorial lighting (soft, directional, high-end fashion aesthetic)
- Clean neutral background (studio white or subtle gradient)
- Model pose: natural, confident, fashion editorial style
- View: {view} angle
- Focus on garment details and branding
- {resolution} resolution, high quality

CRITICAL:
- Logo and branding must match the reference EXACTLY
- All garment details must be accurate to the specification
- No hallucinations - only what's specified

Generate the image."""

    def _save_image(self, image_data: bytes, sku: str, view: str) -> GenerationResult:
        """Save generated image bytes to disk."""
        output_path = OUTPUT_DIR / sku / f"{sku}-model-{view}-gemini.jpg"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(image_data)

        return GenerationResult(
            success=True,
            provider="google",
            model=GENERATION_MODEL,
            output_path=str(output_path),
        )
