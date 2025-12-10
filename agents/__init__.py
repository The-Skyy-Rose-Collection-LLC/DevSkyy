"""
DevSkyy AI Agents Module
========================

Specialized AI agents for SkyyRose operations:
- TripoAssetAgent: 3D model generation via Tripo3D API
- FashnTryOnAgent: Virtual try-on via FASHN API
- WordPressAssetAgent: Asset upload and management

Usage:
    from agents import TripoAssetAgent, FashnTryOnAgent
    
    # Generate 3D model
    tripo = TripoAssetAgent()
    model = await tripo.generate_from_description(
        product_name="Heart aRose Bomber",
        collection="BLACK_ROSE",
        garment_type="jacket"
    )
    
    # Virtual try-on
    fashn = FashnTryOnAgent()
    result = await fashn.virtual_tryon(
        model_image="path/to/model.jpg",
        garment_image="path/to/garment.jpg"
    )
"""

from .tripo_agent import (
    TripoAssetAgent,
    TripoTask,
    TripoTaskStatus,
    ModelFormat,
)

from .fashn_agent import (
    FashnTryOnAgent,
    FashnTask,
    GarmentCategory,
    TryOnMode,
)

from .wordpress_asset_agent import (
    WordPressAssetAgent,
    AssetUploadResult,
)

__all__ = [
    # Tripo3D
    "TripoAssetAgent",
    "TripoTask",
    "TripoTaskStatus",
    "ModelFormat",
    
    # FASHN
    "FashnTryOnAgent",
    "FashnTask",
    "GarmentCategory",
    "TryOnMode",
    
    # WordPress
    "WordPressAssetAgent",
    "AssetUploadResult",
]
