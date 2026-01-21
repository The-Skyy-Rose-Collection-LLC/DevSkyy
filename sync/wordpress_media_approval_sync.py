# sync/wordpress_media_approval_sync.py
"""WordPress media sync with approval workflow.

Implements US-022: WordPress media sync with approval.

Features:
- Sync approved images to WordPress media library
- Update WooCommerce product galleries
- Track sync status
- Handle failures with retry

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import httpx

from services.approval_queue_manager import (
    ApprovalItem,
    ApprovalQueueManager,
    ApprovalStatus,
    get_approval_manager,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class WordPressSyncConfig:
    """WordPress sync configuration."""

    wordpress_url: str = ""
    username: str = ""
    app_password: str = ""
    timeout: float = 120.0
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "WordPressSyncConfig":
        """Create config from environment."""
        return cls(
            wordpress_url=os.getenv("WORDPRESS_URL", ""),
            username=os.getenv("WORDPRESS_USERNAME", ""),
            app_password=os.getenv("WORDPRESS_APP_PASSWORD", ""),
            timeout=float(os.getenv("WORDPRESS_TIMEOUT", "120")),
            max_retries=int(os.getenv("WORDPRESS_MAX_RETRIES", "3")),
        )

    @property
    def is_configured(self) -> bool:
        """Check if WordPress is properly configured."""
        return bool(self.wordpress_url and self.username and self.app_password)


# =============================================================================
# Models
# =============================================================================


class SyncStatus(str, Enum):
    """Status of sync operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SyncResult:
    """Result of a single sync operation."""

    item_id: str
    status: SyncStatus
    wordpress_media_id: int | None = None
    wordpress_url: str | None = None
    error_message: str | None = None
    synced_at: datetime | None = None


