"""
ML Capabilities Module
=======================

Machine learning wrappers (sklearn, Prophet, trend extrapolation)
and the MLCapabilitiesModule that provides ML capabilities per agent type.
"""

import logging
import time
from typing import Any

from .types import MLPrediction, SuperAgentType

logger = logging.getLogger(__name__)


# =============================================================================
# ML Model Wrappers
# =============================================================================


class SklearnModelWrapper:
    """
    Wrapper for scikit-learn models that handles fitting and prediction.

    Supports on-demand fitting with provided training data.
    """

    def __init__(self, model: Any, task: str, fitted: bool = False):
        self.model = model
        self.task = task
        self.fitted = fitted
        self._last_confidence = 0.85

    def fit(self, X: Any, y: Any = None) -> "SklearnModelWrapper":
        """Fit the model with training data."""
        import numpy as np

        X_arr = np.array(X) if not hasattr(X, "shape") else X

        if self.task in ("clustering", "anomaly"):
            self.model.fit(X_arr)
        else:
            if y is None:
                raise ValueError(f"Target y required for {self.task} task")
            y_arr = np.array(y) if not hasattr(y, "shape") else y
            self.model.fit(X_arr, y_arr)

        self.fitted = True
        return self

    def predict(self, X: Any, **kwargs) -> Any:
        """Run prediction on input data."""
        import numpy as np

        X_arr = np.array(X) if not hasattr(X, "shape") else X

        # Ensure 2D input
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)

        if not self.fitted:
            # Auto-fit with synthetic data for demo purposes
            logger.warning(f"Model not fitted, using synthetic training for {self.task}")
            n_features = X_arr.shape[1]
            synthetic_X = np.random.randn(100, n_features)
            if self.task in ("clustering", "anomaly"):
                self.model.fit(synthetic_X)
            else:
                synthetic_y = (
                    np.random.randn(100)
                    if self.task == "regression"
                    else np.random.randint(0, 2, 100)
                )
                self.model.fit(synthetic_X, synthetic_y)
            self.fitted = True
            self._last_confidence = 0.6  # Lower confidence for auto-fitted

        result = self.model.predict(X_arr)

        # For classification, try to get probabilities
        if self.task == "classification" and hasattr(self.model, "predict_proba"):
            try:
                proba = self.model.predict_proba(X_arr)
                self._last_confidence = float(np.max(proba))
            except Exception:
                self._last_confidence = 0.75

        return result.tolist() if hasattr(result, "tolist") else result

    def get_confidence(self) -> float:
        """Return confidence score from last prediction."""
        return self._last_confidence

    def __call__(self, X: Any, **kwargs) -> Any:
        """Make wrapper callable."""
        return self.predict(X, **kwargs)


class ProphetModelWrapper:
    """
    Wrapper for Facebook Prophet time series forecasting.

    Handles data format conversion and prediction periods.
    """

    def __init__(self, model: Any, task: str = "forecast"):
        self.model = model
        self.task = task
        self.fitted = False
        self._last_confidence = 0.8

    def fit(self, df: Any) -> "ProphetModelWrapper":
        """Fit Prophet model with time series data."""
        import pandas as pd

        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)

        if "ds" not in df.columns or "y" not in df.columns:
            raise ValueError("Prophet requires DataFrame with 'ds' and 'y' columns")

        self.model.fit(df)
        self.fitted = True
        return self

    def predict(self, periods: int = 30, **kwargs) -> Any:
        """Generate forecasts for future periods."""
        import pandas as pd

        if not self.fitted:
            # Create synthetic historical data for demo
            logger.warning("Prophet not fitted, using synthetic data")
            dates = pd.date_range(start="2024-01-01", periods=365, freq="D")
            import numpy as np

            values = 100 + np.cumsum(np.random.randn(365) * 2)
            df = pd.DataFrame({"ds": dates, "y": values})
            self.model.fit(df)
            self.fitted = True
            self._last_confidence = 0.6

        freq = kwargs.get("freq", "D")
        future = self.model.make_future_dataframe(periods=periods, freq=freq)
        forecast = self.model.predict(future)

        # Calculate confidence from uncertainty intervals
        if "yhat_lower" in forecast.columns and "yhat_upper" in forecast.columns:
            last_rows = forecast.tail(periods)
            interval_width = (last_rows["yhat_upper"] - last_rows["yhat_lower"]).mean()
            mean_value = last_rows["yhat"].mean()
            if mean_value > 0:
                self._last_confidence = max(0.5, 1.0 - (interval_width / mean_value / 4))

        return {
            "forecast": forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
            .tail(periods)
            .to_dict("records"),
            "periods": periods,
            "fitted": self.fitted,
        }

    def get_confidence(self) -> float:
        """Return confidence score from last prediction."""
        return self._last_confidence

    def __call__(self, periods: int = 30, **kwargs) -> Any:
        """Make wrapper callable."""
        return self.predict(periods, **kwargs)


