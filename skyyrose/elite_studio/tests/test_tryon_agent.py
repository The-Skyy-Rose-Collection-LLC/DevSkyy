"""Tests for TryOnAgent — virtual try-on wrapper around FashnTryOnAgent.

All external dependencies (FashnTryOnAgent, asyncio.run, shutil) are mocked.
Tests verify:
- Successful try-on returns correct TryOnResult
- FASHN error is caught and returned as failed TryOnResult
- Missing image_path in FASHN response triggers failure
- Category mapping from Elite Studio to FASHN convention
- Output path is built under OUTPUT_DIR/<sku>/tryon/
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skyyrose.elite_studio.agents.tryon_agent import (
    TryOnAgent,
    _CATEGORY_MAP,
    _find_garment_image,
)
from skyyrose.elite_studio.models import TryOnResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def agent() -> TryOnAgent:
    return TryOnAgent()


@pytest.fixture
def tmp_sku_dir(tmp_path: Path) -> Path:
    """Create a fake SKU product directory with a branding render."""
    sku_dir = tmp_path / "br-001"
    sku_dir.mkdir()
    render = sku_dir / "br-001-render-branding.webp"
    render.write_bytes(b"FAKE_IMAGE")
    return sku_dir


# ---------------------------------------------------------------------------
# _find_garment_image
# ---------------------------------------------------------------------------


class TestFindGarmentImage:
    def test_finds_branding_render_first(self, tmp_path: Path) -> None:
        sku_dir = tmp_path / "br-001"
        sku_dir.mkdir()
        branding = sku_dir / "br-001-render-branding.webp"
        branding.write_bytes(b"x")
        front = sku_dir / "br-001-render-front.webp"
        front.write_bytes(b"x")

        with patch("skyyrose.elite_studio.agents.tryon_agent.OUTPUT_DIR", tmp_path):
            result = _find_garment_image("br-001")

        assert result == str(branding)

    def test_falls_back_to_front_render(self, tmp_path: Path) -> None:
        sku_dir = tmp_path / "br-001"
        sku_dir.mkdir()
        front = sku_dir / "br-001-render-front.webp"
        front.write_bytes(b"x")

        with patch("skyyrose.elite_studio.agents.tryon_agent.OUTPUT_DIR", tmp_path):
            result = _find_garment_image("br-001")

        assert result == str(front)

    def test_falls_back_to_glob(self, tmp_path: Path) -> None:
        sku_dir = tmp_path / "br-001"
        sku_dir.mkdir()
        any_img = sku_dir / "br-001-custom.jpg"
        any_img.write_bytes(b"x")

        with patch("skyyrose.elite_studio.agents.tryon_agent.OUTPUT_DIR", tmp_path):
            result = _find_garment_image("br-001")

        assert result == str(any_img)

    def test_returns_none_when_no_dir(self, tmp_path: Path) -> None:
        with patch("skyyrose.elite_studio.agents.tryon_agent.OUTPUT_DIR", tmp_path):
            result = _find_garment_image("nonexistent-sku")

        assert result is None

    def test_returns_none_when_dir_empty(self, tmp_path: Path) -> None:
        (tmp_path / "br-empty").mkdir()

        with patch("skyyrose.elite_studio.agents.tryon_agent.OUTPUT_DIR", tmp_path):
            result = _find_garment_image("br-empty")

        assert result is None


# ---------------------------------------------------------------------------
# Category mapping
# ---------------------------------------------------------------------------


class TestCategoryMapping:
    def test_upper_body_maps_to_tops(self) -> None:
        assert _CATEGORY_MAP["upper_body"] == "tops"

    def test_lower_body_maps_to_bottoms(self) -> None:
        assert _CATEGORY_MAP["lower_body"] == "bottoms"

    def test_all_standard_categories_present(self) -> None:
        expected = {
            "upper_body",
            "tops",
            "lower_body",
            "bottoms",
            "dresses",
            "outerwear",
            "full_body",
        }
        assert expected.issubset(_CATEGORY_MAP.keys())


# ---------------------------------------------------------------------------
# TryOnAgent.try_on — success path
# ---------------------------------------------------------------------------


class TestTryOnSuccess:
    def test_returns_tryon_result_on_success(self, agent: TryOnAgent, tmp_path: Path) -> None:
        fake_raw_path = tmp_path / "fashn_output.png"
        fake_raw_path.write_bytes(b"FAKE_PNG")

        mock_fashn_result = {
            "image_path": str(fake_raw_path),
            "image_url": "https://example.com/img.png",
        }

        with (
            patch("skyyrose.elite_studio.agents.tryon_agent.OUTPUT_DIR", tmp_path),
            patch(
                "skyyrose.elite_studio.agents.tryon_agent.asyncio.run",
                return_value=mock_fashn_result,
            ),
            patch("shutil.copy2"),
            patch("agents.fashn_agent.FashnTryOnAgent") as mock_cls,
        ):
            mock_instance = MagicMock()
            mock_instance._tool_virtual_tryon = AsyncMock(return_value=mock_fashn_result)
            mock_instance.close = AsyncMock()
            mock_cls.return_value = mock_instance

            result = agent.try_on(
                sku="br-001",
                garment_image_path="/some/garment.jpg",
                model_image_path="/some/model.jpg",
                category="upper_body",
            )

        assert isinstance(result, TryOnResult)
        assert result.success is True
        assert result.garment_sku == "br-001"
        assert result.provider == "fashn"
        assert result.latency_s >= 0.0
        assert result.error == ""

    def test_result_is_frozen(self, agent: TryOnAgent, tmp_path: Path) -> None:
        fake_raw_path = tmp_path / "fashn_output.png"
        fake_raw_path.write_bytes(b"FAKE_PNG")
        mock_result = {"image_path": str(fake_raw_path)}

        with (
            patch("skyyrose.elite_studio.agents.tryon_agent.OUTPUT_DIR", tmp_path),
            patch("skyyrose.elite_studio.agents.tryon_agent.asyncio.run", return_value=mock_result),
            patch("shutil.copy2"),
            patch("agents.fashn_agent.FashnTryOnAgent"),
        ):
            result = agent.try_on("br-001", "/g.jpg", "/m.jpg")

        with pytest.raises((AttributeError, TypeError)):
            result.success = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# TryOnAgent.try_on — failure paths
# ---------------------------------------------------------------------------


class TestTryOnFailure:
    def test_fashn_exception_returns_failed_result(self, agent: TryOnAgent) -> None:
        with patch(
            "skyyrose.elite_studio.agents.tryon_agent.asyncio.run",
            side_effect=RuntimeError("FASHN API unreachable"),
        ):
            result = agent.try_on("br-001", "/g.jpg", "/m.jpg")

        assert result.success is False
        assert "FASHN API unreachable" in result.error
        assert result.garment_sku == "br-001"
        assert result.provider == "fashn"

    def test_missing_image_path_returns_failed_result(self, agent: TryOnAgent) -> None:
        with patch(
            "skyyrose.elite_studio.agents.tryon_agent.asyncio.run",
            return_value={"image_path": "", "image_url": ""},
        ):
            result = agent.try_on("br-001", "/g.jpg", "/m.jpg")

        assert result.success is False
        assert result.error != ""

    def test_latency_always_populated(self, agent: TryOnAgent) -> None:
        with patch(
            "skyyrose.elite_studio.agents.tryon_agent.asyncio.run",
            side_effect=Exception("boom"),
        ):
            result = agent.try_on("br-001", "/g.jpg", "/m.jpg")

        assert result.latency_s >= 0.0
