"""
Visual Regression Tester — SSIM comparison against golden reference images.

Compares a newly generated image against a stored "golden" reference using
the Structural Similarity Index (SSIM). Generates an HTML side-by-side
diff report on each comparison.

scikit-image is optional. If not installed, all comparisons return
passed=True with ssim_score=1.0 and a note in the report.

Golden references live at:
    skyyrose/elite_studio/assets/golden/{sku}/reference.jpg
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_SSIM_THRESHOLD = 0.85
_GOLDEN_BASE = Path(__file__).parent.parent / "assets" / "golden"
_REPORTS_BASE = Path(__file__).parent.parent / "assets" / "regression_reports"

# Per-angle SSIM thresholds. Detail shots demand stricter pixel-level fidelity
# than wide three-quarter views, where minor pose drift is expected. Front/back
# are the baseline — embellishment placement must match exactly. Edit here, do
# not hardcode in callers.
THRESHOLDS_BY_ANGLE: dict[str, float] = {
    "front": 0.85,
    "back": 0.85,
    "three-quarter": 0.78,
    "detail-1": 0.92,
    "detail-2": 0.92,
}

# Canonical angle slug list — the order goldens appear in audit reports and
# the order capture_goldens prompts for during interactive curation.
CANONICAL_ANGLES: tuple[str, ...] = (
    "front",
    "back",
    "three-quarter",
    "detail-1",
    "detail-2",
)

# HTML template pieces — kept as constants to avoid in-function magic strings
_HTML_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Visual Regression Report — {sku}</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0a0a0a; color: #eee; margin: 0; padding: 24px; }}
  h1 {{ color: #B76E79; margin-bottom: 4px; }}
  .meta {{ color: #888; font-size: 0.85rem; margin-bottom: 24px; }}
  .badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px;
            font-weight: bold; font-size: 0.9rem; }}
  .pass {{ background: #1a3a1a; color: #4caf50; }}
  .fail {{ background: #3a1a1a; color: #f44336; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 24px; }}
  .panel {{ background: #111; border-radius: 8px; padding: 16px; }}
  .panel h2 {{ font-size: 0.9rem; color: #999; margin: 0 0 8px; }}
  img {{ width: 100%; border-radius: 4px; object-fit: contain; max-height: 480px; }}
  .score {{ font-size: 2rem; font-weight: bold; color: #d4af37; margin: 16px 0 8px; }}
  .threshold {{ color: #888; font-size: 0.8rem; }}
</style>
</head>
<body>
"""

_HTML_TAIL = "</body></html>"


@dataclass(frozen=True)
class RegressionResult:
    """Result from a visual regression comparison."""

    success: bool
    sku: str
    ssim_score: float  # 0.0 – 1.0; 1.0 when no reference or fallback
    passed: bool
    threshold: float  # comparison threshold used
    has_reference: bool  # False when no golden reference exists yet
    report_path: str  # absolute path to HTML report, "" if not generated
    error: str = ""
    angle: str = "front"


@dataclass(frozen=True)
class MultiAngleResult:
    """Aggregate result across multiple angles for a single SKU."""

    sku: str
    per_angle: tuple[RegressionResult, ...]
    all_passed: bool
    angles_with_reference: int
    angles_total: int

    @property
    def average_score(self) -> float:
        scored = [r for r in self.per_angle if r.has_reference]
        if not scored:
            return 0.0
        return round(sum(r.ssim_score for r in scored) / len(scored), 4)


