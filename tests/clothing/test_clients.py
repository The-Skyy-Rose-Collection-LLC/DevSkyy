"""
Tests for 3D Clothing Asset API Clients

Tests API client functionality with mocked HTTP responses.
Covers Tripo3D, FASHN, and WordPress media clients.

Truth Protocol Rule #8: Test coverage ≥90%
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile

import httpx
import pytest

from agent.modules.clothing.clients.fashn_client import FASHNClient, FASHNError
from agent.modules.clothing.clients.tripo3d_client import Tripo3DClient, Tripo3DError
from agent.modules.clothing.clients.wordpress_media import (
    WordPressMediaClient,
    WordPressError,
)
from agent.modules.clothing.schemas.schemas import Model3DFormat, TryOnModel


class TestTripo3DClient:
    """Tests for Tripo3D API client."""

    @pytest.fixture
    def client(self) -> Tripo3DClient:
        """Create a test client with mock API key."""
        return Tripo3DClient(
            api_key="test-api-key",
            timeout=10.0,
            max_retries=2,
        )

    @pytest.mark.asyncio
    async def test_initialize_success(self, client: Tripo3DClient) -> None:
        """Test successful client initialization."""
        with patch.object(httpx.AsyncClient, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = await client.initialize()

            assert result is True
            assert client._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_without_api_key(self) -> None:
        """Test initialization fails without API key."""
        client = Tripo3DClient(api_key="")

        with pytest.raises(Tripo3DError) as exc_info:
            await client.initialize()

        assert "TRIPO_API_KEY" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_text_to_3d_success(self, client: Tripo3DClient) -> None:
        """Test successful text-to-3D generation."""
        # Mock the HTTP client
        mock_client = AsyncMock()
        client._client = mock_client
        client._initialized = True

        # Mock task creation response
        mock_create_response = MagicMock()
        mock_create_response.status_code = 200
        mock_create_response.json.return_value = {
            "data": {"task_id": "task_123"}
        }

        # Mock status polling response
        mock_status_response = MagicMock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {
            "data": {
                "status": "success",
                "output": {
                    "model": {"url": "https://api.tripo3d.ai/models/123.glb"},
                    "rendered_image": {"url": "https://api.tripo3d.ai/thumb/123.png"},
                },
            }
        }

        mock_client.request.side_effect = [
            mock_create_response,
            mock_status_response,
        ]

        # Mock model download
        with patch.object(client, "_download_model", return_value=Path("/tmp/model.glb")):
            result = await client.text_to_3d(
                prompt="Black hoodie with rose pattern",
                output_format=Model3DFormat.GLB,
                wait_for_completion=True,
            )

        assert result.task_id == "task_123"
        assert result.status == "success"
        assert result.model_format == Model3DFormat.GLB

    @pytest.mark.asyncio
    async def test_text_to_3d_no_wait(self, client: Tripo3DClient) -> None:
        """Test text-to-3D without waiting for completion."""
        mock_client = AsyncMock()
        client._client = mock_client
        client._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"task_id": "task_456"}
        }
        mock_client.request.return_value = mock_response

        result = await client.text_to_3d(
            prompt="Test prompt",
            wait_for_completion=False,
        )

        assert result.task_id == "task_456"
        assert result.status == "queued"

    @pytest.mark.asyncio
    async def test_image_to_3d_with_url(self, client: Tripo3DClient) -> None:
        """Test image-to-3D with URL."""
        mock_client = AsyncMock()
        client._client = mock_client
        client._initialized = True

        mock_create_response = MagicMock()
        mock_create_response.status_code = 200
        mock_create_response.json.return_value = {
            "data": {"task_id": "task_img_123"}
        }

        mock_status_response = MagicMock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {
            "data": {
                "status": "success",
                "output": {
                    "model": {"url": "https://api.tripo3d.ai/models/img123.glb"},
                },
            }
        }

        mock_client.request.side_effect = [
            mock_create_response,
            mock_status_response,
        ]

        with patch.object(client, "_download_model", return_value=Path("/tmp/model.glb")):
            result = await client.image_to_3d(
                image_url="https://example.com/hoodie.png",
                wait_for_completion=True,
            )

        assert result.task_id == "task_img_123"
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_image_to_3d_missing_image(self, client: Tripo3DClient) -> None:
        """Test image-to-3D fails without image."""
        client._initialized = True

        with pytest.raises(Tripo3DError) as exc_info:
            await client.image_to_3d()

        assert "image_url or image_path" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_task_status(self, client: Tripo3DClient) -> None:
        """Test getting task status."""
        mock_client = AsyncMock()
        client._client = mock_client
        client._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "status": "running",
                "progress": 50,
            }
        }
        mock_client.request.return_value = mock_response

        status = await client.get_task_status("task_789")

        assert status["status"] == "running"
        assert status["progress"] == 50

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, client: Tripo3DClient) -> None:
        """Test retry behavior on rate limit."""
        mock_client = AsyncMock()
        client._client = mock_client
        client._initialized = True

        # First request rate limited, second succeeds
        mock_rate_limited = MagicMock()
        mock_rate_limited.status_code = 429

        mock_success = MagicMock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"data": {"task_id": "task_retry"}}

        mock_client.request.side_effect = [mock_rate_limited, mock_success]

        result = await client._request("POST", "/task", json_data={"type": "test"})

        assert result["data"]["task_id"] == "task_retry"
        assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test client as async context manager."""
        with patch.object(Tripo3DClient, "initialize", return_value=True):
            with patch.object(Tripo3DClient, "close", return_value=None):
                async with Tripo3DClient(api_key="test") as client:
                    assert client._initialized is True


