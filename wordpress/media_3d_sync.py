"""
WordPress 3D Media Sync
=======================

Sync 3D assets (GLB/USDZ) with WordPress WooCommerce products.

Custom WooCommerce meta fields:
- _skyyrose_glb_url: WebGL model URL (GLB format)
- _skyyrose_usdz_url: AR model URL (USDZ format for iOS)
- _skyyrose_ar_enabled: Boolean for AR toggle
- _skyyrose_3d_thumbnail: Generated preview image URL

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp
import structlog

logger = structlog.get_logger(__name__)


# =============================================================================
# Exceptions
# =============================================================================


class WordPress3DSyncError(Exception):
    """Base exception for 3D sync operations."""

    def __init__(self, message: str, product_id: int | None = None) -> None:
        super().__init__(message)
        self.product_id = product_id


class ProductNotFoundError(WordPress3DSyncError):
    """Product not found in WooCommerce."""

    pass


class InvalidAssetURLError(WordPress3DSyncError):
    """Invalid 3D asset URL provided."""

    pass


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class WordPress3DConfig:
    """WordPress 3D media sync configuration."""

    wp_url: str
    username: str
    app_password: str
    api_version: str = "wc/v3"
    timeout: float = 30.0
    max_retries: int = 3
    verify_ssl: bool = True

    @property
    def base_url(self) -> str:
        """Get WooCommerce API base URL."""
        return f"{self.wp_url}/wp-json/{self.api_version}"


# =============================================================================
# WordPress 3D Media Sync Client
# =============================================================================


class WordPress3DMediaSync:
    """
    WordPress 3D Media Sync client.

    Manages 3D assets (GLB/USDZ) for WooCommerce products with custom meta fields.

    Usage:
        sync = WordPress3DMediaSync(
            wp_url="https://skyyrose.com",
            username="admin",
            app_password="xxxx xxxx xxxx xxxx",
        )

        async with sync:
            # Sync 3D model to product
            result = await sync.sync_3d_model(
                product_id=123,
                glb_url="https://cdn.skyyrose.com/models/product-123.glb",
                usdz_url="https://cdn.skyyrose.com/models/product-123.usdz",
                thumbnail_url="https://cdn.skyyrose.com/thumbnails/product-123.jpg",
            )

            # Enable AR for product
            await sync.enable_ar(product_id=123, enabled=True)

            # Get 3D assets
            assets = await sync.get_3d_assets(product_id=123)

            # Bulk sync multiple products
            products = [
                {
                    "product_id": 123,
                    "glb_url": "https://cdn.skyyrose.com/models/product-123.glb",
                },
                {
                    "product_id": 124,
                    "glb_url": "https://cdn.skyyrose.com/models/product-124.glb",
                },
            ]
            results = await sync.bulk_sync(products)

            # Cleanup orphaned assets
            count = await sync.cleanup_orphaned_assets()
    """

    # Meta field keys
    META_GLB_URL = "_skyyrose_glb_url"
    META_USDZ_URL = "_skyyrose_usdz_url"
    META_AR_ENABLED = "_skyyrose_ar_enabled"
    META_3D_THUMBNAIL = "_skyyrose_3d_thumbnail"

    def __init__(
        self,
        wp_url: str,
        username: str,
        app_password: str,
        config: WordPress3DConfig | None = None,
    ) -> None:
        """
        Initialize WordPress 3D Media Sync client.

        Args:
            wp_url: WordPress site URL (e.g., "https://skyyrose.com")
            username: WordPress username
            app_password: WordPress application password
            config: Optional configuration override
        """
        self.config = config or WordPress3DConfig(
            wp_url=wp_url,
            username=username,
            app_password=app_password,
        )
        self._session: aiohttp.ClientSession | None = None
        self._logger = logger.bind(wp_url=wp_url)

    async def __aenter__(self) -> WordPress3DMediaSync:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Initialize HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                auth=aiohttp.BasicAuth(
                    self.config.username,
                    self.config.app_password,
                ),
            )
            self._logger.info("connected", username=self.config.username)

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._logger.info("disconnected")

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """
        Make API request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json: JSON body

        Returns:
            Response JSON

        Raises:
            WordPress3DSyncError: On API error
        """
        await self.connect()
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.config.max_retries):
            try:
                async with self._session.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    ssl=self.config.verify_ssl,
                ) as response:
                    # Handle specific status codes
                    if response.status == 404:
                        text = await response.text()
                        raise ProductNotFoundError(
                            f"Product not found: {text}",
                            product_id=None,
                        )

                    if response.status >= 400:
                        text = await response.text()
                        self._logger.error(
                            "api_error",
                            status=response.status,
                            response=text,
                            attempt=attempt + 1,
                        )
                        raise WordPress3DSyncError(f"API error ({response.status}): {text}")

                    return await response.json()

            except aiohttp.ClientError as e:
                self._logger.warning(
                    "request_failed",
                    error=str(e),
                    attempt=attempt + 1,
                    max_retries=self.config.max_retries,
                )
                if attempt == self.config.max_retries - 1:
                    raise WordPress3DSyncError(
                        f"Request failed after {self.config.max_retries} retries: {e}"
                    )
                await asyncio.sleep(2**attempt)  # Exponential backoff

    def _validate_url(self, url: str | None, field_name: str) -> None:
        """
        Validate asset URL.

        Args:
            url: URL to validate
            field_name: Field name for error messages

        Raises:
            InvalidAssetURLError: If URL is invalid
        """
        if not url:
            return

        if not isinstance(url, str):
            raise InvalidAssetURLError(f"{field_name} must be a string")

        if not url.startswith(("http://", "https://")):
            raise InvalidAssetURLError(f"{field_name} must be a valid HTTP(S) URL")

        # Validate file extension for 3D assets
        if field_name == "glb_url" and not url.lower().endswith(".glb"):
            raise InvalidAssetURLError(f"{field_name} must end with .glb")

        if field_name == "usdz_url" and not url.lower().endswith(".usdz"):
            raise InvalidAssetURLError(f"{field_name} must end with .usdz")

    async def sync_3d_model(
        self,
        product_id: int,
        glb_url: str,
        usdz_url: str | None = None,
        thumbnail_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Sync 3D model to WooCommerce product.

        Updates product meta fields with 3D asset URLs.

        Args:
            product_id: WooCommerce product ID
            glb_url: WebGL model URL (GLB format, required)
            usdz_url: AR model URL (USDZ format for iOS, optional)
            thumbnail_url: Generated preview image URL (optional)

        Returns:
            Updated product data with meta fields

        Raises:
            ProductNotFoundError: If product doesn't exist
            InvalidAssetURLError: If URLs are invalid
            WordPress3DSyncError: On sync error

        Example:
            >>> result = await sync.sync_3d_model(
            ...     product_id=123,
            ...     glb_url="https://cdn.skyyrose.com/models/rose-earrings.glb",
            ...     usdz_url="https://cdn.skyyrose.com/models/rose-earrings.usdz",
            ...     thumbnail_url="https://cdn.skyyrose.com/thumbs/rose-earrings.jpg",
            ... )
        """
        # Validate URLs
        self._validate_url(glb_url, "glb_url")
        self._validate_url(usdz_url, "usdz_url")
        self._validate_url(thumbnail_url, "thumbnail_url")

        self._logger.info(
            "sync_3d_model_start",
            product_id=product_id,
            glb_url=glb_url,
            has_usdz=bool(usdz_url),
            has_thumbnail=bool(thumbnail_url),
        )

        # Build meta data
        meta_data = [
            {"key": self.META_GLB_URL, "value": glb_url},
        ]

        if usdz_url:
            meta_data.append({"key": self.META_USDZ_URL, "value": usdz_url})

        if thumbnail_url:
            meta_data.append({"key": self.META_3D_THUMBNAIL, "value": thumbnail_url})

        # Update product
        try:
            result = await self._request(
                "PUT",
                f"/products/{product_id}",
                json={"meta_data": meta_data},
            )

            self._logger.info(
                "sync_3d_model_success",
                product_id=product_id,
                product_name=result.get("name", ""),
            )

            return result

        except ProductNotFoundError:
            self._logger.error("sync_3d_model_not_found", product_id=product_id)
            raise

        except Exception as e:
            self._logger.error(
                "sync_3d_model_failed",
                product_id=product_id,
                error=str(e),
            )
            raise WordPress3DSyncError(
                f"Failed to sync 3D model for product {product_id}: {e}",
                product_id=product_id,
            )

    async def enable_ar(self, product_id: int, enabled: bool = True) -> dict[str, Any]:
        """
        Enable or disable AR for product.

        Args:
            product_id: WooCommerce product ID
            enabled: Whether to enable AR (default: True)

        Returns:
            Updated product data

        Raises:
            ProductNotFoundError: If product doesn't exist
            WordPress3DSyncError: On update error

        Example:
            >>> result = await sync.enable_ar(product_id=123, enabled=True)
        """
        self._logger.info(
            "enable_ar",
            product_id=product_id,
            enabled=enabled,
        )

        try:
            result = await self._request(
                "PUT",
                f"/products/{product_id}",
                json={"meta_data": [{"key": self.META_AR_ENABLED, "value": str(enabled).lower()}]},
            )

            self._logger.info(
                "enable_ar_success",
                product_id=product_id,
                enabled=enabled,
            )

            return result

        except Exception as e:
            self._logger.error(
                "enable_ar_failed",
                product_id=product_id,
                error=str(e),
            )
            raise WordPress3DSyncError(
                f"Failed to enable AR for product {product_id}: {e}",
                product_id=product_id,
            )

    async def get_3d_assets(self, product_id: int) -> dict[str, Any]:
        """
        Get 3D assets for product.

        Args:
            product_id: WooCommerce product ID

        Returns:
            Dictionary with 3D asset URLs and AR status:
            {
                "product_id": 123,
                "product_name": "Rose Earrings",
                "glb_url": "https://...",
                "usdz_url": "https://..." or None,
                "ar_enabled": True/False,
                "thumbnail_url": "https://..." or None,
            }

        Raises:
            ProductNotFoundError: If product doesn't exist
            WordPress3DSyncError: On fetch error

        Example:
            >>> assets = await sync.get_3d_assets(product_id=123)
            >>> print(assets["glb_url"])
        """
        self._logger.info("get_3d_assets", product_id=product_id)

        try:
            product = await self._request("GET", f"/products/{product_id}")

            # Extract meta data
            meta_data = product.get("meta_data", [])
            meta_dict = {item["key"]: item["value"] for item in meta_data}

            assets = {
                "product_id": product_id,
                "product_name": product.get("name", ""),
                "glb_url": meta_dict.get(self.META_GLB_URL),
                "usdz_url": meta_dict.get(self.META_USDZ_URL),
                "ar_enabled": meta_dict.get(self.META_AR_ENABLED, "false").lower() == "true",
                "thumbnail_url": meta_dict.get(self.META_3D_THUMBNAIL),
            }

            self._logger.info(
                "get_3d_assets_success",
                product_id=product_id,
                has_glb=bool(assets["glb_url"]),
                has_usdz=bool(assets["usdz_url"]),
                ar_enabled=assets["ar_enabled"],
            )

            return assets

        except Exception as e:
            self._logger.error(
                "get_3d_assets_failed",
                product_id=product_id,
                error=str(e),
            )
            raise WordPress3DSyncError(
                f"Failed to get 3D assets for product {product_id}: {e}",
                product_id=product_id,
            )

    async def bulk_sync(self, products: list[dict]) -> list[dict]:
        """
        Bulk sync 3D models to multiple products.

        Args:
            products: List of product sync configurations:
                [
                    {
                        "product_id": 123,
                        "glb_url": "https://...",
                        "usdz_url": "https://..." (optional),
                        "thumbnail_url": "https://..." (optional),
                    },
                    ...
                ]

        Returns:
            List of sync results with status:
            [
                {
                    "product_id": 123,
                    "status": "success" or "failed",
                    "error": "error message" (if failed),
                    "data": {...} (if success),
                },
                ...
            ]

        Example:
            >>> products = [
            ...     {"product_id": 123, "glb_url": "https://..."},
            ...     {"product_id": 124, "glb_url": "https://..."},
            ... ]
            >>> results = await sync.bulk_sync(products)
            >>> success_count = sum(1 for r in results if r["status"] == "success")
        """
        self._logger.info("bulk_sync_start", count=len(products))

        results = []

        # Process in parallel with concurrency limit
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

        async def sync_one(product_config: dict) -> dict:
            async with semaphore:
                product_id = product_config.get("product_id")
                try:
                    result = await self.sync_3d_model(
                        product_id=product_id,
                        glb_url=product_config["glb_url"],
                        usdz_url=product_config.get("usdz_url"),
                        thumbnail_url=product_config.get("thumbnail_url"),
                    )
                    return {
                        "product_id": product_id,
                        "status": "success",
                        "data": result,
                    }
                except Exception as e:
                    self._logger.error(
                        "bulk_sync_item_failed",
                        product_id=product_id,
                        error=str(e),
                    )
                    return {
                        "product_id": product_id,
                        "status": "failed",
                        "error": str(e),
                    }

        # Execute all syncs
        tasks = [sync_one(product) for product in products]
        results = await asyncio.gather(*tasks)

        # Log summary
        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = len(results) - success_count

        self._logger.info(
            "bulk_sync_complete",
            total=len(results),
            success=success_count,
            failed=failed_count,
        )

        return results

    async def cleanup_orphaned_assets(self) -> int:
        """
        Cleanup orphaned 3D assets.

        Removes 3D meta fields from products that no longer exist or
        have invalid/unreachable asset URLs.

        Returns:
            Number of products cleaned up

        Example:
            >>> count = await sync.cleanup_orphaned_assets()
            >>> print(f"Cleaned up {count} products")
        """
        self._logger.info("cleanup_orphaned_assets_start")

        cleaned_count = 0

        try:
            # Get all products (paginated)
            page = 1
            per_page = 100

            while True:
                products = await self._request(
                    "GET",
                    "/products",
                    params={"per_page": per_page, "page": page},
                )

                if not products:
                    break

                for product in products:
                    product_id = product["id"]
                    meta_data = product.get("meta_data", [])

                    # Find 3D meta fields
                    has_3d_meta = any(
                        item["key"]
                        in {
                            self.META_GLB_URL,
                            self.META_USDZ_URL,
                            self.META_AR_ENABLED,
                            self.META_3D_THUMBNAIL,
                        }
                        for item in meta_data
                    )

                    if not has_3d_meta:
                        continue

                    # Check if GLB URL is valid
                    glb_url = next(
                        (item["value"] for item in meta_data if item["key"] == self.META_GLB_URL),
                        None,
                    )

                    if not glb_url:
                        # Remove all 3D meta if no GLB URL
                        try:
                            await self._remove_3d_meta(product_id)
                            cleaned_count += 1
                            self._logger.info(
                                "cleanup_removed_meta",
                                product_id=product_id,
                                reason="no_glb_url",
                            )
                        except Exception as e:
                            self._logger.error(
                                "cleanup_failed",
                                product_id=product_id,
                                error=str(e),
                            )

                page += 1

        except Exception as e:
            self._logger.error("cleanup_orphaned_assets_failed", error=str(e))
            raise WordPress3DSyncError(f"Failed to cleanup orphaned assets: {e}")

        self._logger.info("cleanup_orphaned_assets_complete", count=cleaned_count)

        return cleaned_count

    async def _remove_3d_meta(self, product_id: int) -> None:
        """
        Remove all 3D meta fields from product.

        Args:
            product_id: WooCommerce product ID
        """
        meta_data = [
            {"key": self.META_GLB_URL, "value": None},
            {"key": self.META_USDZ_URL, "value": None},
            {"key": self.META_AR_ENABLED, "value": None},
            {"key": self.META_3D_THUMBNAIL, "value": None},
        ]

        await self._request(
            "PUT",
            f"/products/{product_id}",
            json={"meta_data": meta_data},
        )


__all__ = [
    "WordPress3DMediaSync",
    "WordPress3DConfig",
    "WordPress3DSyncError",
    "ProductNotFoundError",
    "InvalidAssetURLError",
]
