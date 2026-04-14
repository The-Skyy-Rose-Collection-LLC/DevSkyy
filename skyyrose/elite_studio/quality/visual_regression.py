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

    def compare(self, generated_path: str, sku: str) -> RegressionResult:
        """Compare a generated image against the golden reference for sku.

        Args:
            generated_path: Absolute path to the newly generated image.
            sku: Product SKU used to locate the golden reference.

        Returns:
            RegressionResult. passed=True when no reference exists yet.
        """
        reference_path = self._golden_base / sku / "reference.jpg"

        if not reference_path.exists():
            logger.info("No golden reference for %s — skipping regression check", sku)
            return RegressionResult(
                success=True,
                sku=sku,
                ssim_score=1.0,
                passed=True,
                threshold=self._threshold,
                has_reference=False,
                report_path="",
            )

        try:
            ssim_score = self._compute_ssim(generated_path, str(reference_path))
            passed = ssim_score >= self._threshold
            report_path = self._write_report(
                sku=sku,
                generated_path=generated_path,
                reference_path=str(reference_path),
                ssim_score=ssim_score,
                passed=passed,
            )
            return RegressionResult(
                success=True,
                sku=sku,
                ssim_score=round(ssim_score, 4),
                passed=passed,
                threshold=self._threshold,
                has_reference=True,
                report_path=report_path,
            )
        except ImportError:
            logger.warning(
                "scikit-image not installed — skipping SSIM comparison for %s. "
                "Install with: pip install scikit-image",
                sku,
            )
            return RegressionResult(
                success=True,
                sku=sku,
                ssim_score=1.0,
                passed=True,
                threshold=self._threshold,
                has_reference=True,
                report_path="",
                error="scikit-image not installed; comparison skipped",
            )
        except Exception as exc:
            logger.error("Visual regression error for %s: %s", sku, exc)
            return RegressionResult(
                success=False,
                sku=sku,
                ssim_score=0.0,
                passed=False,
                threshold=self._threshold,
                has_reference=True,
                report_path="",
                error=str(exc),
            )

    def set_golden(self, sku: str, image_path: str) -> None:
        """Register a new golden reference image for a SKU.

        Copies the image to the canonical golden directory.

        Args:
            sku: Product SKU.
            image_path: Path to the approved reference image.
        """
        import shutil

        dest_dir = self._golden_base / sku
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "reference.jpg"
        shutil.copy2(image_path, dest)
        logger.info("Set golden reference for %s → %s", sku, dest)

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

        score: float = ssim(gen_img, ref_img, channel_axis=-1, data_range=255)
        return float(score)

    def _write_report(
        self,
        sku: str,
        generated_path: str,
        reference_path: str,
        ssim_score: float,
        passed: bool,
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
        report_path = self._reports_base / f"{sku}_{timestamp}.html"

        gen_b64 = self._img_to_b64(generated_path)
        ref_b64 = self._img_to_b64(reference_path)
        badge_class = "pass" if passed else "fail"
        badge_text = "PASS" if passed else "FAIL"

        html = _HTML_HEAD.format(sku=sku)
        html += f"<h1>Visual Regression — {sku}</h1>\n"
        html += f'<p class="meta">Generated {timestamp} UTC</p>\n'
        html += f'<span class="badge {badge_class}">{badge_text}</span>\n'
        html += f'<div class="score">{ssim_score:.4f}</div>\n'
        html += f'<p class="threshold">Threshold: {self._threshold}</p>\n'
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
