# services/ml/enhancement/__init__.py
"""
DevSkyy Image Enhancement Services.

Provides ML-powered image enhancement capabilities:
- Background removal
- Image upscaling
- Format optimization
- Product authenticity validation

CRITICAL CONSTRAINT: These services enhance images without modifying
product logos, branding, labels, text, colors, or physical features.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from services.ml.enhancement.authenticity_validator import (
    AuthenticityReport,
    AuthenticityValidator,
    ValidationResult,
)
from services.ml.enhancement.background_removal import (
    BackgroundRemovalResult,
    BackgroundRemovalService,
    BackgroundType,
)
from services.ml.enhancement.format_optimizer import (
    FormatOptimizationResult,
    FormatOptimizer,
    ImageVariant,
    OutputFormat,
)
from services.ml.enhancement.lighting_normalization import (
    ColorPreservationError,
    LightingIntensity,
    LightingNormalizationError,
    LightingNormalizationService,
    LightingResult,
)
from services.ml.enhancement.upscaling import (
    UpscaleResult,
    UpscalingService,
)

__all__ = [
    # Background removal
    "BackgroundRemovalService",
    "BackgroundRemovalResult",
    "BackgroundType",
    # Upscaling
    "UpscalingService",
    "UpscaleResult",
    # Lighting normalization
    "LightingNormalizationService",
    "LightingResult",
    "LightingNormalizationError",
    "ColorPreservationError",
    "LightingIntensity",
    # Format optimization
    "FormatOptimizer",
    "FormatOptimizationResult",
    "ImageVariant",
    "OutputFormat",
    # Authenticity validation
    "AuthenticityValidator",
    "AuthenticityReport",
    "ValidationResult",
]
