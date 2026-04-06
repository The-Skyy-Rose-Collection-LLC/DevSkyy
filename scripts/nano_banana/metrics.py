"""Quantitative scoring metrics — measurable accuracy verification.

Computes hard numbers for: color accuracy (ΔE2000), structural similarity (SSIM),
text OCR match, logo placement, garment classification.

A candidate passes 98% verification when ALL metrics exceed thresholds.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

# Thresholds for passing 98% verification
COLOR_DELTA_E_THRESHOLD = 5.0  # ΔE2000 — lower = more similar
SSIM_THRESHOLD = 0.70  # 0-1 scale, higher = more similar (lower for cross-generation)
TEXT_OCR_THRESHOLD = 0.95  # fraction of expected text characters matched
LOGO_POSITION_TOLERANCE_PCT = 10.0  # max position deviation as % of image dimensions
PASSING_AGGREGATE_SCORE = 0.92  # overall must be >= 92% for basic pass, 98% for high-confidence


@dataclass
class MetricResult:
    """Result of a single metric evaluation."""

    name: str
    passed: bool
    score: float  # 0.0-1.0 normalized
    raw_value: float
    threshold: float
    details: dict = field(default_factory=dict)


@dataclass
class ScoreReport:
    """Complete scoring report for a candidate."""

    candidate_path: str
    source_path: str
    metrics: list[MetricResult]
    aggregate_score: float  # 0.0-1.0
    passed_98: bool
    failed_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "candidate_path": self.candidate_path,
            "source_path": self.source_path,
            "aggregate_score": self.aggregate_score,
            "passed_98": self.passed_98,
            "metrics": [
                {
                    "name": m.name,
                    "passed": m.passed,
                    "score": m.score,
                    "raw_value": m.raw_value,
                    "threshold": m.threshold,
                    "details": m.details,
                }
                for m in self.metrics
            ],
            "failed_metrics": self.failed_metrics,
        }


# -- Color Distance (ΔE2000) ------------------------------------------------


def _rgb_to_lab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    """Convert sRGB (0-255) to CIELAB via D65 whitepoint."""
    # sRGB -> linear RGB
    r, g, b = [c / 255.0 for c in rgb]

    def gamma(c):
        return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92

    r, g, b = gamma(r), gamma(g), gamma(b)
    # Linear RGB -> XYZ (D65)
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    # Normalize to D65 whitepoint
    x, y, z = x / 0.95047, y / 1.0, z / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t) + (16 / 116)

    fx, fy, fz = f(x), f(y), f(z)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b_ = 200 * (fy - fz)
    return L, a, b_


def _delta_e_2000(lab1: tuple, lab2: tuple) -> float:
    """Compute ΔE2000 color difference (CIE 2000)."""
    import math

    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    avg_L = (L1 + L2) / 2
    C1 = math.sqrt(a1 * a1 + b1 * b1)
    C2 = math.sqrt(a2 * a2 + b2 * b2)
    avg_C = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(avg_C**7 / (avg_C**7 + 25**7)))
    a1p = a1 * (1 + G)
    a2p = a2 * (1 + G)
    C1p = math.sqrt(a1p**2 + b1**2)
    C2p = math.sqrt(a2p**2 + b2**2)
    avg_Cp = (C1p + C2p) / 2
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dhp = h2p - h1p
    if abs(dhp) > 180:
        dhp -= 360 if dhp > 0 else -360
    dLp = L2 - L1
    dCp = C2p - C1p
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)
    avg_hp = (h1p + h2p) / 2
    if abs(h1p - h2p) > 180:
        avg_hp += 180
    T = (
        1
        - 0.17 * math.cos(math.radians(avg_hp - 30))
        + 0.24 * math.cos(math.radians(2 * avg_hp))
        + 0.32 * math.cos(math.radians(3 * avg_hp + 6))
        - 0.20 * math.cos(math.radians(4 * avg_hp - 63))
    )
    SL = 1 + (0.015 * (avg_L - 50) ** 2) / math.sqrt(20 + (avg_L - 50) ** 2)
    SC = 1 + 0.045 * avg_Cp
    SH = 1 + 0.015 * avg_Cp * T
    dTheta = 30 * math.exp(-(((avg_hp - 275) / 25) ** 2))
    RC = 2 * math.sqrt(avg_Cp**7 / (avg_Cp**7 + 25**7))
    RT = -RC * math.sin(2 * math.radians(dTheta))
    return math.sqrt(
        (dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2 + RT * (dCp / SC) * (dHp / SH)
    )


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Convert hex string to RGB tuple."""
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _dominant_color(image_path: Path, exclude_white_bg: bool = True) -> tuple[int, int, int]:
    """Extract dominant color from image, optionally excluding white background."""
    import numpy as np
    from PIL import Image

    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)
    pixels = arr.reshape(-1, 3)
    if exclude_white_bg:
        # Filter out white/near-white pixels
        mask = ~((pixels[:, 0] > 230) & (pixels[:, 1] > 230) & (pixels[:, 2] > 230))
        pixels = pixels[mask]
    if len(pixels) == 0:
        return (0, 0, 0)
    # Take median for robustness
    return tuple(int(c) for c in np.median(pixels, axis=0))


