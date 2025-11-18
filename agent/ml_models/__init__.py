"""
Machine Learning Models Module
Advanced ML capabilities for all DevSkyy agents
"""

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .base_ml_engine import BaseMLEngine
    from .fashion_ml import FashionMLEngine
    from .forecasting_engine import ForecastingEngine
    from .nlp_engine import NLPEngine
    from .recommendation_engine import RecommendationEngine
    from .vision_engine import VisionEngine

__all__ = [
    "BaseMLEngine",
    "FashionMLEngine",
    "ForecastingEngine",
    "NLPEngine",
    "RecommendationEngine",
    "VisionEngine",
]

__version__ = "1.0.0"
