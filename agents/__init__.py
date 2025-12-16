"""
DevSkyy Agents Module
=====================

Specialized AI agents for fashion e-commerce automation.

Agents:
- FashnTryOnAgent: Virtual try-on using FASHN API
- TripoAssetAgent: 3D model generation using Tripo3D API
- WordPressAssetAgent: WordPress media upload and management

All agents extend the SuperAgent base class and follow the
Plan → Retrieve → Execute → Validate → Emit workflow.
"""

from .fashn_agent import (
    FashnConfig,
    FashnTask,
    FashnTaskStatus,
    FashnTryOnAgent,
    GarmentCategory,
    TryOnMode,
    TryOnResult,
)
from .tripo_agent import (
    COLLECTION_PROMPTS,
    GARMENT_TEMPLATES,
    SKYYROSE_BRAND_DNA,
    GenerationResult,
    ModelFormat,
    ModelStyle,
    TripoAssetAgent,
    TripoConfig,
    TripoTask,
    TripoTaskStatus,
)
from .wordpress_asset_agent import (
    MediaUploadResult,
    ProductAssetResult,
    WordPressAssetAgent,
    WordPressAssetConfig,
)

__all__ = [
    # FASHN Agent
    "FashnTryOnAgent",
    "FashnConfig",
    "FashnTask",
    "TryOnResult",
    "GarmentCategory",
    "TryOnMode",
    "FashnTaskStatus",
    # Tripo Agent
    "TripoAssetAgent",
    "TripoConfig",
    "TripoTask",
    "GenerationResult",
    "ModelFormat",
    "ModelStyle",
    "TripoTaskStatus",
    "SKYYROSE_BRAND_DNA",
    "COLLECTION_PROMPTS",
    "GARMENT_TEMPLATES",
    # WordPress Asset Agent
    "WordPressAssetAgent",
    "WordPressAssetConfig",
    "MediaUploadResult",
    "ProductAssetResult",
]
