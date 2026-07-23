"""Tests for the fail-closed video QC gate (skyyrose.elite_studio.video_qc).

Detector backends (OCR / CLIP / ArcFace) are injected as fakes so aggregation and
the fail-closed verdict logic are exercised without loading any ML model. The one
real-IO test (extract_frames) is guarded on ffmpeg being present.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

from skyyrose.elite_studio import video_qc as vq

_HAS_OCR = importlib.util.find_spec("pytesseract") is not None
_HAS_DEEPFACE = importlib.util.find_spec("deepface") is not None
_HAS_INSIGHTFACE = importlib.util.find_spec("insightface") is not None
_HAS_FACE_BACKEND = _HAS_DEEPFACE or _HAS_INSIGHTFACE
_HAS_FFMPEG = shutil.which("ffmpeg") is not None


# ── helpers ──────────────────────────────────────────────────────────────────


def _fake_frames(n: int) -> list[Path]:
    return [Path(f"frame-{i:03d}.png") for i in range(n)]


# ── _text_ratio ──────────────────────────────────────────────────────────────


def test_text_ratio_exact_match_is_one():
    assert vq._text_ratio("BLACK IS BEAUTIFUL", "black is beautiful") == 1.0


def test_text_ratio_mangled_is_below_threshold():
    # The canonical failure: "BLACK IS BEAUTIFUL" -> "BLACKY"
    assert vq._text_ratio("BLACKY", "BLACK IS BEAUTIFUL") < vq.DEFAULT_TEXT_RATIO_MIN


def test_text_ratio_empty_both_is_one():
    assert vq._text_ratio("", "") == 1.0
    assert vq._text_ratio("x", "") == 0.0


# ── _cosine ──────────────────────────────────────────────────────────────────


def test_cosine_identical_is_one():
    assert vq._cosine([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_cosine_orthogonal_is_zero():
    assert vq._cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_zero_vector_is_zero():
    assert vq._cosine([0.0, 0.0], [1.0, 1.0]) == 0.0


# ── check_video_text ─────────────────────────────────────────────────────────


def test_video_text_best_frame_passes_when_one_frame_reads_clean():
    frames = _fake_frames(4)
    # Only the last frame reads the text correctly; the rest are garbled.
    readings = {
        frames[0]: "BLKY",
        frames[1]: "BC",
        frames[2]: "BLK",
        frames[3]: "BLACK IS BEAUTIFUL",
    }
    res = vq.check_video_text(frames, "BLACK IS BEAUTIFUL", ocr_fn=lambda p: readings[p])
    assert res.available is True
    assert res.passed is True
    assert res.score == 1.0
    assert res.details["frames_read"] == 4


def test_video_text_all_mangled_fails():
    frames = _fake_frames(3)
    res = vq.check_video_text(frames, "BLACK IS BEAUTIFUL", ocr_fn=lambda p: "BLACKY")
    assert res.available is True
    assert res.passed is False


def test_video_text_no_expected_text_passes():
    res = vq.check_video_text(_fake_frames(2), "", ocr_fn=lambda p: "anything")
    assert res.available is True and res.passed is True


@pytest.mark.skipif(_HAS_OCR, reason="OCR backend installed — fail-closed path not exercised")
def test_video_text_fail_closed_when_no_ocr_backend():
    res = vq.check_video_text(_fake_frames(2), "TEXT")
    assert res.available is False
    assert res.passed is None


# ── check_video_garment ──────────────────────────────────────────────────────


def test_video_garment_uses_worst_frame():
    frames = _fake_frames(3)
    scores = {frames[0]: 0.97, frames[1]: 0.55, frames[2]: 0.96}
    res = vq.check_video_garment(frames, Path("ref.png"), score_fn=lambda f, r: scores[f])
    assert res.available is True
    assert res.passed is False  # worst (0.55) < 0.85
    assert res.details["worst_frame_sim"] == pytest.approx(0.55)


def test_video_garment_all_high_passes():
    frames = _fake_frames(3)
    res = vq.check_video_garment(frames, Path("ref.png"), score_fn=lambda f, r: 0.93)
    assert res.passed is True


def test_video_garment_fail_closed_when_scorer_returns_none():
    res = vq.check_video_garment(_fake_frames(2), Path("ref.png"), score_fn=lambda f, r: None)
    assert res.available is False


# ── check_video_identity ─────────────────────────────────────────────────────


def test_video_identity_pass_when_faces_match():
    frames = _fake_frames(2)
    ref = Path("ref.png")
    embeds = {ref: [1.0, 0.0, 0.0], frames[0]: [0.99, 0.14, 0.0], frames[1]: [1.0, 0.0, 0.0]}
    res = vq.check_video_identity(frames, ref, embed_fn=lambda p: embeds[p])
    assert res.available is True and res.passed is True


def test_video_identity_fail_on_drift():
    frames = _fake_frames(2)
    ref = Path("ref.png")
    # frame1 is a different identity (orthogonal embedding) -> worst frame drops.
    embeds = {ref: [1.0, 0.0, 0.0], frames[0]: [1.0, 0.0, 0.0], frames[1]: [0.0, 1.0, 0.0]}
    res = vq.check_video_identity(frames, ref, embed_fn=lambda p: embeds[p])
    assert res.available is True and res.passed is False


def test_video_identity_fail_closed_when_no_face_in_reference():
    res = vq.check_video_identity(_fake_frames(2), Path("ref.png"), embed_fn=lambda p: None)
    assert res.available is False


@pytest.mark.skipif(
    _HAS_FACE_BACKEND, reason="a face backend is installed — fail-closed path not exercised"
)
def test_video_identity_fail_closed_when_no_backend():
    res = vq.check_video_identity(_fake_frames(2), Path("ref.png"))
    assert res.available is False


# ── _verdict precedence ──────────────────────────────────────────────────────


def _cr(name, available, passed):
    return vq.CheckResult(name=name, available=available, passed=passed)


def test_verdict_empty_is_needs_human():
    assert vq._verdict({}) == "needs_human"


def test_verdict_fail_beats_needs_human():
    checks = {"a": _cr("a", True, False), "b": _cr("b", False, None)}
    assert vq._verdict(checks) == "fail"


def test_verdict_needs_human_beats_pass():
    checks = {"a": _cr("a", True, True), "b": _cr("b", False, None)}
    assert vq._verdict(checks) == "needs_human"


def test_verdict_all_available_and_pass():
    checks = {"a": _cr("a", True, True), "b": _cr("b", True, True)}
    assert vq._verdict(checks) == "pass"


# ── run_video_qc_gate (end-to-end, injected backends, extraction skipped) ─────


def test_run_gate_pass_with_all_backends_injected():
    frames = _fake_frames(3)
    ref = frames[0]  # reuse as a path key for embed lookups
    report = vq.run_video_qc_gate(
        "unused.mp4",
        frames=frames,
        expected_text="LOVE HURTS",
        garment_ref=Path("g.png"),
        identity_ref=ref,
        ocr_fn=lambda p: "LOVE HURTS",
        garment_score_fn=lambda f, r: 0.95,
        embed_fn=lambda p: [1.0, 0.0, 0.0],
    )
    assert report["verdict"] == "pass"
    assert report["frames"] == 3
    assert report["reasons"] == []
    assert set(report["checks"]) == {"video_text", "video_garment", "video_identity"}


def test_run_gate_fail_when_one_dimension_rejects():
    frames = _fake_frames(2)
    report = vq.run_video_qc_gate(
        "unused.mp4",
        frames=frames,
        expected_text="LOVE HURTS",
        garment_ref=Path("g.png"),
        ocr_fn=lambda p: "LOVE HURTS",
        garment_score_fn=lambda f, r: 0.40,  # garment drift
    )
    assert report["verdict"] == "fail"
    assert any("video_garment" in r for r in report["reasons"])


def test_run_gate_needs_human_when_backend_unavailable():
    frames = _fake_frames(2)
    # identity requested but embed_fn returns None for the reference -> unavailable
    report = vq.run_video_qc_gate(
        "unused.mp4",
        frames=frames,
        identity_ref=Path("ref.png"),
        embed_fn=lambda p: None,
    )
    assert report["verdict"] == "needs_human"


# ── extract_frames (real ffmpeg IO) ──────────────────────────────────────────


def test_extract_frames_missing_video_raises(tmp_path):
    with pytest.raises(RuntimeError):
        vq.extract_frames(tmp_path / "nope.mp4", num_frames=3)


def test_extract_frames_rejects_zero_frames(tmp_path):
    with pytest.raises(ValueError):
        vq.extract_frames(tmp_path / "x.mp4", num_frames=0)


@pytest.mark.skipif(not _HAS_FFMPEG, reason="ffmpeg not installed")
def test_extract_frames_real(tmp_path):
    video = tmp_path / "src.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=2:size=128x128:rate=10",
            str(video),
        ],
        capture_output=True,
        check=True,
        timeout=60,
    )
    out = tmp_path / "frames"
    frames = vq.extract_frames(video, num_frames=5, out_dir=out)
    assert len(frames) == 5
    assert all(f.exists() and f.stat().st_size > 0 for f in frames)
