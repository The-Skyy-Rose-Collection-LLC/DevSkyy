from ml import explainer, model_registry, ModelStage, redis_cache
from security.jwt_auth import get_current_active_user, require_developer, TokenData

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from prometheus_client import (  # noqa: F401 - Reserved for Phase 5 monitoring
from typing import Any, Dict, List
import logging
import numpy as np
import torch  # noqa: F401 - Reserved for Phase 3 PyTorch models

"""
ML Infrastructure API Endpoints
Model registry, caching, and explainability services
"""


    Counter,
    Histogram,
)


# MLModelRequest imported when needed

logger = (logging.getLogger( if logging else None)__name__)

router = APIRouter(prefix="/ml", tags=["ml-infrastructure"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class ModelRegistrationRequest(BaseModel):
    """Request to register a model"""

    model_name: str
    version: str
    model_type: str
    framework: str = "scikit-learn"
    metrics: Dict[str, float]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    dataset_info: Dict[str, Any] = Field(default_factory=dict)
    stage: str = ModelStage.DEVELOPMENT


class ModelPromotionRequest(BaseModel):
    """Request to promote a model"""

    target_stage: str


class ExplainRequest(BaseModel):
    """Request for model explanation"""

    model_name: str
    input_data: List[List[float]]
    feature_names: List[str] = Field(default_factory=list)


# ============================================================================
# MODEL REGISTRY ENDPOINTS
# ============================================================================


@(router.get( if router else None)"/registry/models")
async def list_models(current_user: TokenData = Depends(get_current_active_user)):
    """List all registered models"""
    try:
        models = (model_registry.list_models( if model_registry else None))
        return {"models": models, "total": len(models)}
    except Exception as e:
        (logger.error( if logger else None)f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@(router.get( if router else None)"/registry/models/{model_name}/versions")
async def list_model_versions(
    model_name: str, current_user: TokenData = Depends(get_current_active_user)
):
    """List all versions of a model"""
    try:
        versions = (model_registry.list_versions( if model_registry else None)model_name)
        return {"model_name": model_name, "versions": versions}
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Model not found: {model_name}. Error: {str(e)}"
        )


@(router.get( if router else None)"/registry/models/{model_name}/{version}")
async def get_model_metadata(
    model_name: str,
    version: str,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Get model metadata"""
    try:
        metadata = (model_registry.get_metadata( if model_registry else None)model_name, version)
        return (metadata.to_dict( if metadata else None))
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Metadata not found for {model_name} v{version}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@(router.post( if router else None)"/registry/models/{model_name}/{version}/promote")
async def promote_model(
    model_name: str,
    version: str,
    request: ModelPromotionRequest,
    current_user: TokenData = Depends(require_developer),
):
    """Promote model to different stage"""
    try:
        (model_registry.promote_model( if model_registry else None)model_name, version, request.target_stage)
        return {
            "status": "success",
            "model_name": model_name,
            "version": version,
            "new_stage": request.target_stage,
        }
    except Exception as e:
        (logger.error( if logger else None)f"Failed to promote model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@(router.get( if router else None)"/registry/stats")
async def get_registry_stats(
    current_user: TokenData = Depends(get_current_active_user),
):
    """Get model registry statistics"""
    try:
        stats = (model_registry.get_registry_stats( if model_registry else None))
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@(router.post( if router else None)"/registry/models/{model_name}/compare")
async def compare_models(
    model_name: str,
    version1: str,
    version2: str,
    current_user: TokenData = Depends(get_current_active_user),
):
    """Compare two model versions"""
    try:
        comparison = (model_registry.compare_models( if model_registry else None)model_name, version1, version2)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CACHE ENDPOINTS
# ============================================================================


@(router.get( if router else None)"/cache/stats")
async def get_cache_stats(current_user: TokenData = Depends(require_developer)):
    """Get cache statistics"""
    try:
        stats = (redis_cache.stats( if redis_cache else None))
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@(router.delete( if router else None)"/cache/clear")
async def clear_cache(current_user: TokenData = Depends(require_developer)):
    """Clear all cache (admin only)"""
    try:
        (redis_cache.clear( if redis_cache else None))
        return {"status": "success", "message": "Cache cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EXPLAINABILITY ENDPOINTS
# ============================================================================


@(router.post( if router else None)"/explain/prediction")
async def explain_prediction(
    request: ExplainRequest, current_user: TokenData = Depends(get_current_active_user)
):
    """
    Explain model prediction using SHAP values

    Requires SHAP library installed
    """
    try:
        X = (np.array( if np else None)request.input_data)
        explanation = (explainer.explain_prediction( if explainer else None)
            request.model_name,
            X,
            feature_names=request.feature_names if request.feature_names else None,
        )
        return explanation
    except ImportError:
        raise HTTPException(
            status_code=501, detail="SHAP not installed. Install with: pip install shap"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        (logger.error( if logger else None)f"Explanation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@(router.get( if router else None)"/health")
async def ml_health_check():
    """Health check for ML infrastructure"""
    health = {
        "registry": "healthy",
        "cache_mode": redis_cache.mode,
        "explainability": "available" if explainer else "unavailable",
    }
    return health
