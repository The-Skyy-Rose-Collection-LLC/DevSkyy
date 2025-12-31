"""
WordPress REST API Client
=========================

Core client for WordPress REST API v2.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class WordPressError(Exception):
    """Base WordPress error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(WordPressError):
    """Authentication failed."""

    pass


class NotFoundError(WordPressError):
    """Resource not found."""

    pass


@dataclass
class WordPressConfig:
    """WordPress API configuration."""

    site_url: str = field(
        default_factory=lambda: os.getenv("WORDPRESS_URL", os.getenv("WP_SITE_URL", ""))
    )
    username: str = field(
        default_factory=lambda: os.getenv("WORDPRESS_USERNAME", os.getenv("WP_USERNAME", ""))
    )
    app_password: str = field(
        default_factory=lambda: os.getenv("WORDPRESS_APP_PASSWORD", os.getenv("WP_APP_PASSWORD", ""))
    )
    api_version: str = "wp/v2"
    timeout: float = 30.0
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> WordPressConfig:
        return cls()

    @property
    def base_url(self) -> str:
        return f"{self.site_url}/wp-json/{self.api_version}"


class WordPressClient:
    """WordPress REST API Client."""

    def __init__(self, config: WordPressConfig | None = None) -> None:
        self.config = config or WordPressConfig.from_env()
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> WordPressClient:
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def connect(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                auth=aiohttp.BasicAuth(self.config.username, self.config.app_password),
            )

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        await self.connect()
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.config.max_retries):
            try:
                async with self._session.request(
                    method, url, params=params, json=json, data=data, headers=headers
                ) as response:
                    if response.status == 401:
                        raise AuthenticationError("Authentication failed", 401)
                    if response.status == 404:
                        raise NotFoundError("Resource not found", 404)
                    if response.status >= 400:
                        text = await response.text()
                        raise WordPressError(text, response.status)
                    if response.status == 204:
                        return {}
                    return await response.json()
            except aiohttp.ClientError as e:
                if attempt == self.config.max_retries - 1:
                    raise WordPressError(str(e))
                await asyncio.sleep(1)

    # Posts
    async def get_posts(self, per_page: int = 10, **kwargs: Any) -> list[dict[str, Any]]:
        return await self._request("GET", "/posts", params={"per_page": per_page, **kwargs})

    async def create_post(
        self, title: str, content: str = "", status: str = "draft", **kwargs: Any
    ) -> dict[str, Any]:
        return await self._request(
            "POST", "/posts", json={"title": title, "content": content, "status": status, **kwargs}
        )

    async def update_post(self, post_id: int, **kwargs: Any) -> dict[str, Any]:
        return await self._request("POST", f"/posts/{post_id}", json=kwargs)

    async def delete_post(self, post_id: int, force: bool = False) -> dict[str, Any]:
        return await self._request("DELETE", f"/posts/{post_id}", params={"force": force})

    # Pages
    async def get_pages(self, per_page: int = 10, **kwargs: Any) -> list[dict[str, Any]]:
        return await self._request("GET", "/pages", params={"per_page": per_page, **kwargs})

    async def create_page(
        self, title: str, content: str = "", status: str = "draft", **kwargs: Any
    ) -> dict[str, Any]:
        return await self._request(
            "POST", "/pages", json={"title": title, "content": content, "status": status, **kwargs}
        )

    async def update_page(self, page_id: int, **kwargs: Any) -> dict[str, Any]:
        return await self._request("POST", f"/pages/{page_id}", json=kwargs)

    # Media
    async def get_media(self, per_page: int = 10, **kwargs: Any) -> list[dict[str, Any]]:
        return await self._request("GET", "/media", params={"per_page": per_page, **kwargs})

    async def upload_media(self, file_path: str, title: str = "") -> dict[str, Any]:
        import mimetypes
        from pathlib import Path

        import aiofiles

        path = Path(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        async with aiofiles.open(file_path, "rb") as f:
            file_data = await f.read()

        headers = {
            "Content-Disposition": f'attachment; filename="{path.name}"',
            "Content-Type": content_type,
        }
        result = await self._request("POST", "/media", data=file_data, headers=headers)

        if title:
            result = await self._request("POST", f"/media/{result['id']}", json={"title": title})

        return result


__all__ = [
    "WordPressClient",
    "WordPressConfig",
    "WordPressError",
    "AuthenticationError",
    "NotFoundError",
]
