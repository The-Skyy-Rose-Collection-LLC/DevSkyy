"""Stage D: FLUX composite inpainting.

Runs a three-provider fallback chain:
  fal-ai/flux-pro/v1/fill (primary)
  → fal-ai/flux-pro/kontext (secondary)
  → Replicate FLUX Fill (tertiary)

Per-call budget gates are applied to each FAL/Replicate method. When
``budget`` is None a WARNING is emitted and the call proceeds (back-compat).
When ELITE_STUDIO_STRICT_BUDGET=1 and budget=None, a RuntimeError is raised
before any paid call is dispatched.

Cost constants (verified against synthesis/state/telemetry.py):
  _FLUX_FILL_FAL_COST_USD       = $0.05
  _FLUX_KONTEXT_FALLBACK_COST_USD = $0.04
  _FLUX_FILL_REPLICATE_COST_USD = $0.05
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

from .infra import _extract_first_image_url, _gate_budget, fal_client

logger = logging.getLogger(__name__)

# Per-call cost constants (USD). Used by _gate_budget and exposed for tests.
_FLUX_FILL_FAL_COST_USD: float = 0.05
_FLUX_KONTEXT_FALLBACK_COST_USD: float = 0.04
_FLUX_FILL_REPLICATE_COST_USD: float = 0.05


def composite_with_flux(
    *,
    scene_url: str,
    subject_url: str,
    mask_url: str,
    prompt: str,
    budget: Any = None,
) -> tuple[bytes, str]:
    """Run the FLUX provider fallback chain: fal-fill → kontext → replicate.

    Each provider returns ``bytes`` on success or ``None`` on any failure
    so we can cleanly fall through. Raises ``RuntimeError`` only when ALL
    three fail.

    Budget gates are applied inside each provider method. When the call
    succeeds, ``budget.spend()`` is called on the success path so that the
    total is correctly tracked even when earlier providers in the chain fail.

    Args:
        scene_url: FAL CDN URL for the scene background.
        subject_url: FAL CDN URL for the relit subject.
        mask_url: FAL CDN URL for the alpha matte (doubles as placement mask).
        prompt: FLUX inpainting prompt from Stage B.
        budget: Optional ``RunBudget`` instance. None = back-compat unbudgeted mode.

    Returns:
        Tuple of (image_bytes, provider_label).

    Raises:
        RuntimeError: when all three providers fail.
    """
    # Primary: fal-fill (pure FLUX Fill Pro)
    out = flux_fill_fal(scene_url, mask_url, prompt, budget=budget)
    if out:
        return out, "fal-fill"

    # Secondary: fal-kontext (uses subject as reference image)
    out = flux_kontext(scene_url, mask_url, subject_url, prompt, budget=budget)
    if out:
        return out, "kontext"

    # Tertiary: Replicate
    out = flux_fill_replicate(scene_url, mask_url, prompt, budget=budget)
    if out:
        return out, "replicate"

    raise RuntimeError("All FLUX providers failed")


def flux_fill_fal(
    scene_url: str,
    mask_url: str,
    prompt: str,
    budget: Any = None,
) -> bytes | None:
    """fal-ai/flux-pro/v1/fill — primary inpainting path.

    Applies a budget gate before dispatch. On success, calls
    ``budget.spend(_FLUX_FILL_FAL_COST_USD)`` so the cost is recorded.

    Args:
        scene_url: FAL CDN URL for the scene background.
        mask_url: FAL CDN URL for the alpha matte.
        prompt: FLUX inpainting prompt.
        budget: Optional ``RunBudget`` instance.

    Returns:
        PNG bytes on success, ``None`` on any failure.
    """
    _gate_budget(budget, _FLUX_FILL_FAL_COST_USD, "flux_fill_fal")

    if fal_client is None:  # pragma: no cover
        return None
    try:
        result = fal_client.run(
            "fal-ai/flux-pro/v1/fill",
            arguments={
                "image_url": scene_url,
                "mask_url": mask_url,
                "prompt": prompt,
                "num_inference_steps": 40,
                "guidance_scale": 7.5,
                "output_format": "png",
                "safety_tolerance": 2,
            },
        )
        url = _extract_first_image_url(result)
        if not url:
            return None
        resp = httpx.get(url, timeout=60.0)
        resp.raise_for_status()
        image_bytes = resp.content
        if budget is not None:
            budget.spend(_FLUX_FILL_FAL_COST_USD)
        return image_bytes
    except Exception as exc:
        logger.warning("fal-fill errored: %s", exc)
        return None


def flux_kontext(
    scene_url: str,
    mask_url: str,
    ref_url: str,
    prompt: str,
    budget: Any = None,
) -> bytes | None:
    """fal-ai/flux-pro/kontext — secondary path with reference conditioning.

    Applies a budget gate before dispatch. On success, calls
    ``budget.spend(_FLUX_KONTEXT_FALLBACK_COST_USD)``.

    Args:
        scene_url: FAL CDN URL for the scene background.
        mask_url: FAL CDN URL for the alpha matte.
        ref_url: FAL CDN URL for the subject reference image.
        prompt: FLUX inpainting prompt.
        budget: Optional ``RunBudget`` instance.

    Returns:
        PNG bytes on success, ``None`` on any failure.
    """
    _gate_budget(budget, _FLUX_KONTEXT_FALLBACK_COST_USD, "flux_kontext")

    if fal_client is None:  # pragma: no cover
        return None
    try:
        result = fal_client.run(
            "fal-ai/flux-pro/kontext",
            arguments={
                "image_url": scene_url,
                "mask_url": mask_url,
                "reference_image_url": ref_url,
                "prompt": prompt,
                "num_inference_steps": 35,
                "guidance_scale": 6.0,
                "output_format": "png",
            },
        )
        url = _extract_first_image_url(result)
        if not url:
            return None
        resp = httpx.get(url, timeout=60.0)
        resp.raise_for_status()
        image_bytes = resp.content
        if budget is not None:
            budget.spend(_FLUX_KONTEXT_FALLBACK_COST_USD)
        return image_bytes
    except Exception as exc:
        logger.warning("kontext errored: %s", exc)
        return None


def flux_fill_replicate(
    scene_url: str,
    mask_url: str,
    prompt: str,
    budget: Any = None,
) -> bytes | None:
    """Replicate FLUX Fill — tertiary fallback when fal is unhealthy.

    Applies a budget gate before dispatch. On success, calls
    ``budget.spend(_FLUX_FILL_REPLICATE_COST_USD)``.

    Args:
        scene_url: FAL CDN URL for the scene background.
        mask_url: FAL CDN URL for the alpha matte.
        prompt: FLUX inpainting prompt.
        budget: Optional ``RunBudget`` instance.

    Returns:
        PNG bytes on success, ``None`` on any failure.
    """
    _gate_budget(budget, _FLUX_FILL_REPLICATE_COST_USD, "flux_fill_replicate")

    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        return None
    try:
        predict = httpx.post(
            "https://api.replicate.com/v1/predictions",
            headers={
                "Authorization": f"Token {token}",
                "Content-Type": "application/json",
            },
            json={
                "version": "black-forest-labs/flux-fill-pro",
                "input": {
                    "image": scene_url,
                    "mask": mask_url,
                    "prompt": prompt,
                    "num_inference_steps": 40,
                    "guidance": 7.5,
                },
            },
            timeout=30.0,
        )
        if not predict.is_success:
            return None
        poll_url = predict.json().get("urls", {}).get("get")
        if not poll_url:
            return None
        # Poll up to 2 minutes.
        for _ in range(60):
            poll = httpx.get(
                poll_url,
                headers={"Authorization": f"Token {token}"},
                timeout=30.0,
            )
            poll.raise_for_status()
            body = poll.json()
            status = body.get("status")
            if status == "succeeded":
                out_url = body.get("output")
                if isinstance(out_url, list):
                    out_url = out_url[0] if out_url else None
                if not out_url:
                    return None
                img = httpx.get(out_url, timeout=60.0)
                img.raise_for_status()
                image_bytes = img.content
                if budget is not None:
                    budget.spend(_FLUX_FILL_REPLICATE_COST_USD)
                return image_bytes
            if status in ("failed", "canceled"):
                return None
            time.sleep(2.0)
        return None
    except Exception as exc:
        logger.warning("Replicate FLUX Fill errored: %s", exc)
        return None
