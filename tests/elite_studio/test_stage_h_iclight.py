"""Tests for Stage H IC-Light V2 relight (mockup-first Architecture A)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from skyyrose.elite_studio.agents.compositor import stage_h_iclight
from skyyrose.elite_studio.agents.compositor.stage_h_iclight import (
    ICLIGHT_ENDPOINT,
    _resolve_denoise,
    relight_composite,
)


@pytest.fixture
def composite_image(tmp_path: Path) -> Path:
    """64x64 RGB composite stand-in (would be Stage D output)."""
    img = Image.new("RGB", (64, 64), color=(80, 60, 40))
    p = tmp_path / "br-001-rasterize.png"
    img.save(p)
    return p


# ----- _resolve_denoise tests ---------------------------------------------


def test_resolve_denoise_defaults_to_0_4(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unset env → plan default 0.4 (preserves product pixels)."""
    monkeypatch.delenv("ELITE_STUDIO_ICLIGHT_DENOISE", raising=False)
    assert _resolve_denoise() == pytest.approx(0.4)


def test_resolve_denoise_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELITE_STUDIO_ICLIGHT_DENOISE", "0.25")
    assert _resolve_denoise() == pytest.approx(0.25)


def test_resolve_denoise_clamps_above_1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELITE_STUDIO_ICLIGHT_DENOISE", "1.5")
    assert _resolve_denoise() == pytest.approx(1.0)


def test_resolve_denoise_clamps_below_0(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELITE_STUDIO_ICLIGHT_DENOISE", "-0.1")
    assert _resolve_denoise() == pytest.approx(0.0)


def test_resolve_denoise_falls_back_on_garbage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELITE_STUDIO_ICLIGHT_DENOISE", "not-a-number")
    assert _resolve_denoise() == pytest.approx(0.4)


# ----- relight_composite tests --------------------------------------------


def test_relight_raises_on_missing_input(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="stage-h iclight input missing"):
        relight_composite(
            composite_path=str(tmp_path / "does-not-exist.png"),
            prompt="soft daylight",
            sku="br-001",
            output_dir=str(tmp_path / "out"),
        )


def test_relight_calls_fal_with_correct_endpoint_and_denoise(
    composite_image: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FAL invocation must use fal-ai/iclight-v2 with the env denoise value."""
    captured: dict = {}

    def fake_upload(p):
        return f"https://fake-fal-cdn/{Path(p).name}"

    def fake_invoke(*, image_url, prompt, highres_denoise):
        captured["image_url"] = image_url
        captured["prompt"] = prompt
        captured["highres_denoise"] = highres_denoise
        # Return synthesized result bytes
        out = Image.new("RGB", (64, 64), color=(120, 100, 80))
        import io

        buf = io.BytesIO()
        out.save(buf, format="PNG")
        return buf.getvalue()

    monkeypatch.setenv("ELITE_STUDIO_ICLIGHT_DENOISE", "0.35")
    monkeypatch.setattr(stage_h_iclight, "upload_to_fal", fake_upload)
    monkeypatch.setattr(stage_h_iclight, "_invoke_iclight_v2", fake_invoke)

    out_path = relight_composite(
        composite_path=str(composite_image),
        prompt="soft volumetric daylight, oakland bay bridge backdrop",
        sku="br-001",
        output_dir=str(tmp_path / "out"),
    )

    assert Path(out_path).exists()
    assert Path(out_path).name == "br-001-relit.png"
    assert captured["prompt"] == "soft volumetric daylight, oakland bay bridge backdrop"
    assert captured["highres_denoise"] == pytest.approx(0.35)
    assert captured["image_url"].endswith("br-001-rasterize.png")


def test_relight_explicit_denoise_overrides_env(
    composite_image: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Caller-passed highres_denoise wins over env."""
    captured: dict = {}

    def fake_invoke(*, image_url, prompt, highres_denoise):
        captured["highres_denoise"] = highres_denoise
        out = Image.new("RGB", (64, 64))
        import io

        buf = io.BytesIO()
        out.save(buf, format="PNG")
        return buf.getvalue()

    monkeypatch.setenv("ELITE_STUDIO_ICLIGHT_DENOISE", "0.9")
    monkeypatch.setattr(stage_h_iclight, "upload_to_fal", lambda p: "https://fake/u.png")
    monkeypatch.setattr(stage_h_iclight, "_invoke_iclight_v2", fake_invoke)

    relight_composite(
        composite_path=str(composite_image),
        prompt="p",
        sku="br-001",
        output_dir=str(tmp_path / "out"),
        highres_denoise=0.2,
    )
    assert captured["highres_denoise"] == pytest.approx(0.2)


def test_relight_falls_back_to_input_on_fal_error(
    composite_image: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FAL failure must not block pipeline — pass-through, logged, QA-gated."""

    def boom(p):
        raise RuntimeError("FAL is down")

    monkeypatch.setattr(stage_h_iclight, "upload_to_fal", boom)

    out_path = relight_composite(
        composite_path=str(composite_image),
        prompt="p",
        sku="br-001",
        output_dir=str(tmp_path / "out"),
    )

    # Output exists and equals input bytes (pass-through)
    assert Path(out_path).exists()
    assert Path(out_path).read_bytes() == composite_image.read_bytes()


def test_relight_falls_back_on_empty_result(
    composite_image: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If FAL returns no images, pass-through with warning."""
    monkeypatch.setattr(stage_h_iclight, "upload_to_fal", lambda p: "https://fake/u.png")
    monkeypatch.setattr(stage_h_iclight, "_invoke_iclight_v2", lambda **kw: None)

    out_path = relight_composite(
        composite_path=str(composite_image),
        prompt="p",
        sku="br-001",
        output_dir=str(tmp_path / "out"),
    )
    assert Path(out_path).read_bytes() == composite_image.read_bytes()


def test_relight_raises_when_fal_client_missing(
    composite_image: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hard error when fal_client not installed — pipeline must surface this."""
    monkeypatch.setattr(stage_h_iclight, "fal_client", None)
    with pytest.raises(RuntimeError, match="fal_client not installed"):
        relight_composite(
            composite_path=str(composite_image),
            prompt="p",
            sku="br-001",
            output_dir=str(tmp_path / "out"),
        )


def test_iclight_endpoint_constant() -> None:
    """Endpoint identifier is the verified fal-ai/iclight-v2 string."""
    assert ICLIGHT_ENDPOINT == "fal-ai/iclight-v2"
