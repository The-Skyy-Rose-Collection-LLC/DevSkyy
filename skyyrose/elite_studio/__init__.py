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

from __future__ import annotations

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
    # Legacy coordinator (lazy — import skyyrose.elite_studio.coordinator directly)
    "Coordinator",
    "NullLogger",
    "PrintLogger",
    # LangGraph engine (lazy — import skyyrose.elite_studio.graph directly)
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


def __getattr__(name: str) -> object:
    """Lazy-load heavy submodules on first attribute access.

    Defers coordinator and graph imports so that submodules like
    fashion.context can be imported without pulling in the full agent tree.
    """
    if name in ("Coordinator", "NullLogger", "PrintLogger"):
        from .coordinator import Coordinator, NullLogger, PrintLogger  # noqa: F401

        _globals = globals()
        _globals["Coordinator"] = Coordinator
        _globals["NullLogger"] = NullLogger
        _globals["PrintLogger"] = PrintLogger
        return _globals[name]

    if name in ("GraphConfig", "build_graph", "run_single", "run_batch"):
        from .graph import GraphConfig, build_graph, run_batch, run_single  # noqa: F401

        _globals = globals()
        _globals["GraphConfig"] = GraphConfig
        _globals["build_graph"] = build_graph
        _globals["run_single"] = run_single
        _globals["run_batch"] = run_batch
        return _globals[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
