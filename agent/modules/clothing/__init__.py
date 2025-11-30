"""
3D Clothing Asset Automation Module for DevSkyy

This module provides production-ready automation for:
- 3D model generation using Tripo3D
- Virtual try-on using FASHN
- WordPress/WooCommerce media upload

Brand: SkyyRose - Oakland luxury streetwear
Collections: BLACK_ROSE, LOVE_HURTS, SIGNATURE

Truth Protocol Compliance:
- Rule #1: All APIs verified from official documentation
- Rule #5: All API keys via environment variables
- Rule #9: Fully documented with type hints
- Rule #10: Error handling with continue policy
"""

from agent.modules.clothing.clothing_asset_agent import ClothingAssetAgent
from agent.modules.clothing.pipeline import ClothingAssetPipeline
from agent.modules.clothing.schemas.schemas import (
    ClothingCollection,
    ClothingItem,
    Model3DResult,
    PipelineResult,
    TryOnResult,
    WordPressUploadResult,
)

__all__ = [
    "ClothingAssetAgent",
    "ClothingAssetPipeline",
    "ClothingCollection",
    "ClothingItem",
    "Model3DResult",
    "TryOnResult",
    "WordPressUploadResult",
    "PipelineResult",
]

__version__ = "1.0.0"
