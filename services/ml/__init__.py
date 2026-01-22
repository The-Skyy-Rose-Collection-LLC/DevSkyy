# services/ml/__init__.py
"""
DevSkyy ML Services Module.

Provides client abstractions for ML services including:
- Replicate API (image processing, 3D generation)
- Gemini API (vision analysis, image generation - Nano Banana Pro)
- Processing queue with fallback chains
- Invisible watermarking
- Model management and caching

Author: DevSkyy Platform Team
Version: 1.1.0
"""

from __future__ import annotations

from services.ml.pipeline_orchestrator import (
    PipelineError,
    PipelineEvent,
    PipelineJob,
    PipelineOrchestrator,
    PipelineResult,
    PipelineStage,
    PipelineStatus,
    ProcessingProfile,
    StageCheckpoint,
)
from services.ml.processing_queue import (
    FallbackChain,
    Job,
    JobStatus,
    ProcessingQueue,
    ProcessingQueueError,
    QueueMetrics,
    TaskType,
)
from services.ml.replicate_client import (
    ReplicateClient,
    ReplicateConfig,
    ReplicateError,
    ReplicatePrediction,
    ReplicatePredictionStatus,
    ReplicateRateLimitError,
    ReplicateTimeoutError,
)
from services.ml.watermark_service import (
    WatermarkDetectionResult,
    WatermarkError,
    WatermarkPayload,
    WatermarkResult,
    WatermarkService,
)

# Optional Gemini client (requires google-genai)
try:
    from services.ml.gemini_client import (
        AspectRatio,
        GeminiClient,
        GeminiConfig,
        GeminiContentFilterError,
        GeminiError,
        GeminiModel,
        GeminiRateLimitError,
        GeneratedImage,
        ImageGenerationRequest,
        ImageGenerationResponse,
        ImageInput,
        ImageSize,
        VisionAnalysisResponse,
    )
except ImportError:
    # google-genai not installed
    GeminiClient = None  # type: ignore[misc, assignment]
    GeminiConfig = None  # type: ignore[misc, assignment]
    GeminiError = None  # type: ignore[misc, assignment]
    GeminiModel = None  # type: ignore[misc, assignment]

__all__ = [
    # Replicate client
    "ReplicateClient",
    "ReplicateConfig",
    "ReplicateError",
    "ReplicatePrediction",
    "ReplicatePredictionStatus",
    "ReplicateRateLimitError",
    "ReplicateTimeoutError",
    # Gemini client (Nano Banana Pro)
    "GeminiClient",
    "GeminiConfig",
    "GeminiError",
    "GeminiRateLimitError",
    "GeminiContentFilterError",
    "GeminiModel",
    "AspectRatio",
    "ImageSize",
    "ImageInput",
    "ImageGenerationRequest",
    "ImageGenerationResponse",
    "GeneratedImage",
    "VisionAnalysisResponse",
    # Pipeline orchestrator
    "PipelineOrchestrator",
    "PipelineJob",
    "PipelineResult",
    "PipelineEvent",
    "PipelineError",
    "PipelineStage",
    "PipelineStatus",
    "ProcessingProfile",
    "StageCheckpoint",
    # Processing queue
    "ProcessingQueue",
    "Job",
    "JobStatus",
    "TaskType",
    "FallbackChain",
    "QueueMetrics",
    "ProcessingQueueError",
    # Watermark service
    "WatermarkService",
    "WatermarkResult",
    "WatermarkDetectionResult",
    "WatermarkError",
    "WatermarkPayload",
]
