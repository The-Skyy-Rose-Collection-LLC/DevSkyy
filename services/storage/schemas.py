# services/storage/schemas.py
"""Storage schemas for asset versioning.

Implements US-023: Asset versioning with retention policies.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class RetentionPolicy(str, Enum):
    """Retention policy for asset versions."""

    KEEP_ALL = "keep_all"  # Keep all versions forever
    KEEP_LAST_N = "keep_last_n"  # Keep only the last N versions
    KEEP_DAYS = "keep_days"  # Keep versions for N days


class VersionStatus(str, Enum):
    """Status of an asset version."""

    ACTIVE = "active"  # Current version in use
    ARCHIVED = "archived"  # Previous version, still accessible
    PENDING_DELETE = "pending_delete"  # Scheduled for deletion
    DELETED = "deleted"  # Soft deleted


# =============================================================================
# Models
# =============================================================================


class VersionInfo(BaseModel):
    """Information about an asset version.

    Attributes:
        version_id: Unique identifier for this version
        asset_id: Parent asset identifier
        version_number: Sequential version number (1, 2, 3, ...)
        is_original: True for v1 (original upload, never deleted)
        is_current: True if this is the active version
        status: Version status (active, archived, deleted)
        r2_key: Full R2 storage key for this version
        content_hash: SHA-256 hash of content for deduplication
        file_size_bytes: Size of the version in bytes
        mime_type: MIME type of the asset
        created_at: When this version was created
        created_by: User ID who created this version
        metadata: Additional version metadata
    """

    version_id: str
    asset_id: str
    version_number: int = Field(ge=1)
    is_original: bool = False
    is_current: bool = False
    status: VersionStatus = VersionStatus.ACTIVE

    # Storage
    r2_key: str
    content_hash: str
    file_size_bytes: int = Field(ge=0)
    mime_type: str | None = None

    # Tracking
    created_at: datetime
    created_by: str | None = None

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Change tracking
    change_description: str | None = Field(
        default=None,
        description="Description of what changed in this version",
    )
    source_version: int | None = Field(
        default=None,
        description="Version number this was created from (for reverts)",
    )


class AssetInfo(BaseModel):
    """Information about an asset with its versions.

    Attributes:
        asset_id: Unique asset identifier
        name: Asset name/filename
        category: Asset category (original, enhanced, etc.)
        product_id: Associated product ID (if any)
        current_version: Current active version number
        total_versions: Total number of versions
        retention_policy: Policy for version retention
        retention_value: Value for retention policy (N for KEEP_LAST_N or days)
        created_at: When the asset was first created
        updated_at: Last modification time
        metadata: Asset-level metadata
    """

    asset_id: str
    name: str
    category: str
    product_id: str | None = None

    # Versioning
    current_version: int = 1
    total_versions: int = 1
    retention_policy: RetentionPolicy = RetentionPolicy.KEEP_ALL
    retention_value: int | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Versions (optional, loaded on demand)
    versions: list[VersionInfo] | None = None


class CreateVersionRequest(BaseModel):
    """Request to create a new asset version.

    Attributes:
        asset_id: Asset to create version for
        content_hash: Hash of the new content
        r2_key: R2 storage key for the new version
        file_size_bytes: Size of the new version
        mime_type: MIME type
        change_description: Description of changes
        metadata: Additional metadata
    """

    asset_id: str
    content_hash: str
    r2_key: str
    file_size_bytes: int = Field(ge=0)
    mime_type: str | None = None
    change_description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RevertVersionRequest(BaseModel):
    """Request to revert to a previous version.

    Attributes:
        asset_id: Asset to revert
        target_version: Version number to revert to
        create_new_version: If True, creates a new version with old content
                           If False, just updates current_version pointer
    """

    asset_id: str
    target_version: int = Field(ge=1)
    create_new_version: bool = True


class UpdateRetentionRequest(BaseModel):
    """Request to update retention policy for an asset.

    Attributes:
        asset_id: Asset to update
        policy: New retention policy
        value: Value for the policy (N versions or days)
    """

    asset_id: str
    policy: RetentionPolicy
    value: int | None = Field(default=None, ge=1)


class VersionListResponse(BaseModel):
    """Response containing list of versions.

    Attributes:
        asset_id: Asset ID
        versions: List of version info
        total: Total number of versions
        current_version: Currently active version number
    """

    asset_id: str
    versions: list[VersionInfo]
    total: int
    current_version: int


class CleanupResult(BaseModel):
    """Result of version cleanup operation.

    Attributes:
        asset_id: Asset that was cleaned up
        versions_deleted: Number of versions deleted
        bytes_freed: Total bytes freed
        versions_retained: Number of versions retained
        errors: Any errors encountered
    """

    asset_id: str
    versions_deleted: int = 0
    bytes_freed: int = 0
    versions_retained: int = 0
    errors: list[str] = Field(default_factory=list)


__all__ = [
    # Enums
    "RetentionPolicy",
    "VersionStatus",
    # Models
    "VersionInfo",
    "AssetInfo",
    "CreateVersionRequest",
    "RevertVersionRequest",
    "UpdateRetentionRequest",
    "VersionListResponse",
    "CleanupResult",
]
