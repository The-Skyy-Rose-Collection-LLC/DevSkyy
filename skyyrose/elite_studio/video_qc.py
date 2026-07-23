"""
Automated QC gate for generated video clips (Seedance / image-to-video outputs).

Implements the §4 pre-filter from ``tasks/fidelity-hardening-research.md``: sample
frames with ffmpeg, then run three independent, cheap checks that catch the
mechanical failure classes video diffusion is prone to —

    1. Text     — OCR each frame, best-frame similarity vs the expected string
                  (catches "BLACK IS BEAUTIFUL" → "BLACKY").
    2. Garment  — CLIP cosine similarity vs a locked garment reference, per frame
                  (catches design/garment drift across the clip).
    3. Identity — ArcFace embedding similarity vs the canonical face reference,
                  per frame (catches character identity drift in motion).

This runs BEFORE the founder's eyes-on full-res QC so human attention concentrates
on subjective judgment instead of pixel-counting.

FAIL-CLOSED CONTRACT (differs from ``fidelity.run_fidelity_gate``, which is
fail-open): a requested check whose backend/dependency is unavailable does NOT
pass silently — it yields verdict ``needs_human``. A clip is certified ``pass``
only when every requested check actually ran AND passed. Verdict precedence:
``fail`` (any hard reject) > ``needs_human`` (any requested check couldn't run) >
``pass``. Absent input/dependency = block, never a green light (bug-230).

The per-check backends (OCR, CLIP scorer, face-embedder) are injectable so the
aggregation and fail-closed logic are unit-testable without heavyweight ML deps,
mirroring ``skyyrose/elite_studio``'s existing ``score_text_match(ocr_fn=...)``.
"""

from __future__ import annotations

import difflib
import importlib.util
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from skyyrose.elite_studio.fidelity import CheckResult, check_clip_similarity

# Thresholds — deliberately looser than the still-image gate: motion frames drift
# from the start-frame conditioning by design, so a per-frame video threshold that
# reused the 0.95 still-image CLIP floor would reject every real clip.
DEFAULT_TEXT_RATIO_MIN = 0.85
DEFAULT_GARMENT_SIM_MIN = 0.85
DEFAULT_IDENTITY_SIM_MIN = 0.60
DEFAULT_NUM_FRAMES = 12

# Type aliases for injectable backends.
OcrFn = Callable[[Path], str]
GarmentScoreFn = Callable[[Path, Path], "float | None"]
FaceEmbedFn = Callable[[Path], "Sequence[float] | None"]


# ─────────────────────────────────────────────────────────────────────────────
# Frame extraction (ffmpeg)
# ─────────────────────────────────────────────────────────────────────────────


