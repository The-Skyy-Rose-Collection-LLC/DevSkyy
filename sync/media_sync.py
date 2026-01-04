# sync/media_sync.py
"""
WordPress Media Synchronization Manager.

Handles synchronization of media assets (images, 3D models) with
WordPress media library.

Features:
- Bulk media upload
- 3D model attachment to products
- Image optimization before upload
- Duplicate detection
"""

from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from errors.production_errors import ConfigurationError, WordPressIntegrationError

logger = logging.getLogger(__name__)


@dataclass
class MediaAsset:
    """Represents a media asset for synchronization."""

    local_path: str
    filename: str
    mime_type: str
    file_size: int
    checksum: str
    remote_id: int | None = None
    remote_url: str | None = None
    last_synced: datetime | None = None

    @classmethod
    def from_path(cls, path: str | Path) -> MediaAsset:
        """Create a MediaAsset from a file path."""
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Calculate checksum
        with open(path, "rb") as f:
            checksum = hashlib.md5(f.read(), usedforsecurity=False).hexdigest()

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type is None:
            # Handle 3D model types
            suffix = path.suffix.lower()
            mime_map = {
                ".glb": "model/gltf-binary",
                ".gltf": "model/gltf+json",
                ".obj": "model/obj",
                ".fbx": "application/octet-stream",
                ".usd": "model/vnd.usd+zip",
                ".usdz": "model/vnd.usdz+zip",
            }
            mime_type = mime_map.get(suffix, "application/octet-stream")

        return cls(
            local_path=str(path),
            filename=path.name,
            mime_type=mime_type,
            file_size=path.stat().st_size,
            checksum=checksum,
        )


