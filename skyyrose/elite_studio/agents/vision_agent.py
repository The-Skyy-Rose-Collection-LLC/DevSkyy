"""
Vision Agent — Multi-Provider Product Analysis

Uses BOTH Gemini Flash AND OpenAI GPT-4o to analyze product reference images.
Synthesizes both analyses into a unified specification for image generation.

Fallback: If one provider fails, the other's analysis is used alone.
"""

from __future__ import annotations

from typing import Any

from ..config import (
    VISION_GEMINI_MODEL,
    VISION_OPENAI_MODEL,
    get_openai_client,
)
from ..models import SynthesizedVision, VisionAnalysis
from ..retry import is_transient_error, retry_on_transient
from ..utils import get_reference_image_path, image_to_base64, load_product_data


def _build_vision_prompt(product_data: Any, sku: str) -> str:
    """Build the shared vision analysis prompt."""
    return f"""Analyze this SkyyRose product photo in extreme detail for AI generation.

PRODUCT: {product_data.garment_type_lock or sku.upper()}
COLLECTION: {product_data.collection}

Provide ultra-detailed specifications:

1. **Garment Construction**
   - Silhouette, fit, cut, length
   - Sleeve style, neckline
   - Construction details

2. **Fabric & Color**
   - Material type, texture, weight, finish
   - Exact color shades
   - Color blocking patterns

3. **Branding & Logos** (CRITICAL FOR ACCURACY)
   - Location of each logo
   - Size (approximate inches)
   - Technique: embroidered / silicone / printed / sublimation / embossed / patch
   - Colors in each logo
   - Readable text

4. **Hardware & Details**
   - Ribbing, drawstrings, pockets
   - Zippers, buttons, snaps
   - Trim or binding

5. **Fit & Drape**
   - How it will hang on a model
   - Key fit points

Be extremely specific - this drives 4K AI generation accuracy."""


class VisionAgent:
    """Multi-provider vision analysis agent.

    Calls Gemini Flash AND OpenAI GPT-4o in sequence (not parallel,
    to respect rate limits). Synthesizes results into a unified spec.
    """

    def analyze(self, sku: str, view: str = "front") -> SynthesizedVision:
        """Run dual-provider vision analysis.

        Returns SynthesizedVision with merged spec from both providers.
        Falls back to single provider if one fails.
        """
        product = load_product_data(sku)
        image_path = get_reference_image_path(sku, view)

        if not image_path:
            return SynthesizedVision(
                success=False,
                error=f"No reference image found for {sku} {view}",
            )

        image_b64 = image_to_base64(image_path)
        prompt = _build_vision_prompt(product, sku)

        results: list[VisionAnalysis] = []
        providers_used: list[str] = []

        # Provider 1: Gemini Flash
        gemini_result = self._analyze_gemini(prompt, image_b64)
        results.append(gemini_result)
        if gemini_result.success:
            providers_used.append("gemini")
            print(f"   [Gemini] {gemini_result.char_count} chars")

        # Provider 2: OpenAI GPT-4o
        openai_result = self._analyze_openai(prompt, image_b64)
        results.append(openai_result)
        if openai_result.success:
            providers_used.append("openai")
            print(f"   [OpenAI] {openai_result.char_count} chars")

        # Synthesize
        if not providers_used:
            return SynthesizedVision(
                success=False,
                error=f"All vision providers failed: "
                f"gemini={gemini_result.error}, openai={openai_result.error}",
                individual_results=tuple(results),
            )

        unified_spec = self._synthesize(results, providers_used)
        return SynthesizedVision(
            success=True,
            unified_spec=unified_spec,
            providers_used=tuple(providers_used),
            individual_results=tuple(results),
        )

    def _analyze_gemini(self, prompt: str, image_b64: str) -> VisionAnalysis:
        """Run Gemini Flash vision analysis via direct REST API."""
        from .. import gemini_rest

        try:
            def _call():
                result = gemini_rest.analyze_vision(
                    model=VISION_GEMINI_MODEL,
                    prompt=prompt,
                    image_b64=image_b64,
                )
                if not result["success"]:
                    raise RuntimeError(result.get("error", "Unknown error"))
                return result["text"]

            text = retry_on_transient(_call, label="[Gemini]")
            return VisionAnalysis(
                success=True,
                provider="google",
                model=VISION_GEMINI_MODEL,
                analysis=text,
                char_count=len(text),
            )
        except Exception as exc:
            return VisionAnalysis(
                success=False,
                provider="google",
                model=VISION_GEMINI_MODEL,
                error=str(exc),
            )

    def _analyze_openai(self, prompt: str, image_b64: str) -> VisionAnalysis:
        """Run OpenAI GPT-4o vision analysis with retry."""
        try:
            def _call():
                client = get_openai_client()
                response = client.chat.completions.create(
                    model=VISION_OPENAI_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_b64}",
                                        "detail": "high",
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=2000,
                    temperature=0.2,
                )
                return response.choices[0].message.content or ""

            text = retry_on_transient(_call, label="[OpenAI]")
            return VisionAnalysis(
                success=True,
                provider="openai",
                model=VISION_OPENAI_MODEL,
                analysis=text,
                char_count=len(text),
            )
        except Exception as exc:
            return VisionAnalysis(
                success=False,
                provider="openai",
                model=VISION_OPENAI_MODEL,
                error=str(exc),
            )

    def _synthesize(
        self,
        results: list[VisionAnalysis],
        providers_used: list[str],
    ) -> str:
        """Merge analyses from multiple providers into unified spec."""
        successful = [r for r in results if r.success]

        if len(successful) == 1:
            return successful[0].analysis

        # Both providers succeeded — merge with headers
        sections: list[str] = []
        for result in successful:
            sections.append(
                f"=== {result.provider.upper()} ANALYSIS ({result.model}) ===\n"
                f"{result.analysis}"
            )

        return (
            "SYNTHESIZED PRODUCT SPECIFICATION\n"
            "Two independent AI vision analyses merged for maximum accuracy.\n\n"
            + "\n\n".join(sections)
        )
