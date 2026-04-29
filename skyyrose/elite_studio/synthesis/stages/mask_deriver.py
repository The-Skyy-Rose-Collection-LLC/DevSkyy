"""Stage 2: Decoration-mask derivation.

Given a Stage 1 candidate render and the dossier, produce a binary mask
where WHITE pixels mark the regions to re-inpaint and BLACK pixels mark
everything else.

In Path B (audit-driven targeted masking) the caller passes
``allowed_regions`` — only violation regions identified by the H4 audit
are masked. Regions that already rendered correctly are left black so
Stage 3 FLUX Fill cannot touch them.

Raises OverMaskError when derived coverage exceeds MAX_MASK_AREA_FRAC — at
that point Stage 3 would near-fully regenerate the garment, which is worse
than accepting the Stage 1 output as-is.

Two derivation paths:
1. Gemini Flash vision (primary) — looks at the image + branding regions
   and outputs bounding boxes per region.
2. Static templates (fallback) — pre-baked region masks per garment type.

Both produce the same shape of output: a PIL Image mode 'L' (grayscale)
matching the input image dimensions, with values 0 or 255.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Techniques that produce VISIBLE applied decoration (worth masking).
# 'stitched' is excluded because it usually describes structural elements
# (body fabric, pocket construction, hood seams) — Stage 1 handles those.
DECORATION_TECHNIQUES: frozenset[str] = frozenset(
    {
        "embossed",
        "debossed",
        "embroidered",
        "embroidered-patch",
        "printed",
        "screen-print",
        "sublimated",
        "patch",
        "woven-label",
        "puff-print",
        "heat-transfer",
        "laser-engraved",
        "tackle-twill",
        "silicone-applique",
    }
)

# Region prefixes that select front vs back entries. A region not matching
# either is rendered in both views (e.g., 'collar-inside', 'left-sleeve').
FRONT_PREFIXES = ("front-",)
BACK_PREFIXES = ("back-",)

# Sanity bounds on mask coverage as a fraction of total pixels.
# Below 0.005: probably empty / failed → fallback or warn.
# Above 0.4: too aggressive, no benefit over no-mask.
MIN_MASK_AREA_FRAC = 0.005
MAX_MASK_AREA_FRAC = 0.4

# Regex matches an entry like:
#   - **front-center-chest** (~3in tall, ...): description.
#     **Technique:** embossed. **Color:** black on black.
# Region must be hyphenated word characters only (validator-compatible).
_ENTRY_RE = re.compile(
    r"^-\s+\*\*(?P<region>[\w-]+)\*\*\s*\([^)]*\):\s*"
    r"(?P<description>.+?)"
    r"\*\*Technique:\*\*\s*(?P<technique>[\w-]+)\.?\s*"
    r"\*\*Color:\*\*\s*(?P<color>.+?)(?:\.\s*$|$)",
    re.MULTILINE | re.DOTALL,
)


@dataclass
class BrandingEntry:
    region: str
    description: str
    technique: str
    color: str
    raw: str = ""

    def is_decoration(self) -> bool:
        """True if this entry describes applied decoration worth masking."""
        return self.technique.strip().lower() in DECORATION_TECHNIQUES

    def matches_view(self, view: str) -> bool:
        # Regions without a front/back prefix (sleeves, collar-inside, hood)
        # appear in both views — only explicitly opposite-prefixed regions are excluded.
        opposite = BACK_PREFIXES if view.lower().strip() == "front" else FRONT_PREFIXES
        return not self.region.startswith(opposite)


@dataclass
class MaskResult:
    """Output of derive_mask — the mask + diagnostic info."""

    mask_path: Path
    method: str  # "gemini-flash" | "static-template" | "fallback-empty"
    region_boxes: list[dict[str, Any]] = field(default_factory=list)
    coverage_frac: float = 0.0
    warnings: list[str] = field(default_factory=list)


def parse_branding_entries(branding_block: str) -> list[BrandingEntry]:
    """Extract structured entries from a dossier's branding_block markdown."""
    entries: list[BrandingEntry] = []
    for match in _ENTRY_RE.finditer(branding_block):
        entries.append(
            BrandingEntry(
                region=match.group("region").strip(),
                description=match.group("description").strip().rstrip("."),
                technique=match.group("technique").strip(),
                color=match.group("color").strip().rstrip("."),
                raw=match.group(0),
            )
        )
    return entries


def filter_decoration_entries(entries: list[BrandingEntry], *, view: str) -> list[BrandingEntry]:
    """Keep only decoration entries visible in the requested view."""
    return [e for e in entries if e.is_decoration() and e.matches_view(view)]


