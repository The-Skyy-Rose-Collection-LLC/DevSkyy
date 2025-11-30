"""
Pydantic models for 3D Clothing Asset Automation

Provides type-safe data models for:
- Clothing items and collections
- 3D model generation results
- Virtual try-on results
- WordPress upload results
- Pipeline orchestration
"""

from agent.modules.clothing.schemas.schemas import (
    ClothingCategory,
    ClothingCollection,
    ClothingItem,
    Model3DFormat,
    Model3DResult,
    PipelineResult,
    PipelineStage,
    TryOnModel,
    TryOnResult,
    WordPressUploadResult,
)

__all__ = [
    "ClothingCategory",
    "ClothingCollection",
    "ClothingItem",
    "Model3DFormat",
    "Model3DResult",
    "TryOnModel",
    "TryOnResult",
    "WordPressUploadResult",
    "PipelineResult",
    "PipelineStage",
]
