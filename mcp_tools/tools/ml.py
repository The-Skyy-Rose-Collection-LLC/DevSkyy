"""Machine learning prediction tool."""

from typing import Any

from pydantic import Field

from mcp_tools.api_client import _format_response, _make_api_request
from mcp_tools.security import secure_tool
from mcp_tools.server import PTC_CALLER, mcp
from mcp_tools.types import BaseAgentInput, MLModelType


class MLPredictionInput(BaseAgentInput):
    """Input for machine learning predictions."""

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


@mcp.tool(
    name="devskyy_ml_prediction",
    annotations={
        "title": "DevSkyy ML Prediction Engine",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
        "allowed_callers": [PTC_CALLER],
        "input_examples": [
            {
                "model_type": "trend_prediction",
                "data": {"items": ["oversized_blazers", "cargo_pants"], "time_horizon": "3_months"},
                "confidence_threshold": 0.7,
            },
            {
                "model_type": "customer_segmentation",
                "data": {"customer_data": [{"age": 25, "location": "US"}], "num_segments": 5},
            },
            {
                "model_type": "demand_forecasting",
                "data": {"product_id": "PROD123", "forecast_days": 30},
                "confidence_threshold": 0.8,
            },
            {
                "model_type": "dynamic_pricing",
                "data": {"product_id": "PROD123", "market_data": {"competitor_price": 49.99}},
            },
        ],
    },
)
@secure_tool("ml_prediction")
async def ml_prediction(params: MLPredictionInput) -> str:
    """Run machine learning predictions for fashion e-commerce.

    The Advanced ML Engine provides state-of-the-art predictions for:

    1. **Trend Prediction**: Identify emerging fashion trends
       - Input: {items: ["item1", "item2"], time_horizon: "3_months"}

    2. **Customer Segmentation**: Group customers by behavior
       - Input: {customer_data: [{age, location, purchase_history}], num_segments: 5}

    3. **Demand Forecasting**: Predict product demand
       - Input: {product_id: "PROD123", forecast_days: 30, historical_data: [...]}

    4. **Dynamic Pricing**: Optimize prices using ML
       - Input: {product_id: "PROD123", market_data: {...}, constraints: {...}}

    5. **Sentiment Analysis**: Analyze customer sentiment
       - Input: {text: "Customer review text", analyze_aspects: true}

    Models use transfer learning and online learning for continuous improvement.

    Args:
        params (MLPredictionInput): Prediction configuration containing:
            - model_type: Type of ML model to use
            - data: Input data (structure varies by model)
            - confidence_threshold: Minimum confidence (0.0-1.0)
            - response_format: Output format (markdown/json)

    Returns:
        str: Predictions with confidence scores and recommendations

    Example:
        >>> ml_prediction({
        ...     "model_type": "trend_prediction",
        ...     "data": {"items": ["oversized_blazers", "cargo_pants"]},
        ...     "confidence_threshold": 0.7
        ... })
    """
    data = await _make_api_request(
        f"ml/predict/{params.model_type.value}",
        method="POST",
        data={"data": params.data, "confidence_threshold": params.confidence_threshold},
    )

    return _format_response(
        data, params.response_format, f"ML Prediction: {params.model_type.value}"
    )
