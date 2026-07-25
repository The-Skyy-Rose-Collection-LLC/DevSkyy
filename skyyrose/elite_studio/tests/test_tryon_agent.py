"""Tests for TryOnResult model and tryon_agent helper functions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from skyyrose.elite_studio.agents import tryon_agent
from skyyrose.elite_studio.models import TryOnResult
from skyyrose.integrations.fashn_client import FashnError


class TestTryOnResultModel:
    def test_frozen(self):
        r = TryOnResult(success=True)
        with pytest.raises((AttributeError, TypeError)):
            r.success = False  # type: ignore[misc]

    def test_defaults(self):
        r = TryOnResult(success=False)
        assert r.output_path == ""
        assert r.garment_sku == ""
        assert r.provider == "fashn"
        assert r.latency_s == 0.0
        assert r.error == ""

    def test_fields_stored(self):
        r = TryOnResult(
            success=True,
            garment_sku="br-001",
            provider="fashn",
            latency_s=1.2,
        )
        assert r.garment_sku == "br-001"
        assert r.latency_s == 1.2


class TestFindGarmentImage:
    def test_resolves_through_sot(self, tmp_path):
        candidate = tmp_path / "br-001-front.webp"
        candidate.write_bytes(b"fake")

        with (
            patch.object(tryon_agent, "resolve_image", return_value="br-001-front.webp"),
            patch.object(tryon_agent, "THEME_ROOT", tmp_path),
        ):
            assert tryon_agent._find_garment_image("br-001") == str(candidate)

    def test_returns_empty_string_when_sot_has_no_image(self):
        with patch.object(tryon_agent, "resolve_image", return_value=None):
            assert tryon_agent._find_garment_image("unknown-sku") == ""

    def test_returns_empty_string_when_resolved_file_missing(self, tmp_path):
        with (
            patch.object(tryon_agent, "resolve_image", return_value="ghost.webp"),
            patch.object(tryon_agent, "THEME_ROOT", tmp_path),
        ):
            assert tryon_agent._find_garment_image("br-999") == ""

    def test_rejects_path_escaping_theme_root(self, tmp_path):
        # resolve_image() itself validates theme-relative paths, but this result
        # feeds a public R2 upload — the consumer-side containment check must
        # hold even if the resolver's guarantee ever changes (mocked here).
        theme = tmp_path / "theme"
        theme.mkdir()
        outside = tmp_path / "outside.webp"
        outside.write_bytes(b"fake")

        with (
            patch.object(tryon_agent, "resolve_image", return_value="../outside.webp"),
            patch.object(tryon_agent, "THEME_ROOT", theme),
        ):
            assert tryon_agent._find_garment_image("br-001") == ""


class TestEnsurePublicUrl:
    def setup_method(self) -> None:
        # _r2_client/_r2_unavailable are lazily-populated module globals — reset
        # between tests so one test's mock client / memoized failure doesn't
        # leak into the next.
        tryon_agent._r2_client = None
        tryon_agent._r2_unavailable = False

    def test_passes_through_existing_public_url(self):
        url = "https://cdn.skyyrose.co/br-001-front.jpg"
        assert tryon_agent.ensure_public_url(url, sku="br-001") == url

    def test_raises_when_local_file_missing(self):
        with pytest.raises(FashnError, match="not found"):
            tryon_agent.ensure_public_url("/no/such/file.jpg", sku="br-001")

    def test_raises_when_r2_not_configured(self, tmp_path):
        local = tmp_path / "garment.jpg"
        local.write_bytes(b"fake")

        with patch.object(tryon_agent, "_get_r2_client", return_value=None):
            with pytest.raises(FashnError, match="R2 storage is not configured"):
                tryon_agent.ensure_public_url(str(local), sku="br-001")

    def test_uploads_local_file_and_returns_cdn_url(self, tmp_path):
        local = tmp_path / "garment.jpg"
        local.write_bytes(b"fake")

        mock_client = MagicMock()
        mock_client.upload_file.return_value = MagicMock(
            cdn_url="https://cdn.example.com/temp/br-001/garment.jpg",
            url="https://r2.example.com/temp/br-001/garment.jpg",
        )

        with patch.object(tryon_agent, "_get_r2_client", return_value=mock_client):
            result = tryon_agent.ensure_public_url(str(local), sku="br-001")

        assert result == "https://cdn.example.com/temp/br-001/garment.jpg"
        mock_client.upload_file.assert_called_once_with(
            local, tryon_agent.AssetCategory.TEMP, product_id="br-001"
        )

    def test_uploads_falls_back_to_url_when_no_cdn_url(self, tmp_path):
        local = tmp_path / "garment.jpg"
        local.write_bytes(b"fake")

        mock_client = MagicMock()
        mock_client.upload_file.return_value = MagicMock(
            cdn_url=None,
            url="https://r2.example.com/temp/br-001/garment.jpg",
        )

        with patch.object(tryon_agent, "_get_r2_client", return_value=mock_client):
            result = tryon_agent.ensure_public_url(str(local), sku="br-001")

        assert result == "https://r2.example.com/temp/br-001/garment.jpg"

    def test_wraps_r2_upload_error_in_fashn_error(self, tmp_path):
        # Docstring contract: callers only ever handle FashnError — an R2Error
        # from the upload itself must not propagate unwrapped.
        local = tmp_path / "garment.jpg"
        local.write_bytes(b"fake")

        mock_client = MagicMock()
        mock_client.upload_file.side_effect = tryon_agent.R2Error("upload exploded")

        with patch.object(tryon_agent, "_get_r2_client", return_value=mock_client):
            with pytest.raises(FashnError, match="failed to upload tryon image"):
                tryon_agent.ensure_public_url(str(local), sku="br-001")


class TestGetR2ClientMemoization:
    def setup_method(self) -> None:
        tryon_agent._r2_client = None
        tryon_agent._r2_unavailable = False

    def teardown_method(self) -> None:
        # Never leak the memoized-failure state into other test modules.
        tryon_agent._r2_client = None
        tryon_agent._r2_unavailable = False

    def test_not_configured_state_is_memoized(self):
        with patch.object(tryon_agent, "R2Config") as mock_config:
            mock_config.from_env.side_effect = tryon_agent.R2Error("no creds")
            assert tryon_agent._get_r2_client() is None
            assert tryon_agent._get_r2_client() is None
        # Second call short-circuits on the memoized failure — env parsed once.
        mock_config.from_env.assert_called_once()