@dataclass
class MediaSyncResult:
    """Result of a media sync operation."""

    success: bool
    uploaded: int = 0
    skipped: int = 0
    failed: int = 0
    assets: list[MediaAsset] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class MediaSyncManager:
    """
    Manages media asset synchronization with WordPress.

    Handles:
    - Image uploads
    - 3D model uploads (.glb, .gltf, .obj)
    - Duplicate detection
    - Asset tracking

    Requires environment variables:
    - WORDPRESS_URL
    - WORDPRESS_USERNAME
    - WORDPRESS_APP_PASSWORD
    """

    # Supported file types
    SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    SUPPORTED_3D = {".glb", ".gltf", ".obj", ".fbx", ".usd", ".usdz"}

    def __init__(
        self,
        wordpress_url: str | None = None,
        username: str | None = None,
        app_password: str | None = None,
    ) -> None:
        """
        Initialize the media sync manager.

        Args:
            wordpress_url: WordPress site URL
            username: WordPress username
            app_password: WordPress application password
        """
        self.url = wordpress_url or os.getenv("WORDPRESS_URL")
        self.username = username or os.getenv("WORDPRESS_USERNAME")
        self.app_password = app_password or os.getenv("WORDPRESS_APP_PASSWORD")

        if not all([self.url, self.username, self.app_password]):
            raise ConfigurationError(
                "WordPress credentials required: WORDPRESS_URL, "
                "WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD",
            )

        self._client = httpx.AsyncClient(
            base_url=f"{self.url}/wp-json/wp/v2",
            auth=(self.username, self.app_password),
            timeout=120.0,  # Longer timeout for file uploads
        )

        # Cache of synced assets by checksum
        self._synced_assets: dict[str, MediaAsset] = {}

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def upload_file(
        self,
        file_path: str | Path,
        title: str | None = None,
        alt_text: str | None = None,
        caption: str | None = None,
    ) -> MediaAsset:
        """
        Upload a file to WordPress media library.

        Args:
            file_path: Path to the file
            title: Optional title
            alt_text: Optional alt text
            caption: Optional caption

        Returns:
            MediaAsset with remote details
        """
        asset = MediaAsset.from_path(file_path)

        # Check for duplicate
        if asset.checksum in self._synced_assets:
            existing = self._synced_assets[asset.checksum]
            if existing.remote_id:
                logger.info(f"Skipping duplicate: {asset.filename}")
                return existing

        try:
            # Read file content
            with open(asset.local_path, "rb") as f:
                file_content = f.read()

            # Prepare headers
            headers = {
                "Content-Disposition": f'attachment; filename="{asset.filename}"',
                "Content-Type": asset.mime_type,
            }

            # Upload
            response = await self._client.post(
                "/media",
                content=file_content,
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            asset.remote_id = data.get("id")
            asset.remote_url = data.get("source_url")
            asset.last_synced = datetime.now(UTC)

            # Update metadata if provided
            if any([title, alt_text, caption]):
                await self._update_media_meta(
                    asset.remote_id,
                    title=title,
                    alt_text=alt_text,
                    caption=caption,
                )

            # Cache the asset
            self._synced_assets[asset.checksum] = asset

            logger.info(f"Uploaded: {asset.filename} -> {asset.remote_url}")
            return asset

        except httpx.HTTPStatusError as e:
            raise WordPressIntegrationError(
                f"Failed to upload {asset.filename}: {e.response.text}",
                endpoint="/media",
                status_code=e.response.status_code,
            )

    async def upload_3d_model(
        self,
        model_path: str | Path,
        product_name: str | None = None,
    ) -> MediaAsset:
        """
        Upload a 3D model to WordPress.

        Args:
            model_path: Path to the 3D model file
            product_name: Optional product name for metadata

        Returns:
            MediaAsset with remote details
        """
        path = Path(model_path)

        if path.suffix.lower() not in self.SUPPORTED_3D:
            raise ValueError(
                f"Unsupported 3D format: {path.suffix}. " f"Supported: {self.SUPPORTED_3D}"
            )

        title = product_name or path.stem
        alt_text = f"3D model of {title}"

        return await self.upload_file(
            model_path,
            title=f"{title} 3D Model",
            alt_text=alt_text,
        )

    async def upload_product_images(
        self,
        image_paths: list[str | Path],
        product_name: str,
    ) -> list[MediaAsset]:
        """
        Upload multiple product images.

        Args:
            image_paths: List of image file paths
            product_name: Product name for metadata

        Returns:
            List of MediaAssets
        """
        assets = []

        for i, path in enumerate(image_paths):
            path = Path(path)

            if path.suffix.lower() not in self.SUPPORTED_IMAGES:
                logger.warning(f"Skipping unsupported image: {path}")
                continue

            position = "main" if i == 0 else f"angle-{i}"
            title = f"{product_name} - {position}"

            try:
                asset = await self.upload_file(
                    path,
                    title=title,
                    alt_text=f"{product_name} product image",
                )
                assets.append(asset)
            except Exception as e:
                logger.error(f"Failed to upload {path}: {e}")

        return assets

    async def sync_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
    ) -> MediaSyncResult:
        """
        Sync all media files in a directory.

        Args:
            directory: Directory to sync
            recursive: Whether to sync subdirectories

        Returns:
            MediaSyncResult with sync details
        """
        directory = Path(directory)
        result = MediaSyncResult(success=True)

        if not directory.exists():
            result.success = False
            result.errors.append(f"Directory not found: {directory}")
            return result

        # Collect files
        pattern = "**/*" if recursive else "*"
        supported = self.SUPPORTED_IMAGES | self.SUPPORTED_3D

        files = [
            f for f in directory.glob(pattern) if f.is_file() and f.suffix.lower() in supported
        ]

        logger.info(f"Found {len(files)} files to sync in {directory}")

        for file_path in files:
            try:
                asset = await self.upload_file(file_path)

                if asset.last_synced:
                    result.uploaded += 1
                else:
                    result.skipped += 1

                result.assets.append(asset)

            except Exception as e:
                result.failed += 1
                result.errors.append(f"{file_path.name}: {str(e)}")

        result.success = result.failed == 0

        return result

    async def get_media_by_filename(
        self,
        filename: str,
    ) -> dict[str, Any] | None:
        """Find media by filename."""
        try:
            response = await self._client.get(
                "/media",
                params={"search": filename},
            )
            response.raise_for_status()

            media = response.json()
            for item in media:
                if item.get("source_url", "").endswith(filename):
                    return item

            return None

        except Exception as e:
            logger.error(f"Failed to search media: {e}")
            return None

    async def delete_media(self, media_id: int, force: bool = True) -> bool:
        """Delete a media item."""
        try:
            response = await self._client.delete(
                f"/media/{media_id}",
                params={"force": force},
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to delete media {media_id}: {e}")
            return False

    async def _update_media_meta(
        self,
        media_id: int,
        title: str | None = None,
        alt_text: str | None = None,
        caption: str | None = None,
    ) -> None:
        """Update media metadata."""
        data = {}

        if title:
            data["title"] = title
        if alt_text:
            data["alt_text"] = alt_text
        if caption:
            data["caption"] = caption

        if data:
            try:
                await self._client.post(f"/media/{media_id}", json=data)
            except Exception as e:
                logger.warning(f"Failed to update media meta: {e}")
