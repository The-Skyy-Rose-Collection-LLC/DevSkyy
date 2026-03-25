"""Virtual try-on tools: single, batch, AI model generation, status."""

from typing import Any, Literal

from pydantic import Field

from mcp_tools.api_client import _format_response, _make_api_request
from mcp_tools.security import secure_tool
from mcp_tools.server import PTC_CALLER, mcp
from mcp_tools.types import BaseAgentInput, ResponseFormat

# ===========================
# Input Models
# ===========================


class VirtualTryOnInput(BaseAgentInput):
    """Input for virtual try-on generation."""

    model_image_url: str = Field(
        ...,
        description="URL of the model/person image to apply garment to",
        max_length=2000,
    )
    garment_image_url: str = Field(
        ...,
        description="URL of the garment image to apply",
        max_length=2000,
    )
    category: Literal["tops", "bottoms", "dresses", "outerwear", "full_body"] = Field(
        default="tops",
        description="Garment category for proper placement",
    )
    mode: Literal["quality", "balanced", "fast"] = Field(
        default="balanced",
        description="Quality/speed tradeoff: quality (~20s), balanced (~12s), fast (~6s)",
    )
    provider: Literal["fashn", "idm_vton", "round_table"] = Field(
        default="fashn",
        description="Try-on provider: fashn (commercial), idm_vton (free), round_table (both compete)",
    )
    product_id: str | None = Field(
        default=None,
        description="Optional product ID for tracking",
        max_length=100,
    )


class BatchVirtualTryOnInput(BaseAgentInput):
    """Input for batch virtual try-on generation."""

    model_image_url: str = Field(
        ...,
        description="URL of the model/person image (same for all garments)",
        max_length=2000,
    )
    garments: list[dict[str, Any]] = Field(
        ...,
        description="List of garments: [{garment_image_url, category, product_id}, ...]",
    )
    mode: Literal["quality", "balanced", "fast"] = Field(
        default="balanced",
        description="Quality/speed tradeoff",
    )
    provider: Literal["fashn", "idm_vton"] = Field(
        default="fashn",
        description="Try-on provider to use",
    )


class AIModelGenerationInput(BaseAgentInput):
    """Input for AI fashion model generation."""

    prompt: str = Field(
        default="Professional fashion model in studio",
        description="Description of the model to generate",
        max_length=500,
    )
    gender: Literal["female", "male", "neutral"] = Field(
        default="neutral",
        description="Model gender",
    )
    style: Literal["professional", "casual", "editorial", "street"] = Field(
        default="professional",
        description="Photography style",
    )


# ===========================
# Tool Handlers
# ===========================


@mcp.tool(
    name="devskyy_virtual_tryon",
    annotations={
        "title": "DevSkyy Virtual Try-On",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
        "allowed_callers": [PTC_CALLER],
        "input_examples": [
            {
                "model_image_url": "https://cdn.skyyrose.co/models/model-front-001.jpg",
                "garment_image_url": "https://cdn.skyyrose.co/products/black-rose-hoodie.jpg",
                "category": "tops",
                "mode": "balanced",
                "provider": "fashn",
            },
            {
                "model_image_url": "https://example.com/model.jpg",
                "garment_image_url": "https://example.com/dress.jpg",
                "category": "dresses",
                "mode": "quality",
                "provider": "idm_vton",
            },
            {
                "model_image_url": "https://example.com/model.jpg",
                "garment_image_url": "https://example.com/jacket.jpg",
                "category": "outerwear",
                "provider": "round_table",
            },
        ],
    },
)
@secure_tool("virtual_tryon")
async def virtual_tryon(params: VirtualTryOnInput) -> str:
    """
    Generate a virtual try-on result that applies a garment image to a model image.

    Parameters:
        params (VirtualTryOnInput): Configuration for the try-on request containing:
            - model_image_url: URL of the model or person image.
            - garment_image_url: URL of the garment to apply.
            - category: Garment category (e.g., "tops", "bottoms", "dresses", "outerwear", "full_body").
            - mode: Quality/speed tradeoff ("quality", "balanced", "fast").
            - provider: Rendering provider ("fashn", "idm_vton", "round_table").
            - product_id: Optional product tracking identifier.
            - response_format: Desired output format (markdown or json).

    Returns:
        str: Formatted response string with the job status and result URL(s) when available; includes error information when the request fails.
    """
    data = await _make_api_request(
        "virtual-tryon/generate",
        method="POST",
        data={
            "model_image_url": params.model_image_url,
            "garment_image_url": params.garment_image_url,
            "category": params.category,
            "mode": params.mode,
            "provider": params.provider,
            "product_id": params.product_id,
        },
    )

    return _format_response(data, params.response_format, "Virtual Try-On Generated")


