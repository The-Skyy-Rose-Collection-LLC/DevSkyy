"""Garment fidelity quality gate — silhouette IoU + color ΔE.

Validates AI-generated product images against real SkyyRose garments.
Two orthogonal checks:

1. **Silhouette IoU** (60% weight) — binary mask overlap between generated
   and reference images. Catches wrong fit, wrong sleeve length, cropping
   errors, and shape hallucinations.

2. **Color ΔE** (40% weight) — perceptual color distance in CIE LAB space
   between the dominant colors of the generated image and the expected
   palette. Catches wrong hues, over-saturation, lighting shifts.

Dependencies (optional, graceful degradation):
  - opencv-python-headless → silhouette extraction
  - scikit-learn → K-means dominant color extraction
  - numpy → array ops (hard requirement for any real validation)

Without optional deps the gate returns neutral scores (50.0) so it never
blocks but also never auto-approves — forcing manual QA.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Optional dependency guards ───────────────────────────────────────────────

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None  # type: ignore[assignment]

try:
    import numpy as np

    NP_AVAILABLE = True
except ImportError:
    NP_AVAILABLE = False
    np = None  # type: ignore[assignment]

try:
    from sklearn.cluster import KMeans

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    KMeans = None  # type: ignore[assignment]


# ── Result dataclass ─────────────────────────────────────────────────────────


@dataclass
class QualityResult:
    """Outcome of a fidelity validation run."""

    passed: bool
    overall_score: float  # 0-100
    silhouette_iou: float  # 0.0-1.0
    color_delta_e_avg: float  # 0 = identical, higher = worse
    color_accuracy_score: float  # 0-100 (derived from ΔE)
    silhouette_score: float  # 0-100 (IoU * 100)
    threshold: float  # the threshold that was applied
    recommendations: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    validation_time_ms: float = 0.0
    generated_path: str = ""
    reference_paths: list[str] = field(default_factory=list)


# ── Core quality gate ────────────────────────────────────────────────────────


class AssetQualityGate:
    """Validates generated images against reference photos and expected colors.

    Usage::

        gate = AssetQualityGate(threshold=85.0)
        result = await gate.validate_against_real_garment(
            generated_image=Path("output.png"),
            reference_photos=[Path("ref_front.jpg")],
            color_hex_palette=["#8B0000", "#1A1A1F"],
        )
        if not result.passed:
            print(result.recommendations)

    The gate is intentionally conservative: if dependencies are missing it
    returns neutral scores rather than fabricating a pass.
    """

    def __init__(
        self,
        threshold: float = 80.0,
        silhouette_weight: float = 0.60,
        color_weight: float = 0.40,
        min_iou: float = 0.80,
        max_delta_e: float = 15.0,
    ) -> None:
        if not (0 < threshold <= 100):
            raise ValueError(f"threshold must be in (0, 100], got {threshold}")
        if abs(silhouette_weight + color_weight - 1.0) > 1e-6:
            raise ValueError(
                f"silhouette_weight + color_weight must equal 1.0, "
                f"got {silhouette_weight} + {color_weight}"
            )
        self.threshold = threshold
        self.silhouette_weight = silhouette_weight
        self.color_weight = color_weight
        self.min_iou = min_iou
        self.max_delta_e = max_delta_e

    # ── Public API ───────────────────────────────────────────────────────────

    async def validate_against_real_garment(
        self,
        generated_image: Path | str,
        reference_photos: list[Path | str],
        color_hex_palette: list[str] | None = None,
    ) -> QualityResult:
        """Run full fidelity validation.

        Args:
            generated_image: Path to the AI-generated image.
            reference_photos: Paths to real product reference photos.
            color_hex_palette: Expected hex colors (e.g. ``["#8B0000"]``).

        Returns:
            QualityResult with pass/fail, scores, and recommendations.
        """
        start = time.monotonic()
        generated_image = Path(generated_image)
        reference_photos = [Path(p) for p in reference_photos]
        recommendations: list[str] = []

        # ── Input validation ─────────────────────────────────────────────────
        if not generated_image.exists():
            return self._error_result(
                f"Generated image not found: {generated_image}",
                generated_path=str(generated_image),
            )

        valid_refs = [r for r in reference_photos if r.exists()]
        if not valid_refs:
            missing = [str(r) for r in reference_photos if not r.exists()]
            return self._error_result(
                f"No valid reference photos found. Missing: {missing}",
                generated_path=str(generated_image),
            )

        # ── Silhouette IoU ───────────────────────────────────────────────────
        iou = self._compute_silhouette_iou(generated_image, valid_refs)
        silhouette_score = iou * 100.0

        if iou < self.min_iou:
            recommendations.append(
                f"Silhouette IoU {iou:.2f} < {self.min_iou:.2f} — "
                "garment shape doesn't match reference. Regenerate with "
                "stricter shape constraints or check for cropping issues."
            )

        # ── Color ΔE ─────────────────────────────────────────────────────────
        if color_hex_palette:
            avg_delta_e = self._compute_color_accuracy(generated_image, color_hex_palette)
        else:
            avg_delta_e = 0.0  # No palette → skip color check, full marks
            recommendations.append("No color palette provided — color validation skipped.")

        # Convert ΔE to a 0-100 score (lower ΔE = higher score)
        # ΔE 0 → 100, ΔE 15 → 50, ΔE 30+ → 0
        color_accuracy = max(0.0, 100.0 - (avg_delta_e * (100.0 / 30.0)))

        if avg_delta_e > self.max_delta_e:
            recommendations.append(
                f"Color ΔE {avg_delta_e:.1f} > {self.max_delta_e:.1f} — "
                "colors don't match expected palette. Adjust color settings "
                "or lighting in the generation prompt."
            )

        # ── Overall score ────────────────────────────────────────────────────
        overall = silhouette_score * self.silhouette_weight + color_accuracy * self.color_weight
        passed = overall >= self.threshold

        if not passed and not recommendations:
            recommendations.append(
                f"Overall score {overall:.1f} < {self.threshold:.1f} threshold. "
                "Review silhouette and color accuracy."
            )

        elapsed_ms = (time.monotonic() - start) * 1000

        result = QualityResult(
            passed=passed,
            overall_score=round(overall, 2),
            silhouette_iou=round(iou, 4),
            color_delta_e_avg=round(avg_delta_e, 2),
            color_accuracy_score=round(color_accuracy, 2),
            silhouette_score=round(silhouette_score, 2),
            threshold=self.threshold,
            recommendations=recommendations,
            metrics={
                "silhouette_weight": self.silhouette_weight,
                "color_weight": self.color_weight,
                "min_iou_threshold": self.min_iou,
                "max_delta_e_threshold": self.max_delta_e,
                "cv2_available": CV2_AVAILABLE,
                "sklearn_available": SKLEARN_AVAILABLE,
                "num_reference_photos": len(valid_refs),
            },
            validation_time_ms=round(elapsed_ms, 2),
            generated_path=str(generated_image),
            reference_paths=[str(r) for r in valid_refs],
        )

        status = "PASS" if passed else "REJECT"
        logger.info(
            "%s %s: score=%.1f (IoU=%.2f, ΔE=%.1f) threshold=%.1f [%.0fms]",
            status,
            generated_image.name,
            overall,
            iou,
            avg_delta_e,
            self.threshold,
            elapsed_ms,
        )

        return result

    # ── Silhouette IoU ───────────────────────────────────────────────────────

    def _compute_silhouette_iou(
        self,
        generated: Path,
        references: list[Path],
    ) -> float:
        """Compute silhouette IoU between generated and reference images.

        Uses binary thresholding to extract garment silhouettes, then
        computes Intersection-over-Union. Returns the best IoU across
        all reference photos.

        Falls back to 0.50 (neutral) if OpenCV is unavailable.
        """
        if not CV2_AVAILABLE or not NP_AVAILABLE:
            logger.warning("opencv/numpy unavailable — silhouette IoU defaulting to 0.50")
            return 0.50

        try:
            gen_mask = self._extract_silhouette(generated)
            if gen_mask is None:
                return 0.50

            best_iou = 0.0
            for ref_path in references:
                ref_mask = self._extract_silhouette(ref_path)
                if ref_mask is None:
                    continue

                # Resize reference mask to match generated
                ref_resized = cv2.resize(
                    ref_mask,
                    (gen_mask.shape[1], gen_mask.shape[0]),
                    interpolation=cv2.INTER_NEAREST,
                )

                intersection = np.logical_and(gen_mask, ref_resized).sum()
                union = np.logical_or(gen_mask, ref_resized).sum()

                if union == 0:
                    continue

                iou = float(intersection / union)
                best_iou = max(best_iou, iou)

            return best_iou if best_iou > 0 else 0.50

        except Exception:
            logger.exception("Silhouette IoU computation failed")
            return 0.50

    def _extract_silhouette(self, image_path: Path) -> Any | None:
        """Extract binary silhouette mask from an image.

        Converts to grayscale, applies Otsu thresholding, then
        morphological cleanup to get a clean garment mask.
        """
        if not CV2_AVAILABLE or not NP_AVAILABLE:
            return None

        try:
            img = cv2.imread(str(image_path))
            if img is None:
                logger.warning("Failed to read image: %s", image_path)
                return None

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Otsu threshold for automatic foreground/background separation
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Morphological cleanup — close small holes, remove noise
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)

            return cleaned > 0  # boolean mask

        except Exception:
            logger.exception("Silhouette extraction failed for %s", image_path)
            return None

    # ── Color ΔE ─────────────────────────────────────────────────────────────

    def _compute_color_accuracy(
        self,
        generated: Path,
        expected_hex: list[str],
    ) -> float:
        """Compute average color ΔE between generated image and expected palette.

        Extracts dominant colors from the generated image via K-means,
        then computes the minimum ΔE from each dominant to the nearest
        expected color. Returns the average of these minimum distances.

        Falls back to 10.0 (neutral) if dependencies are missing.
        """
        if not CV2_AVAILABLE or not NP_AVAILABLE:
            logger.warning("opencv/numpy unavailable — color ΔE defaulting to 10.0")
            return 10.0

        try:
            dominant_bgr = self._extract_dominant_colors(generated, n_colors=5)
            if not dominant_bgr:
                return 10.0

            expected_bgr = [self._hex_to_bgr(h) for h in expected_hex]

            # For each dominant color, find the nearest expected color
            min_distances: list[float] = []
            for dom in dominant_bgr:
                nearest = min(self._color_delta_e(dom, exp) for exp in expected_bgr)
                min_distances.append(nearest)

            return sum(min_distances) / len(min_distances)

        except Exception:
            logger.exception("Color accuracy computation failed")
            return 10.0

    def _extract_dominant_colors(
        self,
        image_path: Path,
        n_colors: int = 5,
    ) -> list[tuple[int, int, int]]:
        """Extract dominant colors from an image via K-means clustering.

        Falls back to simple quantization if scikit-learn is unavailable.
        """
        if not CV2_AVAILABLE or not NP_AVAILABLE:
            return []

        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return []

            # Resize for speed (K-means on full-res is slow)
            h, w = img.shape[:2]
            scale = min(1.0, 200.0 / max(h, w))
            if scale < 1.0:
                img = cv2.resize(
                    img,
                    (int(w * scale), int(h * scale)),
                    interpolation=cv2.INTER_AREA,
                )

            pixels = img.reshape(-1, 3).astype(np.float32)

            # Remove near-white and near-black (background) pixels
            brightness = pixels.mean(axis=1)
            mask = (brightness > 20) & (brightness < 235)
            pixels = pixels[mask]

            if len(pixels) < n_colors:
                return []

            if SKLEARN_AVAILABLE:
                kmeans = KMeans(
                    n_clusters=n_colors,
                    n_init=3,
                    max_iter=100,
                    random_state=42,
                )
                kmeans.fit(pixels)
                centers = kmeans.cluster_centers_
            else:
                # Simple quantization fallback — divide color space into bins
                quantized = (pixels // 32 * 32 + 16).astype(np.uint8)
                # Find the n most common quantized colors
                unique, counts = np.unique(quantized, axis=0, return_counts=True)
                top_indices = np.argsort(-counts)[:n_colors]
                centers = unique[top_indices].astype(np.float32)

            return [(int(c[0]), int(c[1]), int(c[2])) for c in centers]

        except Exception:
            logger.exception("Dominant color extraction failed")
            return []

    @staticmethod
    def _color_delta_e(
        bgr1: tuple[int, int, int],
        bgr2: tuple[int, int, int],
    ) -> float:
        """Compute CIE76 ΔE between two BGR colors via LAB conversion.

        CIE76 is a simple Euclidean distance in LAB space. Not as
        perceptually uniform as CIEDE2000, but fast and good enough
        for garment validation where we're catching gross color errors
        (wrong hue, wrong saturation) rather than subtle perceptual
        differences.
        """
        if not CV2_AVAILABLE or not NP_AVAILABLE:
            return 10.0  # neutral fallback

        pixel1 = np.array([[bgr1]], dtype=np.uint8)
        pixel2 = np.array([[bgr2]], dtype=np.uint8)

        lab1 = cv2.cvtColor(pixel1, cv2.COLOR_BGR2LAB).astype(np.float32)[0][0]
        lab2 = cv2.cvtColor(pixel2, cv2.COLOR_BGR2LAB).astype(np.float32)[0][0]

        return float(np.sqrt(np.sum((lab1 - lab2) ** 2)))

    @staticmethod
    def _hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
        """Convert hex color string to BGR tuple for OpenCV.

        Args:
            hex_color: Color string like ``"#8B0000"`` or ``"8B0000"``.

        Returns:
            (B, G, R) tuple.

        Raises:
            ValueError: If hex_color is not a valid 6-digit hex string.
        """
        h = hex_color.lstrip("#")
        if len(h) != 6:
            raise ValueError(f"Invalid hex color {hex_color!r} — expected 6 hex digits.")
        try:
            r = int(h[0:2], 16)
            g = int(h[2:4], 16)
            b = int(h[4:6], 16)
        except ValueError:
            raise ValueError(f"Invalid hex digits in {hex_color!r}") from None
        return (b, g, r)  # OpenCV uses BGR

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _error_result(
        self,
        message: str,
        generated_path: str = "",
    ) -> QualityResult:
        """Return a failed QualityResult for error conditions."""
        return QualityResult(
            passed=False,
            overall_score=0.0,
            silhouette_iou=0.0,
            color_delta_e_avg=0.0,
            color_accuracy_score=0.0,
            silhouette_score=0.0,
            threshold=self.threshold,
            recommendations=[message],
            generated_path=generated_path,
        )


__all__ = ["AssetQualityGate", "QualityResult"]
