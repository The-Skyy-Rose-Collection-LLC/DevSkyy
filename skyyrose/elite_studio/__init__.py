"""
SkyyRose Elite Production Studio — Multi-Agent Image Pipeline

Architecture:
    VisionAgent  (Gemini Flash + OpenAI GPT-4o)  -> detailed product analysis
    GeneratorAgent  (Gemini 3 Pro Image)          -> fashion model generation
    QualityAgent  (Claude Sonnet)                 -> verification & QC
    Coordinator                                    -> orchestrates pipeline

Usage:
    python -m skyyrose.elite_studio produce br-001
    python -m skyyrose.elite_studio produce-batch --all
"""

from .coordinator import Coordinator, NullLogger, PrintLogger
from .models import (
    GenerationResult,
    ProductData,
    ProductionResult,
    QualityVerification,
    SynthesizedVision,
    VisionAnalysis,
)

__all__ = [
    "Coordinator",
    "NullLogger",
    "PrintLogger",
    "GenerationResult",
    "GenerationResult",
    "ProductData",
    "ProductionResult",
    "QualityVerification",
    "SynthesizedVision",
    "VisionAnalysis",
]
