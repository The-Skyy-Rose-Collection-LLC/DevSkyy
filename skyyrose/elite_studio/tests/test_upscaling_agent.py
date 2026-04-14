"""Tests for UpscalingAgent — Real-ESRGAN primary, PIL LANCZOS fallback."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from skyyrose.elite_studio.agents.upscaling_agent import UpscalingAgent
from skyyrose.elite_studio.models import UpscaleResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_test_image(tmp_path: Path, name: str = "test.jpg", size=(256, 256)) -> Path:
    """Create a small JPEG test image."""
    img_path = tmp_path / name
    img = Image.new("RGB", size, color=(180, 110, 121))
    img.save(str(img_path), "JPEG")
    return img_path


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestUpscaleResultModel:
    def test_frozen(self):
        r = UpscaleResult(success=True)
        with pytest.raises((AttributeError, TypeError)):
            r.success = False  # type: ignore[misc]

    def test_defaults(self):
        r = UpscaleResult(success=False)
        assert r.output_path == ""
        assert r.original_resolution == (0, 0)
        assert r.final_resolution == (0, 0)
        assert r.provider == ""
        assert r.error == ""


# ---------------------------------------------------------------------------
# UpscalingAgent — PIL fallback path (no Replicate key)
# ---------------------------------------------------------------------------


class TestUpscalingAgentPilFallback:
    def setup_method(self):
        self.agent = UpscalingAgent()

    def test_pil_upscale_creates_output(self, tmp_path):
        src = make_test_image(tmp_path, size=(128, 128))
        with patch.dict(os.environ, {}, clear=False):
            # Ensure no Replicate key so PIL path is taken
            env = {
                k: v
                for k, v in os.environ.items()
                if k not in ("REPLICATE_API_TOKEN", "REPLICATE_API_KEY")
            }
            with patch.dict(os.environ, env, clear=True):
                result = self.agent.upscale(str(src), target_resolution=(512, 512))

        assert result.success is True
        assert result.provider == "pil_lanczos"
        assert Path(result.output_path).exists()

    def test_pil_upscale_correct_dimensions(self, tmp_path):
        src = make_test_image(tmp_path, size=(100, 100))
        with patch.dict(os.environ, {}, clear=True):
            result = self.agent.upscale(str(src), target_resolution=(400, 400))

        assert result.success is True
        assert result.final_resolution == (400, 400)

    def test_pil_upscale_records_original_resolution(self, tmp_path):
        src = make_test_image(tmp_path, size=(64, 128))
        with patch.dict(os.environ, {}, clear=True):
            result = self.agent.upscale(str(src), target_resolution=(256, 512))

        assert result.original_resolution == (64, 128)

    def test_output_path_contains_upscaled_suffix(self, tmp_path):
        src = make_test_image(tmp_path, "product.jpg", size=(100, 100))
        with patch.dict(os.environ, {}, clear=True):
            result = self.agent.upscale(str(src))

        assert "upscaled" in Path(result.output_path).name

    def test_default_target_resolution(self, tmp_path):
        src = make_test_image(tmp_path, size=(100, 100))
        with patch.dict(os.environ, {}, clear=True):
            result = self.agent.upscale(str(src))

        assert result.success is True
        assert result.final_resolution == (2048, 2048)

    def test_missing_file_returns_failure(self):
        result = self.agent.upscale("/nonexistent/path/image.jpg")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_result_is_frozen(self, tmp_path):
        src = make_test_image(tmp_path)
        with patch.dict(os.environ, {}, clear=True):
            result = self.agent.upscale(str(src))
        with pytest.raises((AttributeError, TypeError)):
            result.success = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# UpscalingAgent — Replicate success path (mocked via _try_replicate)
# ---------------------------------------------------------------------------


class TestUpscalingAgentReplicatePath:
    def setup_method(self):
        self.agent = UpscalingAgent()

    def test_replicate_path_used_when_key_present(self, tmp_path):
        src = make_test_image(tmp_path, size=(256, 256))
        expected_output = str(tmp_path / "test-upscaled.jpg")

        fake_result = UpscaleResult(
            success=True,
            output_path=expected_output,
            original_resolution=(256, 256),
            final_resolution=(1024, 1024),
            provider="replicate",
        )

        with patch.dict(os.environ, {"REPLICATE_API_TOKEN": "fake-token"}):
            with patch.object(self.agent, "_try_replicate", return_value=fake_result):
                result = self.agent.upscale(str(src), target_resolution=(1024, 1024))

        assert result.success is True
        assert result.provider == "replicate"

    def test_replicate_failure_falls_back_to_pil(self, tmp_path):
        src = make_test_image(tmp_path, size=(128, 128))

        failed_result = UpscaleResult(success=False, error="Replicate down")

        with patch.dict(os.environ, {"REPLICATE_API_TOKEN": "fake-token"}):
            with patch.object(self.agent, "_try_replicate", return_value=failed_result):
                result = self.agent.upscale(str(src), target_resolution=(512, 512))

        # Should fall back to PIL
        assert result.success is True
        assert result.provider == "pil_lanczos"


# ---------------------------------------------------------------------------
# Exception handling
# ---------------------------------------------------------------------------


class TestUpscalingAgentErrorHandling:
    def setup_method(self):
        self.agent = UpscalingAgent()

    def test_unexpected_exception_returns_failure(self, monkeypatch):
        def _boom(*args, **kwargs):
            raise RuntimeError("Unexpected crash")

        monkeypatch.setattr(
            "skyyrose.elite_studio.agents.upscaling_agent.UpscalingAgent._upscale",
            _boom,
        )
        result = self.agent.upscale("/any/path.jpg")
        assert result.success is False
        assert "Unexpected crash" in result.error
