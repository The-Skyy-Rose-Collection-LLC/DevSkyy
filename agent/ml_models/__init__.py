"""
Machine Learning Models Module
Advanced ML capabilities for all DevSkyy agents
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base_ml_engine import BaseMLEngine
    from .fashion_ml import FashionMLEngine
    from .nlp_engine import NLPEngine
    from .vision_engine import VisionEngine
    from .forecasting_engine import ForecastingEngine
    from .recommendation_engine import RecommendationEngine

__all__ = [
    "BaseMLEngine",
    "FashionMLEngine",
    "NLPEngine",
    "VisionEngine",
    "ForecastingEngine",
    "RecommendationEngine",
]

__version__ = "1.0.0"
