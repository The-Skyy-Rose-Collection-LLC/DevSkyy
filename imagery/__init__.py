# imagery/__init__.py
"""DevSkyy Imagery Module.

This module provides:
- 3D model fidelity validation (95% threshold)
- Visual comparison for asset fidelity (90% threshold)
- Image processing utilities
- Virtual photoshoot automation
- Model quality metrics
"""

from imagery.headless_renderer import (
    CameraAngle,
    HeadlessRenderer,
    LightingPreset,
    RenderConfig,
    RenderResult,
    render_glb_to_images,
)
from imagery.image_processor import (
    BackgroundRemover,
    ImagePreprocessor,
    ImageProcessor,
)
from imagery.model_fidelity import (
    MINIMUM_FIDELITY_SCORE,
    FidelityMetrics,
    FidelityReport,
    ModelFidelityValidator,
    validate_model_fidelity,
)
from imagery.quality_gate import (
    AssetFidelityError,
    AssetQualityGate,
    GateStatus,
    QualityGateResult,
    validate_before_upload,
)
from imagery.virtual_photoshoot import (
    PhotoshootConfig,
    PhotoshootResult,
    VirtualPhotoshootPipeline,
)
from imagery.visual_comparison import (
    ComparisonConfidence,
    ComparisonResult,
    ComparisonWeights,
    VisualComparisonEngine,
    compare_images,
)


# SDXL Pipeline (lazy imports to avoid heavy dependencies)
def get_sdxl_pipeline():
    """Get SDXL pipeline (lazy import)."""
    from imagery.sdxl_pipeline import GenerationConfig, SDXLPipeline, SkyyRosePromptBuilder

    return SDXLPipeline, GenerationConfig, SkyyRosePromptBuilder


def get_luxury_photography():
    """Get luxury photography system (lazy import)."""
    from imagery.luxury_photography import GarmentSpecs, LuxuryProductPhotography, PhotoSuite

    return LuxuryProductPhotography, GarmentSpecs, PhotoSuite


def get_lora_trainer():
    """Get LoRA trainer (lazy import)."""
    from imagery.lora_trainer import SkyyRoseLoRATrainer, TrainingConfig, TrainingDataset

    return SkyyRoseLoRATrainer, TrainingConfig, TrainingDataset


def get_premium_3d_pipeline():
    """Get premium 3D pipeline (lazy import)."""
    from imagery.premium_3d_pipeline import FabricType, FinalModel, Premium3DAssetPipeline

    return Premium3DAssetPipeline, FabricType, FinalModel


__all__ = [
    # Fidelity
    "ModelFidelityValidator",
    "FidelityMetrics",
    "FidelityReport",
    "validate_model_fidelity",
    "MINIMUM_FIDELITY_SCORE",
    # Visual Comparison
    "VisualComparisonEngine",
    "ComparisonResult",
    "ComparisonConfidence",
    "ComparisonWeights",
    "compare_images",
    # Headless Rendering
    "HeadlessRenderer",
    "RenderConfig",
    "RenderResult",
    "LightingPreset",
    "CameraAngle",
    "render_glb_to_images",
    # Quality Gate
    "AssetQualityGate",
    "QualityGateResult",
    "GateStatus",
    "AssetFidelityError",
    "validate_before_upload",
    # Image Processing
    "ImageProcessor",
    "ImagePreprocessor",
    "BackgroundRemover",
    # Virtual Photoshoot
    "VirtualPhotoshootPipeline",
    "PhotoshootConfig",
    "PhotoshootResult",
    # Lazy loaders for heavy dependencies
    "get_sdxl_pipeline",
    "get_luxury_photography",
    "get_lora_trainer",
    "get_premium_3d_pipeline",
]
