"""Machine Learning Prediction API Endpoints.

This module provides endpoints for:
- ML predictions (trend prediction, customer segmentation, demand forecasting, etc.)
- Integration with agents/ml_module.py

Version: 1.0.0
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from agents.base_super_agent.ml_module import MLCapabilitiesModule
from agents.base_super_agent.types import MLPrediction as AgentMLPrediction
from agents.base_super_agent.types import SuperAgentType
from core.task_status_store import TaskStatusStore, get_initialized_task_status_store
from security.jwt_oauth2_auth import TokenPayload, get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/ml", tags=["Machine Learning"])


# =============================================================================
# Enums & Models
# =============================================================================


class MLModelType(StrEnum):
    """Machine learning model types."""

    TREND_PREDICTION = "trend_prediction"
    CUSTOMER_SEGMENTATION = "customer_segmentation"
    DEMAND_FORECASTING = "demand_forecasting"
    DYNAMIC_PRICING = "dynamic_pricing"
    SENTIMENT_ANALYSIS = "sentiment_analysis"


# MLCapabilitiesModule carries no version string of its own; this identifies the
# wiring/adapter version surfaced in the response.
_AGENT_ML_VERSION = "agent-ml-1"

# Map each public MLModelType to the (agent type, internal model name) that the
# MLCapabilitiesModule registry actually exposes. Exhaustive over MLModelType.
_MODEL_TYPE_MAP: dict[str, tuple[SuperAgentType, str]] = {
    MLModelType.TREND_PREDICTION.value: (SuperAgentType.MARKETING, "trend_predictor"),
    MLModelType.CUSTOMER_SEGMENTATION.value: (SuperAgentType.ANALYTICS, "clusterer"),
    MLModelType.DEMAND_FORECASTING.value: (SuperAgentType.COMMERCE, "demand_forecaster"),
    MLModelType.DYNAMIC_PRICING.value: (SuperAgentType.COMMERCE, "price_optimizer"),
    MLModelType.SENTIMENT_ANALYSIS.value: (SuperAgentType.MARKETING, "sentiment_analyzer"),
}


class MLPredictionRequest(BaseModel):
    """Request model for ML predictions."""

    model_type: MLModelType = Field(..., description="ML model to use for prediction")
    data: dict[str, Any] = Field(
        ..., description="Input data for prediction (structure varies by model type)"
    )
    confidence_threshold: float = Field(
        default=0.7,
        description="Minimum confidence threshold for predictions (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )


class MLPrediction(BaseModel):
    """Individual ML prediction result."""

    label: str
    confidence: float
    value: Any
    metadata: dict[str, Any] | None = None


class MLPredictionResponse(BaseModel):
    """Response model for ML predictions."""

    prediction_id: str
    status: str
    timestamp: str
    model_type: str
    model_version: str
    predictions: list[MLPrediction]
    metrics: dict[str, Any]


# =============================================================================
# Background Task Processing
# =============================================================================


async def _run_ml_prediction_background(
    prediction_id: str,
    model_type: str,
    data: dict[str, Any],
    confidence_threshold: float,
    user_id: str,
    store: TaskStatusStore,
) -> None:
    """Run ML prediction in the background for heavy computation.

    This prevents request timeouts for complex ML models like demand forecasting
    and customer segmentation which may take significant time.

    Args:
        prediction_id: Unique prediction identifier
        model_type: Type of ML model to run
        data: Input data for the model
        confidence_threshold: Minimum confidence for predictions
        user_id: ID of user who initiated the prediction
        store: TaskStatusStore for persisting status (Redis-backed)
    """
    logger.info(f"Background ML task started: {prediction_id}")

    started_at = datetime.now(UTC).isoformat()

    try:
        await store.set_status(
            prediction_id,
            {
                "status": "processing",
                "model_type": model_type,
                "started_at": started_at,
            },
        )

        predictions, metrics, pred_status = await _compute_prediction(model_type, data)

        await store.set_status(
            prediction_id,
            {
                "status": pred_status,
                "model_type": model_type,
                "model_version": _AGENT_ML_VERSION,
                "started_at": started_at,
                "completed_at": datetime.now(UTC).isoformat(),
                "predictions": [p.model_dump() for p in predictions],
                "metrics": metrics,
            },
        )
        logger.info("Background ML task %s: %s", pred_status, prediction_id)

    except HTTPException as e:
        logger.warning("Background ML task unavailable %s: %s", prediction_id, e.detail)
        await store.set_status(
            prediction_id,
            {
                "status": "failed",
                "model_type": model_type,
                "started_at": started_at,
                "completed_at": datetime.now(UTC).isoformat(),
                "error": str(e.detail),
            },
        )

    except Exception as e:
        logger.error("Background ML task failed: %s: %s", prediction_id, e, exc_info=True)
        await store.set_status(
            prediction_id,
            {
                "status": "failed",
                "model_type": model_type,
                "started_at": started_at,
                "completed_at": datetime.now(UTC).isoformat(),
                "error": str(e),
            },
        )


def _reshape_agent_result(
    result: AgentMLPrediction, model_name: str
) -> tuple[list[MLPrediction], dict[str, Any]]:
    """Adapt the agent-layer MLPrediction dataclass into the API response shape.

    ``predict()`` never raises; it signals failure with ``prediction is None`` or
    ``confidence == 0.0``. In that case return an empty prediction list so the
    endpoint reports ``status="failed"`` honestly instead of fabricating output.
    """
    metrics: dict[str, Any] = {
        "latency_ms": result.latency_ms,
        "model_used": result.model_used,
    }
    if result.prediction is None or result.confidence == 0.0:
        metrics["error"] = (result.metadata or {}).get("error", "prediction unavailable")
        return [], metrics

    # predict() returns model_used="none" on the not-found path (a truthy string),
    # so fall back to the requested model_name only when it is that sentinel.
    label = result.model_used if result.model_used != "none" else model_name
    prediction = MLPrediction(
        label=label,
        confidence=result.confidence,
        value=result.prediction,
        metadata=result.metadata,
    )
    return [prediction], metrics


async def _compute_prediction(
    model_type: str, data: dict[str, Any]
) -> tuple[list[MLPrediction], dict[str, Any], str]:
    """Run a real ML prediction for ``model_type`` via MLCapabilitiesModule.

    Returns ``(predictions, metrics, status)`` where status is ``"completed"`` or
    ``"failed"`` (degraded/unfitted model). Raises ``HTTPException(503)`` when the
    ML module cannot initialize or the model is not available for its agent type;
    the sync endpoint surfaces that as 503 and the background task stores it as a
    failed status.
    """
    agent_type, model_name = _MODEL_TYPE_MAP[model_type]
    module = MLCapabilitiesModule(agent_type)
    try:
        await module.initialize()
    except Exception as e:
        logger.exception("ML module init failed for %s", model_type)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML module is unavailable",
        ) from e

    if model_name not in module.list_available_models():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model for '{model_type}' is unavailable",
        )

    result = await module.predict(model_name, data)
    predictions, metrics = _reshape_agent_result(result, model_name)
    return predictions, metrics, "completed" if predictions else "failed"


# =============================================================================
# Endpoints
# =============================================================================


class MLTaskStatusResponse(BaseModel):
    """Response for ML prediction task status check."""

    prediction_id: str
    status: str  # pending, processing, completed, failed
    model_type: str | None = None
    model_version: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    predictions: list[MLPrediction] | None = None
    metrics: dict[str, Any] | None = None
    error: str | None = None


@router.post("/predict", response_model=MLPredictionResponse, status_code=status.HTTP_200_OK)
async def predict(
    request: MLPredictionRequest,
    background_tasks: BackgroundTasks,
    user: TokenPayload = Depends(get_current_user),
    store: TaskStatusStore = Depends(get_initialized_task_status_store),
) -> MLPredictionResponse:
    """Run machine learning predictions for fashion e-commerce.

    Heavy computation models (demand_forecasting, customer_segmentation) run in
    the background. Use GET /ml/predict/{prediction_id}/status to check progress.

    The Advanced ML Engine provides state-of-the-art predictions for:

    1. **Trend Prediction**: Identify emerging fashion trends
       - Input: {items: ["item1", "item2"], time_horizon: "3_months"}

    2. **Customer Segmentation**: Group customers by behavior (background)
       - Input: {customer_data: [{age, location, purchase_history}], num_segments: 5}

    3. **Demand Forecasting**: Predict product demand (background)
       - Input: {product_id: "PROD123", forecast_days: 30, historical_data: [...]}

    4. **Dynamic Pricing**: Optimize prices using ML
       - Input: {product_id: "PROD123", market_data: {...}, constraints: {...}}

    5. **Sentiment Analysis**: Analyze customer sentiment
       - Input: {text: "Customer review text", analyze_aspects: true}

    Args:
        request: Prediction configuration (model_type, data, confidence_threshold)
        background_tasks: FastAPI background tasks handler
        user: Authenticated user (from JWT token)

    Returns:
        MLPredictionResponse with predictions or task reference for background ops

    Raises:
        HTTPException: If prediction fails
    """
    prediction_id = str(uuid4())
    logger.info(
        f"Starting ML prediction {prediction_id} for user {user.sub}: {request.model_type.value}"
    )

    # Heavy models run in background to prevent timeouts
    heavy_models = {MLModelType.DEMAND_FORECASTING, MLModelType.CUSTOMER_SEGMENTATION}

    if request.model_type in heavy_models:
        # Start background task with Redis-backed store
        background_tasks.add_task(
            _run_ml_prediction_background,
            prediction_id,
            request.model_type.value,
            request.data,
            request.confidence_threshold,
            user.sub,
            store,
        )

        # Return immediately with task reference
        return MLPredictionResponse(
            prediction_id=prediction_id,
            status="processing",
            timestamp=datetime.now(UTC).isoformat(),
            model_type=request.model_type.value,
            model_version="v2.1.0",
            predictions=[],
            metrics={"message": "Task running in background. Poll status endpoint for results."},
        )

    predictions, metrics, pred_status = await _compute_prediction(
        request.model_type.value, request.data
    )

    return MLPredictionResponse(
        prediction_id=prediction_id,
        status=pred_status,
        timestamp=datetime.now(UTC).isoformat(),
        model_type=request.model_type.value,
        model_version=_AGENT_ML_VERSION,
        predictions=predictions,
        metrics=metrics,
    )


@router.get(
    "/predict/{prediction_id}/status",
    response_model=MLTaskStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_prediction_status(
    prediction_id: str,
    user: TokenPayload = Depends(get_current_user),
    store: TaskStatusStore = Depends(get_initialized_task_status_store),
) -> MLTaskStatusResponse:
    """Get the status of a background ML prediction.

    Poll this endpoint to check progress of heavy ML models like
    demand forecasting and customer segmentation.

    Args:
        prediction_id: The prediction ID returned from POST /predict
        user: Authenticated user (from JWT token)
        store: TaskStatusStore for retrieving status (Redis-backed)

    Returns:
        MLTaskStatusResponse with current status and results when complete

    Raises:
        HTTPException: If prediction not found
    """
    status_data = await store.get_status(prediction_id)

    if status_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction {prediction_id} not found",
        )

    predictions = None
    if status_data.get("predictions"):
        predictions = [
            MLPrediction(
                label=p["label"],
                confidence=p["confidence"],
                value=p["value"],
                metadata=p.get("metadata"),
            )
            for p in status_data["predictions"]
        ]

    return MLTaskStatusResponse(
        prediction_id=prediction_id,
        status=status_data.get("status", "unknown"),
        model_type=status_data.get("model_type"),
        model_version=status_data.get("model_version"),
        started_at=status_data.get("started_at"),
        completed_at=status_data.get("completed_at"),
        predictions=predictions,
        metrics=status_data.get("metrics"),
        error=status_data.get("error"),
    )
