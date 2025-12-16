"""
WordPress Media Manager
=======================

Media upload and management utilities.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MediaUpload(BaseModel):
    """Media upload result."""

    id: int
    url: str
    title: str = ""
    alt_text: str = ""
    mime_type: str = ""
    width: int | None = None
    height: int | None = None
    file_size: int = 0


class ImageOptimizer:
    """
    Image optimization utilities.

    Note: Requires Pillow for actual optimization.
    This is a stub implementation.
    """

    def __init__(
        self,
        max_dimension: int = 2048,
        jpeg_quality: int = 85,
        webp_quality: int = 80,
    ) -> None:
        self.max_dimension = max_dimension
        self.jpeg_quality = jpeg_quality
        self.webp_quality = webp_quality

    def optimize(self, file_path: str, output_path: str | None = None) -> str:
        """
        Optimize image file.

        Note: Stub implementation - returns original path.
        In production, would resize and compress using Pillow.
        """
        if output_path:
            # Would copy and optimize
            import shutil

            shutil.copy(file_path, output_path)
            return output_path
        return file_path

    def generate_webp(self, file_path: str) -> str | None:
        """
        Generate WebP version of image.

        Note: Stub implementation.
        """
        # Would convert to WebP using Pillow
        return None


class MediaManager:
    """
    WordPress media management.

    Handles upload, optimization, and organization of media files.
    """

    def __init__(
        self,
        client: Any = None,  # WordPressClient
        optimizer: ImageOptimizer | None = None,
    ) -> None:
        self.client = client
        self.optimizer = optimizer or ImageOptimizer()

    async def upload(
        self,
        file_path: str,
        title: str = "",
        alt_text: str = "",
        optimize: bool = True,
    ) -> MediaUpload:
        """
        Upload media file to WordPress.

        Args:
            file_path: Path to file
            title: Media title
            alt_text: Alt text for images
            optimize: Whether to optimize before upload

        Returns:
            MediaUpload result
        """
        if not self.client:
            raise RuntimeError("WordPress client not configured")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Optimize if requested and is an image
        upload_path = file_path
        if optimize and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            upload_path = self.optimizer.optimize(file_path)

        # Upload
        result = await self.client.upload_media(
            file_path=upload_path,
            title=title or path.stem,
        )

        # Update alt text if provided
        if alt_text and result.get("id"):
            await self.client._request(
                "POST",
                f"/media/{result['id']}",
                json={"alt_text": alt_text},
            )

        return MediaUpload(
            id=result.get("id", 0),
            url=result.get("source_url", ""),
            title=result.get("title", {}).get("rendered", title),
            alt_text=alt_text,
            mime_type=result.get("mime_type", ""),
            width=result.get("media_details", {}).get("width"),
            height=result.get("media_details", {}).get("height"),
            file_size=result.get("media_details", {}).get("filesize", 0),
        )

    async def upload_batch(
        self,
        file_paths: list[str],
        optimize: bool = True,
    ) -> list[MediaUpload]:
        """Upload multiple files."""
        results = []
        for path in file_paths:
            try:
                result = await self.upload(path, optimize=optimize)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to upload {path}: {e}")
        return results

    async def get_by_id(self, media_id: int) -> MediaUpload | None:
        """Get media by ID."""
        if not self.client:
            return None

        result = await self.client._request("GET", f"/media/{media_id}")

        return MediaUpload(
            id=result.get("id", 0),
            url=result.get("source_url", ""),
            title=result.get("title", {}).get("rendered", ""),
            alt_text=result.get("alt_text", ""),
            mime_type=result.get("mime_type", ""),
            width=result.get("media_details", {}).get("width"),
            height=result.get("media_details", {}).get("height"),
        )

    async def delete(self, media_id: int, force: bool = True) -> bool:
        """Delete media."""
        if not self.client:
            return False

        try:
            await self.client._request(
                "DELETE",
                f"/media/{media_id}",
                params={"force": force},
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete media {media_id}: {e}")
            return False


__all__ = ["MediaManager", "MediaUpload", "ImageOptimizer"]
