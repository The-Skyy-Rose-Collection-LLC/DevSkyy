"""
WordPress REST API Client
===========================

Async WordPress REST API client for page, post, and media operations.
Supports Basic Auth via application passwords.

Usage:
    from wordpress.client import WordPressClient

    async with WordPressClient(
        wp_url="https://skyyrose.co",
        username="admin",
        app_password="xxxx xxxx xxxx xxxx",
    ) as client:
        page = await client.create_page(title="New Page", slug="new-page")
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================


class WordPressError(Exception):
    """Base exception for WordPress API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class WordPressAuthError(WordPressError):
    """Authentication failure."""


class WordPressNotFoundError(WordPressError):
    """Resource not found."""


# =============================================================================
# WordPress Client
# =============================================================================


class WordPressClient:
    """
    Async WordPress REST API client.

    Supports the WordPress REST API (v2) with Basic Auth
    via application passwords.

    Can be used as an async context manager:
        async with WordPressClient() as client:
            await client.create_post(title="Hello", content="World")
    """

    def __init__(
        self,
        wp_url: str | None = None,
        username: str | None = None,
        app_password: str | None = None,
        timeout: int = 30,
    ) -> None:
        """
        Initialize WordPress client.

        Args:
            wp_url: WordPress site URL. Falls back to WORDPRESS_URL env var.
            username: Admin username. Falls back to WORDPRESS_USERNAME env var.
            app_password: Application password. Falls back to WORDPRESS_APP_PASSWORD env var.
            timeout: Request timeout in seconds.
        """
        self.wp_url = (wp_url or os.getenv("WORDPRESS_URL", "")).rstrip("/")
        self.username = username or os.getenv("WORDPRESS_USERNAME", "")
        self.app_password = app_password or os.getenv("WORDPRESS_APP_PASSWORD", "")
        self.timeout = timeout
        self._session: Any = None

        # Use index.php?rest_route= for WordPress.com compatibility
        self._api_base = f"{self.wp_url}/index.php?rest_route=/wp/v2"

    async def __aenter__(self) -> WordPressClient:
        """Enter async context manager."""
        try:
            import aiohttp

            auth = None
            if self.username and self.app_password:
                auth = aiohttp.BasicAuth(self.username, self.app_password)

            self._session = aiohttp.ClientSession(
                auth=auth,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )
        except ImportError:
            logger.warning("aiohttp not installed, WordPress client will use mock responses")
            self._session = None
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make an authenticated request to the WordPress REST API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint path (e.g., /posts).
            data: JSON request body.
            **kwargs: Additional request arguments.

        Returns:
            Response data as dictionary.

        Raises:
            WordPressError: On API errors.
            WordPressAuthError: On authentication failures.
            WordPressNotFoundError: On 404 responses.
        """
        url = f"{self._api_base}{endpoint}"

        if self._session is None:
            logger.warning(
                "wordpress_client_no_session",
                extra={"method": method, "endpoint": endpoint},
            )
            return {"id": 0, "status": "mock", "message": "No active session"}

        try:
            async with self._session.request(
                method, url, json=data, **kwargs
            ) as response:
                response_data = await response.json()

                if response.status == 401:
                    raise WordPressAuthError(
                        "Authentication failed",
                        status_code=401,
                        response_data=response_data,
                    )

                if response.status == 404:
                    raise WordPressNotFoundError(
                        f"Resource not found: {endpoint}",
                        status_code=404,
                        response_data=response_data,
                    )

                if response.status >= 400:
                    raise WordPressError(
                        f"API error: {response.status}",
                        status_code=response.status,
                        response_data=response_data,
                    )

                return response_data

        except WordPressError:
            raise
        except Exception as e:
            raise WordPressError(f"Request failed: {e}") from e

    # =========================================================================
    # Posts
    # =========================================================================

    async def create_post(self, **data: Any) -> dict[str, Any]:
        """Create a WordPress post."""
        return await self._request("POST", "/posts", data=data)

    async def update_post(self, post_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Update a WordPress post."""
        return await self._request("PUT", f"/posts/{post_id}", data=data)

    async def delete_post(self, post_id: int) -> dict[str, Any]:
        """Delete a WordPress post (move to trash)."""
        return await self._request("DELETE", f"/posts/{post_id}")

    async def get_post(self, post_id: int) -> dict[str, Any]:
        """Get a WordPress post by ID."""
        return await self._request("GET", f"/posts/{post_id}")

    # =========================================================================
    # Pages
    # =========================================================================

    async def create_page(self, **data: Any) -> dict[str, Any]:
        """Create a WordPress page."""
        return await self._request("POST", "/pages", data=data)

    async def update_page(self, page_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Update a WordPress page."""
        return await self._request("PUT", f"/pages/{page_id}", data=data)

    async def delete_page(self, page_id: int) -> dict[str, Any]:
        """Delete a WordPress page."""
        return await self._request("DELETE", f"/pages/{page_id}")

    # =========================================================================
    # Media
    # =========================================================================

    async def upload_media(
        self,
        file_path: str,
        title: str = "",
        alt_text: str = "",
    ) -> dict[str, Any]:
        """
        Upload a file to the WordPress media library.

        Args:
            file_path: Local path to the file to upload.
            title: Media title.
            alt_text: Alt text for accessibility.

        Returns:
            Uploaded media data including ID and URL.
        """
        path = Path(file_path)
        if not path.exists():
            raise WordPressError(f"File not found: {file_path}")

        if self._session is None:
            return {"id": 0, "source_url": "", "status": "mock"}

        url = f"{self._api_base}/media"

        import aiohttp

        form_data = aiohttp.FormData()
        form_data.add_field(
            "file",
            path.read_bytes(),
            filename=path.name,
            content_type=self._guess_content_type(path),
        )
        if title:
            form_data.add_field("title", title)
        if alt_text:
            form_data.add_field("alt_text", alt_text)

        try:
            async with self._session.post(url, data=form_data) as response:
                result = await response.json()
                if response.status >= 400:
                    raise WordPressError(
                        f"Media upload failed: {response.status}",
                        status_code=response.status,
                        response_data=result,
                    )
                return result
        except WordPressError:
            raise
        except Exception as e:
            raise WordPressError(f"Media upload failed: {e}") from e

    # =========================================================================
    # Post Meta
    # =========================================================================

    async def update_post_meta(
        self,
        post_id: int,
        meta: dict[str, str],
    ) -> dict[str, Any]:
        """
        Update custom meta fields on a post or page.

        Args:
            post_id: WordPress post/page ID.
            meta: Dictionary of meta key-value pairs.

        Returns:
            Updated post data.
        """
        return await self._request(
            "PUT",
            f"/posts/{post_id}",
            data={"meta": meta},
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _guess_content_type(path: Path) -> str:
        """Guess MIME type from file extension."""
        ext_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
            ".glb": "model/gltf-binary",
            ".gltf": "model/gltf+json",
            ".usdz": "model/vnd.usdz+zip",
            ".obj": "text/plain",
            ".mp4": "video/mp4",
            ".pdf": "application/pdf",
        }
        return ext_map.get(path.suffix.lower(), "application/octet-stream")


__all__ = [
    "WordPressClient",
    "WordPressError",
    "WordPressAuthError",
    "WordPressNotFoundError",
]
