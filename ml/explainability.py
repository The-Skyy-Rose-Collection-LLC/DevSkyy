import logging
from typing import Any

import numpy as np
import shap


"""
ML Model Explainability using SHAP
References: SHAP (https://github.com/slundberg/shap), Lundberg & Lee, NIPS 2017
"""

logger = logging.getLogger(__name__)

try:

    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP not installed - explainability features disabled")


class ModelExplainer:
    """ML model explainability using SHAP values"""

    def __init__(self):
        self.explainers = {}
        if not SHAP_AVAILABLE:
            logger.warning("⚠️  SHAP not available - install with: pip install shap")

    def create_explainer(self, model: Any, X_background: np.ndarray, model_name: str):
        """Create SHAP explainer for model"""
        if not SHAP_AVAILABLE:
            raise ImportError("SHAP not installed")

        try:
            # Use TreeExplainer for tree-based models, KernelExplainer for others
            if hasattr(model, "tree_"):
                explainer = shap.TreeExplainer(model)
            else:
                explainer = shap.KernelExplainer(model.predict, X_background)

            self.explainers[model_name] = explainer
            logger.info(f"✅ Created SHAP explainer for {model_name}")
            return explainer
        except Exception as e:
            logger.error(f"Failed to create explainer: {e}")
            return None

    def explain_prediction(
        self, model_name: str, X: np.ndarray, feature_names: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Explain single prediction using SHAP values

        Returns feature importance dict
        """
        if model_name not in self.explainers:
            raise ValueError(f"No explainer found for {model_name}")

        explainer = self.explainers[model_name]
        shap_values = explainer.shap_values(X)

        # Get feature importances
        if feature_names:
            importance = dict(zip(feature_names, np.abs(shap_values[0]), strict=False))
        else:
            importance = {f"feature_{i}": val for i, val in enumerate(np.abs(shap_values[0]))}

        # Sort by importance
        sorted_importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

        return {
            "shap_values": (shap_values.tolist() if hasattr(shap_values, "tolist") else shap_values),
            "feature_importance": sorted_importance,
            "top_features": list(sorted_importance.keys())[:5],
        }

    def explain_dataset(self, model_name: str, X: np.ndarray) -> dict[str, Any]:
        """Get global feature importance for dataset"""
        if model_name not in self.explainers:
            raise ValueError(f"No explainer found for {model_name}")

        explainer = self.explainers[model_name]
        shap_values = explainer.shap_values(X)

        # Calculate mean absolute SHAP values
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)

        return {
            "global_importance": mean_abs_shap.tolist(),
            "summary": "SHAP-based feature importance for entire dataset",
        }


explainer = ModelExplainer()
