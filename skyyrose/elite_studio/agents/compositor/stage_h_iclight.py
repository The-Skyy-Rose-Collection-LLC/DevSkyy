"""Stage H: IC-Light V2 relighting via FAL (Phase 2 Architecture A).

Runs after Stage D rasterize composite to match the lighting of the pasted
product to the scene illumination. Subject preservation is enforced via low
``highres_denoise`` (default 0.4 per ELITE_STUDIO_ICLIGHT_DENOISE env var) —
this is the FAL IC-Light V2 knob that caps how much the diffusion pass alters
the product surface.

Endpoint: ``fal-ai/iclight-v2`` (verified via Context7 against fal.ai docs)
Cost: ~$0.02/call (project telemetry)

Schema (verified from fal.ai/models/fal-ai/iclight-v2/api):
  Required:
    prompt (str), image_url (str)
  Optional with defaults from FAL:
    background_threshold (0.67), num_inference_steps (28), initial_latent ("None"),
    num_images (1), cfg (1), lowres_denoise (0.98), highres_denoise (0.95),
    hr_downscale (0.5), guidance_scale (5), enable_safety_checker (true),
    output_format ("jpeg")

Why `highres_denoise` instead of a single "strength" knob:
FAL IC-Light V2 has no ``denoise_strength`` parameter. The plan's intent
(denoise ≤ 0.4 to preserve product pixels) maps to ``highres_denoise`` which
controls how much the high-resolution pass alters the input. Default 0.95
heavily reshapes; 0.4 preserves the rasterized product surface while still
allowing the lighting environment to be matched to the scene.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from pathlib import Path

import httpx

from .infra import _cache_dir, _file_hash, fal_client, upload_to_fal

logger = logging.getLogger(__name__)

ICLIGHT_ENDPOINT = "fal-ai/iclight-v2"

# Plan #8551 env var. Cap defaults to 0.4 to preserve product pixels.
_DEFAULT_ICLIGHT_DENOISE = 0.4
_DEFAULT_LOWRES_DENOISE = 0.98  # FAL default — lowres pass shapes the scene
_DEFAULT_INFERENCE_STEPS = 28
_DEFAULT_CFG = 1.0
_POLL_TIMEOUT_S = 120.0


def relight_composite(
    composite_path: str,
    prompt: str,
    sku: str,
    output_dir: str,
    *,
    highres_denoise: float | None = None,
) -> str:
    """Match composite lighting to scene via FAL IC-Light V2.

    Args:
        composite_path: Path to the Stage D rasterize output (product pasted
            onto scene, no relighting yet).
        prompt: Scene lighting description from Stage B prompt synth.
        sku: Canonical SKU used to name output + cache key.
        output_dir: Directory where the relit PNG is written.
        highres_denoise: Override for the subject-preservation knob. Default
            reads ``ELITE_STUDIO_ICLIGHT_DENOISE`` env var (0.4 if unset).

    Returns:
        Absolute path to the written ``{sku}-relit.png`` file. Falls back to
        the input ``composite_path`` if FAL is unreachable so the pipeline
        does not block on a single provider — fallback is logged for the
        QA gate to weigh.

    Raises:
        FileNotFoundError: ``composite_path`` does not exist on disk.
        RuntimeError: ``fal_client`` package not installed.
    """
    comp_p = Path(composite_path)
    if not comp_p.exists():
        raise FileNotFoundError(f"stage-h iclight input missing: {comp_p}")
    if fal_client is None:
        raise RuntimeError(
            "fal_client not installed — `pip install fal_client` to enable Stage H IC-Light."
        )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    denoise = highres_denoise if highres_denoise is not None else _resolve_denoise()

    cache_key = _iclight_cache_key(comp_p, prompt, denoise)
    cached = _cache_dir("iclight") / f"{cache_key}.png"
    dest = out / f"{sku}-relit.png"

    if cached.exists():
        dest.write_bytes(cached.read_bytes())
        logger.info("stage-h iclight: cache hit %s", cache_key)
        return str(dest)

    try:
        image_url = upload_to_fal(comp_p)
        result_bytes = _invoke_iclight_v2(
            image_url=image_url,
            prompt=prompt,
            highres_denoise=denoise,
        )
    except Exception as exc:
        logger.warning(
            "stage-h iclight failed for %s — falling back to unrelit composite: %s",
            sku,
            exc,
        )
        # Pass-through fallback so the pipeline does not block.
        dest.write_bytes(comp_p.read_bytes())
        return str(dest)

    if result_bytes is None:
        logger.warning("stage-h iclight returned no bytes — using unrelit composite")
        dest.write_bytes(comp_p.read_bytes())
        return str(dest)

    dest.write_bytes(result_bytes)
    try:
        cached.write_bytes(result_bytes)
    except OSError:  # pragma: no cover — cache write is best-effort
        pass
    logger.info("stage-h iclight: %s -> %s (highres_denoise=%.2f)", sku, dest, denoise)
    return str(dest)


def _resolve_denoise() -> float:
    """Read ELITE_STUDIO_ICLIGHT_DENOISE, clamp to [0.0, 1.0]."""
    raw = os.environ.get("ELITE_STUDIO_ICLIGHT_DENOISE")
    if raw is None:
        return _DEFAULT_ICLIGHT_DENOISE
    try:
        value = float(raw)
    except ValueError:
        logger.warning(
            "ELITE_STUDIO_ICLIGHT_DENOISE=%r is not a float; using default %.2f",
            raw,
            _DEFAULT_ICLIGHT_DENOISE,
        )
        return _DEFAULT_ICLIGHT_DENOISE
    return max(0.0, min(1.0, value))


def _invoke_iclight_v2(
    *,
    image_url: str,
    prompt: str,
    highres_denoise: float,
) -> bytes | None:
    """Submit to FAL IC-Light V2 and return the result image bytes.

    Returns None on graceful failure (logged); raises on hard errors so the
    caller's broad-except can route to the pass-through fallback.

    Tests patch this function directly to avoid live FAL calls.
    """
    result = fal_client.subscribe(  # type: ignore[union-attr]
        ICLIGHT_ENDPOINT,
        arguments={
            "image_url": image_url,
            "prompt": prompt,
            "highres_denoise": highres_denoise,
            "lowres_denoise": _DEFAULT_LOWRES_DENOISE,
            "num_inference_steps": _DEFAULT_INFERENCE_STEPS,
            "cfg": _DEFAULT_CFG,
            "output_format": "png",
        },
    )
    images = result.get("images") if isinstance(result, dict) else None
    if not images:
        return None
    first = images[0]
    out_url = first.get("url") if isinstance(first, dict) else None
    if not out_url:
        return None
    return _download_image(out_url)


def _download_image(url: str) -> bytes:
    """Fetch the relit image from FAL's CDN."""
    with httpx.Client(timeout=_POLL_TIMEOUT_S) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.content


def _iclight_cache_key(comp_p: Path, prompt: str, denoise: float) -> str:
    """Hash of composite content + prompt + denoise — relight is deterministic
    enough to cache on these three inputs."""
    h = hashlib.sha256()
    h.update(_file_hash(str(comp_p)).encode("ascii"))
    h.update(b"|")
    h.update(prompt.encode("utf-8"))
    h.update(b"|")
    h.update(f"{denoise:.4f}".encode("ascii"))
    return h.hexdigest()[:16]


# Re-exported for testability — callers can stub at this name.
__all__ = [
    "ICLIGHT_ENDPOINT",
    "relight_composite",
]
