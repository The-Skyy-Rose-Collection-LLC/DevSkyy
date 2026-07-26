"""3D model review scorer — analytic (free) + VLM (paid) fidelity dimensions.

Wraps imagery/model_fidelity.py::ModelFidelityValidator for the geometry signal
and the free texture-detail floor; adds material/color/proportion analysis via
direct GLB/PBR extraction (pygltflib); adds one paid VLM branding check.

Color and material judgments are made from the raw GLB texture data, never
from a rendered preview image: a rendered preview can look desaturated/gray
from tone-mapping even when the stored PBR data is correct (confirmed on a
real Tripo3D asset — stored base color #1e201f with correct fleece
roughness/metalness, while its own rendered preview looked gray). Branding is
the one dimension that legitimately needs a rendered image (a raw texture
atlas doesn't show placement/silhouette), so it is scored against Tripo's own
rendered preview, never a locally-rendered one (pyrender/OSMesa is confirmed
non-headless-safe on this machine).
"""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import os
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np
from PIL import Image
from pydantic import BaseModel
from pygltflib import GLTF2
from skimage.color import deltaE_ciede2000, rgb2lab

from imagery.model_fidelity import FidelityCategory, ModelFidelityValidator
from skyyrose.character_pipeline._glb_io import image_bytes as _glb_image_bytes

log = logging.getLogger(__name__)

# ── geometry: reuse ModelFidelityValidator's own category weights, renormalized
# to mesh_integrity+geometry_quality only (texture_quality and visual_accuracy
# are scored separately by this module) ──────────────────────────────────────
_GEOMETRY_CATEGORIES = (FidelityCategory.MESH_INTEGRITY, FidelityCategory.GEOMETRY_QUALITY)
_GEOMETRY_WEIGHT_SUM = sum(
    ModelFidelityValidator.CATEGORY_WEIGHTS[cat] for cat in _GEOMETRY_CATEGORIES
)

# ── materials: v1 default expected-range table — generic "fabric" only. A full
# per-garment-material taxonomy is future work; empirically confirmed correct
# on the one Tripo fleece asset inspected this session (roughness ~0.94,
# metalness ~0.03) — one sensible default is enough for v1. ─────────────────
_FABRIC_ROUGHNESS_MIN = 0.6
_FABRIC_ROUGHNESS_TOLERANCE = 0.6
_FABRIC_METALNESS_MAX = 0.15
_FABRIC_METALNESS_TOLERANCE = 0.5

# ── colors: CIEDE2000 falloff bounds. ΔE<=2 is at/below the "just noticeable
# difference" threshold in standard color science -> full score; ΔE>=15 reads
# as a clearly different color -> zero. Linear in between. ──────────────────
_COLOR_DELTAE_PERFECT = 2.0
_COLOR_DELTAE_FLOOR = 15.0

# Texture-atlas padding is real background; a genuinely dark garment is not.
# The session's reference asset stored a CORRECT near-black fleece at
# RGB(30,32,31) -- every channel above 8 -- so an <8 cutoff only ever catches
# actual unused atlas padding, never legitimate dark fabric.
_NEAR_BLACK_THRESHOLD = 8
_NEAR_TRANSPARENT_ALPHA_THRESHOLD = 10
_NEAR_WHITE_THRESHOLD = 240  # studio-white packshot background convention

# ── proportions: relative aspect-ratio deviation falloff (50% relative
# deviation -> score 0) ──────────────────────────────────────────────────────
_PROPORTIONS_TOLERANCE = 0.5

# ── branding VLM judge (the one paid dimension) ──────────────────────────────
_BRANDING_JUDGE_MODEL = "claude-sonnet-4-6"
_BRANDING_ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
_BRANDING_REQUEST_TIMEOUT_S = 180.0
_BRANDING_MAX_OUTPUT_TOKENS = 1500
_BRANDING_JUDGE_API_RETRIES = 2
_BRANDING_JUDGE_RETRY_BACKOFF_S = 1.5
_EST_BRANDING_JUDGE_COST_USD = 0.05
_BRANDING_MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

