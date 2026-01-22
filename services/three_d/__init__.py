# services/three_d/__init__.py
"""3D Generation Provider Abstraction Layer.

Implements US-017: 3D Provider Abstraction for unified 3D model generation
across multiple providers (Replicate, Tripo3D, HuggingFace, Gemini).

Features:
- Protocol-based provider interface
- Automatic failover between providers
- Health checks and availability monitoring
- Consistent request/response models
- Gemini Nano Banana Pro for image generation (no rate limits)

Author: DevSkyy Platform Team
Version: 1.1.0
"""

from services.three_d.provider_factory import (
    ThreeDProviderFactory,
    get_provider_factory,
)
from services.three_d.provider_interface import (
    I3DProvider,
    ProviderHealth,
    ProviderStatus,
    ThreeDCapability,
    ThreeDGenerationError,
    ThreeDProviderError,
    ThreeDRequest,
    ThreeDResponse,
    ThreeDTimeoutError,
)

# Optional Gemini provider
try:
    from services.three_d.gemini_provider import GeminiImageProvider
except ImportError:
    GeminiImageProvider = None  # type: ignore[misc, assignment]

__all__ = [
    # Interface
    "I3DProvider",
    "ThreeDRequest",
    "ThreeDResponse",
    "ProviderHealth",
    "ProviderStatus",
    "ThreeDCapability",
    # Errors
    "ThreeDProviderError",
    "ThreeDGenerationError",
    "ThreeDTimeoutError",
    # Factory
    "ThreeDProviderFactory",
    "get_provider_factory",
    # Gemini provider
    "GeminiImageProvider",
]
