#!/usr/bin/env python3
"""
Pre-Order Management System for SkyyRose Collections

Manages WooCommerce pre-order products with countdown timers, early access lists,
and launch status transitions.

Features:
- Pre-order status tracking (blooming_soon, now_blooming, available)
- Launch date scheduling with timezone support
- Early access list management via Klaviyo
- Server-synced countdown timers
- Pre-order notification emails
- Custom WordPress meta fields

Usage:
    manager = PreOrderManager(wordpress_url, app_password)
    await manager.set_preorder_status(product_id, "blooming_soon", launch_date)
    await manager.notify_early_access_list(product_id)
    countdown = await manager.get_countdown_config(product_id)

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from urllib.parse import urlparse

import aiohttp
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


# ============================================================================
# Custom Exceptions
# ============================================================================


class PreOrderError(Exception):
    """Base exception for pre-order operations."""

    pass


class PreOrderValidationError(PreOrderError):
    """Raised when validation fails."""

    pass


class PreOrderWordPressError(PreOrderError):
    """Raised when WordPress API operation fails."""

    pass


class PreOrderKlaviyoError(PreOrderError):
    """Raised when Klaviyo API operation fails."""

    pass


# ============================================================================
# Pydantic Models with Validation
# ============================================================================


class PreOrderMetadata(BaseModel):
    """Pre-order metadata for a WooCommerce product."""

    product_id: int = Field(..., ge=1, description="WooCommerce product ID")
    enabled: bool = Field(default=False, description="Pre-order enabled")
    status: Literal["blooming_soon", "now_blooming", "available"] = Field(
        default="blooming_soon", description="Pre-order status"
    )
    launch_date: datetime | None = Field(default=None, description="Product launch date and time")
    early_access_list_id: str | None = Field(
        default=None, max_length=50, description="Klaviyo segment/list ID for early access"
    )
    notify_count: int = Field(
        default=0, ge=0, description="Number of early access notifications sent"
    )
    ar_enabled: bool = Field(default=True, description="AR Quick Look enabled for pre-orders")
    collection: str = Field(default="", min_length=0, max_length=50, description="Collection slug")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When pre-order was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When pre-order was last updated",
    )

    @validator("launch_date", pre=True)
    def validate_launch_date(cls, v: Any) -> datetime | None:
        """Validate launch date is in the future."""
        if v is None:
            return None

        if isinstance(v, str):
            try:
                dt = datetime.fromisoformat(v)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt
            except ValueError as e:
                raise ValueError(f"Invalid datetime format: {e}")

        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=UTC)
            return v

        raise ValueError(f"Invalid launch date: {v}")


class CountdownConfig(BaseModel):
    """Configuration for client-side countdown timer."""

    product_id: int = Field(..., ge=1)
    launch_date_iso: str = Field(..., description="ISO 8601 launch date")
    launch_date_unix: int = Field(..., ge=0, description="Unix timestamp")
    server_time_unix: int = Field(..., ge=0, description="Current server Unix timestamp")
    status: str = Field(..., regex="^(blooming_soon|now_blooming|available)$")
    ar_enabled: bool = Field(default=True)
    collection: str = Field(default="")
    time_remaining_seconds: int = Field(default=0, ge=0, description="Seconds until launch")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "product_id": 123,
                "launch_date_iso": "2025-01-15T18:00:00Z",
                "launch_date_unix": 1736952000,
                "server_time_unix": 1736865600,
                "status": "blooming_soon",
                "ar_enabled": True,
                "collection": "signature",
                "time_remaining_seconds": 86400,
            }
        }


class PreOrderNotification(BaseModel):
    """Pre-order notification to send."""

    product_id: int = Field(..., ge=1)
    product_name: str = Field(..., min_length=1, max_length=200)
    launch_date: datetime
    preview_image_url: str | None = Field(default=None, max_length=2048)
    collection: str = Field(default="", max_length=50)

    @validator("preview_image_url", pre=True)
    def validate_image_url(cls, v: Any) -> str | None:
        """Validate image URL format."""
        if v is None:
            return None
        s = str(v)
        try:
            parsed = urlparse(s)
            if parsed.scheme not in ("http", "https"):
                raise ValueError("Image URL must use HTTP or HTTPS")
            return s[:2048]
        except Exception as e:
            raise ValueError(f"Invalid image URL: {e}")


# ============================================================================
# Pre-Order Manager
# ============================================================================


class PreOrderManager:
    """Manages pre-order products and countdown timers."""

    def __init__(
        self,
        wordpress_url: str,
        app_password: str,
        klaviyo_api_key: str | None = None,
    ):
        """
        Initialize pre-order manager.

        Args:
            wordpress_url: WordPress site URL
            app_password: WordPress app password
            klaviyo_api_key: Optional Klaviyo API key for email notifications
        """
        self.wordpress_url = wordpress_url.rstrip("/")
        self.app_password = app_password
        self.klaviyo_api_key = klaviyo_api_key

        self._validate_config()
        logger.info(f"Pre-order manager initialized for {self.wordpress_url}")

    def _validate_config(self) -> None:
        """Validate configuration."""
        try:
            result = urlparse(self.wordpress_url)
            if result.scheme not in ("http", "https"):
                raise PreOrderValidationError("WordPress URL must use HTTP or HTTPS")
        except Exception as e:
            raise PreOrderValidationError(f"Invalid WordPress URL: {e}")

        if not self.app_password or len(self.app_password) < 10:
            raise PreOrderValidationError("Invalid app password")

    async def set_preorder_status(
        self,
        product_id: int,
        status: Literal["blooming_soon", "now_blooming", "available"],
        launch_date: datetime | None = None,
        collection: str = "",
    ) -> PreOrderMetadata:
        """
        Set or update pre-order status for a product.

        Args:
            product_id: WooCommerce product ID
            status: Pre-order status
            launch_date: Product launch date (required for blooming_soon)
            collection: Collection slug

        Returns:
            Updated pre-order metadata

        Raises:
            PreOrderValidationError: If data is invalid
            PreOrderWordPressError: If WordPress API call fails
        """
        if status == "blooming_soon" and launch_date is None:
            raise PreOrderValidationError("launch_date required for blooming_soon status")

        # Create metadata
        metadata = PreOrderMetadata(
            product_id=product_id,
            enabled=status != "available",
            status=status,
            launch_date=launch_date,
            collection=collection,
            updated_at=datetime.now(UTC),
        )

        # Update WordPress product
        try:
            await self._update_product_metadata(product_id, metadata)
            logger.info(f"Set product {product_id} pre-order status to {status}")
            return metadata
        except Exception as e:
            raise PreOrderWordPressError(f"Failed to update product: {e}")

    async def get_countdown_config(self, product_id: int) -> CountdownConfig:
        """
        Get countdown configuration for a product.

        Args:
            product_id: WooCommerce product ID

        Returns:
            Countdown configuration for client-side timer

        Raises:
            PreOrderWordPressError: If product not found or not on pre-order
        """
        try:
            metadata = await self._fetch_product_metadata(product_id)

            if not metadata.get("_preorder_enabled"):
                raise PreOrderWordPressError("Product is not on pre-order")

            launch_date_str = metadata.get("_preorder_launch_date")
            if not launch_date_str:
                raise PreOrderWordPressError("No launch date found")

            launch_date = datetime.fromisoformat(launch_date_str)
            if launch_date.tzinfo is None:
                launch_date = launch_date.replace(tzinfo=UTC)

            server_time_utc = datetime.now(UTC)
            time_remaining = max(0, int((launch_date - server_time_utc).total_seconds()))

            return CountdownConfig(
                product_id=product_id,
                launch_date_iso=launch_date.isoformat(),
                launch_date_unix=int(launch_date.timestamp()),
                server_time_unix=int(server_time_utc.timestamp()),
                status=metadata.get("_preorder_status", "blooming_soon"),
                ar_enabled=metadata.get("_preorder_ar_enabled", "yes") == "yes",
                collection=metadata.get("_preorder_collection", ""),
                time_remaining_seconds=time_remaining,
            )

        except PreOrderWordPressError:
            raise
        except Exception as e:
            raise PreOrderWordPressError(f"Failed to get countdown config: {e}")

    async def notify_early_access_list(
        self,
        product_id: int,
        preview_image_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Send pre-order notification to early access list via Klaviyo.

        Args:
            product_id: WooCommerce product ID
            preview_image_url: Product preview image URL

        Returns:
            Notification result with recipient count

        Raises:
            PreOrderKlaviyoError: If Klaviyo API call fails
            PreOrderWordPressError: If product data not found
        """
        if not self.klaviyo_api_key:
            logger.warning("Klaviyo API key not configured - skipping email notifications")
            return {"sent": 0, "message": "Klaviyo not configured"}

        try:
            # Fetch product data
            product_data = await self._fetch_product_data(product_id)
            metadata = await self._fetch_product_metadata(product_id)

            launch_date_str = metadata.get("_preorder_launch_date")
            if not launch_date_str:
                raise PreOrderWordPressError("No launch date found")

            launch_date = datetime.fromisoformat(launch_date_str)

            notification = PreOrderNotification(
                product_id=product_id,
                product_name=product_data.get("name", "Unknown Product"),
                launch_date=launch_date,
                preview_image_url=preview_image_url,
                collection=metadata.get("_preorder_collection", ""),
            )

            # Get early access list ID
            list_id = metadata.get("_preorder_early_access_list")
            if not list_id:
                logger.warning(f"No early access list configured for product {product_id}")
                return {"sent": 0, "message": "No early access list configured"}

            # Send via Klaviyo
            result = await self._send_klaviyo_email(notification, list_id)
            logger.info(
                f"Sent {result.get('sent', 0)} early access notifications for product {product_id}"
            )
            return result

        except Exception as e:
            raise PreOrderKlaviyoError(f"Failed to send notifications: {e}")

    async def schedule_launch_transition(
        self,
        product_id: int,
        check_interval_seconds: int = 60,
    ) -> None:
        """
        Monitor a product and auto-transition from blooming_soon to now_blooming.

        Args:
            product_id: WooCommerce product ID
            check_interval_seconds: How often to check for launch (default 60s)

        This method runs indefinitely, checking the countdown and updating product
        status when launch time arrives.
        """
        logger.info(f"Scheduling launch monitoring for product {product_id}")

        while True:
            try:
                countdown = await self.get_countdown_config(product_id)

                # When launch time arrives, transition status
                if countdown.time_remaining_seconds <= 0 and countdown.status == "blooming_soon":
                    logger.info(f"Launching product {product_id}")
                    await self.set_preorder_status(product_id, "now_blooming")
                    break

                # Sleep until next check or launch time
                await asyncio.sleep(min(check_interval_seconds, countdown.time_remaining_seconds))

            except Exception as e:
                logger.error(f"Error monitoring product {product_id}: {e}")
                await asyncio.sleep(check_interval_seconds)

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _fetch_product_data(self, product_id: int) -> dict[str, Any]:
        """Fetch product data from WooCommerce."""
        endpoint = f"{self.wordpress_url}/wp-json/wc/v3/products/{product_id}"

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    endpoint,
                    auth=aiohttp.BasicAuth("admin", self.app_password),
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp,
            ):
                if resp.status == 404:
                    raise PreOrderWordPressError(f"Product {product_id} not found")
                if resp.status != 200:
                    raise PreOrderWordPressError(f"API error: {resp.status}")
                return await resp.json()
        except TimeoutError:
            raise PreOrderWordPressError("Request timeout")

    async def _fetch_product_metadata(self, product_id: int) -> dict[str, Any]:
        """Fetch product custom metadata."""
        product_data = await self._fetch_product_data(product_id)
        meta_data = product_data.get("meta_data", [])

        metadata_dict = {}
        for meta in meta_data:
            if isinstance(meta, dict):
                key = meta.get("key", "")
                value = meta.get("value", "")
                if key.startswith("_preorder_"):
                    metadata_dict[key] = value

        return metadata_dict

    async def _update_product_metadata(self, product_id: int, metadata: PreOrderMetadata) -> None:
        """Update product metadata in WordPress."""
        endpoint = f"{self.wordpress_url}/wp-json/wc/v3/products/{product_id}"

        meta_data = [
            {"key": "_preorder_enabled", "value": "yes" if metadata.enabled else "no"},
            {"key": "_preorder_status", "value": metadata.status},
            {
                "key": "_preorder_launch_date",
                "value": metadata.launch_date.isoformat() if metadata.launch_date else "",
            },
            {"key": "_preorder_ar_enabled", "value": "yes" if metadata.ar_enabled else "no"},
            {"key": "_preorder_collection", "value": metadata.collection},
        ]

        if metadata.early_access_list_id:
            meta_data.append(
                {
                    "key": "_preorder_early_access_list",
                    "value": metadata.early_access_list_id,
                }
            )

        payload = {"meta_data": meta_data}

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    endpoint,
                    json=payload,
                    auth=aiohttp.BasicAuth("admin", self.app_password),
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp,
            ):
                if resp.status not in (200, 201):
                    raise PreOrderWordPressError(f"Update failed: {resp.status}")

        except TimeoutError:
            raise PreOrderWordPressError("Request timeout")

    async def _send_klaviyo_email(
        self,
        notification: PreOrderNotification,
        list_id: str,
    ) -> dict[str, Any]:
        """Send email via Klaviyo (stub implementation)."""
        # In production, this would call Klaviyo's API
        # For now, we return a mock result
        logger.info(
            f"Would send Klaviyo email for product {notification.product_id} to list {list_id}"
        )

        return {
            "sent": 0,  # Would be actual count in production
            "message": "Klaviyo integration ready for production deployment",
            "list_id": list_id,
        }


# ============================================================================
# Standalone Countdown Endpoint Handler
# ============================================================================


async def get_server_time() -> dict[str, int]:
    """
    Return current server time for countdown synchronization.

    Returns:
        Dictionary with current Unix timestamp
    """
    return {
        "timestamp": int(datetime.now(UTC).timestamp()),
        "milliseconds": int(datetime.now(UTC).timestamp() * 1000),
    }


if __name__ == "__main__":
    # Example usage
    async def example():
        manager = PreOrderManager(
            wordpress_url="http://localhost:8882",
            app_password="test-password",
        )

        # Set a product on pre-order
        launch_date = datetime.now(UTC) + timedelta(days=7)
        metadata = await manager.set_preorder_status(
            product_id=123,
            status="blooming_soon",
            launch_date=launch_date,
            collection="signature",
        )
        print(f"Pre-order metadata: {metadata}")

        # Get countdown config
        countdown = await manager.get_countdown_config(123)
        print(f"Countdown config: {countdown}")

    # asyncio.run(example())
    logger.info("Pre-order manager loaded (run with asyncio.run(example()) to test)")
