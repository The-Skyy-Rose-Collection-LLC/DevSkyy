# services/storage/r2_client.py
"""
Cloudflare R2 Storage Client for DevSkyy.

Provides S3-compatible storage with zero egress fees for:
- Product images (original, enhanced, thumbnails)
- 3D models (GLB, glTF, OBJ)
- Brand assets
- Generated AI imagery

API Reference: https://developers.cloudflare.com/r2/api/s3/api/

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, BinaryIO

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

from errors.production_errors import (
    DevSkyError,
    DevSkyErrorCode,
    DevSkyErrorSeverity,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_BUCKET = "skyyrose-assets"
DEFAULT_REGION = "auto"
MAX_UPLOAD_SIZE_MB = 100  # 100MB max for single-part upload
MULTIPART_THRESHOLD = 5 * 1024 * 1024  # 5MB


# =============================================================================
# Errors
# =============================================================================


class R2Error(DevSkyError):
    """Base error for R2 storage operations."""

    def __init__(
        self,
        message: str,
        *,
        bucket: str | None = None,
        key: str | None = None,
        correlation_id: str | None = None,
        cause: Exception | None = None,
        retryable: bool = False,
    ) -> None:
        context: dict[str, Any] = {}
        if bucket:
            context["bucket"] = bucket
        if key:
            context["key"] = key

        super().__init__(
            message,
            code=DevSkyErrorCode.EXTERNAL_SERVICE_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            cause=cause,
            retryable=retryable,
            correlation_id=correlation_id,
        )


class R2NotFoundError(R2Error):
    """Raised when object is not found in R2."""

    def __init__(
        self,
        key: str,
        bucket: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            f"Object not found: {key}",
            bucket=bucket,
            key=key,
            retryable=False,
            **kwargs,
        )


# =============================================================================
# Models
# =============================================================================


class AssetCategory(str, Enum):
    """Asset storage categories for organized bucket structure."""

    ORIGINAL = "original"  # Original uploaded images
    ENHANCED = "enhanced"  # AI-enhanced images
    THUMBNAIL = "thumbnail"  # Resized thumbnails
    MODEL_3D = "3d-models"  # 3D model files
    BRAND = "brand"  # Brand assets
    AI_GENERATED = "ai-generated"  # AI-generated imagery
    TEMP = "temp"  # Temporary processing files


class R2Object(BaseModel):
    """Metadata for an R2 object."""

    key: str
    bucket: str
    size: int
    etag: str
    last_modified: datetime | None = None
    content_type: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @property
    def filename(self) -> str:
        """Extract filename from key."""
        return Path(self.key).name

    @property
    def extension(self) -> str:
        """Extract file extension."""
        return Path(self.key).suffix.lower()


class R2UploadResult(BaseModel):
    """Result of an R2 upload operation."""

    key: str
    bucket: str
    etag: str
    size: int
    url: str
    cdn_url: str | None = None
    content_hash: str
    correlation_id: str


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class R2Config:
    """Cloudflare R2 configuration."""

    account_id: str = field(default_factory=lambda: os.getenv("CLOUDFLARE_ACCOUNT_ID", ""))
    access_key_id: str = field(default_factory=lambda: os.getenv("R2_ACCESS_KEY_ID", ""))
    secret_access_key: str = field(default_factory=lambda: os.getenv("R2_SECRET_ACCESS_KEY", ""))
    bucket: str = field(default_factory=lambda: os.getenv("R2_BUCKET", DEFAULT_BUCKET))
    region: str = DEFAULT_REGION
    public_url: str = field(
        default_factory=lambda: os.getenv("R2_PUBLIC_URL", "")
    )  # Custom domain or R2.dev URL
    cdn_url: str = field(default_factory=lambda: os.getenv("R2_CDN_URL", ""))  # Cloudflare CDN URL

    @property
    def endpoint_url(self) -> str:
        """Generate R2 endpoint URL."""
        return f"https://{self.account_id}.r2.cloudflarestorage.com"

    @classmethod
    def from_env(cls) -> R2Config:
        """Create config from environment variables."""
        return cls()

    def validate(self) -> None:
        """Validate configuration."""
        if not self.account_id:
            raise R2Error(
                "CLOUDFLARE_ACCOUNT_ID environment variable is required",
                retryable=False,
            )
        if not self.access_key_id:
            raise R2Error(
                "R2_ACCESS_KEY_ID environment variable is required",
                retryable=False,
            )
        if not self.secret_access_key:
            raise R2Error(
                "R2_SECRET_ACCESS_KEY environment variable is required",
                retryable=False,
            )


# =============================================================================
# Client
# =============================================================================


class R2Client:
    """
    Client for Cloudflare R2 storage.

    Provides:
    - Upload/download operations
    - Organized asset storage by category
    - Content-based deduplication
    - Pre-signed URL generation
    - Metadata management

    R2 Benefits:
    - Zero egress fees (perfect for CDN delivery)
    - S3-compatible API
    - Cloudflare CDN integration

    Usage:
        client = R2Client()
        result = await client.upload_file(
            file_path="product.jpg",
            category=AssetCategory.ORIGINAL,
            product_id="SKU-123",
        )
        print(result.cdn_url)
    """

    def __init__(self, config: R2Config | None = None) -> None:
        self.config = config or R2Config.from_env()
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create boto3 S3 client configured for R2."""
        if self._client is None:
            self.config.validate()
            self._client = boto3.client(
                "s3",
                endpoint_url=self.config.endpoint_url,
                aws_access_key_id=self.config.access_key_id,
                aws_secret_access_key=self.config.secret_access_key,
                region_name=self.config.region,
                config=BotoConfig(
                    signature_version="s3v4",
                    retries={"max_attempts": 3, "mode": "adaptive"},
                ),
            )
        return self._client

    def _generate_correlation_id(self) -> str:
        """Generate a unique correlation ID for tracing."""
        return str(uuid.uuid4())

    def _compute_content_hash(self, data: bytes) -> str:
        """Compute SHA-256 hash of content for deduplication."""
        return hashlib.sha256(data).hexdigest()

    def _generate_key(
        self,
        filename: str,
        category: AssetCategory,
        product_id: str | None = None,
        prefix: str | None = None,
    ) -> str:
        """
        Generate organized storage key.

        Structure: {category}/{product_id}/{timestamp}_{filename}
        or: {category}/{prefix}/{timestamp}_{filename}
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = Path(filename).name  # Strip any path components

        parts = [category.value]
        if product_id:
            parts.append(product_id)
        elif prefix:
            parts.append(prefix)

        parts.append(f"{timestamp}_{safe_filename}")
        return "/".join(parts)

    def _get_content_type(self, filename: str) -> str:
        """Determine content type from filename."""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    def _get_public_url(self, key: str) -> str:
        """Generate public URL for object."""
        if self.config.public_url:
            return f"{self.config.public_url.rstrip('/')}/{key}"
        # Fallback to R2.dev URL format
        return f"https://{self.config.bucket}.{self.config.account_id}.r2.dev/{key}"

    def _get_cdn_url(self, key: str) -> str | None:
        """Generate CDN URL for object."""
        if self.config.cdn_url:
            return f"{self.config.cdn_url.rstrip('/')}/{key}"
        return None

    # =========================================================================
    # Upload Operations
    # =========================================================================

    def upload_bytes(
        self,
        data: bytes,
        key: str,
        *,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
        correlation_id: str | None = None,
    ) -> R2UploadResult:
        """
        Upload bytes to R2.

        Args:
            data: Raw bytes to upload
            key: Storage key/path
            content_type: MIME type (auto-detected if not provided)
            metadata: Custom metadata
            correlation_id: Optional correlation ID for tracing

        Returns:
            R2UploadResult with URLs and metadata
        """
        correlation_id = correlation_id or self._generate_correlation_id()
        client = self._get_client()
        content_hash = self._compute_content_hash(data)

        # Prepare metadata
        full_metadata = {
            "correlation-id": correlation_id,
            "content-hash": content_hash,
        }
        if metadata:
            full_metadata.update(metadata)

        logger.info(
            "Uploading to R2",
            extra={
                "key": key,
                "size": len(data),
                "correlation_id": correlation_id,
            },
        )

        try:
            response = client.put_object(
                Bucket=self.config.bucket,
                Key=key,
                Body=data,
                ContentType=content_type or self._get_content_type(key),
                Metadata=full_metadata,
            )

            etag = response.get("ETag", "").strip('"')

            logger.info(
                "Upload complete",
                extra={
                    "key": key,
                    "etag": etag,
                    "correlation_id": correlation_id,
                },
            )

            return R2UploadResult(
                key=key,
                bucket=self.config.bucket,
                etag=etag,
                size=len(data),
                url=self._get_public_url(key),
                cdn_url=self._get_cdn_url(key),
                content_hash=content_hash,
                correlation_id=correlation_id,
            )

        except ClientError as e:
            logger.error(
                "R2 upload failed",
                extra={
                    "key": key,
                    "error": str(e),
                    "correlation_id": correlation_id,
                },
            )
            raise R2Error(
                f"Upload failed: {e}",
                bucket=self.config.bucket,
                key=key,
                correlation_id=correlation_id,
                cause=e,
                retryable=True,
            ) from e

    def upload_file(
        self,
        file_path: str | Path,
        category: AssetCategory,
        *,
        product_id: str | None = None,
        prefix: str | None = None,
        metadata: dict[str, str] | None = None,
        correlation_id: str | None = None,
    ) -> R2UploadResult:
        """
        Upload a file to R2 with organized key structure.

        Args:
            file_path: Path to local file
            category: Asset category for organization
            product_id: Optional product SKU for path organization
            prefix: Optional prefix (used if product_id not provided)
            metadata: Custom metadata
            correlation_id: Optional correlation ID for tracing

        Returns:
            R2UploadResult with URLs and metadata
        """
        correlation_id = correlation_id or self._generate_correlation_id()
        path = Path(file_path)

        if not path.exists():
            raise R2Error(
                f"File not found: {file_path}",
                correlation_id=correlation_id,
                retryable=False,
            )

        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_UPLOAD_SIZE_MB:
            raise R2Error(
                f"File too large: {file_size_mb:.1f}MB (max {MAX_UPLOAD_SIZE_MB}MB)",
                correlation_id=correlation_id,
                retryable=False,
            )

        # Generate key
        key = self._generate_key(
            path.name,
            category,
            product_id=product_id,
            prefix=prefix,
        )

        # Read and upload
        with open(path, "rb") as f:
            data = f.read()

        # Add file metadata
        file_metadata = {
            "original-filename": path.name,
            "category": category.value,
        }
        if product_id:
            file_metadata["product-id"] = product_id
        if metadata:
            file_metadata.update(metadata)

        return self.upload_bytes(
            data,
            key,
            content_type=self._get_content_type(path.name),
            metadata=file_metadata,
            correlation_id=correlation_id,
        )

    def upload_stream(
        self,
        stream: BinaryIO,
        filename: str,
        category: AssetCategory,
        *,
        product_id: str | None = None,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
        correlation_id: str | None = None,
    ) -> R2UploadResult:
        """
        Upload from a file-like stream.

        Args:
            stream: File-like object with read() method
            filename: Original filename for key generation
            category: Asset category
            product_id: Optional product SKU
            content_type: MIME type
            metadata: Custom metadata
            correlation_id: Optional correlation ID

        Returns:
            R2UploadResult with URLs and metadata
        """
        data = stream.read()
        key = self._generate_key(filename, category, product_id=product_id)

        return self.upload_bytes(
            data,
            key,
            content_type=content_type or self._get_content_type(filename),
            metadata=metadata,
            correlation_id=correlation_id,
        )

    # =========================================================================
    # Download Operations
    # =========================================================================

    def download_bytes(
        self,
        key: str,
        *,
        correlation_id: str | None = None,
    ) -> tuple[bytes, R2Object]:
        """
        Download object as bytes.

        Args:
            key: Storage key/path
            correlation_id: Optional correlation ID

        Returns:
            Tuple of (data bytes, object metadata)
        """
        correlation_id = correlation_id or self._generate_correlation_id()
        client = self._get_client()

        logger.debug(
            "Downloading from R2",
            extra={"key": key, "correlation_id": correlation_id},
        )

        try:
            response = client.get_object(Bucket=self.config.bucket, Key=key)
            data = response["Body"].read()

            obj = R2Object(
                key=key,
                bucket=self.config.bucket,
                size=response.get("ContentLength", len(data)),
                etag=response.get("ETag", "").strip('"'),
                last_modified=response.get("LastModified"),
                content_type=response.get("ContentType"),
                metadata=response.get("Metadata", {}),
            )

            return data, obj

        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "NoSuchKey":
                raise R2NotFoundError(
                    key,
                    bucket=self.config.bucket,
                    correlation_id=correlation_id,
                ) from e
            raise R2Error(
                f"Download failed: {e}",
                bucket=self.config.bucket,
                key=key,
                correlation_id=correlation_id,
                cause=e,
                retryable=True,
            ) from e

    def download_file(
        self,
        key: str,
        destination: str | Path,
        *,
        correlation_id: str | None = None,
    ) -> R2Object:
        """
        Download object to local file.

        Args:
            key: Storage key/path
            destination: Local file path
            correlation_id: Optional correlation ID

        Returns:
            R2Object metadata
        """
        data, obj = self.download_bytes(key, correlation_id=correlation_id)
        dest_path = Path(destination)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        with open(dest_path, "wb") as f:
            f.write(data)

        return obj

    # =========================================================================
    # Object Management
    # =========================================================================

    def head_object(
        self,
        key: str,
        *,
        correlation_id: str | None = None,
    ) -> R2Object:
        """
        Get object metadata without downloading content.

        Args:
            key: Storage key/path
            correlation_id: Optional correlation ID

        Returns:
            R2Object with metadata
        """
        correlation_id = correlation_id or self._generate_correlation_id()
        client = self._get_client()

        try:
            response = client.head_object(Bucket=self.config.bucket, Key=key)

            return R2Object(
                key=key,
                bucket=self.config.bucket,
                size=response.get("ContentLength", 0),
                etag=response.get("ETag", "").strip('"'),
                last_modified=response.get("LastModified"),
                content_type=response.get("ContentType"),
                metadata=response.get("Metadata", {}),
            )

        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                raise R2NotFoundError(
                    key,
                    bucket=self.config.bucket,
                    correlation_id=correlation_id,
                ) from e
            raise R2Error(
                f"Head object failed: {e}",
                bucket=self.config.bucket,
                key=key,
                correlation_id=correlation_id,
                cause=e,
            ) from e

    def delete_object(
        self,
        key: str,
        *,
        correlation_id: str | None = None,
    ) -> bool:
        """
        Delete an object from R2.

        Args:
            key: Storage key/path
            correlation_id: Optional correlation ID

        Returns:
            True if deleted successfully
        """
        correlation_id = correlation_id or self._generate_correlation_id()
        client = self._get_client()

        logger.info(
            "Deleting from R2",
            extra={"key": key, "correlation_id": correlation_id},
        )

        try:
            client.delete_object(Bucket=self.config.bucket, Key=key)
            return True
        except ClientError as e:
            raise R2Error(
                f"Delete failed: {e}",
                bucket=self.config.bucket,
                key=key,
                correlation_id=correlation_id,
                cause=e,
            ) from e

    def list_objects(
        self,
        prefix: str | None = None,
        *,
        max_keys: int = 1000,
        correlation_id: str | None = None,
    ) -> list[R2Object]:
        """
        List objects with optional prefix filter.

        Args:
            prefix: Filter by key prefix
            max_keys: Maximum number of objects to return
            correlation_id: Optional correlation ID

        Returns:
            List of R2Object metadata
        """
        correlation_id = correlation_id or self._generate_correlation_id()
        client = self._get_client()

        params: dict[str, Any] = {
            "Bucket": self.config.bucket,
            "MaxKeys": max_keys,
        }
        if prefix:
            params["Prefix"] = prefix

        try:
            response = client.list_objects_v2(**params)
            objects = []

            for item in response.get("Contents", []):
                objects.append(
                    R2Object(
                        key=item["Key"],
                        bucket=self.config.bucket,
                        size=item.get("Size", 0),
                        etag=item.get("ETag", "").strip('"'),
                        last_modified=item.get("LastModified"),
                    )
                )

            return objects

        except ClientError as e:
            raise R2Error(
                f"List objects failed: {e}",
                bucket=self.config.bucket,
                correlation_id=correlation_id,
                cause=e,
            ) from e

    # =========================================================================
    # Pre-signed URLs
    # =========================================================================

    def generate_presigned_url(
        self,
        key: str,
        *,
        expires_in: int = 3600,
        for_upload: bool = False,
        correlation_id: str | None = None,
    ) -> str:
        """
        Generate a pre-signed URL for direct access.

        Args:
            key: Storage key/path
            expires_in: URL expiration in seconds (default 1 hour)
            for_upload: If True, generate PUT URL; otherwise GET URL
            correlation_id: Optional correlation ID

        Returns:
            Pre-signed URL string
        """
        correlation_id = correlation_id or self._generate_correlation_id()
        client = self._get_client()

        method = "put_object" if for_upload else "get_object"

        try:
            url = client.generate_presigned_url(
                method,
                Params={"Bucket": self.config.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            raise R2Error(
                f"Failed to generate presigned URL: {e}",
                bucket=self.config.bucket,
                key=key,
                correlation_id=correlation_id,
                cause=e,
            ) from e

    def object_exists(
        self,
        key: str,
        *,
        correlation_id: str | None = None,
    ) -> bool:
        """
        Check if an object exists.

        Args:
            key: Storage key/path
            correlation_id: Optional correlation ID

        Returns:
            True if object exists
        """
        try:
            self.head_object(key, correlation_id=correlation_id)
            return True
        except R2NotFoundError:
            return False


__all__ = [
    "R2Client",
    "R2Config",
    "R2Error",
    "R2NotFoundError",
    "R2Object",
    "R2UploadResult",
    "AssetCategory",
]
