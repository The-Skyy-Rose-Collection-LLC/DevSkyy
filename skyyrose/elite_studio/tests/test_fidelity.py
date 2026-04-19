"""Tests for skyyrose.elite_studio.fidelity (Wave 1 fidelity gate)."""

from __future__ import annotations

from pathlib import Path

import pytest

from skyyrose.elite_studio import fidelity

PIL = pytest.importorskip("PIL.Image")


def _solid_image(path: Path, rgb: tuple[int, int, int], size: int = 64) -> Path:
    from PIL import Image

    Image.new("RGB", (size, size), rgb).save(path, "PNG")
    return path


def _striped_image(
    path: Path, rgb_a: tuple[int, int, int], rgb_b: tuple[int, int, int], size: int = 64
) -> Path:
    from PIL import Image

    img = Image.new("RGB", (size, size), rgb_a)
    for y in range(size // 2, size):
        for x in range(size):
            img.putpixel((x, y), rgb_b)
    img.save(path, "PNG")
    return path


# ─── Color fidelity ───────────────────────────────────────────────────────────


def test_check_color_empty_spec_passes(tmp_path: Path) -> None:
    img = _solid_image(tmp_path / "x.png", (10, 10, 10))
    r = fidelity.check_color(img, {})
    assert r.available is True
    assert r.passed is True


def test_check_color_exact_primary_passes(tmp_path: Path) -> None:
    # #0A0A0A = (10, 10, 10)
    img = _solid_image(tmp_path / "dark.png", (10, 10, 10))
    r = fidelity.check_color(img, {"primary": "#0A0A0A"})
    assert r.available is True
    assert r.passed is True
    assert r.score is not None
    assert r.score < 5.0
    assert r.details["per_color"][0]["role"] == "primary"
    assert r.details["per_color"][0]["pass"] is True


def test_check_color_far_off_primary_fails(tmp_path: Path) -> None:
    # White image, expecting black primary — large delta-E.
    img = _solid_image(tmp_path / "white.png", (255, 255, 255))
    r = fidelity.check_color(img, {"primary": "#0A0A0A"})
    assert r.available is True
    assert r.passed is False
    assert r.score is not None
    assert r.score > 10.0


def test_check_color_accents_checked(tmp_path: Path) -> None:
    # Image with dark primary + rose-gold accent.
    img = _striped_image(tmp_path / "striped.png", (10, 10, 10), (0xB7, 0x6E, 0x79))
    r = fidelity.check_color(img, {"primary": "#0A0A0A", "accents": ["#B76E79"]})
    assert r.available is True
    roles = {c["role"] for c in r.details["per_color"]}
    assert roles == {"primary", "accent_0"}
    assert r.passed is True


def test_check_color_missing_accent_fails(tmp_path: Path) -> None:
    img = _solid_image(tmp_path / "dark.png", (10, 10, 10))
    r = fidelity.check_color(
        img, {"primary": "#0A0A0A", "accents": ["#D4AF37"]}
    )  # gold not present
    assert r.available is True
    assert r.passed is False


def test_check_color_uses_custom_threshold(tmp_path: Path) -> None:
    img = _solid_image(tmp_path / "near.png", (20, 20, 20))
    tight = fidelity.check_color(img, {"primary": "#0A0A0A"}, delta_e_max=2.0)
    assert tight.passed is False
    loose = fidelity.check_color(img, {"primary": "#0A0A0A"}, delta_e_max=20.0)
    assert loose.passed is True


# ─── Text fidelity ────────────────────────────────────────────────────────────


def test_check_text_empty_spec_passes(tmp_path: Path) -> None:
    img = _solid_image(tmp_path / "x.png", (0, 0, 0))
    r = fidelity.check_text(img, [])
    assert r.available is True
    assert r.passed is True
    assert r.score == 1.0


def test_check_text_without_pytesseract_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    img = _solid_image(tmp_path / "x.png", (0, 0, 0))
    # Force the import to fail.
    import builtins

    original_import = builtins.__import__

    def fake_import(name: str, *args, **kwargs):
        if name == "pytesseract":
            raise ImportError("forced absent")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    r = fidelity.check_text(img, ["SKYY ROSE"])
    assert r.available is False
    assert "pytesseract" in r.reason


# ─── CLIP fidelity ────────────────────────────────────────────────────────────


def test_check_clip_unavailable_without_dependency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    a = _solid_image(tmp_path / "a.png", (10, 10, 10))
    b = _solid_image(tmp_path / "b.png", (20, 20, 20))
    # Force the loader to treat clip as unavailable even if installed.
    monkeypatch.setattr(
        fidelity,
        "_CLIP_STATE",
        {"loaded": True, "model": None, "preprocess": None, "error": "forced"},
    )
    r = fidelity.check_clip_similarity(a, b)
    assert r.available is False
    assert "forced" in r.reason


# ─── Aggregate gate ───────────────────────────────────────────────────────────


def test_run_fidelity_gate_only_color_when_no_reference(tmp_path: Path) -> None:
    img = _solid_image(tmp_path / "dark.png", (10, 10, 10))
    result = fidelity.run_fidelity_gate(img, color_spec={"primary": "#0A0A0A"})
    assert "color" in result["checks"]
    assert "clip" not in result["checks"]
    assert result["checks_run"] == 1
    assert result["passed_all_available"] is True


def test_run_fidelity_gate_unavailable_checks_dont_fail_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    img = _solid_image(tmp_path / "dark.png", (10, 10, 10))
    ref = _solid_image(tmp_path / "ref.png", (10, 10, 10))
    monkeypatch.setattr(
        fidelity,
        "_CLIP_STATE",
        {"loaded": True, "model": None, "preprocess": None, "error": "no clip"},
    )
    result = fidelity.run_fidelity_gate(
        img,
        color_spec={"primary": "#0A0A0A"},
        text_spec=[],  # empty spec → passes available
        reference_image_path=ref,
    )
    # Color passes, text passes, clip unavailable.
    assert result["checks"]["color"]["passed"] is True
    assert result["checks"]["clip"]["available"] is False
    assert result["passed_all_available"] is True
    assert result["checks_run"] == 2  # clip not counted


def test_run_fidelity_gate_any_failure_blocks_pass(tmp_path: Path) -> None:
    img = _solid_image(tmp_path / "white.png", (255, 255, 255))
    result = fidelity.run_fidelity_gate(img, color_spec={"primary": "#0A0A0A"})
    assert result["passed_all_available"] is False


def test_run_fidelity_gate_returns_serializable_dict(tmp_path: Path) -> None:
    import json

    img = _solid_image(tmp_path / "dark.png", (10, 10, 10))
    result = fidelity.run_fidelity_gate(img, color_spec={"primary": "#0A0A0A"})
    # Must be JSON-serializable to land in telemetry.
    serialized = json.dumps(result)
    assert "color" in serialized
