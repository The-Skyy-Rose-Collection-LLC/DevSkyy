"""3D asset generation tools: text-to-3D, image-to-3D."""

from typing import Literal

from pydantic import Field

from mcp_tools.api_client import _format_response, _make_api_request
from mcp_tools.security import secure_tool
from mcp_tools.server import PTC_CALLER, mcp
from mcp_tools.types import BaseAgentInput


class ThreeDGenerationInput(BaseAgentInput):
    """Input for 3D model generation via Tripo3D."""

    product_name: str = Field(
        ...,
        description="Name of the product to generate 3D model for",
        min_length=1,
        max_length=200,
    )
    collection: str = Field(
        default="SIGNATURE",
        description="SkyyRose collection: SIGNATURE, BLACK_ROSE, or LOVE_HURTS",
        max_length=100,
    )
    garment_type: str = Field(
        default="tee",
        description="Garment type: hoodie, bomber, tee, jacket, shorts, etc.",
        max_length=50,
    )
    additional_details: str = Field(
        default="",
        description="Additional design details (colors, materials, special features)",
        max_length=1000,
    )
    output_format: Literal["glb", "gltf", "fbx", "obj", "usdz", "stl"] = Field(
        default="glb",
        description="Output 3D model format. GLB recommended for web.",
    )


class ThreeDImageInput(BaseAgentInput):
    """Input for image-to-3D generation via Tripo3D."""

    product_name: str = Field(
        ...,
        description="Name of the product to generate 3D model for",
        min_length=1,
        max_length=200,
    )
    image_url: str = Field(
        ...,
        description="URL or base64-encoded image for 3D generation",
        max_length=10000,
    )
    output_format: Literal["glb", "gltf", "fbx", "obj", "usdz", "stl"] = Field(
        default="glb",
        description="Output 3D model format. GLB recommended for web.",
    )


@mcp.tool(
    name="devskyy_generate_3d_from_description",
    annotations={
        "title": "DevSkyy 3D Model Generator (Text-to-3D)",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
        "allowed_callers": [PTC_CALLER],
        "input_examples": [
            {
                "product_name": "Heart Rose Bomber",
                "collection": "BLACK_ROSE",
                "garment_type": "bomber",
                "additional_details": "Rose gold zipper, embroidered rose on back",
                "output_format": "glb",
            },
            {
                "product_name": "Signature Hoodie",
                "collection": "SIGNATURE",
                "garment_type": "hoodie",
                "output_format": "gltf",
            },
            {
                "product_name": "Love Hurts Tee",
                "collection": "LOVE_HURTS",
                "garment_type": "tee",
                "additional_details": "Bleeding heart graphic, distressed print",
                "output_format": "glb",
            },
        ],
    },
)
@secure_tool("generate_3d_from_description")
async def generate_3d_from_description(params: ThreeDGenerationInput) -> str:
    """Generate 3D fashion models from text descriptions using Tripo3D AI.

    **INDUSTRY FIRST**: Automated 3D model generation for fashion e-commerce.

    The 3D Generation Agent creates high-quality 3D models of SkyyRose products
    from detailed text descriptions. Perfect for:
    - Product visualization in online stores
    - Virtual try-on experiences
    - Design iteration and prototyping
    - Cross-platform catalog generation

    **Supported Output Formats:**
    - GLB (Binary glTF) - Recommended for web/AR
    - GLTF (JSON glTF) - Human-readable 3D format
    - FBX (Autodesk) - Professional 3D software
    - OBJ (Wavefront) - Universal 3D format
    - USDZ (Apple) - iOS/macOS AR ready
    - STL - 3D printing format

    **SkyyRose Collections:**
    - SIGNATURE: Timeless essentials with rose gold details
    - BLACK_ROSE: Dark elegance limited editions
    - LOVE_HURTS: Emotional expression with bold design

    **Garment Types:**
    hoodie, bomber, track_pants, tee, sweatshirt, jacket,
    shorts, cap, beanie, and more

    Args:
        params (ThreeDGenerationInput): Generation configuration containing:
            - product_name: Name of the product
            - collection: SkyyRose collection
            - garment_type: Type of garment
            - additional_details: Design specifications
            - output_format: Output 3D format
            - response_format: Output format (markdown/json)

    Returns:
        str: Generation result with model paths, URLs, and metadata

    Example:
        >>> generate_3d_from_description({
        ...     "product_name": "Heart Rose Bomber",
        ...     "collection": "BLACK_ROSE",
        ...     "garment_type": "bomber",
        ...     "additional_details": "Rose gold zipper, embroidered rose",
        ...     "output_format": "glb"
        ... })
    """
    data = await _make_api_request(
        "3d/generate-from-description",
        method="POST",
        data={
            "product_name": params.product_name,
            "collection": params.collection,
            "garment_type": params.garment_type,
            "additional_details": params.additional_details,
            "output_format": params.output_format,
        },
    )

    return _format_response(data, params.response_format, "3D Model Generated (Text-to-3D)")


@mcp.tool(
    name="devskyy_generate_3d_from_image",
    annotations={
        "title": "DevSkyy 3D Model Generator (Image-to-3D)",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
        "allowed_callers": [PTC_CALLER],
        "input_examples": [
            {
                "product_name": "Custom Hoodie",
                "image_url": "https://cdn.skyyrose.co/designs/hoodie-front.jpg",
                "output_format": "glb",
            },
            {
                "product_name": "Sketch to 3D Jacket",
                "image_url": "https://cdn.skyyrose.co/sketches/jacket-v1.png",
                "output_format": "gltf",
            },
        ],
    },
)
@secure_tool("generate_3d_from_image")
async def generate_3d_from_image(params: ThreeDImageInput) -> str:
    """
    Generate a 3D model from a reference image.

    Parameters:
        params (ThreeDImageInput): Input containing:
            - product_name: Human-readable name for the generated model.
            - image_url: Reference image URL or base64-encoded image data.
            - output_format: Desired 3D file format (e.g., "glb", "gltf", "fbx", "obj", "usdz", "stl").
            - response_format: Desired response presentation (markdown or json).

    Returns:
        str: Formatted result containing generated model URLs/paths and related metadata.
    """
    data = await _make_api_request(
        "3d/generate-from-image",
        method="POST",
        data={
            "product_name": params.product_name,
            "image_url": params.image_url,
            "output_format": params.output_format,
        },
    )

    return _format_response(data, params.response_format, "3D Model Generated (Image-to-3D)")
