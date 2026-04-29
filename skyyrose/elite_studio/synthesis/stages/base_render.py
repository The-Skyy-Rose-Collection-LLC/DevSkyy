"""Stage 1: FLUX Kontext Pro — clean garment, no decoration.

Takes a techflat (vector design) + dossier and renders a clean garment in
the right silhouette/fabric/color, but with NO branding anywhere. Stage 3
adds the decoration via masked inpainting.

Why Kontext over plain text-to-image:
  * Kontext accepts an input image as conditioning and follows it tightly.
  * The techflat IS the silhouette spec — Kontext preserves that.
  * Pure text-to-image would invent a generic crewneck that doesn't match
    the cut, fit, or proportions of the actual SkyyRose product.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from ..clients import FalClient
from ..prompts.base_prompts import build_base_prompt
from ..state.telemetry import CostTracker

logger = logging.getLogger(__name__)

FLUX_KONTEXT_ENDPOINT = "fal-ai/flux-pro/kontext"


@dataclass
class BaseRenderResult:
    output_url: str
    output_path: Path
    seed: int | None = None
    duration_ms: int = 0


async def render_base(
    *,
    client: FalClient,
    techflat_path: str | Path,
    dossier: dict,
    out_dir: str | Path,
    sku: str,
    view: str,
    cost_tracker: CostTracker | None = None,
    aspect_ratio: str = "1:1",
    seed: int | None = None,
) -> BaseRenderResult:
    """Stage 1 — FLUX Kontext Pro base render.

    Uploads the techflat to fal CDN, calls Kontext with the dossier-derived
    base prompt (decoration explicitly suppressed), downloads the output.

    Args:
        client: shared FalClient.
        techflat_path: local path to the techflat image.
        dossier: parsed dossier dict.
        out_dir: where to save the output PNG.
        sku, view: identifiers for telemetry + filename.
        cost_tracker: optional CostTracker for spend accounting.
        aspect_ratio: locked to 1:1 by default for downstream mask alignment.
        seed: optional seed for reproducibility.

    Returns:
        BaseRenderResult with the downloaded output path and metadata.
    """
    techflat_path = Path(techflat_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not techflat_path.is_file():
        raise FileNotFoundError(f"techflat not found: {techflat_path}")

    techflat_url = await client.upload(techflat_path)
    prompt = build_base_prompt(dossier, view=view)

    arguments: dict = {
        "image_url": techflat_url,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
        "safety_tolerance": 2,
    }
    if seed is not None:
        arguments["seed"] = seed

    started = time.perf_counter()
    fal_result = await client.subscribe(FLUX_KONTEXT_ENDPOINT, arguments=arguments, with_logs=True)
    duration_ms = int((time.perf_counter() - started) * 1000)

    output_url = fal_result.primary_url
    output_path = out_dir / f"{sku}-{view}-stage1-base.png"
    await _download_to(output_url, output_path)

    if cost_tracker is not None:
        cost_tracker.add(
            model=FLUX_KONTEXT_ENDPOINT,
            sku=sku,
            view=view,
            attempt=1,
            stage="stage_1_base",
            duration_ms=duration_ms,
            output_url=output_url,
        )

    logger.info(
        "stage1 base render: sku=%s view=%s duration_ms=%d url=%s",
        sku,
        view,
        duration_ms,
        output_url,
    )
    return BaseRenderResult(
        output_url=output_url,
        output_path=output_path,
        seed=fal_result.seed,
        duration_ms=duration_ms,
    )


async def _download_to(url: str, dest: Path) -> None:
    """Stream a fal output URL to a local file."""
    import asyncio

    import httpx

    async with httpx.AsyncClient(timeout=60.0) as http:
        resp = await http.get(url)
        resp.raise_for_status()
        await asyncio.to_thread(dest.write_bytes, resp.content)
