"""DualVisionGate — Phase B2 dual-agent vision consensus.

Agent A: Claude Opus 4.6 (Anthropic SDK)
Agent B: Gemini 2.0 Flash (gemini_rest.py — NOT google-genai SDK)
Mode:    Consensus — both must return YES to proceed.

VisionAgent is aliased to DualVisionGate for nodes.py backwards compatibility.
"""
from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

import anthropic

from ..gemini_rest import analyze_vision as gemini_analyze_vision
from ..models import DualAgentResult, PreflightResult, SynthesizedVision, VisionAnalysis

logger = logging.getLogger(__name__)

_CLAUDE_MODEL = "claude-opus-4-6"
_GEMINI_VISION_MODEL = "gemini-2.0-flash"

# Products images live here (relative to project root)
_PRODUCTS_DIR = Path("wordpress-theme/skyyrose-flagship/assets/images/products")


def _reference_path(sku: str) -> str:
    """Resolve the reference image path for a SKU (checks common extensions)."""
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = _PRODUCTS_DIR / f"{sku}.{ext}"
        if p.exists():
            return str(p)
        # Also check without hyphen variants
        slug = sku.replace("-", "_")
        p2 = _PRODUCTS_DIR / f"{slug}.{ext}"
        if p2.exists():
            return str(p2)
    # Return the jpg path anyway — caller handles missing file
    return str(_PRODUCTS_DIR / f"{sku}.jpg")


def _load_image_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


_PREFLIGHT_PROMPT = (
    "You are verifying a product reference image for an e-commerce imagery pipeline. "
    "The product name from the catalog is: '{name}'. "
    "Looking at this image, does it show the correct garment type? "
    "Reply with exactly one word YES or NO on the first line, then one sentence of reasoning."
)

_VISION_SPEC_PROMPT = (
    "You are analyzing a product reference image for SkyyRose luxury fashion brand. "
    "Product: '{name}' (SKU: {sku}). Branding spec: {branding}. "
    "Describe the garment type, colorway, fabric texture, and any visible branding/logos. "
    "Be specific — this description drives AI image generation."
)


class DualVisionGate:
    """Dual-agent vision consensus gate.

    verify_reference() — pre-flight: does the reference image match the spec?
    analyze() — full spec synthesis: returns SynthesizedVision for generator.
    """

    def __init__(self) -> None:
        self._claude = anthropic.Anthropic()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify_reference(
        self,
        image_path: str,
        sku: str,
        expected_garment: str,
    ) -> PreflightResult:
        """Both models must return YES. Either NO blocks the SKU."""
        prompt = _PREFLIGHT_PROMPT.format(name=expected_garment)
        a_text = self._call_claude(image_path, prompt)
        b_text = self._call_gemini(image_path, prompt)

        a_yes = a_text.strip().upper().startswith("YES")
        b_yes = b_text.strip().upper().startswith("YES")

        if a_yes and b_yes:
            return PreflightResult(
                passed=True,
                sku=sku,
                agent_a_verdict=a_text[:120],
                agent_b_verdict=b_text[:120],
            )

        blocking = []
        if not a_yes:
            blocking.append(f"Agent A (Claude): {a_text[:200]}")
        if not b_yes:
            blocking.append(f"Agent B (Gemini): {b_text[:200]}")

        return PreflightResult(
            passed=False,
            sku=sku,
            agent_a_verdict=a_text[:120],
            agent_b_verdict=b_text[:120],
            blocking_reason=" | ".join(blocking),
        )

    def analyze(self, sku: str, view: str) -> SynthesizedVision:
        """Synthesize a generation spec from the reference image."""
        from ..catalog import Catalog

        try:
            cat = Catalog.load()
            product = cat.require(sku)
            name = product.name
            branding = product.branding_summary
        except Exception as exc:
            return SynthesizedVision(success=False, error=f"Catalog load failed: {exc}")

        ref = _reference_path(sku)
        if not Path(ref).exists():
            return SynthesizedVision(
                success=False, error=f"No reference image found for {sku} at {ref}"
            )

        prompt = _VISION_SPEC_PROMPT.format(sku=sku, name=name, branding=branding)

        try:
            a_text = self._call_claude(ref, prompt)
            a_result = VisionAnalysis(
                success=True, provider="anthropic", model=_CLAUDE_MODEL,
                analysis=a_text, char_count=len(a_text),
            )
        except Exception as exc:
            a_result = VisionAnalysis(
                success=False, provider="anthropic", model=_CLAUDE_MODEL, error=str(exc)
            )

        try:
            b_text = self._call_gemini(ref, prompt)
            b_result = VisionAnalysis(
                success=True, provider="google", model=_GEMINI_VISION_MODEL,
                analysis=b_text, char_count=len(b_text),
            )
        except Exception as exc:
            b_result = VisionAnalysis(
                success=False, provider="google", model=_GEMINI_VISION_MODEL, error=str(exc)
            )

        if not a_result.success and not b_result.success:
            return SynthesizedVision(
                success=False, error="Both vision agents failed",
                individual_results=(a_result, b_result),
            )

        texts = [r.analysis for r in (a_result, b_result) if r.success and r.analysis]
        unified = "\n\n---\n\n".join(texts)

        return SynthesizedVision(
            success=True,
            unified_spec=unified,
            providers_used=tuple(r.provider for r in (a_result, b_result) if r.success),
            individual_results=(a_result, b_result),
        )

    # ------------------------------------------------------------------
    # Private helpers (patchable in tests)
    # ------------------------------------------------------------------

    def _call_claude(self, image_path: str, prompt: str) -> str:
        ext = Path(image_path).suffix.lower().lstrip(".")
        media_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        b64 = _load_image_b64(image_path)
        msg = self._claude.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return msg.content[0].text

    def _call_gemini(self, image_path: str, prompt: str) -> str:
        ext = Path(image_path).suffix.lower().lstrip(".")
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        b64 = _load_image_b64(image_path)
        result = gemini_analyze_vision(
            model=_GEMINI_VISION_MODEL,
            prompt=prompt,
            image_b64=b64,
            mime_type=mime,
        )
        if not result.get("success"):
            raise RuntimeError(result.get("error", "Gemini vision failed"))
        return result["text"]


# Backwards-compatible alias — nodes.py imports VisionAgent
VisionAgent = DualVisionGate
