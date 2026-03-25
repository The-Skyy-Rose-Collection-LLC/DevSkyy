"""Shared enums and base input model for all MCP tools."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ResponseFormat(StrEnum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


class AgentCategory(StrEnum):
    """DevSkyy agent categories."""

    INFRASTRUCTURE = "infrastructure"
    AI_INTELLIGENCE = "ai_intelligence"
    ECOMMERCE = "ecommerce"
    MARKETING = "marketing"
    CONTENT = "content"
    INTEGRATION = "integration"
    ADVANCED = "advanced"
    FRONTEND = "frontend"


class MLModelType(StrEnum):
    """Machine learning model types."""

    TREND_PREDICTION = "trend_prediction"
    CUSTOMER_SEGMENTATION = "customer_segmentation"
    DEMAND_FORECASTING = "demand_forecasting"
    DYNAMIC_PRICING = "dynamic_pricing"
    SENTIMENT_ANALYSIS = "sentiment_analysis"


class BaseAgentInput(BaseModel):
    """Base input model for agent operations."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for structured data",
    )
