"""Stage D: deterministic rasterize composite (Phase 2 Architecture A).

Replaces the kontext/FLUX inpainting path with a pure-PIL alpha-composite that
guarantees pixel-exact reproduction of the product graphic. No generative model
touches the product surface — embroidery, prints, and seam stitching survive
the composite intact.

Pipeline position: runs after Stage A matte and Stage B prompt, before Stage E
cleanup. Output is a scene-sized RGB composite plus the scene-aligned mask
already computed by ``_align_mask_to_scene`` in the orchestrator.

Feature flag: ``ELITE_STUDIO_STAGE_D_MODE``
  - ``kontext`` (default during migration): keep current FLUX-Fill path
  - ``rasterize``: use this module's deterministic path

In SkyyRose's current setup the "verified mockup" is the per-SKU golden
source photo at ``skyyrose/elite_studio/assets/golden/{sku}/`` — the actual
product photography, not a generative output. The orchestrator passes that
path through as ``model_image_path`` already; in rasterize mode the same
path becomes ``mockup_path`` here. The ``mockup_path`` argument is the
verified pixel-exact source, not a generative model output.

See: docs/superpowers/specs/2026-05-27-mockup-stage-d-and-cost-ceiling-design.md
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from PIL import Image

from .infra import _cache_dir

logger = logging.getLogger(__name__)


# Composite layout constants — match _align_mask_to_scene's silhouette
# placement so the rasterized product lines up with the scene-aligned mask
# the orchestrator already produces.
_PRODUCT_FILL_RATIO = 0.72  # silhouette occupies 72% of scene height
_PRODUCT_VBIAS = 0.55  # vertical center biased to 55% (slightly below midline)


def rasterize_composite(
    mockup_path: str,
    scene_image_path: str,
    aligned_mask_path: str,
    sku: str,
    output_dir: str,
) -> str:
    """Composite a verified mockup onto a scene using deterministic PIL ops.

    Args:
        mockup_path: Path to the verified pixel-exact mockup (RGBA preferred,
            RGB acceptable; alpha derived from ``aligned_mask_path`` if missing).
        scene_image_path: Path to the locked scene PNG (RGB).
        aligned_mask_path: Path to the scene-sized 8-bit grayscale mask produced
            by ``_align_mask_to_scene`` in the orchestrator (255 = product,
            0 = background).
        sku: Canonical SKU string used to name output files.
        output_dir: Directory where the composite PNG is written.

    Returns:
        Absolute path to the written ``{sku}-rasterize.png`` file.

    Raises:
        FileNotFoundError: Any input path does not exist on disk.
        ValueError: Scene and mask sizes do not match.
    """
    mockup_p = Path(mockup_path)
    scene_p = Path(scene_image_path)
    mask_p = Path(aligned_mask_path)

    for p in (mockup_p, scene_p, mask_p):
        if not p.exists():
            raise FileNotFoundError(f"stage-d rasterize input missing: {p}")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    scene = Image.open(scene_p).convert("RGB")
    mask = Image.open(mask_p).convert("L")

    if scene.size != mask.size:
        raise ValueError(
            f"scene size {scene.size} does not match mask size {mask.size} — "
            "_align_mask_to_scene must run before stage-d rasterize"
        )

    # Cache key over all three inputs — re-running with the same files is
    # free.
    cache_key = _composite_cache_key(mockup_p, scene_p, mask_p)
    cached = _cache_dir("rasterize") / f"{cache_key}.png"
    dest = out / f"{sku}-rasterize.png"

    if cached.exists():
        cached_img = Image.open(cached).convert("RGB")
        cached_img.save(dest, format="PNG")
        logger.info("stage-d rasterize: cache hit %s", cache_key)
        return str(dest)

    product_layer = _prepare_product_layer(mockup_p, mask)
    composite = Image.alpha_composite(scene.convert("RGBA"), product_layer)
    composite = composite.convert("RGB")
    composite.save(dest, format="PNG")

    try:
        composite.save(cached, format="PNG")
    except OSError:  # pragma: no cover — cache write is best-effort
        pass

    logger.info("stage-d rasterize: %s -> %s", sku, dest)
    return str(dest)


def _prepare_product_layer(mockup_p: Path, mask: Image.Image) -> Image.Image:
    """Build a scene-sized RGBA layer with the product placed at the mask's
    silhouette.

    The mockup is scaled to the bounding box of the mask's non-zero region,
    preserving aspect, then pasted into an empty RGBA at the same position.
    Alpha comes from the mask, which keeps the silhouette identical to what
    Stage A / ``_align_mask_to_scene`` already computed.
    """
    scene_size = mask.size
    mockup = Image.open(mockup_p).convert("RGBA")

    bbox = mask.getbbox()
    if bbox is None:
        raise ValueError(f"mask {mockup_p.name} has empty silhouette — alpha matte failed upstream")

    box_w = bbox[2] - bbox[0]
    box_h = bbox[3] - bbox[1]
    scaled = _scale_to_fit(mockup, box_w, box_h)

    # Center the scaled mockup inside the bbox.
    paste_x = bbox[0] + (box_w - scaled.size[0]) // 2
    paste_y = bbox[1] + (box_h - scaled.size[1]) // 2

    layer = Image.new("RGBA", scene_size, (0, 0, 0, 0))
    layer.paste(scaled, (paste_x, paste_y), scaled)

    # Replace the layer's alpha with the canonical mask so the silhouette
    # matches Stage A's output exactly. The mockup's own alpha (if any) is
    # discarded — the mask is authoritative.
    r, g, b, _ = layer.split()
    layer = Image.merge("RGBA", (r, g, b, mask))
    return layer


def _scale_to_fit(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    """Scale ``img`` to fit inside ``max_w × max_h`` preserving aspect ratio."""
    w, h = img.size
    ratio = min(max_w / w, max_h / h)
    new_w = max(1, int(round(w * ratio)))
    new_h = max(1, int(round(h * ratio)))
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


def align_mask_to_scene(
    alpha_path: str,
    scene_image_path: str,
    sku: str,
    output_dir: str,
) -> str:
    """Resize a cutout-sized alpha matte into a scene-sized 8-bit mask.

    Stage A's matte is sized to the source model image (e.g. 864x1184). The
    scene PNG is a different size (e.g. 896x1200). FAL fill rejects size
    mismatches and ``rasterize_composite`` requires aligned inputs. This
    helper scales the silhouette to ``_PRODUCT_FILL_RATIO`` of scene height
    and centers it vertically at ``_PRODUCT_VBIAS``.

    Args:
        alpha_path: Path to Stage A's RGBA matte (alpha channel = subject).
        scene_image_path: Path to the locked scene PNG.
        sku: Canonical SKU used to name the output mask.
        output_dir: Directory where the aligned mask PNG is written.

    Returns:
        Absolute path to the written ``{sku}-mask-aligned.png`` file
        (scene-sized 8-bit grayscale, 255 = product, 0 = background).
    """
    alpha_p = Path(alpha_path)
    scene_p = Path(scene_image_path)
    if not alpha_p.exists():
        raise FileNotFoundError(f"alpha matte missing: {alpha_p}")
    if not scene_p.exists():
        raise FileNotFoundError(f"scene image missing: {scene_p}")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    scene = Image.open(scene_p).convert("RGB")
    scene_w, scene_h = scene.size

    matte = Image.open(alpha_p).convert("RGBA")
    _, _, _, matte_alpha = matte.split()

    bbox = matte_alpha.getbbox()
    if bbox is None:
        raise ValueError(
            f"alpha matte {alpha_p.name} has empty silhouette — Stage A failed upstream"
        )

    cropped = matte_alpha.crop(bbox)
    crop_w = bbox[2] - bbox[0]
    crop_h = bbox[3] - bbox[1]

    target_h = int(round(scene_h * _PRODUCT_FILL_RATIO))
    scale = target_h / crop_h
    target_w = max(1, int(round(crop_w * scale)))
    scaled = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

    aligned = Image.new("L", (scene_w, scene_h), 0)
    paste_x = (scene_w - target_w) // 2
    paste_y = int(round(scene_h * _PRODUCT_VBIAS)) - target_h // 2
    paste_y = max(0, min(paste_y, scene_h - target_h))
    aligned.paste(scaled, (paste_x, paste_y))

    dest = out / f"{sku}-mask-aligned.png"
    aligned.save(dest, format="PNG")
    logger.info("align_mask_to_scene: %s -> %s (scene=%dx%d)", sku, dest, scene_w, scene_h)
    return str(dest)


def _composite_cache_key(mockup_p: Path, scene_p: Path, mask_p: Path) -> str:
    """Hash of the three input file contents — composites are deterministic."""
    h = hashlib.sha256()
    for p in (mockup_p, scene_p, mask_p):
        with open(p, "rb") as f:
            # Stream-hash to keep memory bounded for large scenes.
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    return h.hexdigest()[:16]