# Structured schema forcing a free-text visual_analysis field BEFORE any
# numeric verdict — mirrors scripts/oai_render/qc.py's _JUDGE_SCHEMA design,
# directly motivated by this session's own false-color-negative lesson: force
# grounded observation before a score.
_BRANDING_JUDGE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "visual_analysis": {
            "type": "string",
            "description": "FIRST, before any verdict: describe what the candidate "
            "rendered preview ACTUALLY shows for branding — is a graphic/embroidery/logo "
            "present, what artwork and colorway it carries, and which panel/placement it "
            "sits on. Then compare each to the reference image explicitly. This forced "
            "description must precede the numeric score so it is grounded in observation.",
        },
        "graphic_present": {
            "type": "boolean",
            "description": "True if a graphic/embroidery/logo is visible on the candidate.",
        },
        "artwork_matches_reference": {
            "type": "boolean",
            "description": "True if the visible artwork/colorway matches the reference "
            "image (not necessarily pixel-perfect, but the same design and color family).",
        },
        "placement_correct": {
            "type": "boolean",
            "description": "True if the graphic sits on the same panel/region as the "
            "reference image shows.",
        },
        "branding": {
            "type": "number",
            "description": "0-100 overall branding fidelity score, consistent with the "
            "boolean gates above.",
        },
        "reason": {
            "type": "string",
            "description": "One sentence explaining the score.",
        },
    },
    "required": [
        "visual_analysis",
        "graphic_present",
        "artwork_matches_reference",
        "placement_correct",
        "branding",
        "reason",
    ],
    "additionalProperties": False,
}

_BRANDING_JUDGE_TOOL: dict = {
    "name": "branding_qc_verdict",
    "description": "Record the branding fidelity verdict for the candidate 3D model render.",
    "input_schema": _BRANDING_JUDGE_SCHEMA,
}


class AnalyticScoreResult(BaseModel):
    geometry: float
    materials: float
    colors: float
    proportions: float
    texture_detail_floor: float  # resolution + UV coverage floor; VLM refinement is separate
    overall_partial: float  # mean of the 4 analytic dims, for use before branding is scored


class BrandingScoreResult(BaseModel):
    branding: float
    visual_analysis: str  # forced free-text observation BEFORE the numeric score
    judge_cost_usd: float


def score_analytic(model_path: Path, sku: str, reference_image_path: Path) -> AnalyticScoreResult:
    """Score geometry/materials/colors/proportions + the texture-detail floor.

    Pure function: $0, no DB, no network call, no API key required.
    """
    import trimesh

    log.info("score_analytic: sku=%s model=%s", sku, model_path)
    mesh = trimesh.load(str(model_path), force="mesh")

    category_scores = asyncio.run(_geometry_and_texture_category_scores(mesh, model_path))
    geometry = _weighted_geometry_score(category_scores)
    texture_detail_floor = category_scores.get(FidelityCategory.TEXTURE_QUALITY.value, 0.0)

    materials = _score_materials(model_path)
    colors = _score_colors(model_path, reference_image_path)
    proportions = _score_proportions(mesh, reference_image_path)

    overall_partial = (geometry + materials + colors + proportions) / 4.0

    return AnalyticScoreResult(
        geometry=geometry,
        materials=materials,
        colors=colors,
        proportions=proportions,
        texture_detail_floor=texture_detail_floor,
        overall_partial=overall_partial,
    )


async def _geometry_and_texture_category_scores(mesh, model_path: Path) -> dict[str, float]:
    """Runs ModelFidelityValidator's private metric-extraction + category-scoring
    directly, bypassing validate()'s visual-accuracy step entirely. That step is
    the ONLY place the class can reach pyrender.OffscreenRenderer, confirmed
    non-headless-safe on this machine — calling the private methods trades
    encapsulation for a hard guarantee this path never renders.
    """
    validator = ModelFidelityValidator()
    metrics = await validator._extract_metrics(mesh, model_path)
    return await validator._calculate_category_scores(metrics)


def _weighted_geometry_score(category_scores: dict[str, float]) -> float:
    mesh_integrity = category_scores.get(FidelityCategory.MESH_INTEGRITY.value, 0.0)
    geometry_quality = category_scores.get(FidelityCategory.GEOMETRY_QUALITY.value, 0.0)
    weighted = (
        mesh_integrity * ModelFidelityValidator.CATEGORY_WEIGHTS[FidelityCategory.MESH_INTEGRITY]
        + geometry_quality
        * ModelFidelityValidator.CATEGORY_WEIGHTS[FidelityCategory.GEOMETRY_QUALITY]
    )
    return weighted / _GEOMETRY_WEIGHT_SUM


