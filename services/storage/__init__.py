# services/storage/__init__.py
"""
DevSkyy Storage Services Module.

Provides client abstractions for storage services including:
- Cloudflare R2 (S3-compatible with zero egress fees)
- Asset management and CDN integration
- Asset versioning with retention policies (US-023)

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from services.storage.r2_client import (
    AssetCategory,
    R2Client,
    R2Config,
    R2Error,
    R2NotFoundError,
    R2Object,
    R2UploadResult,
)
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
from services.storage.version_manager import (
    AssetNotFoundError,
    AssetVersionManager,
    VersioningError,
    VersionNotFoundError,
)

__all__ = [
    # R2 Client
    "AssetCategory",
    "R2Client",
    "R2Config",
    "R2Error",
    "R2NotFoundError",
    "R2Object",
    "R2UploadResult",
    # Versioning Schemas
    "AssetInfo",
    "CleanupResult",
    "CreateVersionRequest",
    "RetentionPolicy",
    "RevertVersionRequest",
    "UpdateRetentionRequest",
    "VersionInfo",
    "VersionListResponse",
    "VersionStatus",
    # Version Manager
    "AssetNotFoundError",
    "AssetVersionManager",
    "VersioningError",
    "VersionNotFoundError",
]
