"""Virtual try-on tools: single, batch, AI model generation, status."""

from typing import Any, Literal

from pydantic import Field, model_validator

from mcp_tools.api_client import _format_response, _make_api_request
from mcp_tools.security import secure_tool
from mcp_tools.server import PTC_CALLER, mcp
from mcp_tools.types import BaseAgentInput, ResponseFormat
from skyyrose.core.sot_images import resolve_image

# Theme-relative paths returned by resolve_image() (e.g. "assets/images/products/br-001.jpg")
# are served live by WordPress's get_theme_file_uri() — see
# wordpress-theme/skyyrose-flagship/inc/product-catalog.php:skyyrose_product_image_uri().
_THEME_BASE_URL = "https://skyyrose.co/wp-content/themes/skyyrose-flagship/"

# ===========================
# Input Models
# ===========================


def _resolve_garment_url(product_id: str) -> str:
    """Resolve ``product_id`` to a public garment image URL via the SOT.

    Raises:
        ValueError: the SKU is unknown or has no front image registered.
    """
    relative = resolve_image(product_id, "front")
    if not relative:
        raise ValueError(
            f"could not resolve garment_image_url: product_id {product_id!r} has no "
            "SOT-registered image (skyyrose.core.sot_images.resolve_image returned None)"
        )
    return _THEME_BASE_URL + relative


class VirtualTryOnInput(BaseAgentInput):
    """Input for virtual try-on generation."""

    model_image_url: str = Field(
        ...,
        description="URL of the model/person image to apply garment to",
        max_length=2000,
    )
    garment_image_url: str | None = Field(
        default=None,
        description=(
            "URL of the garment image to apply. Optional when product_id is a known "
            "catalog SKU — the image is then resolved through the SOT "
            "(skyyrose.core.sot_images.resolve_image) and does not need to be supplied."
        ),
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

    @model_validator(mode="after")
    def resolve_garment_url_from_sot(self) -> "VirtualTryOnInput":
        """Fill ``garment_image_url`` from the SOT when the caller omits it.

        An explicit ``garment_image_url`` is always respected as-is and never
        overridden — the SOT-resolution path only fires when it is absent.
        """
        if self.garment_image_url is not None:
            return self
        if not self.product_id:
            raise ValueError(
                "garment_image_url is required unless product_id is a known catalog SKU"
            )
        self.garment_image_url = _resolve_garment_url(self.product_id)
        return self


class BatchVirtualTryOnInput(BaseAgentInput):
    """Input for batch virtual try-on generation."""

    model_image_url: str = Field(
        ...,
        description="URL of the model/person image (same for all garments)",
        max_length=2000,
    )
    garments: list[dict[str, Any]] = Field(
        ...,
        description=(
            "List of garments: [{garment_image_url, category, product_id}, ...]. "
            "garment_image_url is optional per-item when product_id is a known catalog "
            "SKU — it is then resolved through the SOT (skyyrose.core.sot_images.resolve_image)."
        ),
    )
    mode: Literal["quality", "balanced", "fast"] = Field(
        default="balanced",
        description="Quality/speed tradeoff",
    )
    provider: Literal["fashn", "idm_vton"] = Field(
        default="fashn",
        description="Try-on provider to use",
    )

    @model_validator(mode="after")
    def resolve_garment_urls_from_sot(self) -> "BatchVirtualTryOnInput":
        """Fill each garment's ``garment_image_url`` from the SOT when omitted.

        An item with an explicit ``garment_image_url`` is always respected as-is
        and never overridden — the SOT-resolution path only fires when it is
        absent for that item.
        """
        for garment in self.garments:
            if garment.get("garment_image_url"):
                continue
            product_id = garment.get("product_id")
            if not product_id:
                raise ValueError(
                    "each garment needs garment_image_url unless product_id is a known catalog SKU"
                )
            garment["garment_image_url"] = _resolve_garment_url(product_id)
        return self


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
            {
                "model_image_url": "https://cdn.skyyrose.co/models/model-front-001.jpg",
                "product_id": "br-001",
                "category": "outerwear",
                "mode": "balanced",
                "provider": "fashn",
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
            - garment_image_url: URL of the garment to apply. Optional when product_id
              is a known catalog SKU — resolved through the SOT
              (skyyrose.core.sot_images.resolve_image) when omitted.
            - category: Garment category (e.g., "tops", "bottoms", "dresses", "outerwear", "full_body").
            - mode: Quality/speed tradeoff ("quality", "balanced", "fast").
            - provider: Rendering provider ("fashn", "idm_vton", "round_table").
            - product_id: Optional product tracking identifier; also used to resolve
              garment_image_url via the SOT when garment_image_url is not supplied.
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
            {
                "model_image_url": "https://cdn.skyyrose.co/models/model-001.jpg",
                "garments": [
                    {"product_id": "br-001", "category": "outerwear"},
                    {"product_id": "sg-003", "category": "tops"},
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
            - garments: List of garment objects, each with `category`, optional
              `product_id`, and `garment_image_url`. `garment_image_url` is optional
              per-item when `product_id` is a known catalog SKU — resolved through the
              SOT (skyyrose.core.sot_images.resolve_image) when omitted.
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
