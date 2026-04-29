"""Stage 3: FLUX Fill Pro / Kontext-LoRA — masked decoration inpainting.

Takes the Stage 1 base render + the decoration mask + dossier branding
entries and inpaints decoration ONLY inside the white regions of the mask.

Routing:
  * No LoRA active  → ``fal-ai/flux-pro/v1/fill``       (pure FLUX Fill Pro)
  * LoRA available  → ``fal-ai/flux-kontext-lora/inpaint`` with loras=[...]

Both endpoints accept an image + mask + prompt. The LoRA endpoint
additionally accepts a list of LoRA URLs with per-LoRA scale.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..clients import FalClient
from ..prompts.decoration_prompts import build_decoration_prompt
from ..state.telemetry import CostTracker
from .mask_deriver import (
    BrandingEntry,
    filter_decoration_entries,
    parse_branding_entries,
)

logger = logging.getLogger(__name__)

FLUX_FILL_ENDPOINT = "fal-ai/flux-pro/v1/fill"
FLUX_KONTEXT_LORA_ENDPOINT = "fal-ai/flux-kontext-lora/inpaint"

DEFAULT_LORA_SCALE = 0.85
DEFAULT_GUIDANCE = 7.5
DEFAULT_STEPS = 40

# Guidance escalation per attempt — pushes harder toward positive spec on retries.
# FLUX Fill Pro guidance_scale max is 20.
_GUIDANCE_BY_ATTEMPT: dict[int, float] = {1: 7.5, 2: 12.0, 3: 17.0}


@dataclass
class InpaintResult:
    output_url: str
    output_path: Path
    seed: int | None = None
    duration_ms: int = 0
    endpoint: str = ""


async def inpaint_decoration(
    *,
    client: FalClient,
    base_image_path: str | Path,
    mask_path: str | Path,
    dossier: dict,
    out_dir: str | Path,
    sku: str,
    view: str,
    attempt: int = 1,
    prior_violations: list[dict] | None = None,
    lora_url: str | None = None,
    lora_trigger: str | None = None,
    lora_scale: float = DEFAULT_LORA_SCALE,
    cost_tracker: CostTracker | None = None,
    seed: int | None = None,
) -> InpaintResult:
    """Stage 3 — masked decoration inpainting.

    Args:
        client: shared FalClient.
        base_image_path: Stage 1 output path.
        mask_path: Stage 2 mask path (B&W, white = inpaint).
        dossier: parsed dossier dict.
        sku, view: identifiers.
        attempt: 1-based retry counter (the H4 retry feedback adds prior
            violation context to the prompt on attempt > 1).
        prior_violations: list of {element, region, severity} dicts from
            the previous failed attempt's audit. Used on retries.
        lora_url: optional LoRA weights URL — when present, routes through
            the kontext-lora endpoint and prepends ``lora_trigger`` to the
            decoration prompt.
        lora_trigger: trigger word for the LoRA (e.g., "SKYR_EMBOSS").
        lora_scale: 0-1 LoRA influence; 0.85 is the architecture default.
        cost_tracker: optional spend accumulator.
        seed: optional seed for reproducibility.
    """
    base_image_path = Path(base_image_path)
    mask_path = Path(mask_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not base_image_path.is_file():
        raise FileNotFoundError(f"base image not found: {base_image_path}")
    if not mask_path.is_file():
        raise FileNotFoundError(f"mask not found: {mask_path}")

    # Parse branding entries to build the decoration prompt.
    entries = parse_branding_entries(dossier.get("branding_block", ""))
    decoration_entries = filter_decoration_entries(entries, view=view)
    prompt = _compose_decoration_prompt(
        decoration_entries=decoration_entries,
        prior_violations=prior_violations or [],
        attempt=attempt,
        lora_trigger=lora_trigger if lora_url else None,
        negative_block=dossier.get("negative_block", ""),
    )

    # Upload image + mask to fal CDN.
    image_url = await client.upload(base_image_path)
    mask_url = await client.upload(mask_path)

    guidance = _GUIDANCE_BY_ATTEMPT.get(attempt, DEFAULT_GUIDANCE)
    arguments: dict[str, Any] = {
        "image_url": image_url,
        "mask_url": mask_url,
        "prompt": prompt,
        "num_inference_steps": DEFAULT_STEPS,
        "guidance_scale": guidance,
        "output_format": "png",
        "safety_tolerance": 2,
    }
    if seed is not None:
        arguments["seed"] = seed

    if lora_url:
        endpoint = FLUX_KONTEXT_LORA_ENDPOINT
        arguments["loras"] = [{"path": lora_url, "scale": lora_scale}]
    else:
        endpoint = FLUX_FILL_ENDPOINT

    started = time.perf_counter()
    fal_result = await client.subscribe(endpoint, arguments=arguments, with_logs=True)
    duration_ms = int((time.perf_counter() - started) * 1000)

    output_url = fal_result.primary_url
    output_path = out_dir / f"{sku}-{view}-stage3-branded-attempt{attempt}.png"
    await _download_to(output_url, output_path)

    if cost_tracker is not None:
        cost_tracker.add(
            model=endpoint,
            sku=sku,
            view=view,
            attempt=attempt,
            stage="stage_3_inpaint",
            duration_ms=duration_ms,
            output_url=output_url,
        )

    logger.info(
        "stage3 inpaint: sku=%s view=%s attempt=%d endpoint=%s duration_ms=%d url=%s",
        sku,
        view,
        attempt,
        endpoint,
        duration_ms,
        output_url,
    )
    return InpaintResult(
        output_url=output_url,
        output_path=output_path,
        seed=fal_result.seed,
        duration_ms=duration_ms,
        endpoint=endpoint,
    )


def _compose_decoration_prompt(
    *,
    decoration_entries: list[BrandingEntry],
    prior_violations: list[dict],
    attempt: int,
    lora_trigger: str | None,
    negative_block: str = "",
) -> str:
    """Build a single inpaint prompt covering all authorized decorations.

    Per-entry physics descriptions are concatenated. Prior-violation
    feedback (H4 retry loop) is prepended when present. The dossier
    NEGATIVE block is appended as a hard constraint at the end so the
    model cannot generate elements the product physically lacks.
    """
    from ..prompts.decoration_prompts import build_violation_feedback

    if not decoration_entries:
        return (
            "Preserve the existing garment exactly as shown. Make no changes "
            "outside the masked region."
        )

    per_region = [
        build_decoration_prompt(
            decoration_description=e.description,
            technique=e.technique,
            region=e.region,
            color=e.color,
            lora_trigger=lora_trigger,
        )
        for e in decoration_entries
    ]
    body = "\n\n".join(f"REGION {i + 1}: {p}" for i, p in enumerate(per_region))

    feedback = build_violation_feedback(
        prior_violations=prior_violations,
        retry_attempt=attempt,
        max_attempts=3,
    )

    # Append the dossier NEGATIVE block so Stage 3 cannot generate elements
    # the product lacks (e.g. chevron on jacket back, wrong pocket shape).
    # The vision audit uses the same block — both gates must see it.
    negative_contract = ""
    if negative_block.strip():
        negative_contract = (
            "\n\nPRODUCT NEGATIVE CONTRACT — the following elements are physically "
            "absent from this product and must NOT appear anywhere in the render:\n"
            + negative_block.strip()
        )

    return f"{feedback}{body}{negative_contract}"


async def _download_to(url: str, dest: Path) -> None:
    """Stream a fal output URL to a local file."""
    import asyncio

    import httpx

    async with httpx.AsyncClient(timeout=60.0) as http:
        resp = await http.get(url)
        resp.raise_for_status()
        await asyncio.to_thread(dest.write_bytes, resp.content)
