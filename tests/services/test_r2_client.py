# tests/services/test_r2_client.py
"""
Unit tests for Cloudflare R2 storage client.

Tests cover:
- Configuration and validation
- Upload operations (bytes, file, stream)
- Download operations
- Object management (head, delete, list)
- Pre-signed URL generation
- Error handling

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import io
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from services.storage.r2_client import (
    AssetCategory,
    R2Client,
    R2Config,
    R2Error,
    R2NotFoundError,
    R2Object,
    R2UploadResult,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def config() -> R2Config:
    """Create test configuration."""
    return R2Config(
        account_id="test-account-id",
        access_key_id="test-access-key",
        secret_access_key="test-secret-key",
        bucket="test-bucket",
        public_url="https://assets.example.com",
        cdn_url="https://cdn.example.com",
    )


@pytest.fixture
def client(config: R2Config) -> R2Client:
    """Create test client."""
    return R2Client(config)


@pytest.fixture
def mock_s3_client() -> MagicMock:
    """Create mock boto3 S3 client."""
    return MagicMock()


@pytest.fixture
def temp_file() -> Path:
    """Create temporary test file."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".jpg", delete=False) as f:
        f.write(b"test image content")
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)


# =============================================================================
# Configuration Tests
# =============================================================================


class TestR2Config:
    """Tests for R2Config."""

    def test_default_bucket(self) -> None:
        """Test default bucket name."""
        config = R2Config(
            account_id="test",
            access_key_id="test",
            secret_access_key="test",
        )
        assert config.bucket == "skyyrose-assets"

    def test_endpoint_url(self, config: R2Config) -> None:
        """Test endpoint URL generation."""
        expected = "https://test-account-id.r2.cloudflarestorage.com"
        assert config.endpoint_url == expected

    def test_config_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test configuration from environment."""
        monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "env-account")
        monkeypatch.setenv("R2_ACCESS_KEY_ID", "env-key")
        monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "env-secret")
        monkeypatch.setenv("R2_BUCKET", "env-bucket")

        config = R2Config.from_env()
        assert config.account_id == "env-account"
        assert config.access_key_id == "env-key"
        assert config.bucket == "env-bucket"

    def test_config_validation_missing_account(self) -> None:
        """Test validation fails without account ID."""
        config = R2Config(
            account_id="",
            access_key_id="test",
            secret_access_key="test",
        )
        with pytest.raises(R2Error) as exc_info:
            config.validate()
        assert "CLOUDFLARE_ACCOUNT_ID" in str(exc_info.value)

    def test_config_validation_missing_access_key(self) -> None:
        """Test validation fails without access key."""
        config = R2Config(
            account_id="test",
            access_key_id="",
            secret_access_key="test",
        )
        with pytest.raises(R2Error) as exc_info:
            config.validate()
        assert "R2_ACCESS_KEY_ID" in str(exc_info.value)


# =============================================================================
# Model Tests
# =============================================================================


class TestR2Object:
    """Tests for R2Object model."""

    def test_filename_extraction(self) -> None:
        """Test filename extraction from key."""
        obj = R2Object(
            key="original/SKU-123/20240101_product.jpg",
            bucket="test",
            size=1000,
            etag="abc123",
        )
        assert obj.filename == "20240101_product.jpg"

    def test_extension_extraction(self) -> None:
        """Test extension extraction."""
        obj = R2Object(
            key="3d-models/model.glb",
            bucket="test",
            size=5000,
            etag="def456",
        )
        assert obj.extension == ".glb"


class TestR2UploadResult:
    """Tests for R2UploadResult model."""

    def test_upload_result_fields(self) -> None:
        """Test upload result field access."""
        result = R2UploadResult(
            key="test/file.jpg",
            bucket="test-bucket",
            etag="abc123",
            size=1024,
            url="https://public.com/test/file.jpg",
            cdn_url="https://cdn.com/test/file.jpg",
            content_hash="sha256hash",
            correlation_id="corr-123",
        )
        assert result.key == "test/file.jpg"
        assert result.cdn_url == "https://cdn.com/test/file.jpg"


# =============================================================================
# Client Tests - Upload
# =============================================================================


class TestR2ClientUpload:
    """Tests for R2Client upload operations."""

    def test_upload_bytes(self, client: R2Client, mock_s3_client: MagicMock) -> None:
        """Test uploading bytes."""
        mock_s3_client.put_object.return_value = {"ETag": '"abc123"'}

        with patch.object(client, "_get_client", return_value=mock_s3_client):
            result = client.upload_bytes(
                b"test content",
                "test/file.txt",
                content_type="text/plain",
            )

        assert result.key == "test/file.txt"
        assert result.etag == "abc123"
        assert result.size == 12
        assert "assets.example.com" in result.url
        mock_s3_client.put_object.assert_called_once()

    def test_upload_file(
        self, client: R2Client, mock_s3_client: MagicMock, temp_file: Path
    ) -> None:
        """Test uploading a file."""
        mock_s3_client.put_object.return_value = {"ETag": '"def456"'}

        with patch.object(client, "_get_client", return_value=mock_s3_client):
            result = client.upload_file(
                temp_file,
                AssetCategory.ORIGINAL,
                product_id="SKU-123",
            )

        assert AssetCategory.ORIGINAL.value in result.key
        assert result.etag == "def456"
        call_args = mock_s3_client.put_object.call_args
        assert call_args.kwargs["Metadata"]["product-id"] == "SKU-123"

    def test_upload_file_not_found(self, client: R2Client) -> None:
        """Test uploading non-existent file."""
        with pytest.raises(R2Error) as exc_info:
            client.upload_file(
                "/nonexistent/file.jpg",
                AssetCategory.ORIGINAL,
            )
        assert "File not found" in str(exc_info.value)

    def test_upload_stream(self, client: R2Client, mock_s3_client: MagicMock) -> None:
        """Test uploading from stream."""
        mock_s3_client.put_object.return_value = {"ETag": '"stream123"'}
        stream = io.BytesIO(b"stream content")

        with patch.object(client, "_get_client", return_value=mock_s3_client):
            result = client.upload_stream(
                stream,
                "document.pdf",
                AssetCategory.BRAND,
            )

        assert AssetCategory.BRAND.value in result.key
        assert result.etag == "stream123"

    def test_upload_client_error(self, client: R2Client, mock_s3_client: MagicMock) -> None:
        """Test upload with S3 client error."""
        mock_s3_client.put_object.side_effect = ClientError(
            {"Error": {"Code": "InternalError", "Message": "Test error"}},
            "PutObject",
        )

        with (
            patch.object(client, "_get_client", return_value=mock_s3_client),
            pytest.raises(R2Error) as exc_info,
        ):
            client.upload_bytes(b"test", "test/file.txt")

        assert exc_info.value.retryable is True


# =============================================================================
# Client Tests - Download
# =============================================================================


class TestR2ClientDownload:
    """Tests for R2Client download operations."""

    def test_download_bytes(self, client: R2Client, mock_s3_client: MagicMock) -> None:
        """Test downloading bytes."""
        mock_body = MagicMock()
        mock_body.read.return_value = b"downloaded content"
        mock_s3_client.get_object.return_value = {
            "Body": mock_body,
            "ContentLength": 18,
            "ETag": '"ghi789"',
            "ContentType": "text/plain",
        }

        with patch.object(client, "_get_client", return_value=mock_s3_client):
            data, obj = client.download_bytes("test/file.txt")

        assert data == b"downloaded content"
        assert obj.etag == "ghi789"
        assert obj.content_type == "text/plain"

    def test_download_not_found(self, client: R2Client, mock_s3_client: MagicMock) -> None:
        """Test downloading non-existent object."""
        mock_s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}},
            "GetObject",
        )

        with (
            patch.object(client, "_get_client", return_value=mock_s3_client),
            pytest.raises(R2NotFoundError) as exc_info,
        ):
            client.download_bytes("nonexistent/file.txt")

        assert "nonexistent/file.txt" in str(exc_info.value)

    def test_download_file(self, client: R2Client, mock_s3_client: MagicMock) -> None:
        """Test downloading to file."""
        mock_body = MagicMock()
        mock_body.read.return_value = b"file content"
        mock_s3_client.get_object.return_value = {
            "Body": mock_body,
            "ContentLength": 12,
            "ETag": '"file123"',
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "downloaded.txt"

            with patch.object(client, "_get_client", return_value=mock_s3_client):
                obj = client.download_file("test/file.txt", dest)

            assert dest.exists()
            assert dest.read_bytes() == b"file content"
            assert obj.etag == "file123"


# =============================================================================
# Client Tests - Object Management
# =============================================================================


class TestR2ClientObjectManagement:
    """Tests for R2Client object management."""

    def test_head_object(self, client: R2Client, mock_s3_client: MagicMock) -> None:
        """Test getting object metadata."""
        mock_s3_client.head_object.return_value = {
            "ContentLength": 2048,
            "ETag": '"head123"',
            "ContentType": "image/jpeg",
            "LastModified": datetime(2024, 1, 1),
            "Metadata": {"product-id": "SKU-456"},
        }

        with patch.object(client, "_get_client", return_value=mock_s3_client):
            obj = client.head_object("test/image.jpg")

        assert obj.size == 2048
        assert obj.etag == "head123"
        assert obj.metadata["product-id"] == "SKU-456"

    def test_delete_object(self, client: R2Client, mock_s3_client: MagicMock) -> None:
        """Test deleting object."""
        mock_s3_client.delete_object.return_value = {}

        with patch.object(client, "_get_client", return_value=mock_s3_client):
            result = client.delete_object("test/file.txt")

        assert result is True
        mock_s3_client.delete_object.assert_called_once()

    def test_list_objects(self, client: R2Client, mock_s3_client: MagicMock) -> None:
        """Test listing objects."""
        mock_s3_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "original/file1.jpg", "Size": 1000, "ETag": '"a"'},
                {"Key": "original/file2.jpg", "Size": 2000, "ETag": '"b"'},
            ]
        }

        with patch.object(client, "_get_client", return_value=mock_s3_client):
            objects = client.list_objects(prefix="original/")

        assert len(objects) == 2
        assert objects[0].key == "original/file1.jpg"
        assert objects[1].size == 2000

    def test_object_exists_true(self, client: R2Client, mock_s3_client: MagicMock) -> None:
        """Test object exists check - true."""
        mock_s3_client.head_object.return_value = {"ContentLength": 100}

        with patch.object(client, "_get_client", return_value=mock_s3_client):
            exists = client.object_exists("test/file.txt")

        assert exists is True

    def test_object_exists_false(self, client: R2Client, mock_s3_client: MagicMock) -> None:
        """Test object exists check - false."""
        mock_s3_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not found"}},
            "HeadObject",
        )

        with patch.object(client, "_get_client", return_value=mock_s3_client):
            exists = client.object_exists("nonexistent.txt")

        assert exists is False


# =============================================================================
# Client Tests - Pre-signed URLs
# =============================================================================


class TestR2ClientPresignedUrls:
    """Tests for R2Client pre-signed URL generation."""

    def test_generate_presigned_get_url(self, client: R2Client, mock_s3_client: MagicMock) -> None:
        """Test generating GET pre-signed URL."""
        expected_url = "https://presigned.example.com/test/file.txt?signature=abc"
        mock_s3_client.generate_presigned_url.return_value = expected_url

        with patch.object(client, "_get_client", return_value=mock_s3_client):
            url = client.generate_presigned_url("test/file.txt", expires_in=7200)

        assert url == expected_url
        mock_s3_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "test/file.txt"},
            ExpiresIn=7200,
        )

    def test_generate_presigned_put_url(self, client: R2Client, mock_s3_client: MagicMock) -> None:
        """Test generating PUT pre-signed URL."""
        expected_url = "https://presigned.example.com/upload?signature=xyz"
        mock_s3_client.generate_presigned_url.return_value = expected_url

        with patch.object(client, "_get_client", return_value=mock_s3_client):
            result_url = client.generate_presigned_url("upload/new-file.jpg", for_upload=True)

        assert result_url == expected_url
        mock_s3_client.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={"Bucket": "test-bucket", "Key": "upload/new-file.jpg"},
            ExpiresIn=3600,
        )


# =============================================================================
# Helper Method Tests
# =============================================================================


class TestR2ClientHelpers:
    """Tests for R2Client helper methods."""

    def test_generate_key_with_product_id(self, client: R2Client) -> None:
        """Test key generation with product ID."""
        key = client._generate_key(
            "product.jpg",
            AssetCategory.ORIGINAL,
            product_id="SKU-123",
        )
        assert "original/SKU-123/" in key
        assert "product.jpg" in key

    def test_generate_key_with_prefix(self, client: R2Client) -> None:
        """Test key generation with prefix."""
        key = client._generate_key(
            "model.glb",
            AssetCategory.MODEL_3D,
            prefix="batch-001",
        )
        assert "3d-models/batch-001/" in key

    def test_get_content_type(self, client: R2Client) -> None:
        """Test content type detection."""
        assert client._get_content_type("image.jpg") == "image/jpeg"
        # GLB files may not be recognized by default mimetypes
        glb_type = client._get_content_type("model.glb")
        assert glb_type in ("model/gltf-binary", "application/octet-stream")
        # Use truly unknown extension
        assert client._get_content_type("file.qwerty123") == "application/octet-stream"

    def test_compute_content_hash(self, client: R2Client) -> None:
        """Test content hash computation."""
        hash1 = client._compute_content_hash(b"test content")
        hash2 = client._compute_content_hash(b"test content")
        hash3 = client._compute_content_hash(b"different content")

        assert hash1 == hash2  # Same content = same hash
        assert hash1 != hash3  # Different content = different hash
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars

    def test_get_public_url(self, client: R2Client) -> None:
        """Test public URL generation."""
        url = client._get_public_url("test/file.jpg")
        assert url == "https://assets.example.com/test/file.jpg"

    def test_get_cdn_url(self, client: R2Client) -> None:
        """Test CDN URL generation."""
        url = client._get_cdn_url("test/file.jpg")
        assert url == "https://cdn.example.com/test/file.jpg"


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestR2ErrorHandling:
    """Tests for R2 error handling."""

    def test_r2_error_with_context(self) -> None:
        """Test R2Error with context."""
        error = R2Error(
            "Test error",
            bucket="test-bucket",
            key="test/key.txt",
            correlation_id="corr-789",
        )
        assert error.context["bucket"] == "test-bucket"
        assert error.context["key"] == "test/key.txt"
        assert error.correlation_id == "corr-789"

    def test_r2_not_found_error(self) -> None:
        """Test R2NotFoundError."""
        error = R2NotFoundError("missing/file.txt", bucket="my-bucket")
        assert "missing/file.txt" in str(error)
        assert error.retryable is False

    def test_error_to_dict(self) -> None:
        """Test error serialization."""
        error = R2Error(
            "Upload failed",
            bucket="test",
            key="test.txt",
            correlation_id="corr-abc",
        )
        error_dict = error.to_dict()
        assert "error" in error_dict
        assert error_dict["error"]["correlation_id"] == "corr-abc"
