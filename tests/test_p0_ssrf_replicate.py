"""P0 SSRF regression tests — replicate_provider._download_model URL validation.

Covers Finding #4 from the Wave 2 cleanup audit:
  services/three_d/replicate_provider.py _download_model() fetched
  provider-supplied URLs without SSRF validation.

Tests verify that:
1. The services-layer _services_ssrf instance blocks private IPs and metadata
   services (169.254.169.254, 10.x.x.x, localhost, etc.) regardless of domain.
2. Legitimate Replicate CDN URLs pass validation.
3. ThreeDProviderError is raised (not raw ValueError) when _download_model
   receives a blocked URL.
4. The global ssrf_protection singleton correctly blocks the same addresses,
   as a baseline sanity check.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# _services_ssrf instance — direct unit tests
# ---------------------------------------------------------------------------


class TestServicesSSRFInstance:
    """The module-level _services_ssrf in replicate_provider blocks private addresses."""

    @pytest.fixture
    def ssrf(self):
        from services.three_d.replicate_provider import _services_ssrf

        return _services_ssrf

    # --- Addresses that MUST be blocked ---

    def test_blocks_aws_metadata_service(self, ssrf):
        with pytest.raises(ValueError, match="169.254"):
            ssrf.validate_url("http://169.254.169.254/latest/meta-data/")

    def test_blocks_aws_metadata_service_iam(self, ssrf):
        with pytest.raises(ValueError):
            ssrf.validate_url("http://169.254.169.254/latest/meta-data/iam/security-credentials/")

    def test_blocks_localhost_http(self, ssrf):
        with pytest.raises(ValueError):
            ssrf.validate_url("http://localhost/internal")

    def test_blocks_localhost_127(self, ssrf):
        with pytest.raises(ValueError):
            ssrf.validate_url("http://127.0.0.1:8080/admin")

    def test_blocks_private_10_range(self, ssrf):
        with pytest.raises(ValueError):
            ssrf.validate_url("http://10.0.0.1/internal-api")

    def test_blocks_private_192_168(self, ssrf):
        with pytest.raises(ValueError):
            ssrf.validate_url("http://192.168.1.100/api")

    def test_blocks_private_172_16(self, ssrf):
        with pytest.raises(ValueError):
            ssrf.validate_url("http://172.16.0.1/data")

    def test_blocks_file_protocol(self, ssrf):
        with pytest.raises(ValueError):
            ssrf.validate_url("file:///etc/passwd")

    def test_blocks_gopher_protocol(self, ssrf):
        with pytest.raises(ValueError):
            ssrf.validate_url("gopher://127.0.0.1:25/smtp")

    # --- Addresses that MUST be allowed (no domain allowlist) ---

    def test_allows_replicate_cdn(self, ssrf):
        """Standard Replicate CDN URLs must pass."""
        # Should not raise — if it does, the test fails
        ssrf.validate_url("https://replicate.delivery/pbxt/abc123/output.glb")

    def test_allows_public_https(self, ssrf):
        ssrf.validate_url("https://example.com/model.glb")

    def test_allows_huggingface(self, ssrf):
        ssrf.validate_url("https://huggingface.co/spaces/output/mesh.glb")


# ---------------------------------------------------------------------------
# _download_model — integration test with mocked HTTP
# ---------------------------------------------------------------------------


class TestDownloadModelSSRFGuard:
    """_download_model must raise ThreeDProviderError on blocked URLs."""

    @pytest.fixture
    def provider(self):
        from services.three_d.replicate_provider import ReplicateProvider

        p = ReplicateProvider.__new__(ReplicateProvider)
        p.config = MagicMock()
        p.config.output_dir = "/tmp/replicate_test"
        p._http_client = None
        p._client = None
        return p

    @pytest.mark.asyncio
    async def test_download_metadata_url_raises_provider_error(self, provider):
        """Metadata service URL must raise ThreeDProviderError, not raw ValueError."""
        from services.three_d.provider_interface import (
            OutputFormat,
            ThreeDProviderError,
        )

        with pytest.raises(ThreeDProviderError, match="SSRF"):
            await provider._download_model(
                url="http://169.254.169.254/latest/meta-data/",
                output_format=OutputFormat.GLB,
                correlation_id="test-corr-001",
            )

    @pytest.mark.asyncio
    async def test_download_localhost_url_raises_provider_error(self, provider):
        from services.three_d.provider_interface import (
            OutputFormat,
            ThreeDProviderError,
        )

        with pytest.raises(ThreeDProviderError, match="SSRF"):
            await provider._download_model(
                url="http://127.0.0.1:6379/",
                output_format=OutputFormat.GLB,
                correlation_id="test-corr-002",
            )

    @pytest.mark.asyncio
    async def test_download_private_ip_raises_provider_error(self, provider):
        from services.three_d.provider_interface import (
            OutputFormat,
            ThreeDProviderError,
        )

        with pytest.raises(ThreeDProviderError, match="SSRF"):
            await provider._download_model(
                url="http://10.0.0.1/internal",
                output_format=OutputFormat.GLB,
                correlation_id="test-corr-003",
            )

    @pytest.mark.asyncio
    async def test_download_valid_url_proceeds_to_http(self, provider):
        """A valid CDN URL must reach the HTTP client (not be blocked by SSRF)."""
        from services.three_d.provider_interface import OutputFormat

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b"GLB_BINARY_DATA"

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http.is_closed = False

        provider._http_client = mock_http

        import os

        os.makedirs("/tmp/replicate_test", exist_ok=True)

        result = await provider._download_model(
            url="https://replicate.delivery/pbxt/abc123/model.glb",
            output_format=OutputFormat.GLB,
            correlation_id="test-corr-valid",
        )

        mock_http.get.assert_awaited_once_with("https://replicate.delivery/pbxt/abc123/model.glb")
        assert result.endswith(".glb")

    @pytest.mark.asyncio
    async def test_ssrf_error_is_not_retryable(self, provider):
        """SSRF-blocked URLs should not be retried (retryable=False)."""
        from services.three_d.provider_interface import (
            OutputFormat,
            ThreeDProviderError,
        )

        with pytest.raises(ThreeDProviderError) as exc_info:
            await provider._download_model(
                url="http://169.254.169.254/",
                output_format=OutputFormat.GLB,
                correlation_id="test-corr-004",
            )

        assert exc_info.value.retryable is False


# ---------------------------------------------------------------------------
# Global ssrf_protection singleton — baseline sanity check
# ---------------------------------------------------------------------------


class TestGlobalSSRFSingleton:
    """The global ssrf_protection singleton also blocks these addresses."""

    @pytest.fixture
    def global_ssrf(self):
        from security.ssrf_protection import ssrf_protection

        return ssrf_protection

    def test_global_blocks_metadata_service(self, global_ssrf):
        with pytest.raises(ValueError):
            global_ssrf.validate_url("http://169.254.169.254/latest/meta-data/")

    def test_global_blocks_localhost(self, global_ssrf):
        with pytest.raises(ValueError):
            global_ssrf.validate_url("http://localhost/")

    def test_global_blocks_private_10(self, global_ssrf):
        with pytest.raises(ValueError):
            global_ssrf.validate_url("http://10.0.0.1/")
