# services/__init__.py
"""
DevSkyy Services Module.

Provides client abstractions for external services:
- ML services (Replicate, HuggingFace)
- Storage services (Cloudflare R2, S3)
- Integration services

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from services.ml import (
    ReplicateClient,
    ReplicateConfig,
    ReplicateError,
    ReplicatePrediction,
    ReplicatePredictionStatus,
)
from services.storage import (
    AssetCategory,
    R2Client,
    R2Config,
    R2Error,
    R2NotFoundError,
    R2Object,
    R2UploadResult,
)

__all__ = [
    # ML Services
    "ReplicateClient",
    "ReplicateConfig",
    "ReplicateError",
    "ReplicatePrediction",
    "ReplicatePredictionStatus",
    # Storage Services
    "R2Client",
    "R2Config",
    "R2Error",
    "R2NotFoundError",
    "R2Object",
    "R2UploadResult",
    "AssetCategory",
]