# ── materials ─────────────────────────────────────────────────────────────


def _score_materials(model_path: Path) -> float:
    gltf = GLTF2.load(str(model_path))
    subscores: list[float] = []
    for material in gltf.materials:
        pbr = material.pbrMetallicRoughness
        if pbr is None:
            continue
        roughness = pbr.roughnessFactor if pbr.roughnessFactor is not None else 1.0
        metalness = pbr.metallicFactor if pbr.metallicFactor is not None else 1.0
        if pbr.metallicRoughnessTexture is not None:
            channel_means = _orm_channel_means(gltf, pbr.metallicRoughnessTexture.index)
            if channel_means is not None:
                # glTF spec: final value = factor * texture sample. ORM convention:
                # G channel = roughness, B channel = metalness.
                roughness *= channel_means[1]
                metalness *= channel_means[2]
        subscores.append(_material_range_score(roughness=roughness, metalness=metalness))
    if not subscores:
        return 0.0
    return sum(subscores) / len(subscores)


def _orm_channel_means(gltf: GLTF2, texture_index: int) -> tuple[float, float, float] | None:
    image = _decode_gltf_image(gltf, texture_index)
    if image is None:
        return None
    arr = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    means = arr.mean(axis=(0, 1))
    return float(means[0]), float(means[1]), float(means[2])


def _range_penalty_score(
    value: float, *, low: float | None = None, high: float | None = None, tolerance: float
) -> float:
    """100 when value sits within [low, high]; falls off linearly to 0 once the
    deviation reaches `tolerance` beyond the nearer bound."""
    if low is not None and value < low:
        deficit = low - value
    elif high is not None and value > high:
        deficit = value - high
    else:
        return 100.0
    return max(0.0, 100.0 * (1.0 - deficit / tolerance))


def _material_range_score(*, roughness: float, metalness: float) -> float:
    roughness_score = _range_penalty_score(
        roughness, low=_FABRIC_ROUGHNESS_MIN, tolerance=_FABRIC_ROUGHNESS_TOLERANCE
    )
    metalness_score = _range_penalty_score(
        metalness, high=_FABRIC_METALNESS_MAX, tolerance=_FABRIC_METALNESS_TOLERANCE
    )
    return (roughness_score + metalness_score) / 2.0


# ── colors ────────────────────────────────────────────────────────────────


def _score_colors(model_path: Path, reference_image_path: Path) -> float:
    texture_rgb = _extract_base_color(model_path)
    with Image.open(reference_image_path) as ref_img:
        reference_rgb = _dominant_color_rgb(ref_img.convert("RGBA"), background="light")
    delta_e = _delta_e_rgb(texture_rgb, reference_rgb)
    return _color_score_from_delta_e(delta_e)


def _extract_base_color(model_path: Path) -> tuple[float, float, float]:
    gltf = GLTF2.load(str(model_path))
    for material in gltf.materials:
        pbr = material.pbrMetallicRoughness
        if pbr is None:
            continue
        if pbr.baseColorTexture is not None:
            image = _decode_gltf_image(gltf, pbr.baseColorTexture.index)
            if image is not None:
                return _dominant_color_rgb(image, background="dark")
        if pbr.baseColorFactor:
            r, g, b = pbr.baseColorFactor[:3]
            return r * 255.0, g * 255.0, b * 255.0
    # No usable base-color signal on any material — neutral mid-gray, scored as
    # a large-but-bounded deviation rather than crashing the whole pipeline.
    return 128.0, 128.0, 128.0


def _decode_gltf_image(gltf: GLTF2, texture_index: int) -> Image.Image | None:
    if texture_index >= len(gltf.textures):
        return None
    texture = gltf.textures[texture_index]
    if texture.source is None:
        return None
    image_meta = gltf.images[texture.source]
    if image_meta.bufferView is None:
        return None
    blob = gltf.binary_blob()
    if not blob:
        return None
    raw = _glb_image_bytes(gltf, blob, texture.source)
    try:
        return Image.open(io.BytesIO(raw)).convert("RGBA")
    except Exception as exc:
        log.warning("Failed to decode embedded GLB image %d: %s", texture.source, exc)
        return None


