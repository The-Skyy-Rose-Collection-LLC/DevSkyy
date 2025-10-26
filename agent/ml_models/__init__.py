    from .forecasting_engine import ForecastingEngine
    from .recommendation_engine import RecommendationEngine

    from .base_ml_engine import BaseMLEngine
    from .fashion_ml import FashionMLEngine
    from .nlp_engine import NLPEngine
    from .vision_engine import VisionEngine
from typing import TYPE_CHECKING

"""
Machine Learning Models Module
Advanced ML capabilities for all DevSkyy agents
"""


if TYPE_CHECKING:

__all__ = [
    "BaseMLEngine",
    "FashionMLEngine",
    "NLPEngine",
    "VisionEngine",
    "ForecastingEngine",
    "RecommendationEngine",
]

__VERSION__ =  "1.0.0"
