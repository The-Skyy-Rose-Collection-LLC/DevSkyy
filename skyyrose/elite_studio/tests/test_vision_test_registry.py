"""Tests for scripts/vision_test_registry.py (Wave 1 registry alignment)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

vt = pytest.importorskip(  # noqa: E402
    "vision_test_registry",
    reason="scripts/vision_test_registry.py not yet merged to main",
)

PIL = pytest.importorskip("PIL.Image")


def _solid(path: Path, rgb: tuple[int, int, int], size: int = 64) -> Path:
    from PIL import Image

    Image.new("RGB", (size, size), rgb).save(path, "PNG")
    return path


# ─── gather_images ─────────────────────────────────────────────────────────


def test_gather_images_skips_references_and_hidden(tmp_path: Path) -> None:
    (tmp_path / "a.png").touch()
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.webp").touch()
    (tmp_path / "_references").mkdir()
    (tmp_path / "_references" / "c.png").touch()
    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "d.png").touch()
    (tmp_path / "ignored.txt").touch()

    names = {p.name for p in vt.gather_images(tmp_path)}
    assert names == {"a.png", "b.webp"}


def test_gather_images_sorted(tmp_path: Path) -> None:
    for n in ("z.png", "a.png", "m.png"):
        (tmp_path / n).touch()
    names = [p.name for p in vt.gather_images(tmp_path)]
    assert names == ["a.png", "m.png", "z.png"]


# ─── combined_score strategies ─────────────────────────────────────────────


def test_combined_score_veto_disqualifies_on_color_fail() -> None:
    color = {"score": 42.0, "passed": False, "available": True}
    text = {"score": 1.0, "passed": True, "available": True}
    assert vt.combined_score(color, text, "veto") == float("inf")


def test_combined_score_veto_disqualifies_on_text_fail_when_available() -> None:
    color = {"score": 3.0, "passed": True, "available": True}
    text = {"score": 0.0, "passed": False, "available": True}
    assert vt.combined_score(color, text, "veto") == float("inf")


def test_combined_score_veto_ignores_text_when_unavailable() -> None:
    color = {"score": 4.5, "passed": True, "available": True}
    text = {"available": False}
    assert vt.combined_score(color, text, "veto") == 4.5


def test_combined_score_weighted_penalises_missing_text() -> None:
    color = {"score": 5.0, "passed": True, "available": True}
    text = {"score": 0.0, "passed": False, "available": True}
    # 5.0 + (1 - 0) * 5 = 10.0
    assert vt.combined_score(color, text, "weighted") == 10.0


def test_combined_score_weighted_rewards_full_text_match() -> None:
    color = {"score": 5.0, "passed": True, "available": True}
    text = {"score": 1.0, "passed": True, "available": True}
    assert vt.combined_score(color, text, "weighted") == 5.0


def test_combined_score_color_only_ignores_text() -> None:
    color = {"score": 7.0, "passed": True, "available": True}
    text = {"score": 0.0, "passed": False, "available": True}
    assert vt.combined_score(color, text, "color-only") == 7.0


def test_combined_score_missing_color_score_is_infinite() -> None:
    color = {"score": None, "available": False}
    text = {"score": 1.0, "passed": True, "available": True}
    assert vt.combined_score(color, text, "veto") == float("inf")


# ─── _match_text ───────────────────────────────────────────────────────────


def test_match_text_reports_found_and_missing() -> None:
    res = vt._match_text("welcome to the skyy rose drop", ["SKYY ROSE", "MISSING"]).to_dict()
    assert res["score"] == 0.5
    assert res["passed"] is False
    assert "SKYY ROSE" in res["details"]["found"]
    assert "MISSING" in res["details"]["missing"]


def test_match_text_all_found_passes() -> None:
    res = vt._match_text("skyy rose collection drop", ["skyy", "rose"]).to_dict()
    assert res["score"] == 1.0
    assert res["passed"] is True


def test_match_text_empty_spec_passes_trivially() -> None:
    res = vt._match_text("anything", []).to_dict()
    assert res["passed"] is True
    assert res["score"] == 1.0


def test_match_text_unavailable_when_ocr_none() -> None:
    res = vt._match_text(None, ["needle"]).to_dict()
    assert res["available"] is False


# ─── end-to-end driver ────────────────────────────────────────────────────


def test_run_vision_test_ranks_matching_image_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest_path = tmp_path / "manifest.json"
    monkeypatch.setenv("SKYYROSE_MASTER_MANIFEST_PATH", str(manifest_path))

    from skyyrose.elite_studio.master_registry import Manifest

    m = Manifest.load()
    m.register_pending(
        sku="test-001",
        collection="black-rose",
        color_spec={"primary": "#0A0A0A", "accents": []},
        text_spec=[],
        notes="test-only",
    )
    m.save()

    img_dir = tmp_path / "images"
    img_dir.mkdir()
    _solid(img_dir / "near-black.png", (10, 10, 10))
    _solid(img_dir / "bright-red.png", (240, 30, 30))

    images = vt.gather_images(img_dir)
    report = vt.run_vision_test(Manifest.load(), images, strategy="veto", top_n=2)

    assert "test-001" in report["skus"]
    candidates = report["skus"]["test-001"]["candidates"]
    assert len(candidates) == 2
    best = candidates[0]
    assert "near-black.png" in best["image"]
    assert best["combined_score"] != "inf"


def test_run_vision_test_skips_locked_and_filters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest_path = tmp_path / "manifest.json"
    monkeypatch.setenv("SKYYROSE_MASTER_MANIFEST_PATH", str(manifest_path))

    from skyyrose.elite_studio.master_registry import Manifest

    m = Manifest.load()
    m.register_pending(
        sku="br-x",
        collection="black-rose",
        color_spec={"primary": "#0A0A0A", "accents": []},
        text_spec=[],
    )
    m.register_pending(
        sku="sg-x",
        collection="signature",
        color_spec={"primary": "#D4AF37", "accents": []},
        text_spec=[],
    )
    m.save()

    img_dir = tmp_path / "images"
    img_dir.mkdir()
    _solid(img_dir / "black.png", (10, 10, 10))

    images = vt.gather_images(img_dir)
    # Collection filter restricts to one SKU
    report = vt.run_vision_test(
        Manifest.load(),
        images,
        strategy="veto",
        top_n=1,
        collection_filter="black-rose",
    )
    assert list(report["skus"].keys()) == ["br-x"]
    assert report["sku_count"] == 1