def _dominant_color_rgb(image: Image.Image, *, background: str) -> tuple[float, float, float]:
    """Mean RGB (0-255) of non-background pixels.

    `background` selects the masking convention: "dark" for GLB base-color
    textures (near-black/near-transparent atlas padding), "light" for real
    product packshots (studio-white backdrop).
    """
    rgba = np.asarray(image.convert("RGBA"), dtype=np.float32)
    rgb, alpha = rgba[..., :3], rgba[..., 3]
    if background == "dark":
        is_background = (rgb.max(axis=-1) < _NEAR_BLACK_THRESHOLD) | (
            alpha < _NEAR_TRANSPARENT_ALPHA_THRESHOLD
        )
    else:
        is_background = (rgb.min(axis=-1) > _NEAR_WHITE_THRESHOLD) | (
            alpha < _NEAR_TRANSPARENT_ALPHA_THRESHOLD
        )
    foreground = ~is_background
    if not np.any(foreground):
        foreground = np.ones_like(is_background)  # fully masked/degenerate: fall back to all
    mean_rgb = rgb[foreground].mean(axis=0)
    return float(mean_rgb[0]), float(mean_rgb[1]), float(mean_rgb[2])


def _delta_e_rgb(rgb_a: tuple[float, float, float], rgb_b: tuple[float, float, float]) -> float:
    lab_a = rgb2lab(np.array([[[c / 255.0 for c in rgb_a]]], dtype=np.float64))
    lab_b = rgb2lab(np.array([[[c / 255.0 for c in rgb_b]]], dtype=np.float64))
    return float(deltaE_ciede2000(lab_a, lab_b).squeeze())


def _color_score_from_delta_e(delta_e: float) -> float:
    if delta_e <= _COLOR_DELTAE_PERFECT:
        return 100.0
    if delta_e >= _COLOR_DELTAE_FLOOR:
        return 0.0
    span = _COLOR_DELTAE_FLOOR - _COLOR_DELTAE_PERFECT
    return 100.0 * (1.0 - (delta_e - _COLOR_DELTAE_PERFECT) / span)


# ── proportions ───────────────────────────────────────────────────────────


def _score_proportions(mesh, reference_image_path: Path) -> float:
    bounds = np.asarray(mesh.bounding_box.bounds, dtype=np.float64)
    extents = bounds[1] - bounds[0]
    width_3d, height_3d = float(extents[0]), float(extents[1])
    if height_3d <= 0:
        return 50.0  # degenerate mesh extent — no signal, neutral score

    with Image.open(reference_image_path) as ref_img:
        aspect_2d = _garment_bbox_aspect(ref_img.convert("RGBA"))
    if aspect_2d is None:
        return 50.0  # fully-masked/blank reference — no signal, neutral score

    aspect_3d = width_3d / height_3d
    relative_error = abs(aspect_3d - aspect_2d) / aspect_2d
    return max(0.0, 100.0 * (1.0 - relative_error / _PROPORTIONS_TOLERANCE))


def _garment_bbox_aspect(image: Image.Image) -> float | None:
    rgba = np.asarray(image, dtype=np.float32)
    rgb, alpha = rgba[..., :3], rgba[..., 3]
    is_background = (rgb.min(axis=-1) > _NEAR_WHITE_THRESHOLD) | (
        alpha < _NEAR_TRANSPARENT_ALPHA_THRESHOLD
    )
    ys, xs = np.nonzero(~is_background)
    if ys.size == 0 or xs.size == 0:
        return None
    width_px = float(xs.max() - xs.min() + 1)
    height_px = float(ys.max() - ys.min() + 1)
    if height_px <= 0:
        return None
    return width_px / height_px


# ── branding (paid VLM judge) ────────────────────────────────────────────


def score_branding_vlm(
    rendered_preview_path: Path,
    reference_image_path: Path,
    sku: str,
    judge_fn: Callable[[dict], tuple[dict, float]] | None = None,
) -> BrandingScoreResult:
    """The one paid dimension — VLM judge for graphic/embroidery presence,
    artwork match, and placement, comparing Tripo's own rendered preview
    against the SOT reference photo.

    Fail-hard on missing API key when no judge_fn is injected — no silent
    fallback (this codebase's established rule, see scripts/oai_render/qc.py).
    """
    if judge_fn is None:
        _require_anthropic_key()

    request = {
        "instructions": _branding_judge_instructions(sku),
        "rendered_preview_path": rendered_preview_path,
        "reference_image_path": reference_image_path,
    }
    if judge_fn is not None:
        verdict, cost = judge_fn(request)
    else:
        verdict, cost = _call_anthropic_branding_judge(request)
    return _branding_result_from_verdict(verdict, cost)