def _probe_duration(video_path: Path) -> float | None:
    """Return video duration in seconds via ffprobe, or None if unavailable."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        return None
    try:
        out = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        return float(out.stdout.strip())
    except (subprocess.SubprocessError, ValueError):
        return None


def extract_frames(
    video_path: str | Path,
    *,
    num_frames: int = DEFAULT_NUM_FRAMES,
    out_dir: str | Path | None = None,
) -> list[Path]:
    """Sample ``num_frames`` evenly spaced frames from ``video_path`` as PNGs.

    Returns the written frame paths (sorted). Raises ``RuntimeError`` if ffmpeg is
    missing or the video is unreadable — a QC gate that cannot see the frames must
    not pretend it looked (fail-closed at the source).
    """
    video_path = Path(video_path)
    if num_frames < 1:
        raise ValueError("num_frames must be >= 1")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg not found on PATH — cannot extract frames")
    if not video_path.exists():
        raise RuntimeError(f"video not found: {video_path}")

    dest = Path(out_dir) if out_dir is not None else Path(tempfile.mkdtemp(prefix="videoqc_"))
    dest.mkdir(parents=True, exist_ok=True)

    duration = _probe_duration(video_path)
    frames: list[Path] = []
    if duration and duration > 0:
        # Deterministic even sampling: midpoints of num_frames equal segments.
        for i in range(num_frames):
            ts = duration * (i + 0.5) / num_frames
            out_path = dest / f"frame-{i:03d}.png"
            try:
                subprocess.run(
                    [
                        ffmpeg,
                        "-nostdin",
                        "-y",
                        "-ss",
                        f"{ts:.3f}",
                        "-i",
                        str(video_path),
                        "-frames:v",
                        "1",
                        "-q:v",
                        "2",
                        str(out_path),
                    ],
                    capture_output=True,
                    timeout=60,
                    check=True,
                )
            except subprocess.SubprocessError:
                continue
            if out_path.exists() and out_path.stat().st_size > 0:
                frames.append(out_path)
    else:
        # No probe — fall back to ffmpeg's own even thumbnail selection.
        pattern = dest / "frame-%03d.png"
        try:
            subprocess.run(
                [
                    ffmpeg,
                    "-nostdin",
                    "-y",
                    "-i",
                    str(video_path),
                    "-vf",
                    f"thumbnail,fps=1/max(1\\,{num_frames})",
                    "-frames:v",
                    str(num_frames),
                    str(pattern),
                ],
                capture_output=True,
                timeout=120,
                check=True,
            )
        except subprocess.SubprocessError as exc:
            raise RuntimeError(f"ffmpeg frame extraction failed: {exc}") from exc
        frames = sorted(dest.glob("frame-*.png"))

    if not frames:
        raise RuntimeError(f"no frames extracted from {video_path}")
    return sorted(frames)


# ─────────────────────────────────────────────────────────────────────────────
# Text check — OCR + best-frame string similarity
# ─────────────────────────────────────────────────────────────────────────────


def _text_ratio(a: str, b: str) -> float:
    """Normalized similarity in [0,1]. Uses python-Levenshtein if present, else
    stdlib difflib (always available) — so the ratio never becomes a missing dep."""
    a_n, b_n = a.strip().lower(), b.strip().lower()
    if not a_n and not b_n:
        return 1.0
    if not a_n or not b_n:
        return 0.0
    try:
        import Levenshtein  # type: ignore[import-not-found]

        return float(Levenshtein.ratio(a_n, b_n))
    except Exception:
        return difflib.SequenceMatcher(None, a_n, b_n).ratio()


def _default_ocr(path: Path) -> str:
    import pytesseract  # type: ignore[import-not-found]
    from PIL import Image

    with Image.open(path) as img:
        return pytesseract.image_to_string(img)


def check_video_text(
    frames: Sequence[str | Path],
    expected_text: str,
    *,
    min_ratio: float = DEFAULT_TEXT_RATIO_MIN,
    ocr_fn: OcrFn | None = None,
) -> CheckResult:
    """Best-frame OCR similarity to ``expected_text``.

    Score = the *maximum* per-frame similarity (the clip's clearest reading of the
    text). ``available=False`` when no OCR backend is present — the caller treats
    that as needs_human, never a pass.
    """
    if not expected_text:
        return CheckResult(
            name="video_text", available=True, passed=True, score=1.0, reason="no expected_text"
        )
    if ocr_fn is None:
        if (
            importlib.util.find_spec("pytesseract") is None
            or importlib.util.find_spec("PIL") is None
        ):
            return CheckResult(
                name="video_text",
                available=False,
                reason="OCR backend unavailable: pytesseract/Pillow not installed",
            )
        ocr_fn = _default_ocr

    best_ratio = 0.0
    best_text = ""
    read_count = 0
    for f in frames:
        try:
            extracted = ocr_fn(Path(f))
        except Exception:
            continue
        read_count += 1
        r = _text_ratio(extracted, expected_text)
        if r > best_ratio:
            best_ratio, best_text = r, extracted.strip()
    if read_count == 0:
        return CheckResult(
            name="video_text", available=False, reason="OCR produced no readings on any frame"
        )
    return CheckResult(
        name="video_text",
        available=True,
        score=round(best_ratio, 3),
        threshold=min_ratio,
        passed=best_ratio >= min_ratio,
        details={"expected": expected_text, "best_reading": best_text, "frames_read": read_count},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Garment check — CLIP similarity vs a locked reference, worst frame
# ─────────────────────────────────────────────────────────────────────────────


def _default_garment_score(frame: Path, ref: Path) -> float | None:
    result = check_clip_similarity(frame, ref, min_similarity=0.0)
    return result.score if result.available else None


def check_video_garment(
    frames: Sequence[str | Path],
    garment_ref: str | Path,
    *,
    min_similarity: float = DEFAULT_GARMENT_SIM_MIN,
    score_fn: GarmentScoreFn | None = None,
) -> CheckResult:
    """CLIP similarity of every frame to a locked garment reference.

    Score = the *worst* (minimum) per-frame similarity: a garment that drifts on
    even one sampled frame fails, since drift is what we are hunting.
    """
    scorer = score_fn if score_fn is not None else _default_garment_score
    sims: list[float] = []
    for f in frames:
        s = scorer(Path(f), Path(garment_ref))
        if s is not None:
            sims.append(s)
    if not sims:
        return CheckResult(
            name="video_garment",
            available=False,
            reason="CLIP scorer unavailable or produced no scores",
        )
    worst = min(sims)
    return CheckResult(
        name="video_garment",
        available=True,
        score=round(worst, 4),
        threshold=min_similarity,
        passed=worst >= min_similarity,
        details={
            "worst_frame_sim": round(worst, 4),
            "mean_sim": round(sum(sims) / len(sims), 4),
            "frames_scored": len(sims),
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Identity check — ArcFace embedding similarity vs canonical face, worst frame
# ─────────────────────────────────────────────────────────────────────────────


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _default_face_embed(path: Path) -> Sequence[float] | None:
    from deepface import DeepFace  # type: ignore[import-not-found]

    reps = DeepFace.represent(str(path), model_name="ArcFace", enforce_detection=False)
    if not reps:
        return None
    return reps[0]["embedding"]


def check_video_identity(
    frames: Sequence[str | Path],
    identity_ref: str | Path,
    *,
    min_similarity: float = DEFAULT_IDENTITY_SIM_MIN,
    embed_fn: FaceEmbedFn | None = None,
) -> CheckResult:
    """ArcFace cosine similarity of each frame's face to the canonical reference.

    Score = the *worst* (minimum) per-frame similarity. ``available=False`` when no
    face-embedding backend is present (needs_human, never a pass).
    """
    if embed_fn is None:
        if importlib.util.find_spec("deepface") is None:
            return CheckResult(
                name="video_identity",
                available=False,
                reason="face-embedding backend unavailable: deepface not installed",
            )
        embed_fn = _default_face_embed

    try:
        ref_vec = embed_fn(Path(identity_ref))
    except Exception as e:
        return CheckResult(
            name="video_identity", available=False, reason=f"reference face embedding failed: {e}"
        )
    if ref_vec is None:
        return CheckResult(
            name="video_identity", available=False, reason="no face detected in identity reference"
        )

    sims: list[float] = []
    for f in frames:
        try:
            vec = embed_fn(Path(f))
        except Exception:
            continue
        if vec is not None:
            sims.append(_cosine(ref_vec, vec))
    if not sims:
        return CheckResult(
            name="video_identity", available=False, reason="no face detected in any sampled frame"
        )
    worst = min(sims)
    return CheckResult(
        name="video_identity",
        available=True,
        score=round(worst, 4),
        threshold=min_similarity,
        passed=worst >= min_similarity,
        details={
            "worst_frame_sim": round(worst, 4),
            "mean_sim": round(sum(sims) / len(sims), 4),
            "frames_scored": len(sims),
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Aggregate gate (FAIL-CLOSED)
# ─────────────────────────────────────────────────────────────────────────────


def _verdict(checks: dict[str, CheckResult]) -> str:
    """fail > needs_human > pass. Any requested check that couldn't run blocks."""
    if not checks:
        return "needs_human"
    if any(c.available and c.passed is False for c in checks.values()):
        return "fail"
    if any(not c.available for c in checks.values()):
        return "needs_human"
    return "pass"


