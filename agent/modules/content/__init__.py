"""Content generation agents."""

from .visual_content_generation_agent import (
    visual_content_agent,
    VisualContentGenerationAgent,
    GenerationRequest,
    GenerationResult,
    ContentProvider,
    ContentType,
    StylePreset,
)

from .asset_preprocessing_pipeline import (
    asset_pipeline,
    AssetPreprocessingPipeline,
    ProcessingRequest,
    ProcessingResult,
    AssetMetadata,
    AssetType,
    UpscaleQuality,
    ProcessingStage,
)

from .virtual_tryon_huggingface_agent import (
    virtual_tryon_agent,
    VirtualTryOnHuggingFaceAgent,
    TryOnRequest,
    TryOnResult,
    ModelSpecification,
    PoseType,
    ModelEthnicity,
    BodyType,
    ModelType,
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
