"""DualVisionGate — Phase B2 dual-agent vision consensus.

Promoted to ADK SuperAgent for comprehensive "Back Data" (telemetry) and
high-fidelity dual-agent vision consensus.

Agent A: Claude Opus 4.6 (Anthropic SDK)
Agent B: Gemini 2.0 Flash (gemini_rest.py)
Mode:    Consensus — both must return YES to proceed.

VisionAgent is aliased to DualVisionGate for nodes.py backwards compatibility.
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path

from adk.base import ADKProvider, AgentConfig
from adk.super_agents import BaseSuperAgent

from ..gemini_rest import analyze_vision as gemini_analyze_vision
from ..models import PreflightResult, SynthesizedVision, VisionAnalysis

logger = logging.getLogger(__name__)

from ..config import VISION_CLAUDE_MODEL as _CLAUDE_MODEL
from ..config import VISION_GEMINI_MODEL as _GEMINI_VISION_MODEL

# Products images live here (relative to project root)
_PRODUCTS_DIR = Path("wordpress-theme/skyyrose-flagship/assets/images/products")


def _reference_path(sku: str) -> str:
    """Resolve the reference image path for a SKU.

    Checks the catalog for 'render_source_override' first, then common extensions.
    """
    try:
        from ..catalog import Catalog

        cat = Catalog.load()
        product = cat.get(sku)
        if product and product.source_files:
            p = _PRODUCTS_DIR / product.source_files[0]
            if p.exists():
                return str(p)
    except Exception:
        pass

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


class DualVisionGate(BaseSuperAgent):
    """Dual-agent vision consensus gate promoted to ADK SuperAgent."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        if config is None:
            config = AgentConfig(
                name="legendary_vision_gate",
                provider=ADKProvider.GOOGLE,
                model=_GEMINI_VISION_MODEL,
                system_prompt="You are the Legendary Vision Gate for SkyyRose. You ensure product integrity with 100% precision.",
            )
        super().__init__(config)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def verify_reference(
        self,
        image_path: str,
        sku: str,
        expected_garment: str,
    ) -> PreflightResult:
        """Both models must return YES. Either NO blocks the SKU. Capture Back Data."""
        # Trigger ADK for observability
        adk_prompt = f"PREFLIGHT TASK: SKU={sku}, Image={image_path}, Expected={expected_garment}"
        logger.info(f"Running Legendary Preflight for {sku} via ADK...")
        await self.execute(adk_prompt)

        prompt = _PREFLIGHT_PROMPT.format(name=expected_garment)

        try:
            a_text = await self._call_claude(image_path, prompt)
            b_text = await self._call_gemini(image_path, prompt)
        except Exception as exc:
            logger.error(f"Preflight vision calls failed: {exc}")
            return PreflightResult(
                passed=False,
                sku=sku,
                agent_a_verdict="ERROR",
                agent_b_verdict="ERROR",
                blocking_reason=str(exc),
            )

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

    async def analyze(self, sku: str, view: str) -> SynthesizedVision:
        """Synthesize a generation spec from the reference image with Back Data."""
        # Trigger ADK for observability
        adk_prompt = f"VISION ANALYSIS TASK: SKU={sku}, VIEW={view}"
        logger.info(f"Running Legendary Vision Analysis for {sku} via ADK...")
        await self.execute(adk_prompt)

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
            a_text = await self._call_claude(ref, prompt)
            a_result = VisionAnalysis(
                success=True,
                provider="anthropic",
                model=_CLAUDE_MODEL,
                analysis=a_text,
                char_count=len(a_text),
            )
        except Exception as exc:
            a_result = VisionAnalysis(
                success=False, provider="anthropic", model=_CLAUDE_MODEL, error=str(exc)
            )

        try:
            b_text = await self._call_gemini(ref, prompt)
            b_result = VisionAnalysis(
                success=True,
                provider="google",
                model=_GEMINI_VISION_MODEL,
                analysis=b_text,
                char_count=len(b_text),
            )
        except Exception as exc:
            b_result = VisionAnalysis(
                success=False, provider="google", model=_GEMINI_VISION_MODEL, error=str(exc)
            )

        if not a_result.success and not b_result.success:
            return SynthesizedVision(
                success=False,
                error="Both vision agents failed",
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
    # Private helpers
    # ------------------------------------------------------------------

    async def _call_claude(self, image_path: str, prompt: str) -> str:
        from ..config import get_anthropic_client

        client = get_anthropic_client()

        ext = Path(image_path).suffix.lower().lstrip(".")
        media_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        b64 = _load_image_b64(image_path)
        msg = client.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": media_type, "data": b64},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        return msg.content[0].text

    async def _call_gemini(self, image_path: str, prompt: str) -> str:
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
