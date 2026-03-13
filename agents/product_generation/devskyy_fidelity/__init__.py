"""DevSkyy Garment Fidelity Layer.

Production-grade quality assurance system for validating AI-generated
product images against real SkyyRose garments before upload.

Validation checks:
  1. Silhouette IoU (60% weight) — garment shape matching
  2. Color ΔE in LAB space (40% weight) — perceptual color accuracy
  3. Per-collection thresholds — BLACK_ROSE 85%, LOVE_HURTS 82%, SIGNATURE 80%

Usage:
    from agents.product_generation.devskyy_fidelity import (
        AssetQualityGate,
        ProductImagePipeline,
    )

    gate = AssetQualityGate()
    result = await gate.validate_against_real_garment(
        generated_image=Path("output.png"),
        reference_photos=[Path("ref_front.jpg")],
        color_hex_palette=["#8B0000", "#1A1A1F"],
    )
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "DevSkyy Platform Team"

from agents.product_generation.devskyy_fidelity.config import (
    BLACK_ROSE_CONFIG,
    LOVE_HURTS_CONFIG,
    SIGNATURE_CONFIG,
    CollectionFidelityConfig,
    FidelityLevel,
    get_fidelity_config,
    get_fidelity_threshold,
)
from agents.product_generation.devskyy_fidelity.pipeline import (
    ImageStatus,
    ProductImageMetadata,
    ProductImagePipeline,
)
from agents.product_generation.devskyy_fidelity.quality_gate import (
    AssetQualityGate,
    QualityResult,
)

__all__ = [
    "AssetQualityGate",
    "QualityResult",
    "ProductImagePipeline",
    "ProductImageMetadata",
    "ImageStatus",
    "CollectionFidelityConfig",
    "FidelityLevel",
    "BLACK_ROSE_CONFIG",
    "LOVE_HURTS_CONFIG",
    "SIGNATURE_CONFIG",
    "get_fidelity_config",
    "get_fidelity_threshold",
]
