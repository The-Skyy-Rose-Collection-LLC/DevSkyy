"""Content generation agents."""

from .asset_preprocessing_pipeline import (
    AssetMetadata,
    AssetPreprocessingPipeline,
    AssetType,
    ProcessingRequest,
    ProcessingResult,
    ProcessingStage,
    UpscaleQuality,
    asset_pipeline,
)
from .virtual_tryon_huggingface_agent import (
    BodyType,
    ModelEthnicity,
    ModelSpecification,
    ModelType,
    PoseType,
    TryOnRequest,
    TryOnResult,
    VirtualTryOnHuggingFaceAgent,
    virtual_tryon_agent,
)
from .visual_content_generation_agent import (
    ContentProvider,
    ContentType,
    GenerationRequest,
    GenerationResult,
    StylePreset,
    VisualContentGenerationAgent,
    visual_content_agent,
)


__all__ = [
    # Visual Content Generation
    "visual_content_agent",
    "VisualContentGenerationAgent",
    "GenerationRequest",
    "GenerationResult",
    "ContentProvider",
    "ContentType",
    "StylePreset",
    # Asset Preprocessing
    "asset_pipeline",
    "AssetPreprocessingPipeline",
    "ProcessingRequest",
    "ProcessingResult",
    "AssetMetadata",
    "AssetType",
    "UpscaleQuality",
    "ProcessingStage",
    # Virtual Try-On
    "virtual_tryon_agent",
    "VirtualTryOnHuggingFaceAgent",
    "TryOnRequest",
    "TryOnResult",
    "ModelSpecification",
    "PoseType",
    "ModelEthnicity",
    "BodyType",
    "ModelType",
]
