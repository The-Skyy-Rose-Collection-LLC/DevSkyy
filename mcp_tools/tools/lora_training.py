"""LoRA training tools: train, dataset preview, version info, product history."""

from pydantic import Field

from mcp_tools.api_client import _format_response, _make_api_request
from mcp_tools.security import secure_tool
from mcp_tools.server import mcp
from mcp_tools.types import BaseAgentInput

# ===========================
# Input Models
# ===========================


class TrainLoRAInput(BaseAgentInput):
    """Input for LoRA training from WooCommerce products."""

    collections: list[str] | None = Field(
        default=None,
        description="Collections to train on: BLACK_ROSE, LOVE_HURTS, SIGNATURE (null = all collections)",
        max_length=10,
    )
    max_products: int | None = Field(
        default=None,
        description="Maximum number of products to use (null = no limit)",
        ge=1,
        le=1000,
    )
    epochs: int = Field(
        default=100,
        description="Number of training epochs",
        ge=1,
        le=1000,
    )
    version: str | None = Field(
        default=None,
        description="LoRA version string (e.g., 'v1.1.0'). Auto-generated if null.",
        max_length=50,
    )


class LoRADatasetPreviewInput(BaseAgentInput):
    """Input for previewing LoRA training dataset."""

    collections: list[str] | None = Field(
        default=None,
        description="Collections to preview: BLACK_ROSE, LOVE_HURTS, SIGNATURE (null = all)",
        max_length=10,
    )
    max_products: int | None = Field(
        default=50,
        description="Maximum products to preview",
        ge=1,
        le=1000,
    )


class LoRAVersionInfoInput(BaseAgentInput):
    """Input for retrieving LoRA version information."""

    version: str = Field(
        ...,
        description="LoRA version string (e.g., 'v1.1.0')",
        min_length=1,
        max_length=50,
    )


class LoRAProductHistoryInput(BaseAgentInput):
    """Input for retrieving product LoRA history."""

    sku: str = Field(
        ...,
        description="Product SKU (e.g., 'SRS-BR-001')",
        min_length=1,
        max_length=100,
    )


# ===========================
# Tool Handlers
# ===========================


@mcp.tool(
    name="devskyy_train_lora_from_products",
    annotations={
        "title": "Train SkyyRose LoRA from WooCommerce Products",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
        "category": "ai",
    },
)
@secure_tool("train_lora_from_products")
async def train_lora_from_products(params: TrainLoRAInput) -> str:
    """Train SkyyRose LoRA using WooCommerce product images.

    This tool orchestrates end-to-end LoRA training:
    1. Fetches products from WooCommerce (filtered by collection)
    2. Downloads and caches product images
    3. Evaluates image quality (resolution, blur, brightness)
    4. Prepares training dataset with brand DNA captions
    5. Trains SDXL LoRA with PEFT (rank 32, alpha 32)
    6. Saves version to SQLite database for tracking
    7. Generates training metadata and progress logs

    Collections:
    - BLACK_ROSE: Dark romantic aesthetic, gothic elegance
    - LOVE_HURTS: Edgy romance, heart motifs, vulnerable strength
    - SIGNATURE: Classic SkyyRose style, rose gold accents, timeless sophistication

    Training typically takes 2-4 hours for 100 products on GPU.

    Args:
        params: Training parameters including collections, epochs, version

    Returns:
        str: Training status with version info, dataset stats, and model path
    """
    data = await _make_api_request(
        "lora/train",
        method="POST",
        data={
            "collections": params.collections,
            "max_products": params.max_products,
            "epochs": params.epochs,
            "version": params.version,
        },
    )

    return _format_response(data, params.response_format, "LoRA Training Started")


@mcp.tool(
    name="devskyy_lora_dataset_preview",
    annotations={
        "title": "Preview LoRA Training Dataset",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
        "defer_loading": True,
        "category": "ai",
    },
)
@secure_tool("lora_dataset_preview")
async def lora_dataset_preview(params: LoRADatasetPreviewInput) -> str:
    """Preview LoRA training dataset before starting training.

    Shows:
    - Total products and images that would be used
    - Collection breakdown (BLACK_ROSE, LOVE_HURTS, SIGNATURE)
    - Sample product SKUs and names
    - Image quality scores
    - Estimated training time

    Use this to validate your dataset before committing to a full training run.

    Args:
        params: Preview parameters including collections filter and max products

    Returns:
        str: Dataset preview with product counts, collections, and sample data
    """
    data = await _make_api_request(
        "lora/dataset/preview",
        method="GET",
        params={
            "collections": (",".join(params.collections) if params.collections else None),
            "max_products": params.max_products,
        },
    )

    return _format_response(data, params.response_format, "LoRA Dataset Preview")


@mcp.tool(
    name="devskyy_lora_version_info",
    annotations={
        "title": "Get LoRA Version Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
        "defer_loading": True,
        "category": "ai",
    },
)
@secure_tool("lora_version_info")
async def lora_version_info(params: LoRAVersionInfoInput) -> str:
    """Get detailed information about a specific LoRA version.

    Returns:
    - Version metadata (created date, base model, training config)
    - Dataset statistics (total images, total products, collection breakdown)
    - Product contributions (SKUs, names, image counts, quality scores)
    - Training metrics (epochs, loss, learning rate)
    - Model path for downloading weights

    Args:
        params: Version query with version string (e.g., 'v1.1.0')

    Returns:
        str: Complete version information with all metadata and product details
    """
    data = await _make_api_request(f"lora/versions/{params.version}", method="GET")

    return _format_response(data, params.response_format, f"LoRA Version: {params.version}")


@mcp.tool(
    name="devskyy_lora_product_history",
    annotations={
        "title": "Get Product LoRA Training History",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
        "defer_loading": True,
        "category": "ai",
    },
)
@secure_tool("lora_product_history")
async def lora_product_history(params: LoRAProductHistoryInput) -> str:
    """Find all LoRA versions that include a specific product.

    This tool searches the version database to find every LoRA training run
    that used images from the specified product SKU.

    Returns:
    - List of all versions including this product
    - Version creation dates
    - Image counts used from this product in each version
    - Quality scores for this product's images

    Useful for:
    - Understanding which products contributed to model improvements
    - Debugging why certain products generate better results
    - Tracking product representation across model versions

    Args:
        params: Product query with SKU (e.g., 'SRS-BR-001')

    Returns:
        str: Product training history across all LoRA versions
    """
    data = await _make_api_request(
        f"lora/products/{params.sku}/history",
        method="GET",
    )

    return _format_response(data, params.response_format, f"Product History: {params.sku}")