def _require_anthropic_key() -> None:
    key = os.environ.get(_BRANDING_ANTHROPIC_API_KEY_ENV, "").strip()
    if not key:
        raise RuntimeError(
            f"{_BRANDING_ANTHROPIC_API_KEY_ENV} not set — the branding VLM judge cannot "
            "start. Pass a judge_fn for testing, or set the key to make a real call."
        )


def _branding_judge_instructions(sku: str) -> str:
    return (
        "You are a product-branding QC judge. The FIRST image is a rendered preview of "
        f"a generated 3D model for SKU {sku}. The SECOND image is the real product "
        "reference photo. FIRST, in `visual_analysis`, describe exactly what "
        "graphic/embroidery/logo (if any) appears on the candidate, its artwork and "
        "colorway, and which panel/placement it sits on — then compare explicitly to "
        "the reference. Only after that description, decide: is a graphic present "
        "(`graphic_present`), does its artwork match the reference "
        "(`artwork_matches_reference`), and is its placement/panel correct "
        "(`placement_correct`)? Then give an overall 0-100 `branding` fidelity score "
        "consistent with those gates, and a one-sentence `reason`."
    )


def _image_block(path: Path) -> dict:
    """One base64 image content block for the Anthropic messages API."""
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": _mime_for(path),
            "data": _b64_raw(path.read_bytes()),
        },
    }


def _branding_judge_content(
    rendered_preview_path: Path, reference_image_path: Path, instructions: str
) -> list[dict]:
    """Judge content blocks: instructions, then the rendered preview FIRST and
    the reference photo SECOND — the judge instructions depend on that order."""
    return [
        {"type": "text", "text": instructions},
        _image_block(rendered_preview_path),
        _image_block(reference_image_path),
    ]


def _call_anthropic_branding_judge(request: dict) -> tuple[dict, float]:
    import anthropic

    key = os.environ.get(_BRANDING_ANTHROPIC_API_KEY_ENV, "").strip()
    if not key:
        raise RuntimeError(
            f"{_BRANDING_ANTHROPIC_API_KEY_ENV} not set — the branding VLM judge cannot start."
        )
    client = anthropic.Anthropic(api_key=key, timeout=_BRANDING_REQUEST_TIMEOUT_S)

    content = _branding_judge_content(
        request["rendered_preview_path"],
        request["reference_image_path"],
        request["instructions"],
    )

    def _send():
        return client.messages.create(
            model=_BRANDING_JUDGE_MODEL,
            max_tokens=_BRANDING_MAX_OUTPUT_TOKENS,
            tools=[_BRANDING_JUDGE_TOOL],
            tool_choice={"type": "any"},  # forces exactly one branding_qc_verdict tool call
            messages=[{"role": "user", "content": content}],
        )

    resp = _call_with_retries(_send)
    verdict: dict = {}
    for block in resp.content:
        if (
            getattr(block, "type", None) == "tool_use"
            and block.name == _BRANDING_JUDGE_TOOL["name"]
        ):
            verdict = dict(block.input)
            break
    if not verdict:
        raise RuntimeError("no branding_qc_verdict tool_use block in judge response")
    return verdict, _EST_BRANDING_JUDGE_COST_USD


def _call_with_retries(send: Callable[[], object], *, retries: int = _BRANDING_JUDGE_API_RETRIES):
    for attempt in range(retries + 1):
        try:
            return send()
        except Exception:
            if attempt == retries:
                raise
            delay = _BRANDING_JUDGE_RETRY_BACKOFF_S * (attempt + 1)
            log.warning(
                "Branding judge API call failed (attempt %d) — retrying in %.1fs",
                attempt + 1,
                delay,
            )
            time.sleep(delay)


def _mime_for(path: Path) -> str:
    return _BRANDING_MIME_MAP.get(path.suffix.lower(), "image/png")


def _b64_raw(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _branding_result_from_verdict(verdict: dict, cost: float) -> BrandingScoreResult:
    branding = max(0.0, min(100.0, float(verdict.get("branding", 0.0))))
    visual_analysis = str(verdict.get("visual_analysis", ""))
    return BrandingScoreResult(
        branding=branding, visual_analysis=visual_analysis, judge_cost_usd=float(cost)
    )