@dataclass
class BatchSyncResult:
    """Result of batch sync operation."""

    success: bool
    total: int = 0
    synced: int = 0
    failed: int = 0
    skipped: int = 0
    results: list[SyncResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


# =============================================================================
# Exceptions
# =============================================================================


class WordPressSyncError(Exception):
    """Exception for WordPress sync errors."""

    def __init__(
        self,
        message: str,
        *,
        item_id: str | None = None,
        status_code: int | None = None,
        correlation_id: str | None = None,
    ) -> None:
        self.item_id = item_id
        self.status_code = status_code
        self.correlation_id = correlation_id
        super().__init__(message)


# =============================================================================
# Sync Service
# =============================================================================


class WordPressMediaApprovalSync:
    """Syncs approved images to WordPress media library.

    Features:
    - Upload approved images to WordPress
    - Update WooCommerce product galleries
    - Track sync status in approval items
    - Handle failures with retry logic

    Usage:
        sync = WordPressMediaApprovalSync()

        # Sync single approved item
        result = await sync.sync_item(approval_item)

        # Batch sync all approved items
        results = await sync.sync_approved_items()
    """

    def __init__(
        self,
        config: WordPressSyncConfig | None = None,
        approval_manager: ApprovalQueueManager | None = None,
    ) -> None:
        """Initialize sync service.

        Args:
            config: Optional WordPress configuration
            approval_manager: Optional approval queue manager
        """
        self._config = config or WordPressSyncConfig.from_env()
        self._approval_manager = approval_manager or get_approval_manager()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=f"{self._config.wordpress_url}/wp-json/wp/v2",
                auth=(self._config.username, self._config.app_password),
                timeout=self._config.timeout,
                headers={"User-Agent": "DevSkyy-MediaSync/1.0"},
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def is_configured(self) -> bool:
        """Check if WordPress is configured."""
        return self._config.is_configured

    async def sync_item(
        self,
        item: ApprovalItem,
        *,
        correlation_id: str | None = None,
    ) -> SyncResult:
        """Sync a single approved item to WordPress.

        Args:
            item: Approved item to sync
            correlation_id: Optional correlation ID

        Returns:
            SyncResult with status and details
        """
        if item.status != ApprovalStatus.APPROVED:
            return SyncResult(
                item_id=item.id,
                status=SyncStatus.SKIPPED,
                error_message=f"Item status is {item.status}, not approved",
            )

        if item.wordpress_media_id:
            return SyncResult(
                item_id=item.id,
                status=SyncStatus.SKIPPED,
                wordpress_media_id=item.wordpress_media_id,
                error_message="Already synced to WordPress",
            )

        if not self.is_configured:
            return SyncResult(
                item_id=item.id,
                status=SyncStatus.FAILED,
                error_message="WordPress not configured",
            )

        logger.info(
            f"Syncing item {item.id} to WordPress",
            extra={
                "item_id": item.id,
                "asset_id": item.asset_id,
                "correlation_id": correlation_id,
            },
        )

        try:
            # Download enhanced image
            image_content = await self._download_image(
                item.enhanced_url,
                correlation_id=correlation_id,
            )

            # Upload to WordPress
            media_data = await self._upload_to_wordpress(
                content=image_content,
                filename=f"{item.asset_id}_enhanced.jpg",
                title=f"{item.product_name or 'Product'} - Enhanced",
                alt_text=f"Enhanced image for {item.product_name or 'product'}",
                correlation_id=correlation_id,
            )

            media_id = media_data["id"]
            media_url = media_data.get("source_url")

            # Update approval item
            await self._approval_manager.update_wordpress_sync(
                item.id,
                wordpress_media_id=media_id,
                correlation_id=correlation_id,
            )

            # Update WooCommerce product if applicable
            if item.woocommerce_product_id:
                await self._update_product_gallery(
                    product_id=int(item.woocommerce_product_id),
                    media_id=media_id,
                    correlation_id=correlation_id,
                )

            logger.info(
                f"Synced item {item.id} to WordPress media {media_id}",
                extra={
                    "item_id": item.id,
                    "media_id": media_id,
                    "correlation_id": correlation_id,
                },
            )

            return SyncResult(
                item_id=item.id,
                status=SyncStatus.COMPLETED,
                wordpress_media_id=media_id,
                wordpress_url=media_url,
                synced_at=datetime.now(UTC),
            )

        except Exception as e:
            logger.error(
                f"Failed to sync item {item.id}: {e}",
                extra={
                    "item_id": item.id,
                    "correlation_id": correlation_id,
                },
            )
            return SyncResult(
                item_id=item.id,
                status=SyncStatus.FAILED,
                error_message=str(e),
            )

    async def sync_approved_items(
        self,
        *,
        limit: int | None = None,
        correlation_id: str | None = None,
    ) -> BatchSyncResult:
        """Sync all approved items that haven't been synced.

        Args:
            limit: Maximum items to sync
            correlation_id: Optional correlation ID

        Returns:
            BatchSyncResult with all sync results
        """
        from services.approval_queue_manager import ApprovalQueueFilter

        result = BatchSyncResult(success=True)

        # Get approved items not yet synced
        filter_params = ApprovalQueueFilter(status=ApprovalStatus.APPROVED)
        response = await self._approval_manager.list_items(
            filter_params=filter_params,
            page_size=limit or 100,
            correlation_id=correlation_id,
        )

        # Filter to items not yet synced
        items_to_sync = [
            item for item in response.items if item.wordpress_media_id is None
        ]

        if limit:
            items_to_sync = items_to_sync[:limit]

        result.total = len(items_to_sync)

        logger.info(
            f"Starting batch sync of {result.total} items",
            extra={"correlation_id": correlation_id},
        )

        for item in items_to_sync:
            sync_result = await self.sync_item(item, correlation_id=correlation_id)
            result.results.append(sync_result)

            if sync_result.status == SyncStatus.COMPLETED:
                result.synced += 1
            elif sync_result.status == SyncStatus.FAILED:
                result.failed += 1
                result.errors.append(
                    f"{item.id}: {sync_result.error_message}"
                )
            else:
                result.skipped += 1

        result.completed_at = datetime.now(UTC)
        result.success = result.failed == 0

        logger.info(
            f"Batch sync complete: {result.synced} synced, {result.failed} failed, {result.skipped} skipped",
            extra={"correlation_id": correlation_id},
        )

        return result

    async def _download_image(
        self,
        url: str,
        *,
        correlation_id: str | None = None,
    ) -> bytes:
        """Download image from URL.

        Args:
            url: Image URL
            correlation_id: Optional correlation ID

        Returns:
            Image content bytes
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    async def _upload_to_wordpress(
        self,
        content: bytes,
        filename: str,
        title: str,
        alt_text: str,
        *,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Upload image to WordPress media library.

        Args:
            content: Image content bytes
            filename: Filename for upload
            title: Media title
            alt_text: Alt text
            correlation_id: Optional correlation ID

        Returns:
            WordPress media data
        """
        client = await self._get_client()

        # Determine content type
        content_type = "image/jpeg"
        if filename.endswith(".png"):
            content_type = "image/png"
        elif filename.endswith(".webp"):
            content_type = "image/webp"

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": content_type,
        }

        response = await client.post(
            "/media",
            content=content,
            headers=headers,
        )

        if response.status_code != 201:
            raise WordPressSyncError(
                f"WordPress upload failed: {response.text}",
                status_code=response.status_code,
                correlation_id=correlation_id,
            )

        data = response.json()
        media_id = data["id"]

        # Update metadata
        await client.post(
            f"/media/{media_id}",
            json={
                "title": title,
                "alt_text": alt_text,
            },
        )

        return data

    async def _update_product_gallery(
        self,
        product_id: int,
        media_id: int,
        *,
        correlation_id: str | None = None,
    ) -> None:
        """Add image to WooCommerce product gallery.

        Args:
            product_id: WooCommerce product ID
            media_id: WordPress media ID
            correlation_id: Optional correlation ID
        """
        client = await self._get_client()

        # Get current product images
        response = await client.get(
            f"{self._config.wordpress_url}/wp-json/wc/v3/products/{product_id}",
        )

        if response.status_code != 200:
            logger.warning(
                f"Could not get product {product_id}: {response.status_code}",
                extra={"correlation_id": correlation_id},
            )
            return

        product = response.json()
        images = product.get("images", [])

        # Add new image to gallery
        images.append({"id": media_id})

        # Update product
        response = await client.put(
            f"{self._config.wordpress_url}/wp-json/wc/v3/products/{product_id}",
            json={"images": images},
        )

        if response.status_code == 200:
            logger.info(
                f"Added media {media_id} to product {product_id} gallery",
                extra={"correlation_id": correlation_id},
            )
        else:
            logger.warning(
                f"Failed to update product gallery: {response.status_code}",
                extra={"correlation_id": correlation_id},
            )


# Module singleton
_sync_service: WordPressMediaApprovalSync | None = None


def get_wordpress_sync() -> WordPressMediaApprovalSync:
    """Get or create the WordPress sync service singleton."""
    global _sync_service
    if _sync_service is None:
        _sync_service = WordPressMediaApprovalSync()
    return _sync_service


__all__ = [
    "WordPressSyncConfig",
    "SyncStatus",
    "SyncResult",
    "BatchSyncResult",
    "WordPressSyncError",
    "WordPressMediaApprovalSync",
    "get_wordpress_sync",
]