class TestFASHNClient:
    """Tests for FASHN API client."""

    @pytest.fixture
    def client(self) -> FASHNClient:
        """Create a test client with mock API key."""
        return FASHNClient(
            api_key="test-fashn-key",
            timeout=10.0,
            max_retries=2,
        )

    @pytest.mark.asyncio
    async def test_initialize_success(self, client: FASHNClient) -> None:
        """Test successful client initialization."""
        result = await client.initialize()

        assert result is True
        assert client._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_without_api_key(self) -> None:
        """Test initialization fails without API key."""
        client = FASHNClient(api_key="")

        with pytest.raises(FASHNError) as exc_info:
            await client.initialize()

        assert "FASHN_API_KEY" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_virtual_tryon_success(self, client: FASHNClient) -> None:
        """Test successful virtual try-on."""
        mock_client = AsyncMock()
        client._client = mock_client
        client._initialized = True

        # Mock run response
        mock_run_response = MagicMock()
        mock_run_response.status_code = 200
        mock_run_response.json.return_value = {"id": "tryon_123"}

        # Mock status response
        mock_status_response = MagicMock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {
            "status": "completed",
            "output": {"image_url": "https://api.fashn.ai/results/123.png"},
        }

        mock_client.request.side_effect = [
            mock_run_response,
            mock_status_response,
        ]

        with patch.object(client, "_download_image", return_value=Path("/tmp/tryon.png")):
            result = await client.virtual_tryon(
                garment_image_url="https://example.com/garment.png",
                model_type=TryOnModel.FEMALE,
            )

        assert result.task_id == "tryon_123"
        assert result.status == "completed"
        assert result.model_type == TryOnModel.FEMALE

    @pytest.mark.asyncio
    async def test_virtual_tryon_missing_garment(self, client: FASHNClient) -> None:
        """Test virtual try-on fails without garment image."""
        client._initialized = True

        with pytest.raises(FASHNError) as exc_info:
            await client.virtual_tryon()

        assert "garment_image_url or garment_image_path" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_batch_tryon(self, client: FASHNClient) -> None:
        """Test batch try-on for multiple model types."""
        mock_client = AsyncMock()
        client._client = mock_client
        client._initialized = True

        # Mock responses for female and male models
        mock_run_response = MagicMock()
        mock_run_response.status_code = 200
        mock_run_response.json.return_value = {"id": "tryon_batch"}

        mock_status_response = MagicMock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {
            "status": "completed",
            "output": {"image_url": "https://api.fashn.ai/results/batch.png"},
        }

        mock_client.request.return_value = mock_run_response

        with patch.object(client, "virtual_tryon") as mock_tryon:
            mock_tryon.return_value = MagicMock(
                task_id="tryon_batch",
                status="completed",
                model_type=TryOnModel.FEMALE,
            )

            results = await client.batch_tryon(
                garment_image_url="https://example.com/garment.png",
                model_types=[TryOnModel.FEMALE, TryOnModel.MALE],
            )

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_default_model_id(self, client: FASHNClient) -> None:
        """Test getting default model IDs."""
        assert client._get_default_model_id(TryOnModel.FEMALE) == "model_female_01"
        assert client._get_default_model_id(TryOnModel.MALE) == "model_male_01"
        assert client._get_default_model_id(TryOnModel.UNISEX) == "model_unisex_01"