class MaskDeriver:
    """Derives the decoration mask for a single render.

    The Gemini path is primary; the static-template path is fallback for
    when Gemini fails or returns invalid bounding boxes. The static path
    is also used for unit tests (no API calls).
    """

    def __init__(
        self,
        *,
        gemini_caller: Any | None = None,
        template_dir: Path | None = None,
    ) -> None:
        # Inject for tests; default uses skyyrose.elite_studio.gemini_rest.
        self._gemini_caller = gemini_caller
        self._template_dir = template_dir

    def derive(
        self,
        *,
        image_path: str | Path,
        dossier: dict,
        view: str,
        out_dir: str | Path,
        allowed_regions: list[str] | None = None,
    ) -> MaskResult:
        """Build the decoration mask for ``image_path``.

        Args:
            image_path: Stage 1 candidate render.
            dossier: parsed dossier dict including ``branding_block``.
            view: 'front' or 'back'.
            out_dir: where to write the mask PNG.
            allowed_regions: when set (Path B), restrict masking to this subset
                of region names — only violation regions identified by the H4
                audit.  None means mask all decoration regions in the dossier.

        Returns:
            MaskResult with mask_path + method + diagnostics.

        Raises:
            OverMaskError: if derived coverage exceeds MAX_MASK_AREA_FRAC.
        """
        from PIL import Image  # local import — keeps top-level imports cheap

        image_path = Path(image_path)
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        mask_path = out_dir / f"{image_path.stem}-mask.png"

        with Image.open(image_path) as im:
            width, height = im.size

        entries = parse_branding_entries(dossier.get("branding_block", ""))
        decoration_entries = filter_decoration_entries(entries, view=view)
        if allowed_regions is not None:
            normalized = {r.lower().replace(" ", "-") for r in allowed_regions}
            decoration_entries = [e for e in decoration_entries if e.region.lower() in normalized]
        if not decoration_entries:
            logger.warning(
                "no decoration entries in dossier for sku=%s view=%s — "
                "writing empty mask (Stage 3 will be a no-op)",
                dossier.get("sku") or dossier.get("name"),
                view,
            )
            empty = Image.new("L", (width, height), 0)
            empty.save(mask_path)
            return MaskResult(
                mask_path=mask_path,
                method="fallback-empty",
                coverage_frac=0.0,
                warnings=["no decoration entries"],
            )

        boxes: list[dict[str, Any]] = []
        method = "gemini-flash"
        try:
            boxes = self._derive_via_gemini(
                image_path=image_path,
                entries=decoration_entries,
                dossier=dossier,
                image_size=(width, height),
            )
        except _GeminiUnusable as exc:
            logger.warning("gemini mask derivation unusable: %s — falling back", exc)
            method = "static-template"
        except Exception:  # pragma: no cover - defensive
            logger.exception("unexpected gemini mask derivation error — falling back")
            method = "static-template"

        if not boxes:
            method = "static-template"
            boxes = self._derive_via_templates(
                entries=decoration_entries,
                image_size=(width, height),
                garment_type=dossier.get("garment_type", ""),
            )

        mask = _rasterize_boxes(boxes, image_size=(width, height))
        coverage = _coverage_fraction(mask)
        warnings: list[str] = []

        if coverage < MIN_MASK_AREA_FRAC:
            warnings.append(f"mask coverage {coverage:.4f} below sanity floor {MIN_MASK_AREA_FRAC}")
        if coverage > MAX_MASK_AREA_FRAC:
            raise OverMaskError(
                f"mask coverage {coverage:.4f} exceeds ceiling {MAX_MASK_AREA_FRAC:.2f} "
                f"({len(boxes)} regions, sku={dossier.get('sku')!r}). "
                "Stage 3 would near-fully regenerate. Reduce allowed_regions or "
                "raise MAX_MASK_AREA_FRAC explicitly."
            )

        mask.save(mask_path)
        logger.info(
            "mask derived: sku=%s view=%s method=%s coverage=%.3f boxes=%d",
            dossier.get("sku"),
            view,
            method,
            coverage,
            len(boxes),
        )

        return MaskResult(
            mask_path=mask_path,
            method=method,
            region_boxes=boxes,
            coverage_frac=coverage,
            warnings=warnings,
        )

    # --- Gemini path ---

    def _derive_via_gemini(
        self,
        *,
        image_path: Path,
        entries: list[BrandingEntry],
        dossier: dict,
        image_size: tuple[int, int],
    ) -> list[dict[str, Any]]:
        prompt = _build_mask_prompt(
            entries=entries,
            garment_name=dossier.get("name", "garment"),
            image_size=image_size,
        )
        raw = self._call_gemini(image_path=image_path, prompt=prompt)
        return _parse_gemini_boxes(raw, image_size=image_size)

    def _call_gemini(self, *, image_path: Path, prompt: str) -> str:
        """Call Gemini Flash for vision analysis. Returns raw text response."""
        if self._gemini_caller is not None:
            # Test injection path
            return str(self._gemini_caller(image_path=image_path, prompt=prompt))

        import base64

        from skyyrose.elite_studio.config import GEMINI_VISION_MODEL
        from skyyrose.elite_studio.gemini_rest import analyze_vision

        ext = image_path.suffix.lower().lstrip(".")
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        image_b64 = base64.standard_b64encode(image_path.read_bytes()).decode("ascii")

        response = analyze_vision(
            model=GEMINI_VISION_MODEL,
            prompt=prompt,
            image_b64=image_b64,
            mime_type=mime,
        )
        if not response.get("success"):
            raise _GeminiUnusable(f"vision call failed: {response.get('error', 'unknown')}")
        return str(response.get("text", ""))

    # --- Static template path ---

    def _derive_via_templates(
        self,
        *,
        entries: list[BrandingEntry],
        image_size: tuple[int, int],
        garment_type: str,
    ) -> list[dict[str, Any]]:
        """Fallback: derive bounding boxes from a static per-region registry.

        Boxes are normalized 0-1 coordinates per region — converted to
        absolute pixels here.
        """
        boxes: list[dict[str, Any]] = []
        width, height = image_size
        for entry in entries:
            normalized = STATIC_REGION_BOXES.get(entry.region)
            if normalized is None:
                logger.warning(
                    "no static template for region '%s' (garment_type=%s)",
                    entry.region,
                    garment_type,
                )
                continue
            x1, y1, x2, y2 = normalized
            boxes.append(
                {
                    "region": entry.region,
                    "bbox": [
                        int(round(x1 * width)),
                        int(round(y1 * height)),
                        int(round(x2 * width)),
                        int(round(y2 * height)),
                    ],
                    "source": "static-template",
                }
            )
        return boxes


