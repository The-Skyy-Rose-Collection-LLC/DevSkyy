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
    Image optimization utilities using Pillow.

    Features:
    - Resize images to fit within max dimensions while maintaining aspect ratio
    - Compress JPEG images with configurable quality
    - Convert images to WebP format for better web performance
    - Preserve EXIF data optionally
    - Support for JPEG, PNG, WebP, and GIF formats

    Requires: Pillow (PIL) library
    """

    def __init__(
        self,
        max_dimension: int = 2048,
        jpeg_quality: int = 85,
        webp_quality: int = 80,
        preserve_exif: bool = False,
    ) -> None:
        """
        Initialize the image optimizer.

        Args:
            max_dimension: Maximum width or height (image will be scaled to fit)
            jpeg_quality: JPEG compression quality (1-100, higher is better quality)
            webp_quality: WebP compression quality (1-100, higher is better quality)
            preserve_exif: Whether to preserve EXIF metadata
        """
        self.max_dimension = max_dimension
        self.jpeg_quality = jpeg_quality
        self.webp_quality = webp_quality
        self.preserve_exif = preserve_exif
        self._pillow_available = self._check_pillow()

    def _check_pillow(self) -> bool:
        """Check if Pillow is available."""
        try:
            from PIL import Image  # noqa: F401

            return True
        except ImportError:
            logger.warning("Pillow not installed - image optimization will be limited")
            return False

    def optimize(self, file_path: str, output_path: str | None = None) -> str:
        """
        Optimize image file by resizing and compressing.

        Args:
            file_path: Path to the source image
            output_path: Path for the optimized image (if None, overwrites original)

        Returns:
            Path to the optimized image

        Raises:
            FileNotFoundError: If source file doesn't exist
            RuntimeError: If Pillow is not installed
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")

        if not self._pillow_available:
            logger.warning("Pillow not installed, returning original file")
            if output_path:
                import shutil

                shutil.copy(file_path, output_path)
                return output_path
            return file_path

        from PIL import Image

        output = Path(output_path) if output_path else path
        suffix = path.suffix.lower()

        try:
            with Image.open(file_path) as img:
                # Get EXIF data if preserving
                exif_data = None
                if self.preserve_exif and hasattr(img, "_getexif"):
                    exif_data = img._getexif()

                # Convert RGBA to RGB for JPEG output
                if img.mode == "RGBA" and suffix in {".jpg", ".jpeg"}:
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                elif img.mode not in ("RGB", "L", "P"):
                    img = img.convert("RGB")

                # Resize if needed
                original_size = img.size
                if max(img.size) > self.max_dimension:
                    img.thumbnail(
                        (self.max_dimension, self.max_dimension), Image.Resampling.LANCZOS
                    )
                    logger.debug(f"Resized image from {original_size} to {img.size}")

                # Save with appropriate quality
                save_kwargs: dict[str, Any] = {}

                if suffix in {".jpg", ".jpeg"}:
                    save_kwargs["quality"] = self.jpeg_quality
                    save_kwargs["optimize"] = True
                elif suffix == ".png":
                    save_kwargs["optimize"] = True
                elif suffix == ".webp":
                    save_kwargs["quality"] = self.webp_quality
                    save_kwargs["method"] = 6  # Best compression

                # Preserve EXIF if available and requested
                if exif_data and self.preserve_exif:
                    try:
                        # Pillow requires exif bytes, not dict
                        if hasattr(img, "info") and "exif" in img.info:
                            save_kwargs["exif"] = img.info["exif"]
                    except Exception as e:
                        logger.debug(f"Could not preserve EXIF: {e}")

                img.save(str(output), **save_kwargs)
                logger.info(f"Optimized image: {file_path} -> {output}")

            return str(output)

        except Exception as e:
            logger.error(f"Failed to optimize image {file_path}: {e}")
            # Fallback: copy original if output path specified
            if output_path and output_path != file_path:
                import shutil

                shutil.copy(file_path, output_path)
                return output_path
            return file_path

    def generate_webp(self, file_path: str, output_path: str | None = None) -> str | None:
        """
        Generate WebP version of image.

        WebP provides better compression than JPEG/PNG while maintaining quality,
        resulting in faster page loads and better Core Web Vitals scores.

        Args:
            file_path: Path to the source image
            output_path: Path for the WebP image (if None, uses same name with .webp extension)

        Returns:
            Path to the WebP image, or None if conversion failed
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Image file not found: {file_path}")
            return None

        if not self._pillow_available:
            logger.warning("Pillow not installed, cannot generate WebP")
            return None

        from PIL import Image

        # Determine output path
        webp_path = Path(output_path) if output_path else path.with_suffix(".webp")

        try:
            with Image.open(file_path) as img:
                # Convert mode if necessary
                if img.mode == "RGBA":
                    # Preserve transparency in WebP
                    pass
                elif img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                # Resize if needed
                if max(img.size) > self.max_dimension:
                    img.thumbnail(
                        (self.max_dimension, self.max_dimension), Image.Resampling.LANCZOS
                    )

                # Save as WebP
                img.save(
                    str(webp_path),
                    "WEBP",
                    quality=self.webp_quality,
                    method=6,  # Best compression (slower but smaller file)
                )

                # Log size comparison
                original_size = path.stat().st_size
                webp_size = webp_path.stat().st_size
                savings = (1 - webp_size / original_size) * 100 if original_size > 0 else 0
                logger.info(
                    f"Generated WebP: {file_path} -> {webp_path} "
                    f"({original_size / 1024:.1f}KB -> {webp_size / 1024:.1f}KB, {savings:.1f}% savings)"
                )

                return str(webp_path)

        except Exception as e:
            logger.error(f"Failed to generate WebP for {file_path}: {e}")
            return None

    def generate_responsive_sizes(
        self,
        file_path: str,
        sizes: list[int] | None = None,
        output_dir: str | None = None,
    ) -> dict[int, str]:
        """
        Generate multiple sizes for responsive images.

        Args:
            file_path: Path to the source image
            sizes: List of widths to generate (default: [320, 640, 1024, 1920])
            output_dir: Directory for output files (default: same as source)

        Returns:
            Dict mapping width to file path
        """
        if sizes is None:
            sizes = [320, 640, 1024, 1920]

        path = Path(file_path)
        if not path.exists():
            logger.error(f"Image file not found: {file_path}")
            return {}

        if not self._pillow_available:
            logger.warning("Pillow not installed, cannot generate responsive sizes")
            return {}

        from PIL import Image

        output_directory = Path(output_dir) if output_dir else path.parent
        output_directory.mkdir(parents=True, exist_ok=True)

        results: dict[int, str] = {}

        try:
            with Image.open(file_path) as img:
                original_width = img.size[0]

                for width in sizes:
                    if width >= original_width:
                        continue  # Don't upscale

                    # Calculate height maintaining aspect ratio
                    ratio = width / original_width
                    height = int(img.size[1] * ratio)

                    # Create resized copy
                    resized = img.copy()
                    resized.thumbnail((width, height), Image.Resampling.LANCZOS)

                    # Generate filename
                    output_name = f"{path.stem}-{width}w{path.suffix}"
                    output_file = output_directory / output_name

                    # Save with appropriate format
                    save_kwargs: dict[str, Any] = {}
                    if path.suffix.lower() in {".jpg", ".jpeg"}:
                        save_kwargs["quality"] = self.jpeg_quality
                        save_kwargs["optimize"] = True
                    elif path.suffix.lower() == ".webp":
                        save_kwargs["quality"] = self.webp_quality

                    resized.save(str(output_file), **save_kwargs)
                    results[width] = str(output_file)
                    logger.debug(f"Generated {width}w version: {output_file}")

            return results

        except Exception as e:
            logger.error(f"Failed to generate responsive sizes for {file_path}: {e}")
            return results


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