class TestWordPressMediaClient:
    """Tests for WordPress Media API client."""

    @pytest.fixture
    def client(self) -> WordPressMediaClient:
        """Create a test client with mock credentials."""
        return WordPressMediaClient(
            site_url="https://test.wordpress.com",
            username="admin",
            app_password="xxxx xxxx xxxx",
            timeout=10.0,
        )

    @pytest.mark.asyncio
    async def test_initialize_success(self, client: WordPressMediaClient) -> None:
        """Test successful client initialization."""
        with patch.object(httpx.AsyncClient, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = await client.initialize()

            assert result is True
            assert client._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_missing_credentials(self) -> None:
        """Test initialization fails with missing credentials."""
        client = WordPressMediaClient(site_url="", username="", app_password="")

        with pytest.raises(WordPressError) as exc_info:
            await client.initialize()

        assert "WORDPRESS_SITE_URL" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_success(self, client: WordPressMediaClient) -> None:
        """Test successful file upload."""
        mock_client = AsyncMock()
        client._client = mock_client
        client._initialized = True

        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            f.write(b"mock GLB content")
            temp_path = f.name

        try:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": 12345,
                "source_url": "https://test.wordpress.com/wp-content/uploads/model.glb",
                "mime_type": "model/gltf-binary",
                "title": {"rendered": "Test Model"},
            }
            mock_client.post.return_value = mock_response

            result = await client.upload_file(
                file_path=temp_path,
                title="Test Model",
                alt_text="A test 3D model",
            )

            assert result.media_id == 12345
            assert result.mime_type == "model/gltf-binary"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_upload_file_not_found(self, client: WordPressMediaClient) -> None:
        """Test upload fails with non-existent file."""
        client._initialized = True

        with pytest.raises(WordPressError) as exc_info:
            await client.upload_file(file_path="/nonexistent/file.glb")

        assert "File not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_from_url(self, client: WordPressMediaClient) -> None:
        """Test upload from URL."""
        mock_client = AsyncMock()
        client._client = mock_client
        client._initialized = True

        # Mock download
        with patch("httpx.AsyncClient") as mock_download_client:
            mock_download = AsyncMock()
            mock_download_client.return_value.__aenter__.return_value = mock_download

            mock_download_response = MagicMock()
            mock_download_response.status_code = 200
            mock_download_response.content = b"mock image content"
            mock_download_response.headers = {"content-type": "image/png"}
            mock_download.get.return_value = mock_download_response

            # Mock upload
            mock_upload_response = MagicMock()
            mock_upload_response.status_code = 201
            mock_upload_response.json.return_value = {
                "id": 67890,
                "source_url": "https://test.wordpress.com/wp-content/uploads/image.png",
                "mime_type": "image/png",
                "title": {"rendered": "Test Image"},
            }
            mock_client.post.return_value = mock_upload_response

            result = await client.upload_from_url(
                url="https://example.com/image.png",
                title="Test Image",
            )

            assert result.media_id == 67890

    @pytest.mark.asyncio
    async def test_delete_media(self, client: WordPressMediaClient) -> None:
        """Test media deletion."""
        mock_client = AsyncMock()
        client._client = mock_client
        client._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.delete.return_value = mock_response

        result = await client.delete_media(12345)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_media(self, client: WordPressMediaClient) -> None:
        """Test getting media details."""
        mock_client = AsyncMock()
        client._client = mock_client
        client._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 12345,
            "title": {"rendered": "Test Media"},
        }
        mock_client.get.return_value = mock_response

        result = await client.get_media(12345)

        assert result is not None
        assert result["id"] == 12345

    def test_auth_header_generation(self, client: WordPressMediaClient) -> None:
        """Test Basic auth header generation."""
        auth_header = client._get_auth_header()

        assert auth_header.startswith("Basic ")

    def test_media_endpoint(self, client: WordPressMediaClient) -> None:
        """Test media endpoint URL construction."""
        assert client.media_endpoint == "https://test.wordpress.com/wp-json/wp/v2/media"