class TrendExtrapolationWrapper:
    """
    Simple trend extrapolation fallback when Prophet is not available.

    Uses linear regression for basic forecasting.
    """

    def __init__(self):
        self.slope = 0.0
        self.intercept = 0.0
        self.fitted = False
        self._last_confidence = 0.6

    def fit(self, data: list | Any) -> "TrendExtrapolationWrapper":
        """Fit linear trend to data."""
        import numpy as np

        if hasattr(data, "tolist"):
            values = data.tolist()
        elif isinstance(data, list):
            values = data
        else:
            values = list(data)

        n = len(values)
        if n < 2:
            return self

        x = np.arange(n)
        y = np.array(values)

        # Simple linear regression
        x_mean = x.mean()
        y_mean = y.mean()

        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)

        if denominator > 0:
            self.slope = numerator / denominator
            self.intercept = y_mean - self.slope * x_mean
        else:
            self.slope = 0
            self.intercept = y_mean

        self.fitted = True
        return self

    def predict(self, periods: int = 30, **kwargs) -> Any:
        """Extrapolate trend for future periods."""
        if not self.fitted:
            logger.warning("TrendExtrapolation not fitted, returning baseline")
            return {
                "forecast": [{"period": i, "value": 100.0} for i in range(periods)],
                "confidence": 0.5,
            }

        start = kwargs.get("start_index", 0)
        forecasts = []

        for i in range(periods):
            idx = start + i
            value = self.intercept + self.slope * idx
            forecasts.append({"period": i, "value": value})

        return {
            "forecast": forecasts,
            "slope": self.slope,
            "intercept": self.intercept,
        }

    def get_confidence(self) -> float:
        """Return confidence score."""
        return self._last_confidence if self.fitted else 0.5

    def __call__(self, periods: int = 30, **kwargs) -> Any:
        """Make wrapper callable."""
        return self.predict(periods, **kwargs)


# =============================================================================
# ML Capabilities Module
# =============================================================================