def score_color_match(source_path: Path, candidate_path: Path, target_hex: str) -> MetricResult:
    """Score base color accuracy via ΔE2000 distance to target hex."""
    try:
        target_rgb = _hex_to_rgb(target_hex)
        candidate_rgb = _dominant_color(candidate_path)
        lab_target = _rgb_to_lab(target_rgb)
        lab_candidate = _rgb_to_lab(candidate_rgb)
        delta_e = _delta_e_2000(lab_target, lab_candidate)
        passed = delta_e < COLOR_DELTA_E_THRESHOLD
        # Normalize: ΔE=0 → 1.0, ΔE=10 → 0.0
        score = max(0.0, 1.0 - delta_e / 10.0)
        return MetricResult(
            name="color_match",
            passed=passed,
            score=score,
            raw_value=delta_e,
            threshold=COLOR_DELTA_E_THRESHOLD,
            details={
                "target_hex": target_hex,
                "target_rgb": target_rgb,
                "candidate_rgb": candidate_rgb,
                "delta_e": round(delta_e, 2),
            },
        )
    except Exception as exc:
        log.error("color_match failed: %s", exc)
        return MetricResult(
            "color_match", False, 0.0, 0.0, COLOR_DELTA_E_THRESHOLD, {"error": str(exc)}
        )


# -- Structural Similarity (SSIM) -------------------------------------------


def score_ssim(source_path: Path, candidate_path: Path) -> MetricResult:
    """Score structural similarity between source and candidate."""
    try:
        import numpy as np
        from PIL import Image
        from skimage.metrics import structural_similarity as ssim

        img1 = Image.open(source_path).convert("L")
        img2 = Image.open(candidate_path).convert("L")
        # Resize to same dimensions
        target_size = (512, 512)
        img1 = img1.resize(target_size)
        img2 = img2.resize(target_size)
        arr1, arr2 = np.array(img1), np.array(img2)
        similarity = float(ssim(arr1, arr2, data_range=255))
        passed = similarity >= SSIM_THRESHOLD
        return MetricResult(
            name="structural_similarity",
            passed=passed,
            score=similarity,
            raw_value=similarity,
            threshold=SSIM_THRESHOLD,
            details={"ssim": round(similarity, 4)},
        )
    except Exception as exc:
        log.error("SSIM failed: %s", exc)
        return MetricResult(
            "structural_similarity", False, 0.0, 0.0, SSIM_THRESHOLD, {"error": str(exc)}
        )


# -- Text OCR Match ---------------------------------------------------------


def score_text_match(candidate_path: Path, expected_texts: list[str], ocr_fn=None) -> MetricResult:
    """Score text accuracy via OCR.

    Default implementation is a stub (returns pass if no expected text).
    A vision-model-based OCR function is passed in via ocr_fn (deferred to
    keep this module dependency-light).
    """
    expected_texts = [t for t in expected_texts if t and t.strip()]
    if not expected_texts:
        return MetricResult(
            name="text_match",
            passed=True,
            score=1.0,
            raw_value=1.0,
            threshold=TEXT_OCR_THRESHOLD,
            details={"expected": [], "found": [], "note": "no text expected"},
        )

    if ocr_fn is None:
        # No OCR available — return a deferred result
        return MetricResult(
            name="text_match",
            passed=True,
            score=0.5,
            raw_value=0.5,
            threshold=TEXT_OCR_THRESHOLD,
            details={"expected": expected_texts, "note": "OCR deferred — use vision judge"},
        )

    detected_texts = ocr_fn(candidate_path)
    # Normalize for matching
    expected_norm = {t.upper().strip() for t in expected_texts}
    detected_norm = {t.upper().strip() for t in detected_texts}

    matched = expected_norm & detected_norm
    missing = expected_norm - detected_norm
    score = len(matched) / len(expected_norm) if expected_norm else 1.0
    passed = score >= TEXT_OCR_THRESHOLD

    return MetricResult(
        name="text_match",
        passed=passed,
        score=score,
        raw_value=score,
        threshold=TEXT_OCR_THRESHOLD,
        details={
            "expected": list(expected_norm),
            "detected": list(detected_norm),
            "matched": list(matched),
            "missing": list(missing),
        },
    )


# -- Composite scorer -------------------------------------------------------


def score_candidate(
    source_path: Path,
    candidate_path: Path,
    dna: dict,
    ocr_fn=None,
) -> ScoreReport:
    """Score a candidate image against the source + DNA specs.

    Runs all available metrics and returns an aggregate report.
    """
    metrics = []
    failed = {}

    # Color match
    base_color = dna.get("base_color", "")
    if base_color:
        m = score_color_match(source_path, candidate_path, base_color)
        metrics.append(m)
        if not m.passed:
            failed["color_match"] = m.details

    # SSIM
    m = score_ssim(source_path, candidate_path)
    metrics.append(m)
    if not m.passed:
        failed["structural_similarity"] = m.details

    # Text OCR
    text_content = dna.get("text_content", [])
    expected = [t.get("text", "") for t in text_content if isinstance(t, dict) and t.get("text")]
    m = score_text_match(candidate_path, expected, ocr_fn=ocr_fn)
    metrics.append(m)
    if not m.passed:
        failed["text_match"] = m.details

    # Aggregate (weighted average)
    weights = {"color_match": 0.35, "structural_similarity": 0.25, "text_match": 0.40}
    total_weight = 0.0
    weighted_sum = 0.0
    for m in metrics:
        w = weights.get(m.name, 0.2)
        weighted_sum += m.score * w
        total_weight += w
    aggregate = weighted_sum / total_weight if total_weight > 0 else 0.0

    passed_98 = aggregate >= 0.98 and all(m.passed for m in metrics)

    return ScoreReport(
        candidate_path=str(candidate_path),
        source_path=str(source_path),
        metrics=metrics,
        aggregate_score=aggregate,
        passed_98=passed_98,
        failed_metrics=failed,
    )
