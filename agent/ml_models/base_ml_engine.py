"""
Base ML Engine
Foundational machine learning capabilities for all agents
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


logger = logging.getLogger(__name__)


class BaseMLEngine(ABC):
    """
    Base machine learning engine providing common ML operations

    Features:
    - Data preprocessing and normalization
    - Model training and evaluation
    - Prediction with confidence scores
    - Model persistence and versioning
    - A/B testing support
    - Performance monitoring
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.training_history = []
        self.performance_metrics = {}
        self.version = "1.0.0"

        logger.info(f"🤖 ML Engine initialized: {model_name}")

    @abstractmethod
    async def train(self, X: np.ndarray, y: np.ndarray, **kwargs) -> dict[str, Any]:
        """Train the ML model"""

    @abstractmethod
    async def predict(self, X: np.ndarray, **kwargs) -> tuple[np.ndarray, np.ndarray]:
        """Make predictions with confidence scores"""

    async def preprocess_data(self, data: np.ndarray, fit: bool = False) -> np.ndarray:
        """
        Preprocess and normalize data

        Args:
            data: Input data array
            fit: Whether to fit the scaler (training) or just transform (inference)

        Returns:
            Preprocessed data
        """
        try:
            if fit:
                return self.scaler.fit_transform(data)
            else:
                return self.scaler.transform(data)
        except Exception as e:
            logger.error(f"Data preprocessing failed: {e}")
            return data

    async def split_data(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Split data into training and testing sets"""
        return train_test_split(X, y, test_size=test_size, random_state=random_state)

    async def evaluate_model(self, X_test: np.ndarray, y_test: np.ndarray) -> dict[str, float]:
        """
        Evaluate model performance

        Returns:
            Dictionary of performance metrics
        """
        try:
            predictions, confidence = await self.predict(X_test)

            # Calculate metrics
            from sklearn.metrics import (
                accuracy_score,
                f1_score,
                precision_score,
                recall_score,
            )

            metrics = {
                "accuracy": float(accuracy_score(y_test, predictions)),
                "precision": float(precision_score(y_test, predictions, average="weighted", zero_division=0)),
                "recall": float(recall_score(y_test, predictions, average="weighted", zero_division=0)),
                "f1_score": float(f1_score(y_test, predictions, average="weighted", zero_division=0)),
                "avg_confidence": float(np.mean(confidence)),
                "timestamp": datetime.utcnow().isoformat(),
            }

            self.performance_metrics = metrics
            return metrics

        except Exception as e:
            logger.error(f"Model evaluation failed: {e}")
            return {"error": str(e)}

    async def get_feature_importance(self) -> dict[str, float] | None:
        """Get feature importance scores if model supports it"""
        try:
            if hasattr(self.model, "feature_importances_"):
                return {
                    f"feature_{i}": float(importance) for i, importance in enumerate(self.model.feature_importances_)
                }
            elif hasattr(self.model, "coef_"):
                return {f"feature_{i}": float(abs(coef)) for i, coef in enumerate(self.model.coef_[0])}
            return None
        except Exception as e:
            logger.error(f"Failed to get feature importance: {e}")
            return None

    async def save_model(self, path: str) -> bool:
        """Save model to disk"""
        try:
            import joblib

            model_data = {
                "model": self.model,
                "scaler": self.scaler,
                "label_encoder": self.label_encoder,
                "is_trained": self.is_trained,
                "version": self.version,
                "performance_metrics": self.performance_metrics,
                "training_history": self.training_history,
            }

            joblib.dump(model_data, path)
            logger.info(f"✅ Model saved to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    async def load_model(self, path: str) -> bool:
        """Load model from disk"""
        try:
            import joblib

            model_data = joblib.load(path)

            self.model = model_data["model"]
            self.scaler = model_data["scaler"]
            self.label_encoder = model_data["label_encoder"]
            self.is_trained = model_data["is_trained"]
            self.version = model_data.get("version", "1.0.0")
            self.performance_metrics = model_data.get("performance_metrics", {})
            self.training_history = model_data.get("training_history", [])

            logger.info(f"✅ Model loaded from {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    async def get_model_info(self) -> dict[str, Any]:
        """Get comprehensive model information"""
        return {
            "name": self.model_name,
            "version": self.version,
            "is_trained": self.is_trained,
            "performance_metrics": self.performance_metrics,
            "training_history": self.training_history[-5:],  # Last 5 training sessions
            "model_type": str(type(self.model).__name__) if self.model else None,
        }

    async def continuous_learning(
        self, new_X: np.ndarray, new_y: np.ndarray, retrain_threshold: float = 0.1
    ) -> dict[str, Any]:
        """
        Implement continuous learning

        Args:
            new_X: New training data
            new_y: New labels
            retrain_threshold: Performance drop threshold to trigger retraining

        Returns:
            Dictionary with learning results
        """
        try:
            # Evaluate current performance on new data
            current_metrics = await self.evaluate_model(new_X, new_y)

            # Check if performance has degraded
            if self.performance_metrics:
                prev_f1 = self.performance_metrics.get("f1_score", 0)
                current_f1 = current_metrics.get("f1_score", 0)

                if prev_f1 - current_f1 > retrain_threshold:
                    logger.warning(f"Performance degradation detected: {prev_f1:.3f} -> {current_f1:.3f}")

                    # Retrain model
                    train_result = await self.train(new_X, new_y)

                    return {
                        "action": "retrained",
                        "previous_f1": prev_f1,
                        "current_f1": current_f1,
                        "new_f1": train_result.get("f1_score"),
                        "improvement": train_result.get("f1_score", 0) - prev_f1,
                    }

            return {"action": "no_action_needed", "metrics": current_metrics}

        except Exception as e:
            logger.error(f"Continuous learning failed: {e}")
            return {"error": str(e)}
