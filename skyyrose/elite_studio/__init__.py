"""
SkyyRose Elite Production Studio — Multi-Agent Image Pipeline

Architecture:
    VisionAgent  (Gemini Flash + OpenAI GPT-4o)  -> detailed product analysis
    GeneratorAgent  (Gemini 3 Pro Image)          -> fashion model generation
    QualityAgent  (Claude Sonnet)                 -> verification & QC
    Coordinator                                    -> orchestrates pipeline (legacy)
    graph.build_graph()                            -> LangGraph engine (new)

Usage:
    python -m skyyrose.elite_studio produce br-001
    python -m skyyrose.elite_studio produce br-001 --graph
    python -m skyyrose.elite_studio produce-batch --all
"""

from .coordinator import Coordinator, NullLogger, PrintLogger
from .graph import GraphConfig, build_graph, run_batch, run_single
from .models import (
    CompositorResult,
    GenerationResult,
    ProductData,
    ProductionResult,
    QualityVerification,
    SynthesizedVision,
    VisionAnalysis,
)

__all__ = [
    # Legacy coordinator
    "Coordinator",
    "NullLogger",
    "PrintLogger",
    # LangGraph engine
    "GraphConfig",
    "build_graph",
    "run_single",
    "run_batch",
    # Models
    "CompositorResult",
    "GenerationResult",
    "ProductData",
    "ProductionResult",
    "QualityVerification",
    "SynthesizedVision",
    "VisionAnalysis",
]
