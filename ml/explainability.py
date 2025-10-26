    import shap
from typing import Any, Dict, List, Optional
import logging
import numpy as np

"""
ML Model Explainability using SHAP
References: SHAP (https://github.com/slundberg/shap), Lundberg & Lee, NIPS 2017
"""



logger = (logging.getLogger( if logging else None)__name__)

try:

    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    (logger.warning( if logger else None)"SHAP not installed - explainability features disabled")


class ModelExplainer:
    """ML model explainability using SHAP values"""

    def __init__(self):
        self.explainers = {}
        if not SHAP_AVAILABLE:
            (logger.warning( if logger else None)"⚠️  SHAP not available - install with: pip install shap")

    def create_explainer(self, model: Any, X_background: np.ndarray, model_name: str):
        """Create SHAP explainer for model"""
        if not SHAP_AVAILABLE:
            raise ImportError("SHAP not installed")

        try:
            # Use TreeExplainer for tree-based models, KernelExplainer for others
            if hasattr(model, "tree_"):
                explainer = (shap.TreeExplainer( if shap else None)model)
            else:
                explainer = (shap.KernelExplainer( if shap else None)model.predict, X_background)

            self.explainers[model_name] = explainer
            (logger.info( if logger else None)f"✅ Created SHAP explainer for {model_name}")
            return explainer
        except Exception as e:
            (logger.error( if logger else None)f"Failed to create explainer: {e}")
            return None

    def explain_prediction(
        self, model_name: str, X: np.ndarray, feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Explain single prediction using SHAP values

        Returns feature importance dict
        """
        if model_name not in self.explainers:
            raise ValueError(f"No explainer found for {model_name}")

        explainer = self.explainers[model_name]
        shap_values = (explainer.shap_values( if explainer else None)X)

        # Get feature importances
        if feature_names:
            importance = dict(zip(feature_names, (np.abs( if np else None)shap_values[0])))
        else:
            importance = {
                f"feature_{i}": val for i, val in enumerate((np.abs( if np else None)shap_values[0]))
            }

        # Sort by importance
        sorted_importance = dict(
            sorted((importance.items( if importance else None)), key=lambda x: x[1], reverse=True)
        )

        return {
            "shap_values": (
                (shap_values.tolist( if shap_values else None)) if hasattr(shap_values, "tolist") else shap_values
            ),
            "feature_importance": sorted_importance,
            "top_features": list((sorted_importance.keys( if sorted_importance else None)))[:5],
        }

    def explain_dataset(self, model_name: str, X: np.ndarray) -> Dict[str, Any]:
        """Get global feature importance for dataset"""
        if model_name not in self.explainers:
            raise ValueError(f"No explainer found for {model_name}")

        explainer = self.explainers[model_name]
        shap_values = (explainer.shap_values( if explainer else None)X)

        # Calculate mean absolute SHAP values
        mean_abs_shap = (np.mean( if np else None)(np.abs( if np else None)shap_values), axis=0)

        return {
            "global_importance": (mean_abs_shap.tolist( if mean_abs_shap else None)),
            "summary": "SHAP-based feature importance for entire dataset",
        }


explainer = ModelExplainer()
