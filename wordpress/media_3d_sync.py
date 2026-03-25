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
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import aiohttp
import structlog
from pydantic import BaseModel

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
            wp_url="https://skyyrose.co",
            username="admin",
            app_password="xxxx xxxx xxxx xxxx",
        )

        async with sync:
            # Sync 3D model to product
            result = await sync.sync_3d_model(
                product_id=123,
                glb_url="https://cdn.skyyrose.co/models/product-123.glb",
                usdz_url="https://cdn.skyyrose.co/models/product-123.usdz",
                thumbnail_url="https://cdn.skyyrose.co/thumbnails/product-123.jpg",
            )

            # Enable AR for product
            await sync.enable_ar(product_id=123, enabled=True)

            # Get 3D assets
            assets = await sync.get_3d_assets(product_id=123)

            # Bulk sync multiple products
            products = [
                {
                    "product_id": 123,
                    "glb_url": "https://cdn.skyyrose.co/models/product-123.glb",
                },
                {
                    "product_id": 124,
                    "glb_url": "https://cdn.skyyrose.co/models/product-124.glb",
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
            wp_url: WordPress site URL (e.g., "https://skyyrose.co")
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
        assert self._session is not None, "Session not initialized"
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
            ...     glb_url="https://cdn.skyyrose.co/models/rose-earrings.glb",
            ...     usdz_url="https://cdn.skyyrose.co/models/rose-earrings.usdz",
            ...     thumbnail_url="https://cdn.skyyrose.co/thumbs/rose-earrings.jpg",
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
            result = cast(
                dict[str, Any],
                await self._request(
                    "PUT",
                    f"/products/{product_id}",
                    json={"meta_data": meta_data},
                ),
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
            result = cast(
                dict[str, Any],
                await self._request(
                    "PUT",
                    f"/products/{product_id}",
                    json={
                        "meta_data": [{"key": self.META_AR_ENABLED, "value": str(enabled).lower()}]
                    },
                ),
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
                if product_id is None:
                    return {"status": "error", "error": "Missing product_id", "product_id": None}
                try:
                    result = await self.sync_3d_model(
                        product_id=cast(int, product_id),
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


class QAApprovedModel(BaseModel):
    """Model representing an approved 3D model from the QA queue."""

    model_config = {"protected_namespaces": ()}

    id: str
    product_id: int
    product_name: str
    collection: str
    glb_path: str
    usdz_path: str | None = None
    thumbnail_path: str | None = None
    fidelity_score: float
    approved_at: str
    sku: str | None = None


class WordPress3DPipelineSync:
    """
    Pipeline sync for approved 3D models.

    Bridges the generation pipeline with WordPress/WooCommerce by:
    - Syncing approved models from QA queue
    - Uploading GLB/USDZ files to WordPress media library
    - Updating product meta with 3D URLs
    - Regenerating hotspot configurations

    Usage:
        sync = WordPress3DPipelineSync(
            wp_url="https://skyyrose.co",
            username="admin",
            app_password="xxxx xxxx xxxx xxxx",
            cdn_base_url="https://cdn.skyyrose.co",
        )

        async with sync:
            # Sync all approved models from QA queue
            results = await sync.sync_approved_models()

            # Sync a single approved model
            result = await sync.sync_single_model(model)

            # Regenerate hotspots for collection
            await sync.regenerate_collection_hotspots("black-rose")
    """

    def __init__(
        self,
        wp_url: str,
        username: str,
        app_password: str,
        cdn_base_url: str = "https://cdn.skyyrose.co",
        generated_models_dir: str = "./assets/3d-models-generated",
        hotspots_dir: str = "./wordpress/hotspots",
    ) -> None:
        """
        Initialize pipeline sync.

        Args:
            wp_url: WordPress site URL
            username: WordPress username
            app_password: WordPress application password
            cdn_base_url: Base URL for CDN-hosted 3D models
            generated_models_dir: Directory containing generated GLB files
            hotspots_dir: Directory for hotspot configuration files
        """
        self.media_sync = WordPress3DMediaSync(
            wp_url=wp_url,
            username=username,
            app_password=app_password,
        )
        self.cdn_base_url = cdn_base_url.rstrip("/")
        self.generated_models_dir = Path(generated_models_dir)
        self.hotspots_dir = Path(hotspots_dir)
        self._logger = logger.bind(component="pipeline_sync")

    async def __aenter__(self) -> WordPress3DPipelineSync:
        """Async context manager entry."""
        await self.media_sync.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.media_sync.close()

    async def sync_approved_models(
        self,
        qa_queue_path: str = "./data/qa_queue.json",
    ) -> list[dict[str, Any]]:
        """
        Sync all approved models from QA queue to WordPress.

        Args:
            qa_queue_path: Path to QA queue JSON file

        Returns:
            List of sync results for each model

        Raises:
            WordPress3DSyncError: If sync fails
        """
        self._logger.info("sync_approved_models_start", queue_path=qa_queue_path)

        try:
            # Load QA queue
            queue_path = Path(qa_queue_path)
            if not queue_path.exists():
                self._logger.warning("qa_queue_not_found", path=qa_queue_path)
                return []

            with open(queue_path) as f:
                queue_data = json.load(f)

            # Filter approved models
            approved = [
                QAApprovedModel.model_validate(item)
                for item in queue_data.get("items", [])
                if item.get("status") == "approved"
            ]

            if not approved:
                self._logger.info("no_approved_models")
                return []

            self._logger.info("found_approved_models", count=len(approved))

            # Sync each model
            results = []
            for model in approved:
                result = await self.sync_single_model(model)
                results.append(result)

            # Update QA queue status
            await self._mark_synced_in_queue(queue_path, [m.id for m in approved])

            # Group by collection and regenerate hotspots
            collections = {m.collection for m in approved}
            for collection in collections:
                await self.regenerate_collection_hotspots(collection)

            self._logger.info(
                "sync_approved_models_complete",
                total=len(results),
                success=sum(1 for r in results if r["status"] == "success"),
            )

            return results

        except Exception as e:
            self._logger.error("sync_approved_models_failed", error=str(e))
            raise WordPress3DSyncError(f"Failed to sync approved models: {e}")

    async def sync_single_model(
        self,
        model: QAApprovedModel,
    ) -> dict[str, Any]:
        """
        Sync a single approved model to WordPress.

        Args:
            model: Approved model from QA queue

        Returns:
            Sync result with status and details
        """
        self._logger.info(
            "sync_single_model_start",
            model_id=model.id,
            product_id=model.product_id,
            collection=model.collection,
        )

        try:
            # Build CDN URLs from paths
            glb_url = self._build_cdn_url(model.glb_path)
            usdz_url = self._build_cdn_url(model.usdz_path) if model.usdz_path else None
            thumbnail_url = (
                self._build_cdn_url(model.thumbnail_path) if model.thumbnail_path else None
            )

            # Verify GLB file exists
            glb_path = self.generated_models_dir / model.collection / Path(model.glb_path).name
            if not glb_path.exists():
                self._logger.warning(
                    "glb_file_not_found",
                    path=str(glb_path),
                    model_id=model.id,
                )

            # Sync to WordPress
            result = await self.media_sync.sync_3d_model(
                product_id=model.product_id,
                glb_url=glb_url,
                usdz_url=usdz_url,
                thumbnail_url=thumbnail_url,
            )

            # Enable AR if USDZ available
            if usdz_url:
                await self.media_sync.enable_ar(model.product_id, enabled=True)

            self._logger.info(
                "sync_single_model_success",
                model_id=model.id,
                product_id=model.product_id,
            )

            return {
                "model_id": model.id,
                "product_id": model.product_id,
                "status": "success",
                "glb_url": glb_url,
                "usdz_url": usdz_url,
                "fidelity_score": model.fidelity_score,
            }

        except Exception as e:
            self._logger.error(
                "sync_single_model_failed",
                model_id=model.id,
                error=str(e),
            )
            return {
                "model_id": model.id,
                "product_id": model.product_id,
                "status": "failed",
                "error": str(e),
            }

    def _build_cdn_url(self, path: str) -> str:
        """
        Build CDN URL from local path.

        Args:
            path: Local file path or relative path

        Returns:
            Full CDN URL
        """
        # Extract relative path from full path
        path_obj = Path(path)
        if path_obj.is_absolute():
            # Convert absolute path to relative from generated_models_dir
            try:
                rel_path = path_obj.relative_to(self.generated_models_dir)
            except ValueError:
                rel_path = path_obj.name
        else:
            rel_path = path_obj

        return f"{self.cdn_base_url}/models/{rel_path}"

    async def _mark_synced_in_queue(
        self,
        queue_path: Path,
        model_ids: list[str],
    ) -> None:
        """
        Mark models as synced in QA queue.

        Args:
            queue_path: Path to QA queue JSON
            model_ids: List of model IDs to mark as synced
        """
        try:
            with open(queue_path) as f:
                queue_data = json.load(f)

            # Update status for synced models
            for item in queue_data.get("items", []):
                if item.get("id") in model_ids:
                    item["status"] = "synced"
                    item["synced_at"] = datetime.now().isoformat()

            # Write back
            with open(queue_path, "w") as f:
                json.dump(queue_data, f, indent=2)

            self._logger.info("marked_synced", count=len(model_ids))

        except Exception as e:
            self._logger.warning("mark_synced_failed", error=str(e))

    async def regenerate_collection_hotspots(
        self,
        collection: str,
    ) -> Path | None:
        """
        Regenerate hotspot configuration for a collection.

        Updates hotspot configs with new 3D model URLs for products
        that have been synced.

        Args:
            collection: Collection slug (black-rose, love-hurts, signature)

        Returns:
            Path to updated hotspot config file, or None if failed
        """
        from wordpress.hotspot_config_generator import (
            CollectionType,
            HotspotConfigGenerator,
        )

        self._logger.info("regenerate_hotspots_start", collection=collection)

        try:
            # Map collection slug to enum
            collection_map = {
                "black-rose": CollectionType.BLACK_ROSE,
                "love-hurts": CollectionType.LOVE_HURTS,
                "signature": CollectionType.SIGNATURE,
            }

            if collection not in collection_map:
                self._logger.warning("unknown_collection", collection=collection)
                return None

            collection_type = collection_map[collection]

            # Load existing hotspot config
            hotspot_file = self.hotspots_dir / f"{collection}-hotspots.json"
            if not hotspot_file.exists():
                self._logger.warning(
                    "hotspot_file_not_found",
                    path=str(hotspot_file),
                )
                return None

            with open(hotspot_file) as f:
                hotspot_data = json.load(f)

            # Get 3D assets for all products in collection
            updated_count = 0
            for hotspot in hotspot_data.get("hotspots", []):
                product_id = hotspot.get("product_id")
                if not product_id:
                    continue

                try:
                    assets = await self.media_sync.get_3d_assets(product_id)

                    # Update hotspot with 3D URLs
                    if assets.get("glb_url"):
                        hotspot["glb_url"] = assets["glb_url"]
                        hotspot["usdz_url"] = assets.get("usdz_url")
                        hotspot["ar_enabled"] = assets.get("ar_enabled", False)
                        updated_count += 1

                except Exception as e:
                    self._logger.warning(
                        "hotspot_update_failed",
                        product_id=product_id,
                        error=str(e),
                    )

            # Update timestamp
            hotspot_data["updated_at"] = datetime.now().isoformat()
            hotspot_data["models_count"] = updated_count

            # Write back
            with open(hotspot_file, "w") as f:
                json.dump(hotspot_data, f, indent=2)

            self._logger.info(
                "regenerate_hotspots_complete",
                collection=collection,
                updated=updated_count,
            )

            return hotspot_file

        except Exception as e:
            self._logger.error(
                "regenerate_hotspots_failed",
                collection=collection,
                error=str(e),
            )
            return None

    async def sync_batch_results(
        self,
        batch_id: str,
        results_path: str,
    ) -> dict[str, Any]:
        """
        Sync results from a batch generation job.

        Args:
            batch_id: Batch job ID
            results_path: Path to batch results JSON file

        Returns:
            Summary of sync operation
        """
        self._logger.info(
            "sync_batch_results_start",
            batch_id=batch_id,
            results_path=results_path,
        )

        try:
            # Load batch results
            with open(results_path) as f:
                batch_data = json.load(f)

            # Filter completed results
            completed = [
                r for r in batch_data.get("results", []) if r.get("status") == "completed"
            ]

            if not completed:
                self._logger.info("no_completed_results", batch_id=batch_id)
                return {"batch_id": batch_id, "synced": 0, "status": "empty"}

            # Build sync configs
            products = []
            for result in completed:
                product_id = result.get("product_id")
                glb_path = result.get("glb_path")

                if not product_id or not glb_path:
                    continue

                products.append(
                    {
                        "product_id": product_id,
                        "glb_url": self._build_cdn_url(glb_path),
                        "usdz_url": (
                            self._build_cdn_url(result["usdz_path"])
                            if result.get("usdz_path")
                            else None
                        ),
                        "thumbnail_url": (
                            self._build_cdn_url(result["thumbnail_path"])
                            if result.get("thumbnail_path")
                            else None
                        ),
                    }
                )

            # Bulk sync to WordPress
            results = await self.media_sync.bulk_sync(products)

            success_count = sum(1 for r in results if r["status"] == "success")

            self._logger.info(
                "sync_batch_results_complete",
                batch_id=batch_id,
                total=len(results),
                success=success_count,
            )

            return {
                "batch_id": batch_id,
                "total": len(results),
                "synced": success_count,
                "failed": len(results) - success_count,
                "status": "complete",
            }

        except Exception as e:
            self._logger.error(
                "sync_batch_results_failed",
                batch_id=batch_id,
                error=str(e),
            )
            raise WordPress3DSyncError(f"Failed to sync batch results: {e}")


# =============================================================================
# CLI Entry Point
# =============================================================================


async def main() -> None:
    """CLI entry point for syncing approved models."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="WordPress 3D Media Sync")
    parser.add_argument(
        "--mode",
        choices=["approved", "batch", "cleanup"],
        default="approved",
        help="Sync mode",
    )
    parser.add_argument(
        "--qa-queue",
        default="./data/qa_queue.json",
        help="Path to QA queue JSON",
    )
    parser.add_argument(
        "--batch-id",
        help="Batch ID for batch mode",
    )
    parser.add_argument(
        "--batch-results",
        help="Path to batch results JSON",
    )

    args = parser.parse_args()

    # Load credentials from environment
    wp_url = os.environ.get("WP_URL", "https://skyyrose.co")
    wp_user = os.environ.get("WP_USERNAME", "")
    wp_pass = os.environ.get("WP_APP_PASSWORD", "")
    cdn_url = os.environ.get("CDN_BASE_URL", "https://cdn.skyyrose.co")

    if not wp_user or not wp_pass:
        print("Error: WP_USERNAME and WP_APP_PASSWORD environment variables required")
        return

    sync = WordPress3DPipelineSync(
        wp_url=wp_url,
        username=wp_user,
        app_password=wp_pass,
        cdn_base_url=cdn_url,
    )

    async with sync:
        if args.mode == "approved":
            results = await sync.sync_approved_models(args.qa_queue)
            print(f"Synced {len(results)} models")

        elif args.mode == "batch":
            if not args.batch_id or not args.batch_results:
                print("Error: --batch-id and --batch-results required for batch mode")
                return
            result = await sync.sync_batch_results(args.batch_id, args.batch_results)
            print(f"Batch sync complete: {result}")

        elif args.mode == "cleanup":
            count = await sync.media_sync.cleanup_orphaned_assets()
            print(f"Cleaned up {count} orphaned assets")


if __name__ == "__main__":
    asyncio.run(main())


__all__ = [
    "WordPress3DMediaSync",
    "WordPress3DConfig",
    "WordPress3DSyncError",
    "ProductNotFoundError",
    "InvalidAssetURLError",
    "QAApprovedModel",
    "WordPress3DPipelineSync",
]
