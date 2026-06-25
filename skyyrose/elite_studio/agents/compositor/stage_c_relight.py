"""Stage C: IC-Light relighting.

Matches subject lighting to the scene via IC-Light v2 (Replicate primary,
local libcom fallback, alpha pass-through final fallback).
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import time
from pathlib import Path

import httpx
from PIL import Image

from .infra import _cache_dir, _file_hash

logger = logging.getLogger(__name__)


class RelightStageError(RuntimeError):
    """Raised when every IC-Light provider fails.

    Returning the unrelit alpha here (the old behavior) let an unrelit
    composite pass QC silently — the documented "QA will be stricter"
    promise was never wired. Fail closed; the caller decides hold/skip/abort.
    """


def relight_subject(
    alpha_path: str,
    scene_path: str,
    prompt: str,
    sku: str,
    output_dir: str,
) -> str:
    """Match subject lighting to scene via IC-Light.

    Tries Replicate IC-Light first, then a local libcom path. If every provider
    fails, raises RelightStageError — it never returns the unrelit alpha
    unchanged, which would silently poison downstream QC.

    Args:
        alpha_path: Path to the Stage A alpha matte.
        scene_path: Path to the scene reference image.
        prompt: FLUX prompt from Stage B (used as IC-Light conditioning).
        sku: Canonical SKU string.
        output_dir: Directory where the relit image is written.

    Returns:
        Path to the relit image.

    Raises:
        RelightStageError: if every provider fails — never returns the unrelit
            alpha (which would silently poison downstream QC).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    cache = _cache_dir("relight")
    cache_key = hashlib.sha256(
        f"{_file_hash(alpha_path)}:{_file_hash(scene_path)}:{prompt}".encode()
    ).hexdigest()[:16]
    cached = cache / f"{cache_key}.png"
    if cached.exists():
        dest = out / f"{sku}-relit.png"
        dest.write_bytes(cached.read_bytes())
        return str(dest)

    # Try Replicate IC-Light
    try:
        relit_bytes = _run_iclight_replicate(
            alpha_path=alpha_path,
            scene_path=scene_path,
            prompt=prompt,
        )
        if relit_bytes:
            dest = out / f"{sku}-relit.png"
            dest.write_bytes(relit_bytes)
            cached.write_bytes(relit_bytes)
            return str(dest)
    except Exception as exc:
        logger.warning("IC-Light Replicate failed for %s: %s", sku, exc)

    # Try local libcom
    try:
        relit_bytes = _run_iclight(
            alpha_path=alpha_path,
            scene_path=scene_path,
            prompt=prompt,
        )
        if relit_bytes:
            dest = out / f"{sku}-relit.png"
            dest.write_bytes(relit_bytes)
            cached.write_bytes(relit_bytes)
            return str(dest)
    except Exception as exc:
        logger.warning("IC-Light local fallback failed for %s: %s", sku, exc)

    # Both providers failed — fail closed (see RelightStageError).
    raise RelightStageError(
        f"relight_subject: all providers failed for SKU {sku!r} "
        "(Replicate IC-Light + local libcom both unavailable)"
    )


def _run_iclight_replicate(
    *,
    alpha_path: str,
    scene_path: str,
    prompt: str,
) -> bytes | None:
    """Replicate IC-Light v2 — preferred relighting path.

    Returns the relit image bytes, or None on graceful failure (which
    triggers the libcom fallback). Tests patch this function directly.
    """
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:  # pragma: no cover - tests always patch
        return None
    try:
        with httpx.Client(timeout=120.0) as client:
            with open(alpha_path, "rb") as f:
                subject_b64 = base64.b64encode(f.read()).decode("ascii")
            with open(scene_path, "rb") as f:
                bg_b64 = base64.b64encode(f.read()).decode("ascii")
            resp = client.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "version": "iclight-v2",
                    "input": {
                        "subject_image": f"data:image/png;base64,{subject_b64}",
                        "background_image": f"data:image/png;base64,{bg_b64}",
                        "prompt": prompt,
                        "image_width": 768,
                        "image_height": 1024,
                        "steps": 25,
                    },
                },
            )
            if not resp.is_success:
                return None
            pred = resp.json()
            poll_url = pred.get("urls", {}).get("get")
            if not poll_url:
                return None
            # Poll until done (capped attempts).
            for _ in range(60):
                poll = client.get(
                    poll_url,
                    headers={"Authorization": f"Token {token}"},
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
                    img = client.get(out_url)
                    img.raise_for_status()
                    return img.content
                if status in ("failed", "canceled"):
                    return None
                time.sleep(2.0)
            return None
    except Exception as exc:
        logger.warning("Replicate IC-Light call errored: %s", exc)
        return None


def _run_iclight(
    *,
    alpha_path: str,
    scene_path: str,
    prompt: str,
) -> bytes | None:
    """Local libcom relighting path.

    libcom (https://github.com/bcmi/libcom) provides ImageHarmonizer that
    approximates relighting for image composites. We fail soft if libcom
    is not installed — tests patch this function directly anyway.
    """
    try:
        from libcom import ImageHarmonizationModel  # type: ignore[import-not-found]
    except ImportError:
        return None

    try:
        # libcom's type stubs declare device: int but the runtime accepts
        # the literal "cpu" — well-documented usage in their README.
        harmonizer = ImageHarmonizationModel(device="cpu", model_type="PCTNet")  # type: ignore[arg-type]
        with Image.open(alpha_path).convert("RGBA") as subject:
            # Build a binary mask from the alpha channel for libcom.
            mask = subject.split()[-1]
            mask_path = Path(alpha_path).with_suffix(".mask.png")
            mask.save(mask_path)
            rgb_path = Path(alpha_path).with_suffix(".rgb.jpg")
            subject.convert("RGB").save(rgb_path, format="JPEG", quality=95)
            # Composite over scene to produce the harmonization input.
            with Image.open(scene_path).convert("RGB") as scene:
                scene = scene.resize(subject.size)
                base_path = Path(alpha_path).with_suffix(".composite.jpg")
                scene.save(base_path, format="JPEG", quality=95)
        result_path = Path(alpha_path).with_suffix(".relit.jpg")
        harmonizer(str(base_path), str(mask_path), save_path=str(result_path))  # type: ignore[call-arg]
        return Path(result_path).read_bytes()
    except Exception as exc:
        logger.warning("libcom IC-Light errored: %s", exc)
        return None
