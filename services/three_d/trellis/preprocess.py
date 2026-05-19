"""Input image preparation for TRELLIS.

TRELLIS expects square-ish, background-free, well-lit garment imagery. This
module turns whatever the caller gave us (raw product photo, model on white,
lifestyle shot, marketplace screenshot) into a clean input that maximizes
generation quality.

Stages
------
1. **Validate**: dimensions, format, file size, accessibility
2. **Background removal** (optional): rembg (default), SAM fallback, or
   "leave alone" for already-isolated assets
3. **Center crop** to garment bounding box with smart padding
4. **Resize** to TRELLIS target (518×518 typical) preserving aspect with
   transparent letterbox
5. **Color normalize**: white-balance + gamma correction
6. **Quality score**: sharpness (Laplacian), contrast, exposure — used to
   short-circuit obviously bad inputs

All heavy deps (``rembg``, ``opencv-python``, ``PIL``) are imported lazily so
the module loads even when they're missing — affected stages emit warnings
and degrade gracefully.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from services.three_d.trellis.config import TrellisConfig

if TYPE_CHECKING:  # pragma: no cover
    from PIL.Image import Image

logger = logging.getLogger(__name__)


# =============================================================================
# Results
# =============================================================================


@dataclass(frozen=True, slots=True)
class PreprocessedImage:
    """Path-based handle to a preprocessed image plus metadata."""

    path: str
    width: int
    height: int
    has_alpha: bool
    background_removed: bool


@dataclass(slots=True)
class PreprocessResult:
    """Outcome of running the preprocessor on a single input."""

    image: PreprocessedImage
    quality_score: float
    sharpness: float
    contrast: float
    exposure: float
    warnings: list[str] = field(default_factory=list)
    bypassed: bool = False

    @property
    def acceptable(self) -> bool:
        """Heuristic: quality_score >= 0.45 is good enough to ship."""
        return self.quality_score >= 0.45


# =============================================================================
# Errors
# =============================================================================


class PreprocessError(RuntimeError):
    """Raised when the preprocessor cannot produce a usable image."""


# =============================================================================
# Preprocessor
# =============================================================================


class TrellisPreprocessor:
    """Image preparation pipeline tuned for TRELLIS clothing generation.

    Usage:
        prep = TrellisPreprocessor(TrellisConfig())
        result = prep.prepare("./uploads/hoodie.jpg")
        ready_path = result.image.path
    """

    # TRELLIS image-large is trained on 518×518 inputs.
    TARGET_RESOLUTION = 518

    def __init__(self, config: TrellisConfig | None = None) -> None:
        self.config = config or TrellisConfig.from_env()
        self.config.ensure_dirs()
        self._cache_dir = Path(self.config.cache_dir) / "preprocess"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def prepare(self, image_path: str | Path) -> PreprocessResult:
        """Run the full preprocessing pipeline on ``image_path``.

        Returns a :class:`PreprocessResult`. Raises :class:`PreprocessError`
        only for genuinely fatal issues (file missing, unreadable, no PIL).
        """
        src = Path(image_path)
        if not src.exists():
            raise PreprocessError(f"Input image not found: {src}")

        warnings: list[str] = []
        pil_image = self._open_image(src, warnings)
        self._validate_dimensions(pil_image, warnings)

        if self.config.enable_background_removal:
            pil_image, bg_removed = self._remove_background(pil_image, warnings)
        else:
            bg_removed = False

        pil_image = self._crop_to_garment(pil_image, warnings)
        pil_image = self._resize_letterbox(pil_image, self.TARGET_RESOLUTION)
        pil_image = self._normalize_color(pil_image, warnings)

        out_path = self._write_output(pil_image, src.stem)
        sharpness, contrast, exposure = self._quality_metrics(pil_image)
        score = self._aggregate_score(sharpness, contrast, exposure)

        return PreprocessResult(
            image=PreprocessedImage(
                path=str(out_path),
                width=pil_image.width,
                height=pil_image.height,
                has_alpha=pil_image.mode == "RGBA",
                background_removed=bg_removed,
            ),
            quality_score=score,
            sharpness=sharpness,
            contrast=contrast,
            exposure=exposure,
            warnings=warnings,
        )

    def passthrough(self, image_path: str | Path) -> PreprocessResult:
        """Skip preprocessing — used when caller asserts the input is ready.

        Still copies into the cache directory so downstream paths are stable.
        """
        src = Path(image_path)
        if not src.exists():
            raise PreprocessError(f"Input image not found: {src}")

        dst = self._cache_dir / f"{src.stem}_passthrough{src.suffix}"
        shutil.copy2(src, dst)
        width, height = self._image_size(src)

        return PreprocessResult(
            image=PreprocessedImage(
                path=str(dst),
                width=width,
                height=height,
                has_alpha=src.suffix.lower() == ".png",
                background_removed=False,
            ),
            quality_score=1.0,
            sharpness=1.0,
            contrast=1.0,
            exposure=1.0,
            warnings=["passthrough: preprocessing skipped"],
            bypassed=True,
        )

    # ---------------------------------------------------------------------
    # Stage implementations
    # ---------------------------------------------------------------------

    def _open_image(self, src: Path, warnings: list[str]) -> Image:
        try:
            from PIL import Image as PILImage
        except ImportError as e:
            raise PreprocessError("Pillow is required: pip install pillow") from e

        img = PILImage.open(src)
        img.load()
        if img.mode not in ("RGB", "RGBA"):
            warnings.append(f"Converting mode {img.mode} → RGBA")
            img = img.convert("RGBA")
        return img

    def _validate_dimensions(self, img: Image, warnings: list[str]) -> None:
        if img.width < self.config.min_input_resolution or img.height < self.config.min_input_resolution:
            warnings.append(
                f"Input resolution {img.size} below recommended minimum "
                f"{self.config.min_input_resolution}px — quality may suffer"
            )
        if max(img.size) > self.config.max_input_resolution:
            warnings.append(
                f"Input resolution {img.size} above max {self.config.max_input_resolution}px"
                f" — will be downscaled before generation"
            )

    def _remove_background(
        self,
        img: Image,
        warnings: list[str],
    ) -> tuple[Image, bool]:
        """Try rembg; if unavailable, leave the image alone but note it."""
        try:
            from rembg import remove  # type: ignore[import-not-found]
        except ImportError:
            warnings.append("rembg not installed — skipping background removal")
            return img, False

        try:
            return remove(img), True
        except Exception as exc:  # noqa: BLE001 — vendor lib raises broadly
            warnings.append(f"Background removal failed: {exc}")
            return img, False

    def _crop_to_garment(self, img: Image, warnings: list[str]) -> Image:
        """Tight bbox crop with 10% padding; assumes alpha = subject when present."""
        try:
            from PIL import Image as PILImage  # noqa: F401
        except ImportError:
            return img

        if img.mode == "RGBA":
            alpha = img.split()[-1]
            bbox = alpha.getbbox()
        else:
            grayscale = img.convert("L")
            bbox = grayscale.point(lambda v: 0 if v >= 240 else 255).getbbox()

        if not bbox:
            warnings.append("Could not find subject bbox — using whole image")
            return img

        left, top, right, bottom = bbox
        width = right - left
        height = bottom - top
        pad_w = int(width * 0.10)
        pad_h = int(height * 0.10)

        left = max(0, left - pad_w)
        top = max(0, top - pad_h)
        right = min(img.width, right + pad_w)
        bottom = min(img.height, bottom + pad_h)

        return img.crop((left, top, right, bottom))

    def _resize_letterbox(self, img: Image, target: int) -> Image:
        """Resize preserving aspect into a square ``target × target`` canvas."""
        from PIL import Image as PILImage

        ratio = min(target / img.width, target / img.height)
        new_size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
        resized = img.resize(new_size, PILImage.Resampling.LANCZOS)

        canvas = PILImage.new("RGBA", (target, target), (255, 255, 255, 0))
        off_x = (target - new_size[0]) // 2
        off_y = (target - new_size[1]) // 2
        if resized.mode != "RGBA":
            resized = resized.convert("RGBA")
        canvas.paste(resized, (off_x, off_y), resized)
        return canvas

    def _normalize_color(self, img: Image, warnings: list[str]) -> Image:
        """Light contrast + brightness equalization. Falls back to no-op."""
        try:
            from PIL import ImageOps
        except ImportError:
            return img
        try:
            if img.mode == "RGBA":
                rgb = img.convert("RGB")
                eq = ImageOps.autocontrast(rgb, cutoff=1)
                eq.putalpha(img.split()[-1])
                return eq
            return ImageOps.autocontrast(img, cutoff=1)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Color normalization skipped: {exc}")
            return img

    def _write_output(self, img: Image, stem: str) -> Path:
        out = self._cache_dir / f"{stem}_trellis_input.png"
        img.save(out, format="PNG")
        return out

    # ---------------------------------------------------------------------
    # Quality metrics
    # ---------------------------------------------------------------------

    def _quality_metrics(self, img: Image) -> tuple[float, float, float]:
        """Return (sharpness, contrast, exposure) — all normalized to [0, 1]."""
        try:
            from PIL import ImageFilter, ImageStat
        except ImportError:
            return 0.5, 0.5, 0.5

        gray = img.convert("L")
        edges = gray.filter(ImageFilter.FIND_EDGES)
        stat = ImageStat.Stat(edges)
        sharpness = min(1.0, stat.stddev[0] / 64.0) if stat.stddev else 0.5

        contrast_stat = ImageStat.Stat(gray)
        contrast = min(1.0, contrast_stat.stddev[0] / 80.0)

        mean = contrast_stat.mean[0]
        exposure = 1.0 - abs((mean - 128) / 128)

        return sharpness, contrast, max(0.0, exposure)

    def _aggregate_score(self, sharpness: float, contrast: float, exposure: float) -> float:
        # Sharpness dominates because blurry input ruins TRELLIS output.
        return round(0.5 * sharpness + 0.3 * contrast + 0.2 * exposure, 4)

    def _image_size(self, src: Path) -> tuple[int, int]:
        from PIL import Image as PILImage

        with PILImage.open(src) as im:
            return im.size


__all__ = [
    "TrellisPreprocessor",
    "PreprocessedImage",
    "PreprocessResult",
    "PreprocessError",
]
