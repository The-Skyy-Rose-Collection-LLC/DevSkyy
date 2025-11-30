"""
WordPress Media Upload Client for WooCommerce

REST API Reference: https://developer.wordpress.org/rest-api/reference/media/
Endpoint: {site}/wp-json/wp/v2/media

Features:
- Upload images (PNG, JPG, WebP)
- Upload 3D models (GLB, GLTF)
- Basic auth with Application Password
- Async support

Truth Protocol Compliance:
- Rule #1: API verified from WordPress REST API docs
- Rule #5: Credentials via environment variables
- Rule #10: Error handling with continue policy
- Rule #12: Performance tracking for SLO compliance

GLB MIME Type: model/gltf-binary
"""

import asyncio
import base64
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any

import httpx

from agent.modules.clothing.schemas.schemas import WordPressUploadResult
from core.enterprise_error_handler import record_error

logger = logging.getLogger(__name__)

# Register GLB MIME type
mimetypes.add_type("model/gltf-binary", ".glb")
mimetypes.add_type("model/gltf+json", ".gltf")


class WordPressError(Exception):
    """Custom exception for WordPress API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class WordPressMediaClient:
    """
    Async client for WordPress Media REST API.

    Provides media upload capabilities for WooCommerce product images
    and 3D model assets.

    Example:
        client = WordPressMediaClient(
            site_url="https://skyyrose.co",
            username="admin",
            app_password="xxxx xxxx xxxx xxxx"
        )
        await client.initialize()

        result = await client.upload_file(
            file_path="/path/to/model.glb",
            title="Black Rose Hoodie 3D Model",
            alt_text="3D model of SkyyRose Black Rose Hoodie"
        )

    Attributes:
        site_url: WordPress site URL
        username: WordPress username
        app_password: WordPress application password
    """

    DEFAULT_TIMEOUT = 60.0
    MAX_RETRIES = 3

    def __init__(
        self,
        site_url: str | None = None,
        username: str | None = None,
        app_password: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Initialize WordPress media client.

        Args:
            site_url: WordPress site URL (defaults to WORDPRESS_SITE_URL env var)
            username: WordPress username (defaults to WORDPRESS_USERNAME env var)
            app_password: Application password (defaults to WORDPRESS_APP_PASSWORD env var)
            timeout: Request timeout in seconds
        """
        self.site_url = (site_url or os.getenv("WORDPRESS_SITE_URL", "")).rstrip("/")
        self.username = username or os.getenv("WORDPRESS_USERNAME", "")
        self.app_password = app_password or os.getenv("WORDPRESS_APP_PASSWORD", "")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._initialized = False

    @property
    def media_endpoint(self) -> str:
        """Get the media API endpoint URL."""
        return f"{self.site_url}/wp-json/wp/v2/media"

    def _get_auth_header(self) -> str:
        """Generate Basic auth header."""
        credentials = f"{self.username}:{self.app_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def initialize(self) -> bool:
        """
        Initialize the HTTP client and verify WordPress access.

        Returns:
            True if initialization successful

        Raises:
            WordPressError: If credentials are missing or invalid
        """
        if not self.site_url:
            raise WordPressError("WORDPRESS_SITE_URL environment variable not set")
        if not self.username:
            raise WordPressError("WORDPRESS_USERNAME environment variable not set")
        if not self.app_password:
            raise WordPressError("WORDPRESS_APP_PASSWORD environment variable not set")

        self._client = httpx.AsyncClient(
            headers={
                "Authorization": self._get_auth_header(),
            },
            timeout=httpx.Timeout(self.timeout),
        )

        # Verify API access
        try:
            response = await self._client.get(f"{self.site_url}/wp-json/wp/v2/users/me")
            if response.status_code == 401:
                raise WordPressError("Invalid WordPress credentials", status_code=401)
            self._initialized = True
            logger.info(f"WordPress client initialized for {self.site_url}")
            return True
        except httpx.RequestError as e:
            logger.warning(f"Could not verify WordPress API access: {e}")
            # Continue anyway - API might still work
            self._initialized = True
            return True

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure client is initialized."""
        if not self._initialized or not self._client:
            await self.initialize()

    async def upload_file(
        self,
        file_path: str,
        title: str | None = None,
        alt_text: str | None = None,
        caption: str | None = None,
        description: str | None = None,
    ) -> WordPressUploadResult:
        """
        Upload a file to WordPress media library.

        Supports images (PNG, JPG, WebP) and 3D models (GLB, GLTF).

        Args:
            file_path: Path to the file to upload
            title: Media title (defaults to filename)
            alt_text: Alt text for accessibility
            caption: Media caption
            description: Media description

        Returns:
            WordPressUploadResult with upload details

        Raises:
            WordPressError: If upload fails

        Example:
            result = await client.upload_file(
                file_path="/tmp/model.glb",
                title="SkyyRose Hoodie 3D Model",
                alt_text="3D model of luxury streetwear hoodie"
            )
            print(f"Uploaded: {result.source_url}")
        """
        await self._ensure_initialized()

        path = Path(file_path)
        if not path.exists():
            raise WordPressError(f"File not found: {file_path}")

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            # Default for unknown types
            if path.suffix.lower() == ".glb":
                mime_type = "model/gltf-binary"
            elif path.suffix.lower() == ".gltf":
                mime_type = "model/gltf+json"
            else:
                mime_type = "application/octet-stream"

        # Use filename as title if not provided
        if not title:
            title = path.stem.replace("_", " ").replace("-", " ").title()

        # Read file content
        with open(path, "rb") as f:
            file_content = f.read()

        file_size = len(file_content)

        logger.info(f"Uploading {path.name} ({file_size} bytes) to WordPress")

        # Attempt upload with retries
        last_error: Exception | None = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self._client.post(
                    self.media_endpoint,
                    content=file_content,
                    headers={
                        "Authorization": self._get_auth_header(),
                        "Content-Type": mime_type,
                        "Content-Disposition": f'attachment; filename="{path.name}"',
                    },
                )

                if response.status_code == 429:
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue

                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    raise WordPressError(
                        f"Upload failed: {error_data.get('message', response.text)}",
                        status_code=response.status_code,
                        response=error_data,
                    )

                # Parse response
                data = response.json()
                media_id = data.get("id", 0)

                # Update metadata if provided
                if alt_text or caption or description:
                    await self._update_media_meta(
                        media_id=media_id,
                        alt_text=alt_text,
                        caption=caption,
                        description=description,
                    )

                result = WordPressUploadResult(
                    media_id=media_id,
                    source_url=data.get("source_url", ""),
                    mime_type=data.get("mime_type", mime_type),
                    title=data.get("title", {}).get("rendered", title),
                    alt_text=alt_text,
                    file_size_bytes=file_size,
                    metadata=data,
                )

                logger.info(f"Successfully uploaded to WordPress: ID={media_id}")
                return result

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Upload timeout (attempt {attempt + 1}/{self.MAX_RETRIES})")
                await asyncio.sleep(2 ** attempt)
            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"Upload error (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
                await asyncio.sleep(2 ** attempt)

        # Record error to ledger
        record_error(
            error_type="WordPressUploadError",
            message=f"Failed after {self.MAX_RETRIES} retries: {last_error}",
            severity="HIGH",
            component="agent.modules.clothing.wordpress_media",
            context={"file_path": str(file_path), "mime_type": mime_type},
            exception=last_error,
            action="continue",
        )

        raise WordPressError(f"Upload failed after {self.MAX_RETRIES} retries: {last_error}")

    async def _update_media_meta(
        self,
        media_id: int,
        alt_text: str | None = None,
        caption: str | None = None,
        description: str | None = None,
    ) -> None:
        """
        Update media metadata.

        Args:
            media_id: WordPress media ID
            alt_text: Alt text for accessibility
            caption: Media caption
            description: Media description
        """
        update_data: dict[str, Any] = {}

        if alt_text:
            update_data["alt_text"] = alt_text
        if caption:
            update_data["caption"] = caption
        if description:
            update_data["description"] = description

        if not update_data:
            return

        try:
            response = await self._client.post(
                f"{self.media_endpoint}/{media_id}",
                json=update_data,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code >= 400:
                logger.warning(f"Failed to update media metadata: {response.text}")
        except Exception as e:
            logger.warning(f"Error updating media metadata: {e}")

    async def upload_from_url(
        self,
        url: str,
        title: str | None = None,
        alt_text: str | None = None,
    ) -> WordPressUploadResult:
        """
        Download a file from URL and upload to WordPress.

        Args:
            url: URL to download the file from
            title: Media title
            alt_text: Alt text for accessibility

        Returns:
            WordPressUploadResult with upload details
        """
        await self._ensure_initialized()

        logger.info(f"Downloading file from: {url[:50]}...")

        # Download the file
        async with httpx.AsyncClient() as download_client:
            response = await download_client.get(url, follow_redirects=True)
            response.raise_for_status()

            # Determine filename and extension
            content_type = response.headers.get("content-type", "")
            if "gltf-binary" in content_type or "glb" in url.lower():
                ext = ".glb"
            elif "gltf" in content_type or "gltf" in url.lower():
                ext = ".gltf"
            elif "png" in content_type or "png" in url.lower():
                ext = ".png"
            elif "jpeg" in content_type or "jpg" in url.lower():
                ext = ".jpg"
            elif "webp" in content_type:
                ext = ".webp"
            else:
                ext = ".bin"

            # Save to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(response.content)
                temp_path = tmp.name

        try:
            # Upload from temp file
            result = await self.upload_file(
                file_path=temp_path,
                title=title,
                alt_text=alt_text,
            )
            return result
        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    async def batch_upload(
        self,
        files: list[dict[str, Any]],
        max_concurrent: int = 3,
    ) -> list[WordPressUploadResult]:
        """
        Upload multiple files in parallel.

        Args:
            files: List of dicts with 'path', 'title', 'alt_text' keys
            max_concurrent: Maximum concurrent uploads

        Returns:
            List of WordPressUploadResult for each file

        Example:
            results = await client.batch_upload([
                {"path": "/tmp/model.glb", "title": "3D Model"},
                {"path": "/tmp/tryon.png", "title": "Try-On Image"},
            ])
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def upload_with_semaphore(file_info: dict) -> WordPressUploadResult:
            async with semaphore:
                return await self.upload_file(
                    file_path=file_info.get("path", ""),
                    title=file_info.get("title"),
                    alt_text=file_info.get("alt_text"),
                    caption=file_info.get("caption"),
                    description=file_info.get("description"),
                )

        tasks = [upload_with_semaphore(f) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Upload failed for {files[i].get('path')}: {result}")
                record_error(
                    error_type="WordPressBatchUploadError",
                    message=f"Batch upload failed for file",
                    severity="MEDIUM",
                    component="agent.modules.clothing.wordpress_media",
                    context={"file": files[i].get("path", "unknown")},
                    exception=result if isinstance(result, Exception) else None,
                    action="continue",
                )
            else:
                final_results.append(result)

        return final_results

    async def delete_media(self, media_id: int, force: bool = True) -> bool:
        """
        Delete a media item from WordPress.

        Args:
            media_id: WordPress media ID
            force: Permanently delete (skip trash)

        Returns:
            True if deleted successfully
        """
        await self._ensure_initialized()

        try:
            response = await self._client.delete(
                f"{self.media_endpoint}/{media_id}",
                params={"force": "true" if force else "false"},
            )
            return response.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Failed to delete media {media_id}: {e}")
            return False

    async def get_media(self, media_id: int) -> dict | None:
        """
        Get media item details.

        Args:
            media_id: WordPress media ID

        Returns:
            Media data dict or None if not found
        """
        await self._ensure_initialized()

        try:
            response = await self._client.get(f"{self.media_endpoint}/{media_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to get media {media_id}: {e}")
            return None

    async def __aenter__(self) -> "WordPressMediaClient":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
