"""
Pydantic Schemas for 3D Clothing Asset Automation

Truth Protocol Compliance:
- Rule #7: All input validated with Pydantic
- Rule #9: Fully documented with type hints
- Rule #3: Standards cited where applicable

Author: DevSkyy Enterprise
Version: 1.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ClothingCollection(str, Enum):
    """
    SkyyRose clothing collections.

    Brand: SkyyRose - Oakland luxury streetwear, "where love meets luxury"
    """

    BLACK_ROSE = "black_rose"  # Dark elegance collection
    LOVE_HURTS = "love_hurts"  # Emotional expression collection
    SIGNATURE = "signature"  # Essential pieces collection


class ClothingCategory(str, Enum):
    """Categories of clothing items."""

    HOODIE = "hoodie"
    T_SHIRT = "t_shirt"
    JACKET = "jacket"
    PANTS = "pants"
    SHORTS = "shorts"
    DRESS = "dress"
    SKIRT = "skirt"
    SWEATER = "sweater"
    TANK_TOP = "tank_top"
    COAT = "coat"


class Model3DFormat(str, Enum):
    """Supported 3D model output formats from Tripo3D."""

    GLB = "glb"  # GL Transmission Format Binary
    FBX = "fbx"  # Autodesk FBX
    OBJ = "obj"  # Wavefront OBJ
    USDZ = "usdz"  # Apple AR format


class TryOnModel(str, Enum):
    """Virtual try-on model types from FASHN."""

    FEMALE = "female"
    MALE = "male"
    UNISEX = "unisex"


class PipelineStage(str, Enum):
    """Pipeline execution stages."""

    PENDING = "pending"
    GENERATING_3D = "generating_3d"
    VIRTUAL_TRYON = "virtual_tryon"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


class ClothingItem(BaseModel):
    """
    Input model for a clothing item to process.

    Represents a single clothing product from SkyyRose inventory
    that will be processed through the 3D generation pipeline.
    """

    item_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique identifier for the clothing item",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Product name",
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Detailed product description for 3D generation",
    )
    collection: ClothingCollection = Field(
        ...,
        description="SkyyRose collection this item belongs to",
    )
    category: ClothingCategory = Field(
        ...,
        description="Type of clothing item",
    )
    color: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Primary color of the item",
    )
    reference_image_url: str | None = Field(
        default=None,
        description="URL to reference image for image-to-3D generation",
    )
    reference_image_path: str | None = Field(
        default=None,
        description="Local path to reference image",
    )
    price: float = Field(
        ...,
        gt=0,
        description="Price in USD",
    )
    sku: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Stock Keeping Unit",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Product tags for categorization",
    )

    @field_validator("reference_image_url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        """Validate URL format if provided."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("reference_image_url must be a valid HTTP(S) URL")
        return v

    @property
    def prompt_for_3d(self) -> str:
        """Generate optimized prompt for 3D model generation."""
        collection_style = {
            ClothingCollection.BLACK_ROSE: "dark elegant luxury streetwear with rose motifs",
            ClothingCollection.LOVE_HURTS: "emotional expressive streetwear with heart designs",
            ClothingCollection.SIGNATURE: "classic premium streetwear essentials",
        }

        style = collection_style.get(self.collection, "luxury streetwear")

        return (
            f"High-quality 3D model of a {self.color} {self.category.value.replace('_', ' ')}, "
            f"{style} style. {self.description}. "
            f"Professional fashion photography quality, studio lighting, detailed fabric texture."
        )


class Model3DResult(BaseModel):
    """
    Result from Tripo3D 3D model generation.

    Contains the generated 3D model data and metadata.
    """

    task_id: str = Field(
        ...,
        description="Tripo3D task identifier",
    )
    status: str = Field(
        ...,
        description="Generation status (queued, running, success, failed)",
    )
    model_url: str | None = Field(
        default=None,
        description="URL to download the generated 3D model",
    )
    model_format: Model3DFormat = Field(
        default=Model3DFormat.GLB,
        description="Format of the generated model",
    )
    local_path: str | None = Field(
        default=None,
        description="Local file path after download",
    )
    thumbnail_url: str | None = Field(
        default=None,
        description="URL to model thumbnail/preview",
    )
    generation_time_seconds: float | None = Field(
        default=None,
        ge=0,
        description="Time taken to generate the model",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata from Tripo3D",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of generation",
    )