def run_video_qc_gate(
    video_path: str | Path,
    *,
    expected_text: str | None = None,
    garment_ref: str | Path | None = None,
    identity_ref: str | Path | None = None,
    num_frames: int = DEFAULT_NUM_FRAMES,
    text_ratio_min: float = DEFAULT_TEXT_RATIO_MIN,
    garment_sim_min: float = DEFAULT_GARMENT_SIM_MIN,
    identity_sim_min: float = DEFAULT_IDENTITY_SIM_MIN,
    frames: Sequence[str | Path] | None = None,
    ocr_fn: OcrFn | None = None,
    garment_score_fn: GarmentScoreFn | None = None,
    embed_fn: FaceEmbedFn | None = None,
) -> dict[str, Any]:
    """Run the requested checks over sampled frames and return a fail-closed report.

    Only dimensions whose reference input is provided are requested. Pass ``frames``
    to skip extraction (already-sampled frames); otherwise frames are extracted from
    ``video_path``. Returns::

        {"verdict": "pass"|"fail"|"needs_human", "frames": int,
         "checks": {name: CheckResult.to_dict()}, "reasons": [...]}
    """
    if frames is None:
        sampled = extract_frames(video_path, num_frames=num_frames)
    else:
        sampled = [Path(f) for f in frames]

    checks: dict[str, CheckResult] = {}
    if expected_text is not None:
        checks["video_text"] = check_video_text(
            sampled, expected_text, min_ratio=text_ratio_min, ocr_fn=ocr_fn
        )
    if garment_ref is not None:
        checks["video_garment"] = check_video_garment(
            sampled, garment_ref, min_similarity=garment_sim_min, score_fn=garment_score_fn
        )
    if identity_ref is not None:
        checks["video_identity"] = check_video_identity(
            sampled, identity_ref, min_similarity=identity_sim_min, embed_fn=embed_fn
        )

    verdict = _verdict(checks)
    reasons = [
        f"{c.name}: {c.reason}" for c in checks.values() if (not c.available) or c.passed is False
    ]
    return {
        "verdict": verdict,
        "frames": len(sampled),
        "checks": {k: v.to_dict() for k, v in checks.items()},
        "reasons": reasons,
    }