@mcp.tool(
    name="devskyy_batch_virtual_tryon",
    annotations={
        "title": "DevSkyy Batch Virtual Try-On",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
        "allowed_callers": [PTC_CALLER],
        "input_examples": [
            {
                "model_image_url": "https://cdn.skyyrose.co/models/model-001.jpg",
                "garments": [
                    {
                        "garment_image_url": "https://cdn.skyyrose.co/products/hoodie.jpg",
                        "category": "tops",
                        "product_id": "SKR-001",
                    },
                    {
                        "garment_image_url": "https://cdn.skyyrose.co/products/jacket.jpg",
                        "category": "outerwear",
                        "product_id": "SKR-002",
                    },
                    {
                        "garment_image_url": "https://cdn.skyyrose.co/products/tee.jpg",
                        "category": "tops",
                        "product_id": "SKR-003",
                    },
                ],
                "mode": "balanced",
                "provider": "fashn",
            },
        ],
    },
)
@secure_tool("batch_virtual_tryon")
async def batch_virtual_tryon(params: BatchVirtualTryOnInput) -> str:
    """
    Process a batch of garments on a single model image and return the formatted results.

    Parameters:
        params (BatchVirtualTryOnInput): Batch configuration containing:
            - model_image_url: URL of the model image to apply garments to.
            - garments: List of garment objects, each with `garment_image_url`, `category`, and optional `product_id`.
            - mode: Processing quality/speed preference (`quality`, `balanced`, or `fast`).
            - provider: Service provider to use (`fashn` or `idm_vton`).
            - response_format: Desired output format (`ResponseFormat`) for the returned string.

    Returns:
        str: Batch job status with individual item results formatted according to `params.response_format`.
    """
    data = await _make_api_request(
        "virtual-tryon/batch",
        method="POST",
        data={
            "model_image_url": params.model_image_url,
            "garments": params.garments,
            "mode": params.mode,
            "provider": params.provider,
        },
    )

    return _format_response(data, params.response_format, "Batch Virtual Try-On")


@mcp.tool(
    name="devskyy_generate_ai_model",
    annotations={
        "title": "DevSkyy AI Fashion Model Generator",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
        "input_examples": [
            {
                "prompt": "Professional fashion model, studio lighting, full body shot",
                "gender": "female",
                "style": "professional",
            },
            {
                "prompt": "Casual street style model, urban background",
                "gender": "male",
                "style": "street",
            },
            {
                "prompt": "Editorial fashion model, high fashion pose, dramatic lighting",
                "gender": "neutral",
                "style": "editorial",
            },
        ],
    },
)
@secure_tool("generate_ai_model")
async def generate_ai_model(params: AIModelGenerationInput) -> str:
    """
    Generate an AI fashion model image from the provided prompt, gender, and style.

    Parameters:
        params (AIModelGenerationInput): Generation configuration with:
            - prompt: Description of the desired model and pose.
            - gender: "female", "male", or "neutral".
            - style: "professional", "casual", "editorial", or "street".
            - response_format: Desired output format (markdown or json).

    Returns:
        str: Formatted response containing the generation result and the image URL or error details.
    """
    data = await _make_api_request(
        "virtual-tryon/models/generate",
        method="POST",
        data={
            "prompt": params.prompt,
            "gender": params.gender,
            "style": params.style,
        },
    )

    return _format_response(data, params.response_format, "AI Fashion Model Generated")


@mcp.tool(
    name="devskyy_virtual_tryon_status",
    annotations={
        "title": "DevSkyy Virtual Try-On Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
        # Always loaded for status checks
        "defer_loading": False,
    },
)
@secure_tool("virtual_tryon_status")
async def virtual_tryon_status(response_format: ResponseFormat = ResponseFormat.MARKDOWN) -> str:
    """
    Get virtual try-on pipeline status and provider availability.

    Returns a formatted status report containing provider health, queue metrics, daily usage and limits, and cost estimates.

    Parameters:
        response_format (ResponseFormat): Output format (`markdown` or `json`).

    Returns:
        str: Formatted pipeline status report.
    """
    data = await _make_api_request("virtual-tryon/status", method="GET")

    return _format_response(data, response_format, "Virtual Try-On Pipeline Status")
