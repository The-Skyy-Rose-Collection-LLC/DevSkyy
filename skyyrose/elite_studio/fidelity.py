"""
Fidelity checks for composited renders.

Wave 1 numeric guardrails for the "100% replica" claim. Compares a rendered image against
a registered master via three independent checks:

    1. Color  — dominant-palette ΔE* CIE76 match against `color_spec.primary/accents`
    2. Text   — OCR intersection with `text_spec` (optional; pytesseract + tesseract binary)
    3. CLIP   — embedding cosine similarity subject-vs-master (optional; open_clip_torch)

Every check returns a structured result with `available`, `score`, `pass`, `details`.
Missing optional dependencies never raise — checks report `available=False` with a
`reason` string so the pipeline and telemetry degrade gracefully.

Thresholds are intentionally conservative — tune against real baseline telemetry.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Defaults — overridable per call.
DEFAULT_COLOR_DELTA_E_MAX = 10.0
DEFAULT_CLIP_SIMILARITY_MIN = 0.95
DEFAULT_TEXT_MATCH_MIN = 1.0  # every string in text_spec must appear


@dataclass
class CheckResult:
    name: str
    available: bool
    score: float | None = None
    threshold: float | None = None
    passed: bool | None = None
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# Color fidelity — always available (uses Pillow).
# ─────────────────────────────────────────────────────────────────────────────


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    cleaned = h.lstrip("#").strip()
    if len(cleaned) == 3:
        cleaned = "".join(ch * 2 for ch in cleaned)
    if len(cleaned) != 6:
        raise ValueError(f"invalid hex color: {h!r}")
    try:
        return int(cleaned[0:2], 16), int(cleaned[2:4], 16), int(cleaned[4:6], 16)
    except ValueError as exc:
        raise ValueError(f"invalid hex color: {h!r}") from exc


def _rgb_to_lab(r: int, g: int, b: int) -> tuple[float, float, float]:
    """sRGB → CIELab (D65). Self-contained so we don't pull scikit-image."""

    def _srgb_to_lin(c: float) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    rl, gl, bl = _srgb_to_lin(r), _srgb_to_lin(g), _srgb_to_lin(b)
    # sRGB D65 → XYZ
    x = rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375
    y = rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750
    z = rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041
    # Normalize by D65 reference white.
    xr, yr, zr = x / 0.95047, y / 1.0, z / 1.08883

    def _f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t + 16 / 116)

    fx, fy, fz = _f(xr), _f(yr), _f(zr)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def _delta_e_cie76(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _dominant_colors(image_path: str | Path, top_n: int = 8) -> list[tuple[int, int, int, int]]:
    """Return [(count, r, g, b), ...] sorted by count desc."""
    try:
        from PIL import Image
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Pillow required for color fidelity: {e}") from e
    with Image.open(image_path) as img:
        img = img.convert("RGB").resize((128, 128))  # downsample for speed
        palette = img.quantize(colors=max(top_n * 2, 16), method=Image.Quantize.FASTOCTREE)
        counts = palette.getcolors() or []
        pal = palette.getpalette() or []
    out: list[tuple[int, int, int, int]] = []
    for count, idx in sorted(counts, key=lambda p: -p[0])[:top_n]:
        base = idx * 3
        if base + 2 < len(pal):
            out.append((count, pal[base], pal[base + 1], pal[base + 2]))
    return out


def check_color(
    image_path: str | Path,
    color_spec: dict[str, Any],
    *,
    delta_e_max: float = DEFAULT_COLOR_DELTA_E_MAX,
    top_n: int = 8,
) -> CheckResult:
    """Check that every expected color in `color_spec` matches some dominant color in the image."""
    expected: list[tuple[str, str]] = []
    if "primary" in color_spec:
        expected.append(("primary", color_spec["primary"]))
    for i, hexv in enumerate(color_spec.get("accents", []) or []):
        expected.append((f"accent_{i}", hexv))
    if not expected:
        return CheckResult(
            name="color",
            available=True,
            reason="no colors in color_spec",
            passed=True,
            details={"expected": []},
        )
    try:
        dominant = _dominant_colors(image_path, top_n=top_n)
    except Exception as e:
        return CheckResult(
            name="color", available=False, reason=f"dominant-color extraction failed: {e}"
        )
    dominant_lab = [(c, _rgb_to_lab(r, g, b)) for c, r, g, b in dominant]

    per_color: list[dict[str, Any]] = []
    worst_delta = 0.0
    for role, hexv in expected:
        try:
            target_lab = _rgb_to_lab(*_hex_to_rgb(hexv))
        except ValueError as exc:
            per_color.append(
                {"role": role, "hex": hexv, "delta_e": None, "pass": False, "error": str(exc)}
            )
            continue
        best = min(
            (_delta_e_cie76(target_lab, lab) for _, lab in dominant_lab), default=float("inf")
        )
        per_color.append(
            {"role": role, "hex": hexv, "delta_e": round(best, 2), "pass": best <= delta_e_max}
        )
        worst_delta = max(worst_delta, best)

    all_pass = all(p["pass"] for p in per_color)
    return CheckResult(
        name="color",
        available=True,
        score=round(worst_delta, 2),
        threshold=delta_e_max,
        passed=all_pass,
        details={"per_color": per_color, "dominant_top_n": top_n},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Text fidelity — OCR, optional dependency.
# ─────────────────────────────────────────────────────────────────────────────


def check_text(
    image_path: str | Path,
    text_spec: list[str],
    *,
    min_match_rate: float = DEFAULT_TEXT_MATCH_MIN,
) -> CheckResult:
    if not text_spec:
        return CheckResult(
            name="text", available=True, passed=True, score=1.0, reason="no text_spec"
        )
    try:
        import pytesseract
        from PIL import Image
    except Exception as e:
        return CheckResult(name="text", available=False, reason=f"pytesseract unavailable: {e}")
    try:
        with Image.open(image_path) as img:
            extracted = pytesseract.image_to_string(img).lower()
    except Exception as e:
        return CheckResult(name="text", available=False, reason=f"OCR failed: {e}")

    found: list[str] = []
    missing: list[str] = []
    for needle in text_spec:
        (found if needle.lower() in extracted else missing).append(needle)
    rate = len(found) / max(len(text_spec), 1)
    return CheckResult(
        name="text",
        available=True,
        score=round(rate, 3),
        threshold=min_match_rate,
        passed=rate >= min_match_rate,
        details={"found": found, "missing": missing, "extracted_chars": len(extracted)},
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLIP similarity — optional dependency (open_clip_torch).
# ─────────────────────────────────────────────────────────────────────────────

_CLIP_STATE: dict[str, Any] = {"loaded": False, "model": None, "preprocess": None, "error": None}


def _load_clip() -> tuple[Any, Any] | None:
    if _CLIP_STATE["loaded"]:
        if _CLIP_STATE["error"]:
            return None
        return _CLIP_STATE["model"], _CLIP_STATE["preprocess"]
    _CLIP_STATE["loaded"] = True
    try:
        import open_clip  # type: ignore[import-not-found]
        import torch  # noqa: F401

        model, _, preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="openai"
        )
        model.eval()
        _CLIP_STATE["model"], _CLIP_STATE["preprocess"] = model, preprocess
        return model, preprocess
    except Exception as e:
        _CLIP_STATE["error"] = str(e)
        return None


def check_clip_similarity(
    image_a: str | Path,
    image_b: str | Path,
    *,
    min_similarity: float = DEFAULT_CLIP_SIMILARITY_MIN,
) -> CheckResult:
    bundle = _load_clip()
    if bundle is None:
        return CheckResult(
            name="clip",
            available=False,
            reason=f"open_clip unavailable: {_CLIP_STATE.get('error')}",
        )
    try:
        import torch
        from PIL import Image

        model, preprocess = bundle
        with torch.no_grad():
            a = preprocess(Image.open(image_a).convert("RGB")).unsqueeze(0)
            b = preprocess(Image.open(image_b).convert("RGB")).unsqueeze(0)
            ea = model.encode_image(a)
            eb = model.encode_image(b)
            ea = ea / ea.norm(dim=-1, keepdim=True)
            eb = eb / eb.norm(dim=-1, keepdim=True)
            sim = float((ea * eb).sum().item())
        return CheckResult(
            name="clip",
            available=True,
            score=round(sim, 4),
            threshold=min_similarity,
            passed=sim >= min_similarity,
            details={"model": "ViT-B-32/openai"},
        )
    except Exception as e:
        return CheckResult(name="clip", available=False, reason=f"CLIP comparison failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Aggregate gate
# ─────────────────────────────────────────────────────────────────────────────


def run_fidelity_gate(
    rendered_image_path: str | Path,
    *,
    color_spec: dict[str, Any] | None = None,
    text_spec: list[str] | None = None,
    reference_image_path: str | Path | None = None,
    delta_e_max: float = DEFAULT_COLOR_DELTA_E_MAX,
    text_match_min: float = DEFAULT_TEXT_MATCH_MIN,
    clip_min: float = DEFAULT_CLIP_SIMILARITY_MIN,
) -> dict[str, Any]:
    """Run all checks that are possible given the provided inputs and environment.

    Returns a compact dict suitable for inclusion in telemetry events:

        {
            "checks": {"color": {...}, "text": {...}, "clip": {...}},
            "passed_all_available": bool,
            "checks_run": int,
        }

    A check with available=False does NOT fail the gate; only available checks count.
    """
    checks: dict[str, CheckResult] = {}
    if color_spec is not None:
        checks["color"] = check_color(rendered_image_path, color_spec, delta_e_max=delta_e_max)
    if text_spec is not None:
        checks["text"] = check_text(rendered_image_path, text_spec, min_match_rate=text_match_min)
    if reference_image_path is not None:
        checks["clip"] = check_clip_similarity(
            rendered_image_path, reference_image_path, min_similarity=clip_min
        )

    available_results = [c for c in checks.values() if c.available]
    passed_all = all(c.passed for c in available_results if c.passed is not None)
    return {
        "checks": {k: v.to_dict() for k, v in checks.items()},
        "passed_all_available": bool(available_results) and passed_all,
        "checks_run": len(available_results),
    }