class TryOnResult(BaseModel):
    """
    Result from FASHN virtual try-on.

    Contains the generated try-on image and metadata.
    """

    task_id: str = Field(
        ...,
        description="FASHN task identifier",
    )
    status: str = Field(
        ...,
        description="Try-on status (processing, completed, failed)",
    )
    image_url: str | None = Field(
        default=None,
        description="URL to the try-on result image",
    )
    local_path: str | None = Field(
        default=None,
        description="Local file path after download",
    )
    model_type: TryOnModel = Field(
        default=TryOnModel.UNISEX,
        description="Type of model used for try-on",
    )
    resolution: tuple[int, int] = Field(
        default=(576, 864),
        description="Output image resolution (width, height)",
    )
    processing_time_seconds: float | None = Field(
        default=None,
        ge=0,
        description="Time taken for try-on processing",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata from FASHN",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of generation",
    )


class WordPressUploadResult(BaseModel):
    """
    Result from WordPress media upload.

    Contains information about the uploaded media in WooCommerce.
    """

    media_id: int = Field(
        ...,
        gt=0,
        description="WordPress media library ID",
    )
    source_url: str = Field(
        ...,
        description="Public URL of the uploaded media",
    )
    mime_type: str = Field(
        ...,
        description="MIME type of the uploaded file",
    )
    title: str = Field(
        ...,
        description="Media title in WordPress",
    )
    alt_text: str | None = Field(
        default=None,
        description="Alt text for accessibility",
    )
    file_size_bytes: int | None = Field(
        default=None,
        ge=0,
        description="Size of uploaded file in bytes",
    )
    uploaded_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of upload",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional WordPress metadata",
    )


class PipelineResult(BaseModel):
    """
    Complete result from the clothing asset pipeline.

    Aggregates results from all pipeline stages for a single item.
    """

    item_id: str = Field(
        ...,
        description="Clothing item identifier",
    )
    item_name: str = Field(
        ...,
        description="Clothing item name",
    )
    stage: PipelineStage = Field(
        default=PipelineStage.PENDING,
        description="Current pipeline stage",
    )
    success: bool = Field(
        default=False,
        description="Overall pipeline success status",
    )
    model_3d: Model3DResult | None = Field(
        default=None,
        description="3D model generation result",
    )
    try_on_results: list[TryOnResult] = Field(
        default_factory=list,
        description="Virtual try-on results (multiple model types)",
    )
    wordpress_uploads: list[WordPressUploadResult] = Field(
        default_factory=list,
        description="WordPress upload results",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Errors encountered during processing",
    )
    total_processing_time_seconds: float = Field(
        default=0.0,
        ge=0,
        description="Total time for entire pipeline",
    )
    started_at: datetime = Field(
        default_factory=datetime.now,
        description="Pipeline start timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Pipeline completion timestamp",
    )

    @property
    def has_3d_model(self) -> bool:
        """Check if 3D model was successfully generated."""
        return self.model_3d is not None and self.model_3d.status == "success"

    @property
    def try_on_count(self) -> int:
        """Count of successful try-on results."""
        return len([r for r in self.try_on_results if r.status == "completed"])

    @property
    def upload_count(self) -> int:
        """Count of successful WordPress uploads."""
        return len(self.wordpress_uploads)


class BatchPipelineRequest(BaseModel):
    """Request model for batch processing multiple clothing items."""

    items: list[ClothingItem] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of clothing items to process",
    )
    generate_3d: bool = Field(
        default=True,
        description="Enable 3D model generation",
    )
    generate_tryon: bool = Field(
        default=True,
        description="Enable virtual try-on generation",
    )
    tryon_models: list[TryOnModel] = Field(
        default=[TryOnModel.FEMALE, TryOnModel.MALE],
        description="Model types for virtual try-on",
    )
    upload_to_wordpress: bool = Field(
        default=True,
        description="Enable WordPress upload",
    )
    model_format: Model3DFormat = Field(
        default=Model3DFormat.GLB,
        description="Preferred 3D model output format",
    )
    parallel_processing: bool = Field(
        default=True,
        description="Enable parallel processing of items",
    )
    max_concurrent: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent operations",
    )


class BatchPipelineResult(BaseModel):
    """Result model for batch pipeline processing."""

    batch_id: str = Field(
        ...,
        description="Unique identifier for this batch",
    )
    total_items: int = Field(
        ...,
        ge=0,
        description="Total number of items in batch",
    )
    successful: int = Field(
        default=0,
        ge=0,
        description="Number of successfully processed items",
    )
    failed: int = Field(
        default=0,
        ge=0,
        description="Number of failed items",
    )
    results: list[PipelineResult] = Field(
        default_factory=list,
        description="Individual item results",
    )
    total_processing_time_seconds: float = Field(
        default=0.0,
        ge=0,
        description="Total batch processing time",
    )
    started_at: datetime = Field(
        default_factory=datetime.now,
        description="Batch start timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Batch completion timestamp",
    )

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.successful / self.total_items) * 100