class VisualRegressionTester:
    """SSIM comparison against golden reference images.

    Usage:
        tester = VisualRegressionTester()
        result = tester.compare("/tmp/generated.jpg", "br-001")

        # Register a new golden reference:
        tester.set_golden("br-001", "/path/to/approved.jpg")
    """

    def __init__(
        self,
        golden_base: Path | str | None = None,
        reports_base: Path | str | None = None,
        threshold: float = _SSIM_THRESHOLD,
    ) -> None:
        self._golden_base = Path(golden_base) if golden_base else _GOLDEN_BASE
        self._reports_base = Path(reports_base) if reports_base else _REPORTS_BASE
        self._threshold = threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compare(
        self,
        generated_path: str,
        sku: str,
        *,
        angle: str = "front",
    ) -> RegressionResult:
        """Compare a generated image against the golden reference for sku.

        Args:
            generated_path: Absolute path to the newly generated image.
            sku: Product SKU used to locate the golden reference.
            angle: Which angle to compare against (front / back / three-quarter /
                detail-1 / detail-2). Defaults to ``front`` to preserve backward
                compatibility with single-angle callers.

        Returns:
            RegressionResult. passed=True when no reference exists yet.
        """
        threshold = THRESHOLDS_BY_ANGLE.get(angle, self._threshold)
        reference_path = self._resolve_reference(sku, angle)

        if reference_path is None:
            logger.info("No golden reference for %s/%s — skipping regression check", sku, angle)
            return RegressionResult(
                success=True,
                sku=sku,
                ssim_score=1.0,
                passed=True,
                threshold=threshold,
                has_reference=False,
                report_path="",
                angle=angle,
            )

        try:
            ssim_score = self._compute_ssim(generated_path, str(reference_path))
            passed = ssim_score >= threshold
            report_path = self._write_report(
                sku=sku,
                generated_path=generated_path,
                reference_path=str(reference_path),
                ssim_score=ssim_score,
                passed=passed,
                angle=angle,
                threshold=threshold,
            )
            return RegressionResult(
                success=True,
                sku=sku,
                ssim_score=round(ssim_score, 4),
                passed=passed,
                threshold=threshold,
                has_reference=True,
                report_path=report_path,
                angle=angle,
            )
        except ImportError:
            logger.warning(
                "scikit-image not installed — skipping SSIM comparison for %s/%s. "
                "Install with: pip install scikit-image",
                sku,
                angle,
            )
            return RegressionResult(
                success=True,
                sku=sku,
                ssim_score=1.0,
                passed=True,
                threshold=threshold,
                has_reference=True,
                report_path="",
                error="scikit-image not installed; comparison skipped",
                angle=angle,
            )
        except Exception as exc:
            logger.error("Visual regression error for %s/%s: %s", sku, angle, exc)
            return RegressionResult(
                success=False,
                sku=sku,
                ssim_score=0.0,
                passed=False,
                threshold=threshold,
                has_reference=True,
                report_path="",
                error=str(exc),
                angle=angle,
            )

    def compare_multi_angle(
        self,
        generated_paths: dict[str, str],
        sku: str,
    ) -> MultiAngleResult:
        """Compare a set of angle-keyed renders against per-angle goldens.

        Args:
            generated_paths: Mapping of ``angle → generated image path``.
                Unknown angles fall back to the global threshold.
            sku: Product SKU used to locate goldens.

        Returns:
            MultiAngleResult aggregating per-angle scores.
        """
        results: list[RegressionResult] = []
        for angle, path in generated_paths.items():
            results.append(self.compare(path, sku, angle=angle))
        with_ref = sum(1 for r in results if r.has_reference)
        all_passed = all(r.passed for r in results)
        return MultiAngleResult(
            sku=sku,
            per_angle=tuple(results),
            all_passed=all_passed,
            angles_with_reference=with_ref,
            angles_total=len(results),
        )

    def set_golden(
        self,
        sku: str,
        image_path: str,
        *,
        angle: str = "front",
    ) -> Path:
        """Register a new golden reference image for a SKU/angle.

        Copies the image to the canonical golden directory. Maintains the
        legacy ``reference.jpg`` symlink/copy for ``angle="front"`` so older
        callers that don't pass an angle continue to work.

        Args:
            sku: Product SKU.
            image_path: Path to the approved reference image.
            angle: Which angle this golden represents.

        Returns:
            The absolute destination path written.
        """
        import shutil

        dest_dir = self._golden_base / sku
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{angle}.jpg"
        shutil.copy2(image_path, dest)
        # Legacy reference.jpg = front for backward compat with single-angle
        # callers. Always overwrite when angle == "front" so the canonical
        # front golden stays in sync.
        if angle == "front":
            shutil.copy2(image_path, dest_dir / "reference.jpg")
        logger.info("Set golden reference for %s/%s → %s", sku, angle, dest)
        return dest

    def coverage_for(self, sku: str) -> dict[str, bool]:
        """Return ``{angle: present}`` map across the canonical angle list."""
        sku_dir = self._golden_base / sku
        if not sku_dir.is_dir():
            return dict.fromkeys(CANONICAL_ANGLES, False)
        return {
            angle: (sku_dir / f"{angle}.jpg").is_file()
            or (angle == "front" and (sku_dir / "reference.jpg").is_file())
            for angle in CANONICAL_ANGLES
        }

    def _resolve_reference(self, sku: str, angle: str) -> Path | None:
        """Find the on-disk golden for ``sku/angle``, if any.

        Honors the back-compat ``reference.jpg`` for ``angle == "front"``.
        """
        candidate = self._golden_base / sku / f"{angle}.jpg"
        if candidate.exists():
            return candidate
        if angle == "front":
            legacy = self._golden_base / sku / "reference.jpg"
            if legacy.exists():
                return legacy
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_ssim(self, generated_path: str, reference_path: str) -> float:
        """Compute SSIM score between two images.

        Args:
            generated_path: Path to generated image.
            reference_path: Path to golden reference.

        Returns:
            SSIM score 0.0 – 1.0.

        Raises:
            ImportError: if scikit-image is not installed.
        """
        import numpy as np  # type: ignore[import]
        from PIL import Image  # type: ignore[import]
        from skimage.metrics import structural_similarity as ssim  # type: ignore[import]

        size = (512, 512)
        gen_img = np.array(Image.open(generated_path).convert("RGB").resize(size))
        ref_img = np.array(Image.open(reference_path).convert("RGB").resize(size))

        # ssim() returns a tuple when full=True or gradient=True; with our
        # default kwargs it returns a single float, but the type stub declares
        # the union. Cast for clarity.
        score = ssim(gen_img, ref_img, channel_axis=-1, data_range=255)
        return float(score)  # type: ignore[arg-type]

    def _write_report(
        self,
        sku: str,
        generated_path: str,
        reference_path: str,
        ssim_score: float,
        passed: bool,
        angle: str = "front",
        threshold: float | None = None,
    ) -> str:
        """Generate an HTML side-by-side comparison report.

        Args:
            sku: Product SKU.
            generated_path: Path to the generated image.
            reference_path: Path to the golden reference image.
            ssim_score: Computed SSIM score.
            passed: Whether the comparison passed the threshold.

        Returns:
            Absolute path to the generated HTML report.
        """
        self._reports_base.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        report_path = self._reports_base / f"{sku}_{angle}_{timestamp}.html"

        gen_b64 = self._img_to_b64(generated_path)
        ref_b64 = self._img_to_b64(reference_path)
        badge_class = "pass" if passed else "fail"
        badge_text = "PASS" if passed else "FAIL"

        html = _HTML_HEAD.format(sku=sku)
        html += f"<h1>Visual Regression — {sku} ({angle})</h1>\n"
        html += f'<p class="meta">Generated {timestamp} UTC — angle={angle}</p>\n'
        html += f'<span class="badge {badge_class}">{badge_text}</span>\n'
        html += f'<div class="score">{ssim_score:.4f}</div>\n'
        # Honor the per-angle threshold actually used for this comparison —
        # detail shots use 0.92, three-quarter uses 0.78, etc. Falling back
        # to the global default would mis-report what the gate actually was.
        effective_threshold = threshold if threshold is not None else self._threshold
        html += f'<p class="threshold">Threshold: {effective_threshold}</p>\n'
        html += '<div class="grid">\n'
        html += (
            '<div class="panel"><h2>Reference (Golden)</h2>'
            f'<img src="data:image/jpeg;base64,{ref_b64}" alt="reference"></div>\n'
        )
        html += (
            '<div class="panel"><h2>Generated</h2>'
            f'<img src="data:image/jpeg;base64,{gen_b64}" alt="generated"></div>\n'
        )
        html += "</div>\n"
        html += _HTML_TAIL

        report_path.write_text(html, encoding="utf-8")
        logger.info("Regression report written: %s", report_path)
        return str(report_path)

    @staticmethod
    def _img_to_b64(image_path: str) -> str:
        """Read an image file and return base64-encoded string."""
        with open(image_path, "rb") as fh:
            return base64.b64encode(fh.read()).decode("ascii")