class MLCapabilitiesModule:
    """
    Machine Learning capabilities for SuperAgents.

    Capabilities per agent type:
    - Commerce: Demand forecasting, dynamic pricing, inventory optimization
    - Creative: Style transfer, image classification, quality scoring
    - Marketing: Sentiment analysis, trend prediction, audience segmentation
    - Support: Intent classification, FAQ matching, escalation prediction
    - Operations: Anomaly detection, log analysis, performance prediction
    - Analytics: Time series forecasting, clustering, recommendation
    """

    def __init__(self, agent_type: SuperAgentType):
        self.agent_type = agent_type
        self._models: dict[str, Any] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize ML models for this agent type"""
        logger.info(f"Initializing ML capabilities for {self.agent_type}")

        # Load models based on agent type
        model_configs = self._get_model_configs()
        for name, config in model_configs.items():
            try:
                self._models[name] = await self._load_model(config)
            except Exception as e:
                logger.warning(f"Failed to load model {name}: {e}")

        self._initialized = True

    def _get_model_configs(self) -> dict[str, dict]:
        """Get ML model configurations for this agent type"""
        configs = {
            SuperAgentType.COMMERCE: {
                "demand_forecaster": {"type": "prophet", "task": "time_series"},
                "price_optimizer": {"type": "sklearn", "task": "regression"},
                "inventory_predictor": {"type": "sklearn", "task": "regression"},
            },
            SuperAgentType.CREATIVE: {
                "style_classifier": {
                    "type": "transformers",
                    "model": "google/vit-base-patch16-224",
                },
                "quality_scorer": {"type": "custom", "task": "image_quality"},
            },
            SuperAgentType.MARKETING: {
                "sentiment_analyzer": {
                    "type": "transformers",
                    "model": "cardiffnlp/twitter-roberta-base-sentiment",
                },
                "trend_predictor": {"type": "prophet", "task": "trend"},
            },
            SuperAgentType.SUPPORT: {
                "intent_classifier": {"type": "transformers", "model": "facebook/bart-large-mnli"},
                "escalation_predictor": {"type": "sklearn", "task": "classification"},
            },
            SuperAgentType.OPERATIONS: {
                "anomaly_detector": {"type": "sklearn", "task": "anomaly"},
                "performance_predictor": {"type": "sklearn", "task": "regression"},
            },
            SuperAgentType.ANALYTICS: {
                "forecaster": {"type": "prophet", "task": "forecast"},
                "clusterer": {"type": "sklearn", "task": "clustering"},
            },
        }
        return configs.get(self.agent_type, {})

    async def _load_model(self, config: dict) -> Any:
        """Load a specific ML model based on configuration."""
        model_type = config.get("type")
        task = config.get("task", "default")

        if model_type == "transformers":
            try:
                from transformers import pipeline

                model_name = config.get("model", "distilbert-base-uncased")
                if "sentiment" in model_name or "sentiment" in task:
                    return pipeline("sentiment-analysis", model=model_name)
                elif "mnli" in model_name or "classification" in task:
                    return pipeline("zero-shot-classification", model=model_name)
                elif "vit" in model_name or "image" in task:
                    return pipeline("image-classification", model=model_name)
                else:
                    return pipeline("text-classification", model=model_name)
            except ImportError:
                logger.warning("transformers not installed, using sklearn fallback")
                return self._create_sklearn_model({"task": "classification"})

        elif model_type == "sklearn":
            return self._create_sklearn_model(config)

        elif model_type == "prophet":
            return self._create_prophet_model(config)

        return None

    def _create_sklearn_model(self, config: dict) -> Any:
        """Create a scikit-learn model wrapper."""
        task = config.get("task", "regression")

        try:
            if task == "regression":
                from sklearn.linear_model import Ridge

                model = Ridge()
            elif task == "classification":
                from sklearn.linear_model import LogisticRegression

                model = LogisticRegression(max_iter=1000)
            elif task == "clustering":
                from sklearn.cluster import KMeans

                model = KMeans(n_clusters=3, n_init=10)
            elif task == "anomaly":
                from sklearn.ensemble import IsolationForest

                model = IsolationForest(contamination=0.1)
            else:
                from sklearn.linear_model import Ridge

                model = Ridge()

            return SklearnModelWrapper(model=model, task=task, fitted=False)

        except ImportError:
            logger.warning("scikit-learn not installed")
            return None

    def _create_prophet_model(self, config: dict) -> Any:
        """Create a Prophet model wrapper for time series forecasting."""
        try:
            from prophet import Prophet

            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
            )
            return ProphetModelWrapper(model=model, task=config.get("task", "forecast"))

        except ImportError:
            logger.warning("prophet not installed, using trend extrapolation fallback")
            return TrendExtrapolationWrapper()

    async def predict(
        self,
        model_name: str,
        input_data: Any,
        **kwargs,
    ) -> MLPrediction:
        """Run prediction using specified model."""
        start_time = time.time()

        model = self._models.get(model_name)
        if not model:
            return MLPrediction(
                task=model_name,
                prediction=None,
                confidence=0.0,
                model_used="none",
                latency_ms=0.0,
                metadata={"error": f"Model {model_name} not found"},
            )

        try:
            if callable(model):
                result = model(input_data)
                prediction = result[0] if isinstance(result, list) else result
                confidence = self._extract_confidence(result)
            elif hasattr(model, "predict"):
                prediction = model.predict(input_data, **kwargs)
                confidence = 0.85
            elif isinstance(
                model, SklearnModelWrapper | ProphetModelWrapper | TrendExtrapolationWrapper
            ):
                prediction = model.predict(input_data, **kwargs)
                confidence = model.get_confidence()
            else:
                prediction = {"input": str(input_data)[:100], "model_type": str(type(model))}
                confidence = 0.5

            latency = (time.time() - start_time) * 1000

            return MLPrediction(
                task=model_name,
                prediction=prediction,
                confidence=confidence,
                model_used=model_name,
                latency_ms=latency,
                metadata=kwargs,
            )

        except Exception as e:
            return MLPrediction(
                task=model_name,
                prediction=None,
                confidence=0.0,
                model_used=model_name,
                latency_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
            )

    def _extract_confidence(self, result: Any) -> float:
        """Extract confidence score from model result."""
        if isinstance(result, dict):
            return result.get("score", result.get("confidence", 0.8))
        elif isinstance(result, list) and len(result) > 0:
            first = result[0]
            if isinstance(first, dict):
                return first.get("score", first.get("confidence", 0.8))
        return 0.8

    def list_available_models(self) -> list[str]:
        """List available ML models for this agent"""
        return list(self._models.keys())


__all__ = [
    "SklearnModelWrapper",
    "ProphetModelWrapper",
    "TrendExtrapolationWrapper",
    "MLCapabilitiesModule",
]