# Static normalized 0-1 bounding boxes per common region name.
# Coordinates are (x1, y1, x2, y2) on a portrait product render with the
# garment centered. Slightly generous (10% padding).
STATIC_REGION_BOXES: dict[str, tuple[float, float, float, float]] = {
    # Chest / front
    "front-center-chest": (0.38, 0.20, 0.62, 0.42),
    "front-left-chest": (0.30, 0.18, 0.48, 0.34),
    "front-right-chest": (0.52, 0.18, 0.70, 0.34),
    "front-chest": (0.30, 0.18, 0.70, 0.42),
    "front-chevron": (0.20, 0.10, 0.80, 0.32),
    "front-body": (0.20, 0.20, 0.80, 0.75),
    # Back
    "back-yoke": (0.40, 0.10, 0.60, 0.24),
    "back-neck": (0.42, 0.06, 0.58, 0.18),
    "back-center": (0.30, 0.30, 0.70, 0.62),
    "back-body": (0.20, 0.15, 0.80, 0.75),
    # Sleeves & cuffs
    "left-sleeve": (0.06, 0.20, 0.24, 0.62),
    "right-sleeve": (0.76, 0.20, 0.94, 0.62),
    "left-cuff": (0.06, 0.55, 0.20, 0.66),
    "right-cuff": (0.80, 0.55, 0.94, 0.66),
    # Collar / hood / hem
    "collar-inside": (0.40, 0.04, 0.60, 0.14),
    "back-collar-inside": (0.40, 0.04, 0.60, 0.14),
    "hood": (0.30, 0.00, 0.70, 0.15),
    "hood-front": (0.30, 0.00, 0.70, 0.15),
    "hem": (0.20, 0.85, 0.80, 0.95),
    "waistband": (0.20, 0.78, 0.80, 0.88),
    # Pants regions (used by sets like sg-014, sg-015)
    "front-thigh-chevron": (0.22, 0.20, 0.78, 0.55),
    "front-thigh-chevron-pants": (0.22, 0.20, 0.78, 0.55),
    "front-left-pocket-pants": (0.20, 0.18, 0.40, 0.35),
    "front-right-pocket-pants": (0.60, 0.18, 0.80, 0.35),
    "left-ankle-cuff-pants": (0.20, 0.86, 0.40, 0.96),
    "right-ankle-cuff-pants": (0.60, 0.86, 0.80, 0.96),
    # Dossier-name aliases — some dossiers use bare "left-ankle-cuff" / "right-ankle-cuff"
    # without the "-pants" suffix; map to the same coordinates so both names hit the fallback.
    "left-ankle-cuff": (0.20, 0.86, 0.40, 0.96),
    "right-ankle-cuff": (0.60, 0.86, 0.80, 0.96),
    # Windbreaker-set / jacket-specific aliases (sg-015 dossier uses these names)
    "left-cuff-jacket": (0.06, 0.55, 0.20, 0.66),
    "right-cuff-jacket": (0.80, 0.55, 0.94, 0.66),
    "waistband-jacket": (0.20, 0.78, 0.80, 0.88),
    "waistband-pants": (0.20, 0.78, 0.80, 0.88),
}


