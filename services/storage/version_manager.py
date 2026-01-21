# services/storage/version_manager.py
"""Asset Version Manager Service.

Implements US-023: Asset versioning with retention policies.

Features:
- Sequential version numbering per asset
- Original version preservation (v1 never deleted)
- Multiple retention policies (keep_all, keep_last_n, keep_days)
- Version history and revert capability
- Automatic cleanup based on retention

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from errors.production_errors import (
    DevSkyError,
    DevSkyErrorCode,
    DevSkyErrorSeverity,
)
from services.storage.r2_client import AssetCategory, R2Client
from services.storage.schemas import (
    AssetInfo,
    CleanupResult,
    CreateVersionRequest,
    RetentionPolicy,
    RevertVersionRequest,
    UpdateRetentionRequest,
    VersionInfo,
    VersionListResponse,
    VersionStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Errors
# =============================================================================


class VersioningError(DevSkyError):
    """Error in asset versioning operations."""

    def __init__(
        self,
        message: str,
        *,
        asset_id: str | None = None,
        version: int | None = None,
        correlation_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        context: dict[str, Any] = {}
        if asset_id:
            context["asset_id"] = asset_id
        if version:
            context["version"] = version

        super().__init__(
            message,
            code=DevSkyErrorCode.INTERNAL_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            cause=cause,
            correlation_id=correlation_id,
        )


class VersionNotFoundError(VersioningError):
    """Specific version not found."""

    def __init__(
        self,
        asset_id: str,
        version: int,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            f"Version {version} not found for asset {asset_id}",
            asset_id=asset_id,
            version=version,
            **kwargs,
        )


class AssetNotFoundError(VersioningError):
    """Asset not found."""

    def __init__(
        self,
        asset_id: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            f"Asset not found: {asset_id}",
            asset_id=asset_id,
            **kwargs,
        )


# =============================================================================
# Version Manager
# =============================================================================


class AssetVersionManager:
    """Manages asset versions with retention policies.

    Key features:
    - Sequential version numbers per asset
    - Original (v1) is always preserved
    - Configurable retention policies
    - R2 storage integration with versioned key structure

    Storage key pattern: versioned/{asset_id}/v{n}/{filename}

    Usage:
        manager = AssetVersionManager(r2_client)

        # Create initial version
        version = await manager.create_version(
            CreateVersionRequest(
                asset_id="asset_123",
                content_hash="sha256...",
                r2_key="versioned/asset_123/v1/image.jpg",
                file_size_bytes=1024,
            )
        )

        # Create new version
        new_version = await manager.create_version(
            CreateVersionRequest(
                asset_id="asset_123",
                content_hash="sha256...",
                r2_key="versioned/asset_123/v2/image.jpg",
                file_size_bytes=2048,
                change_description="Enhanced lighting",
            )
        )

        # Revert to previous version
        reverted = await manager.revert_version(
            RevertVersionRequest(
                asset_id="asset_123",
                target_version=1,
            )
        )
    """

    def __init__(
        self,
        r2_client: R2Client | None = None,
    ) -> None:
        self._r2_client = r2_client
        # In-memory storage for demo; replace with database in production
        self._assets: dict[str, AssetInfo] = {}
        self._versions: dict[str, list[VersionInfo]] = {}  # asset_id -> versions

    def _generate_id(self) -> str:
        """Generate unique ID."""
        return str(uuid.uuid4())

    def _generate_correlation_id(self) -> str:
        """Generate correlation ID."""
        return str(uuid.uuid4())

    def _generate_versioned_key(
        self,
        asset_id: str,
        version: int,
        filename: str,
    ) -> str:
        """Generate R2 key for versioned asset.

        Pattern: versioned/{asset_id}/v{n}/{filename}
        """
        return f"versioned/{asset_id}/v{version}/{filename}"

    async def get_asset(
        self,
        asset_id: str,
        *,
        include_versions: bool = False,
        correlation_id: str | None = None,
    ) -> AssetInfo:
        """Get asset info by ID.

        Args:
            asset_id: Asset identifier
            include_versions: If True, include version history
            correlation_id: Optional correlation ID

        Returns:
            AssetInfo with optional versions

        Raises:
            AssetNotFoundError: If asset not found
        """
        asset = self._assets.get(asset_id)
        if not asset:
            raise AssetNotFoundError(asset_id, correlation_id=correlation_id)

        if include_versions:
            asset.versions = self._versions.get(asset_id, [])

        return asset

    async def get_version(
        self,
        asset_id: str,
        version_number: int,
        *,
        correlation_id: str | None = None,
    ) -> VersionInfo:
        """Get specific version of an asset.

        Args:
            asset_id: Asset identifier
            version_number: Version number to retrieve
            correlation_id: Optional correlation ID

        Returns:
            VersionInfo for the specified version

        Raises:
            AssetNotFoundError: If asset not found
            VersionNotFoundError: If version not found
        """
        if asset_id not in self._assets:
            raise AssetNotFoundError(asset_id, correlation_id=correlation_id)

        versions = self._versions.get(asset_id, [])
        for version in versions:
            if version.version_number == version_number:
                return version

        raise VersionNotFoundError(asset_id, version_number, correlation_id=correlation_id)

    async def list_versions(
        self,
        asset_id: str,
        *,
        include_deleted: bool = False,
        correlation_id: str | None = None,
    ) -> VersionListResponse:
        """List all versions of an asset.

        Args:
            asset_id: Asset identifier
            include_deleted: If True, include soft-deleted versions
            correlation_id: Optional correlation ID

        Returns:
            VersionListResponse with all versions

        Raises:
            AssetNotFoundError: If asset not found
        """
        asset = await self.get_asset(asset_id, correlation_id=correlation_id)
        versions = self._versions.get(asset_id, [])

        # Filter out deleted versions unless requested
        if not include_deleted:
            versions = [
                v for v in versions
                if v.status not in (VersionStatus.DELETED, VersionStatus.PENDING_DELETE)
            ]

        return VersionListResponse(
            asset_id=asset_id,
            versions=sorted(versions, key=lambda v: v.version_number, reverse=True),
            total=len(versions),
            current_version=asset.current_version,
        )

    async def create_asset(
        self,
        name: str,
        category: str,
        *,
        product_id: str | None = None,
        retention_policy: RetentionPolicy = RetentionPolicy.KEEP_ALL,
        retention_value: int | None = None,
        metadata: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> AssetInfo:
        """Create a new asset record.

        Args:
            name: Asset name/filename
            category: Asset category
            product_id: Optional product ID
            retention_policy: Version retention policy
            retention_value: Value for retention policy
            metadata: Additional metadata
            correlation_id: Optional correlation ID

        Returns:
            Created AssetInfo
        """
        asset_id = self._generate_id()
        now = datetime.now(UTC)

        asset = AssetInfo(
            asset_id=asset_id,
            name=name,
            category=category,
            product_id=product_id,
            current_version=0,  # Will be updated when first version created
            total_versions=0,
            retention_policy=retention_policy,
            retention_value=retention_value,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )

        self._assets[asset_id] = asset
        self._versions[asset_id] = []

        logger.info(
            f"Created asset {asset_id}",
            extra={
                "asset_id": asset_id,
                "name": name,
                "correlation_id": correlation_id,
            },
        )

        return asset

    async def create_version(
        self,
        request: CreateVersionRequest,
        *,
        created_by: str | None = None,
        correlation_id: str | None = None,
    ) -> VersionInfo:
        """Create a new version for an asset.

        Args:
            request: Version creation request
            created_by: User ID creating the version
            correlation_id: Optional correlation ID

        Returns:
            Created VersionInfo

        Raises:
            AssetNotFoundError: If asset not found
        """
        correlation_id = correlation_id or self._generate_correlation_id()
        asset = await self.get_asset(request.asset_id, correlation_id=correlation_id)

        # Calculate new version number
        new_version_number = asset.current_version + 1
        is_original = new_version_number == 1

        # Create version info
        version = VersionInfo(
            version_id=self._generate_id(),
            asset_id=request.asset_id,
            version_number=new_version_number,
            is_original=is_original,
            is_current=True,
            status=VersionStatus.ACTIVE,
            r2_key=request.r2_key,
            content_hash=request.content_hash,
            file_size_bytes=request.file_size_bytes,
            mime_type=request.mime_type,
            created_at=datetime.now(UTC),
            created_by=created_by,
            metadata=request.metadata,
            change_description=request.change_description,
        )

        # Mark previous version as not current
        for v in self._versions.get(request.asset_id, []):
            if v.is_current:
                v.is_current = False
                v.status = VersionStatus.ARCHIVED

        # Add new version
        self._versions[request.asset_id].append(version)

        # Update asset
        asset.current_version = new_version_number
        asset.total_versions = new_version_number
        asset.updated_at = datetime.now(UTC)

        logger.info(
            f"Created version {new_version_number} for asset {request.asset_id}",
            extra={
                "asset_id": request.asset_id,
                "version": new_version_number,
                "is_original": is_original,
                "correlation_id": correlation_id,
            },
        )

        # Apply retention policy
        await self._apply_retention(request.asset_id, correlation_id=correlation_id)

        return version

    async def revert_version(
        self,
        request: RevertVersionRequest,
        *,
        reverted_by: str | None = None,
        correlation_id: str | None = None,
    ) -> VersionInfo:
        """Revert asset to a previous version.

        Args:
            request: Revert request with target version
            reverted_by: User ID performing the revert
            correlation_id: Optional correlation ID

        Returns:
            New or updated VersionInfo

        Raises:
            AssetNotFoundError: If asset not found
            VersionNotFoundError: If target version not found
        """
        correlation_id = correlation_id or self._generate_correlation_id()

        # Get target version
        target = await self.get_version(
            request.asset_id,
            request.target_version,
            correlation_id=correlation_id,
        )

        if request.create_new_version:
            # Create new version with content from target
            asset = await self.get_asset(request.asset_id, correlation_id=correlation_id)
            new_version_number = asset.current_version + 1

            new_version = VersionInfo(
                version_id=self._generate_id(),
                asset_id=request.asset_id,
                version_number=new_version_number,
                is_original=False,
                is_current=True,
                status=VersionStatus.ACTIVE,
                r2_key=target.r2_key,  # Same content as target
                content_hash=target.content_hash,
                file_size_bytes=target.file_size_bytes,
                mime_type=target.mime_type,
                created_at=datetime.now(UTC),
                created_by=reverted_by,
                metadata=target.metadata.copy(),
                change_description=f"Reverted to version {request.target_version}",
                source_version=request.target_version,
            )

            # Mark previous current as archived
            for v in self._versions.get(request.asset_id, []):
                if v.is_current:
                    v.is_current = False
                    v.status = VersionStatus.ARCHIVED

            self._versions[request.asset_id].append(new_version)

            # Update asset
            asset.current_version = new_version_number
            asset.total_versions = new_version_number
            asset.updated_at = datetime.now(UTC)

            logger.info(
                f"Reverted asset {request.asset_id} to version {request.target_version} "
                f"(created v{new_version_number})",
                extra={
                    "asset_id": request.asset_id,
                    "target_version": request.target_version,
                    "new_version": new_version_number,
                    "correlation_id": correlation_id,
                },
            )

            return new_version

        else:
            # Just update the current version pointer
            asset = await self.get_asset(request.asset_id, correlation_id=correlation_id)

            for v in self._versions.get(request.asset_id, []):
                if v.is_current:
                    v.is_current = False
                if v.version_number == request.target_version:
                    v.is_current = True
                    v.status = VersionStatus.ACTIVE

            asset.current_version = request.target_version
            asset.updated_at = datetime.now(UTC)

            logger.info(
                f"Reverted asset {request.asset_id} pointer to version {request.target_version}",
                extra={
                    "asset_id": request.asset_id,
                    "target_version": request.target_version,
                    "correlation_id": correlation_id,
                },
            )

            return target

    async def update_retention(
        self,
        request: UpdateRetentionRequest,
        *,
        correlation_id: str | None = None,
    ) -> AssetInfo:
        """Update retention policy for an asset.

        Args:
            request: Retention update request
            correlation_id: Optional correlation ID

        Returns:
            Updated AssetInfo

        Raises:
            AssetNotFoundError: If asset not found
            VersioningError: If invalid policy configuration
        """
        correlation_id = correlation_id or self._generate_correlation_id()
        asset = await self.get_asset(request.asset_id, correlation_id=correlation_id)

        # Validate policy configuration
        if request.policy == RetentionPolicy.KEEP_LAST_N and not request.value:
            raise VersioningError(
                "KEEP_LAST_N policy requires a value (number of versions to keep)",
                asset_id=request.asset_id,
                correlation_id=correlation_id,
            )

        if request.policy == RetentionPolicy.KEEP_DAYS and not request.value:
            raise VersioningError(
                "KEEP_DAYS policy requires a value (number of days to keep)",
                asset_id=request.asset_id,
                correlation_id=correlation_id,
            )

        asset.retention_policy = request.policy
        asset.retention_value = request.value
        asset.updated_at = datetime.now(UTC)

        logger.info(
            f"Updated retention policy for asset {request.asset_id} to {request.policy.value}",
            extra={
                "asset_id": request.asset_id,
                "policy": request.policy.value,
                "value": request.value,
                "correlation_id": correlation_id,
            },
        )

        # Apply new retention policy
        await self._apply_retention(request.asset_id, correlation_id=correlation_id)

        return asset

    async def _apply_retention(
        self,
        asset_id: str,
        *,
        correlation_id: str | None = None,
    ) -> CleanupResult:
        """Apply retention policy to asset versions.

        Never deletes the original (v1) version.

        Args:
            asset_id: Asset to apply retention to
            correlation_id: Optional correlation ID

        Returns:
            CleanupResult with statistics
        """
        asset = await self.get_asset(asset_id, correlation_id=correlation_id)
        versions = self._versions.get(asset_id, [])

        result = CleanupResult(
            asset_id=asset_id,
            versions_retained=0,
        )

        if asset.retention_policy == RetentionPolicy.KEEP_ALL:
            result.versions_retained = len(versions)
            return result

        # Sort versions by number (newest first)
        sorted_versions = sorted(versions, key=lambda v: v.version_number, reverse=True)

        versions_to_delete: list[VersionInfo] = []

        if asset.retention_policy == RetentionPolicy.KEEP_LAST_N:
            keep_n = asset.retention_value or 5
            for v in sorted_versions[keep_n:]:
                if not v.is_original:  # Never delete original
                    versions_to_delete.append(v)

        elif asset.retention_policy == RetentionPolicy.KEEP_DAYS:
            days = asset.retention_value or 30
            cutoff = datetime.now(UTC) - timedelta(days=days)
            for v in sorted_versions:
                if not v.is_original and v.created_at < cutoff:
                    versions_to_delete.append(v)

        # Mark versions for deletion
        for v in versions_to_delete:
            v.status = VersionStatus.PENDING_DELETE
            result.versions_deleted += 1
            result.bytes_freed += v.file_size_bytes

        result.versions_retained = len(versions) - result.versions_deleted

        if result.versions_deleted > 0:
            logger.info(
                f"Marked {result.versions_deleted} versions for deletion on asset {asset_id}",
                extra={
                    "asset_id": asset_id,
                    "versions_deleted": result.versions_deleted,
                    "bytes_freed": result.bytes_freed,
                    "correlation_id": correlation_id,
                },
            )

        return result

    async def delete_version(
        self,
        asset_id: str,
        version_number: int,
        *,
        correlation_id: str | None = None,
    ) -> None:
        """Soft-delete a specific version.

        Marks the version as PENDING_DELETE. Actual deletion happens during cleanup.
        The original version (v1) cannot be deleted.

        Args:
            asset_id: Asset identifier
            version_number: Version number to delete
            correlation_id: Optional correlation ID

        Raises:
            AssetNotFoundError: If asset not found
            VersionNotFoundError: If version not found
            VersioningError: If trying to delete original version
        """
        correlation_id = correlation_id or self._generate_correlation_id()

        if version_number == 1:
            raise VersioningError(
                "Cannot delete the original version (v1)",
                asset_id=asset_id,
                version=version_number,
                correlation_id=correlation_id,
            )

        version = await self.get_version(
            asset_id,
            version_number,
            correlation_id=correlation_id,
        )

        if version.is_original:
            raise VersioningError(
                "Cannot delete the original version",
                asset_id=asset_id,
                version=version_number,
                correlation_id=correlation_id,
            )

        version.status = VersionStatus.PENDING_DELETE

        logger.info(
            f"Version {version_number} of asset {asset_id} marked for deletion",
            extra={
                "asset_id": asset_id,
                "version": version_number,
                "correlation_id": correlation_id,
            },
        )

    async def cleanup_deleted_versions(
        self,
        *,
        correlation_id: str | None = None,
    ) -> dict[str, CleanupResult]:
        """Permanently delete versions marked for deletion.

        Should be run periodically as a background job.

        Args:
            correlation_id: Optional correlation ID

        Returns:
            Dict of asset_id to CleanupResult
        """
        correlation_id = correlation_id or self._generate_correlation_id()
        results: dict[str, CleanupResult] = {}

        for asset_id, versions in self._versions.items():
            result = CleanupResult(asset_id=asset_id)

            for version in versions[:]:  # Copy list for modification
                if version.status == VersionStatus.PENDING_DELETE:
                    try:
                        # Delete from R2 if client available
                        if self._r2_client:
                            self._r2_client.delete_object(
                                version.r2_key,
                                correlation_id=correlation_id,
                            )

                        result.bytes_freed += version.file_size_bytes
                        result.versions_deleted += 1

                        # Remove from list
                        versions.remove(version)

                    except Exception as e:
                        result.errors.append(f"Failed to delete v{version.version_number}: {e}")

            if result.versions_deleted > 0:
                results[asset_id] = result

        if results:
            total_deleted = sum(r.versions_deleted for r in results.values())
            total_bytes = sum(r.bytes_freed for r in results.values())
            logger.info(
                f"Cleanup completed: {total_deleted} versions, {total_bytes} bytes freed",
                extra={
                    "versions_deleted": total_deleted,
                    "bytes_freed": total_bytes,
                    "correlation_id": correlation_id,
                },
            )

        return results


__all__ = [
    "AssetVersionManager",
    "VersioningError",
    "VersionNotFoundError",
    "AssetNotFoundError",
]
