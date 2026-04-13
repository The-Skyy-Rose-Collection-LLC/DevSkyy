"""
TryOnAgent — wraps the FASHN virtual try-on pipeline for Elite Studio.

Runs as a synchronous node in the LangGraph graph. Errors are swallowed
and returned as TryOnResult(success=False) so the main job never fails
due to optional try-on processing.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from ..config import OUTPUT_DIR
from ..models import TryOnResult

logger = logging.getLogger(__name__)

# Category mapping from Elite Studio conventions to FASHN agent conventions
_CATEGORY_MAP: dict[str, str] = {
    "upper_body": "tops",
    "tops": "tops",
    "lower_body": "bottoms",
    "bottoms": "bottoms",
    "dresses": "dresses",
    "outerwear": "outerwear",
    "full_body": "full_body",
}


def _find_garment_image(sku: str) -> str | None:
    """Search product image directories for a garment render for the given SKU.

    Searches OUTPUT_DIR/<sku>/ for front-facing renders in priority order:
    webp branding render → jpg model front → any jpg/png/webp.

    Returns:
        Absolute path string if found, None otherwise.
    """
    sku_dir = OUTPUT_DIR / sku
    if not sku_dir.is_dir():
        logger.debug("No product image directory for SKU %s at %s", sku, sku_dir)
        return None

    # Priority: branding render → model front → any image
    candidates = [
        sku_dir / f"{sku}-render-branding.webp",
        sku_dir / f"{sku}-render-front.webp",
        sku_dir / f"{sku}-model-front-gemini.jpg",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    # Fallback: first image file found
    for ext in ("*.webp", "*.jpg", "*.jpeg", "*.png"):
        matches = sorted(sku_dir.glob(ext))
        if matches:
            return str(matches[0])

    return None


class TryOnAgent:
    """Wraps the FASHN virtual try-on agent for use in the Elite Studio graph.

    Import is deferred so the heavy agent dependency tree is only loaded
    when try-on is actually enabled.

    All public methods are synchronous — async FASHN calls are executed
    inside a fresh event loop via asyncio.run().
    """

    def try_on(
        self,
        sku: str,
        garment_image_path: str,
        model_image_path: str,
        category: str = "upper_body",
    ) -> TryOnResult:
        """Run virtual try-on using the FASHN API.

        Args:
            sku: Product SKU (used for output path naming).
            garment_image_path: Local path to the garment/product image.
            model_image_path: Local path to the fashion model image.
            category: Garment category in Elite Studio convention
                      (upper_body, lower_body, dresses, outerwear, full_body).

        Returns:
            TryOnResult. On any error, returns TryOnResult(success=False, error=...).
        """
        start = time.monotonic()
        fashn_category = _CATEGORY_MAP.get(category, "tops")

        try:
            result_path = self._run_fashn(
                sku=sku,
                garment_image_path=garment_image_path,
                model_image_path=model_image_path,
                fashn_category=fashn_category,
            )
            latency = round(time.monotonic() - start, 2)
            return TryOnResult(
                success=True,
                output_path=result_path,
                garment_sku=sku,
                model_image_path=model_image_path,
                provider="fashn",
                latency_s=latency,
            )

        except Exception as exc:
            latency = round(time.monotonic() - start, 2)
            logger.warning("TryOnAgent failed for SKU %s: %s", sku, exc)
            return TryOnResult(
                success=False,
                garment_sku=sku,
                model_image_path=model_image_path,
                provider="fashn",
                latency_s=latency,
                error=str(exc),
            )

    def _run_fashn(
        self,
        sku: str,
        garment_image_path: str,
        model_image_path: str,
        fashn_category: str,
    ) -> str:
        """Execute the async FASHN agent and save the output image.

        Returns:
            Absolute path to the saved output image.

        Raises:
            Exception: Propagated from the FASHN agent on API failure.
        """
        from agents.fashn_agent import FashnTryOnAgent

        agent = FashnTryOnAgent()

        async def _invoke() -> dict:
            try:
                return await agent._tool_virtual_tryon(
                    model_image=model_image_path,
                    garment_image=garment_image_path,
                    category=fashn_category,
                    mode="balanced",
                )
            finally:
                await agent.close()

        result = asyncio.run(_invoke())

        raw_path: str = result.get("image_path", "")
        if not raw_path:
            raise ValueError("FASHN returned no image_path")

        # Copy to canonical Elite Studio output location
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest_dir = OUTPUT_DIR / sku / "tryon"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / f"{sku}-tryon-{timestamp}.jpg"

        shutil.copy2(raw_path, dest_path)
        return str(dest_path)