# --- Helpers ---


class _GeminiUnusable(Exception):
    """Internal sentinel — Gemini failed in a way that should fall back."""


class OverMaskError(Exception):
    """Raised when derived mask coverage exceeds MAX_MASK_AREA_FRAC.

    Stage 3 FLUX Fill would near-fully regenerate the garment rather than
    surgically inpainting decoration regions. Callers must not proceed to
    Stage 3 — reduce the set of violation regions or investigate the dossier.
    """


def _build_mask_prompt(
    *,
    entries: list[BrandingEntry],
    garment_name: str,
    image_size: tuple[int, int],
) -> str:
    width, height = image_size
    region_lines = "\n".join(
        f"  - region '{e.region}': {e.description} ({e.technique})" for e in entries
    )
    return (
        f"You are a fashion product imagery preprocessor. The attached image "
        f"shows a {garment_name}. Image size: {width}x{height} pixels.\n\n"
        f"Locate the pixel bounding boxes for each of these decoration regions "
        f"on the garment. These are the only regions that may be re-inpainted — "
        f"everything outside them must remain untouched.\n\n"
        f"Regions to locate:\n"
        f"{region_lines}"
        f"\n\nFor EACH region, output a bounding box in pixel coordinates "
        f"relative to the top-left of the image. Be slightly generous "
        f"(~10% padding around the visible zone).\n\n"
        f"Output ONLY a JSON array, no prose, no code fences:\n"
        f'[{{"region":"<region>","bbox":[x1,y1,x2,y2]}}, ...]\n\n'
        f"Coordinates must be integers in the range [0, {width}] for x and "
        f"[0, {height}] for y, with x1<x2 and y1<y2."
    )


def _parse_gemini_boxes(raw: str, *, image_size: tuple[int, int]) -> list[dict[str, Any]]:
    """Extract a list of {region, bbox} dicts from Gemini's text response."""
    if not raw:
        raise _GeminiUnusable("empty gemini response")

    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    arr_match = re.search(r"\[.*\]", text, re.DOTALL)
    if not arr_match:
        raise _GeminiUnusable("no JSON array in gemini response")

    try:
        data = json.loads(arr_match.group(0))
    except json.JSONDecodeError as exc:
        raise _GeminiUnusable(f"gemini JSON parse failed: {exc}") from exc

    if not isinstance(data, list):
        raise _GeminiUnusable("gemini response root is not a list")

    width, height = image_size
    boxes: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        region = str(item.get("region", "")).strip()
        bbox = item.get("bbox")
        if not region or not isinstance(bbox, list) or len(bbox) != 4:
            continue
        try:
            x1, y1, x2, y2 = (int(round(float(v))) for v in bbox)
        except (TypeError, ValueError):
            continue
        # Clip to image bounds
        x1, x2 = sorted((max(0, min(width, x1)), max(0, min(width, x2))))
        y1, y2 = sorted((max(0, min(height, y1)), max(0, min(height, y2))))
        if x2 <= x1 or y2 <= y1:
            continue
        boxes.append(
            {
                "region": region,
                "bbox": [x1, y1, x2, y2],
                "source": "gemini-flash",
            }
        )

    if not boxes:
        raise _GeminiUnusable("no valid bounding boxes after parsing+clipping")
    return boxes


def _rasterize_boxes(
    boxes: list[dict[str, Any]], *, image_size: tuple[int, int]
) -> Any:  # PIL.Image.Image
    """Render a list of bbox dicts to a binary PIL mask."""
    from PIL import Image, ImageDraw

    width, height = image_size
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    for box in boxes:
        x1, y1, x2, y2 = box["bbox"]
        draw.rectangle([x1, y1, x2, y2], fill=255)
    return mask


def _coverage_fraction(mask: Any) -> float:
    """Fraction of mask pixels that are white."""
    width, height = mask.size
    total = width * height
    if total == 0:
        return 0.0
    # PIL histogram for mode 'L' is a 256-element list; index 255 = full white.
    hist = mask.histogram()
    white = hist[255]
    return white / total
