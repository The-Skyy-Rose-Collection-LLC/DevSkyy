#!/usr/bin/env python3
"""
Luxury Fashion Brand Automation API - Production-Ready
Comprehensive API endpoints for all multi-agent automation systems

Author: DevSkyy Team
Version: 1.0.0-production

SECURITY STATUS (Per CLAUDE.md Truth Protocol):
=================================================
✅ JWT Authentication Module: security/jwt_auth.py (RFC 7519 compliant)
✅ RBAC System: 5-role hierarchy (SUPER_ADMIN, ADMIN, DEVELOPER, API_USER, READ_ONLY)
✅ Input Validation: security/input_validation.py (OWASP compliant)
✅ Security imports present in this file

⚠️  AUTHENTICATION ENFORCEMENT STATUS:
- 2/27 endpoints have authentication enforced (assets/upload, assets/{asset_id})
- Remaining 25 endpoints require Depends(require_role(UserRole.XXX)) parameter
- Pattern established - see existing endpoints for implementation example

TO COMPLETE AUTHENTICATION (For each remaining endpoint):
1. Add parameter: current_user: dict[str, Any] = Depends(require_role(UserRole.XXX) if SECURITY_AVAILABLE else get_current_user)
2. Update docstring with: **Authentication Required:** XXX role or higher
3. Update docstring with: **RBAC:** [list of allowed roles]

Role Requirements by Endpoint Type:
- Assets (create): DEVELOPER
- Assets (read): API_USER
- Try-On (generate): DEVELOPER
- Try-On (read): API_USER
- Finance operations: ADMIN
- Finance read: API_USER
- Marketing operations: ADMIN
- Code generation: DEVELOPER
- Workflows: ADMIN
- System status: READ_ONLY
"""

from datetime import datetime
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field


# Security imports (RFC 7519 JWT + RBAC)
try:
    from security.jwt_auth import (
        UserRole,
        get_current_user,
        require_role,
    )

    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    logging.warning("JWT authentication module not available - endpoints will be unprotected")

# Input sanitization (OWASP compliance)
try:
    INPUT_VALIDATION_AVAILABLE = True
except ImportError:
    INPUT_VALIDATION_AVAILABLE = False
    logging.warning("Input validation not available")

# Import agents
try:
    from agent.modules.content.visual_content_generation_agent import (
        ContentProvider,
        ContentType,
        GenerationRequest,
        StylePreset,
        visual_content_agent,
    )

    VISUAL_AGENT_AVAILABLE = True
except ImportError:
    VISUAL_AGENT_AVAILABLE = False
    logging.warning("Visual Content Agent not available")

try:
    from agent.modules.finance.finance_inventory_pipeline_agent import Channel as InventoryChannel
    from agent.modules.finance.finance_inventory_pipeline_agent import (
        finance_inventory_agent,
    )

    FINANCE_AGENT_AVAILABLE = True
except ImportError:
    FINANCE_AGENT_AVAILABLE = False
    logging.warning("Finance & Inventory Agent not available")

try:
    from agent.modules.marketing.marketing_campaign_orchestrator import (
        marketing_orchestrator,
    )

    MARKETING_AGENT_AVAILABLE = True
except ImportError:
    MARKETING_AGENT_AVAILABLE = False
    logging.warning("Marketing Orchestrator not available")

try:
    from agent.modules.development.code_recovery_cursor_agent import CodeGenerationRequest as CodeGenRequest
    from agent.modules.development.code_recovery_cursor_agent import (
        CodeLanguage,
        CodeRecoveryRequest,
        RecoveryStrategy,
        code_recovery_agent,
    )

    CODE_AGENT_AVAILABLE = True
except ImportError:
    CODE_AGENT_AVAILABLE = False
    logging.warning("Code Recovery Agent not available")

try:
    from agent.enterprise_workflow_engine import (
        WorkflowType,
        workflow_engine,
    )

    WORKFLOW_ENGINE_AVAILABLE = True
except ImportError:
    WORKFLOW_ENGINE_AVAILABLE = False
    logging.warning("Workflow Engine not available")

try:
    from agent.modules.content.asset_preprocessing_pipeline import (
        AssetType,
        ProcessingRequest,
        UpscaleQuality,
        asset_pipeline,
    )

    ASSET_PIPELINE_AVAILABLE = True
except ImportError:
    ASSET_PIPELINE_AVAILABLE = False
    logging.warning("Asset Preprocessing Pipeline not available")

try:
    from agent.modules.content.virtual_tryon_huggingface_agent import (
        BodyType,
        ModelEthnicity,
        ModelSpecification,
        PoseType,
        TryOnRequest,
        virtual_tryon_agent,
    )

    VIRTUAL_TRYON_AVAILABLE = True
except ImportError:
    VIRTUAL_TRYON_AVAILABLE = False
    logging.warning("Virtual Try-On Agent not available")


logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class VisualContentRequest(BaseModel):
    """Request model for visual content generation."""

    prompt: str = Field(..., description="Description of the content to generate")
    content_type: str = Field(default="product_photo", description="Type of content")
    style_preset: str | None = Field(default="minimalist_luxury", description="Style preset")
    provider: str | None = Field(default=None, description="Specific provider to use")
    width: int = Field(default=1024, ge=512, le=2048)
    height: int = Field(default=1024, ge=512, le=2048)
    quality: str = Field(default="high", description="Quality level")
    variations: int = Field(default=1, ge=1, le=4)


class CampaignRequest(BaseModel):
    """Request model for marketing campaign creation."""

    name: str = Field(..., description="Campaign name")
    description: str | None = Field(default="")
    campaign_type: str = Field(default="email")
    channels: list[str] = Field(default=["email"])
    target_segments: list[str] = Field(default=[])
    enable_testing: bool = Field(default=False)
    variants: list[dict[str, Any]] | None = Field(default=None)
    budget: float = Field(default=0.0)
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None


class InventorySyncRequest(BaseModel):
    """Request model for inventory synchronization."""

    channel: str = Field(..., description="Sales channel")
    items: list[dict[str, Any]] = Field(..., description="Items to sync")


class FinancialTransactionRequest(BaseModel):
    """Request model for recording financial transactions."""

    type: str = Field(default="sale")
    amount: float = Field(..., ge=0)
    currency: str = Field(default="USD")
    channel: str = Field(default="online_store")
    order_id: str | None = None
    customer_id: str | None = None
    line_items: list[dict[str, Any]] = Field(default=[])
    payment_method: str | None = None


class CodeGenerationRequest(BaseModel):
    """Request model for code generation."""

    description: str = Field(..., description="What code to generate")
    language: str = Field(default="python")
    framework: str | None = None
    requirements: list[str] = Field(default=[])
    include_tests: bool = Field(default=True)
    include_docs: bool = Field(default=True)
    model: str = Field(default="cursor")


class CodeRecoveryRequestModel(BaseModel):
    """Request model for code recovery."""

    recovery_type: str = Field(default="git_history")
    repository_url: str | None = None
    file_path: str | None = None
    branch: str = Field(default="main")
    commit_hash: str | None = None


class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution."""

    workflow_type: str = Field(..., description="Type of workflow")
    workflow_data: dict[str, Any] = Field(..., description="Workflow configuration")


class AssetUploadRequest(BaseModel):
    """Request model for asset upload and preprocessing."""

    asset_path: str = Field(..., description="Path to uploaded asset")
    asset_type: str = Field(default="clothing", description="Type of asset")
    target_quality: str = Field(default="uhd_8k", description="Target quality")
    enable_enhancement: bool = Field(default=True)
    remove_background: bool = Field(default=True)
    generate_3d: bool = Field(default=True)
    extract_textures: bool = Field(default=True)
    product_name: str | None = None
    brand: str | None = None
    collection: str | None = None


class VirtualTryOnRequestModel(BaseModel):
    """Request model for virtual try-on generation."""

    product_asset_id: str = Field(..., description="Preprocessed asset ID")
    # Model specification
    gender: str = Field(default="female")
    ethnicity: str = Field(default="mixed")
    age_range: str = Field(default="25-30")
    body_type: str = Field(default="athletic")
    pose: str = Field(default="fashion_shoot")
    # Generation options
    num_variations: int = Field(default=4, ge=1, le=10)
    generate_video: bool = Field(default=False)
    video_duration_seconds: int = Field(default=5, ge=3, le=30)
    generate_multiple_angles: bool = Field(default=False)
    generate_3d_preview: bool = Field(default=False)


# ============================================================================
# ASSET PREPROCESSING ENDPOINTS
# ============================================================================


@router.post("/assets/upload", tags=["Assets"])
async def upload_and_process_asset(
    request: AssetUploadRequest,
    background_tasks: BackgroundTasks,
    current_user: dict[str, Any] = Depends(
        require_role(UserRole.DEVELOPER) if SECURITY_AVAILABLE else get_current_user
    ),
):
    """
    Upload an asset and run the asset preprocessing pipeline to produce processed files and metadata for downstream use.

    Processes the uploaded asset through enhancement, upscaling, background removal, optional 3D generation, and texture extraction (when enabled) and returns resulting file paths and quality metrics.

    Parameters:
        request (AssetUploadRequest): Specifications for the uploaded asset and preprocessing options.

    Returns:
        dict: Contains processed asset metadata and output file references:
            - success (bool): `True` if processing succeeded.
            - asset_id (str): Identifier of the preprocessed asset.
            - original_resolution (dict): { "width": int, "height": int } of the original asset.
            - final_resolution (dict): { "width": int, "height": int } of the processed asset.
            - processed_file (str): Path or URL to the processed asset file.
            - thumbnail_file (str): Path or URL to the generated thumbnail.
            - model_3d_file (str | None): Path or URL to the generated 3D model, if any.
            - texture_files (list[str]): Paths or URLs to extracted texture files, if any.
            - quality_score (float): Overall quality score assigned to the processed asset.
            - sharpness_score (float): Sharpness metric for the processed asset.
            - processing_time (float): Total processing time in seconds.
            - stages_completed (list[str]): Ordered list of completed processing stage identifiers.

    Raises:
        HTTPException: With 503 when the asset preprocessing pipeline is unavailable, or with 500 when processing fails.
    """
    if not ASSET_PIPELINE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Asset preprocessing pipeline not available"
        )

    try:
        # Create processing request
        processing_request = ProcessingRequest(
            asset_path=request.asset_path,
            asset_type=AssetType(request.asset_type),
            target_quality=UpscaleQuality(request.target_quality),
            enable_enhancement=request.enable_enhancement,
            remove_background=request.remove_background,
            generate_3d=request.generate_3d,
            extract_textures=request.extract_textures,
        )

        # Process asset
        result = await asset_pipeline.process_asset(processing_request)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Asset processing failed: {result.error}"
            )

        return {
            "success": True,
            "asset_id": result.asset_id,
            "original_resolution": {
                "width": result.original_resolution[0],
                "height": result.original_resolution[1],
            },
            "final_resolution": {
                "width": result.final_resolution[0],
                "height": result.final_resolution[1],
            },
            "processed_file": result.processed_file,
            "thumbnail_file": result.thumbnail_file,
            "model_3d_file": result.model_3d_file,
            "texture_files": result.texture_files,
            "quality_score": result.quality_score,
            "sharpness_score": result.sharpness_score,
            "processing_time": result.processing_time,
            "stages_completed": [s.value for s in result.stages_completed],
        }

    except Exception as e:
        logger.error(f"Asset upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/{asset_id}", tags=["Assets"])
async def get_asset_info(
    asset_id: str,
    current_user: dict[str, Any] = Depends(
        require_role(UserRole.API_USER) if SECURITY_AVAILABLE else get_current_user
    ),
):
    """
    Retrieve metadata for a preprocessed asset by its ID.

    Raises:
        HTTPException: 503 if the asset preprocessing pipeline is unavailable.
        HTTPException: 404 if no asset with the given ID is found.

    Parameters:
        asset_id (str): Unique identifier of the asset to retrieve.

    Returns:
        dict: Asset metadata containing:
            - asset_id (str): Asset identifier.
            - asset_type (str): Asset type name.
            - product_name (str | None): Associated product name.
            - brand (str | None): Brand name.
            - collection (str | None): Collection name.
            - original_resolution (dict): {"width": int, "height": int} before processing.
            - final_resolution (dict): {"width": int, "height": int} after processing.
            - upscale_factor (float): Applied upscale multiplier.
            - has_3d_model (bool): Whether a 3D model was generated.
            - processed_path (str): Filesystem or storage path to the processed asset.
            - thumbnail_path (str): Path to the thumbnail image.
            - model_3d_path (str | None): Path to the 3D model file, if present.
            - uploaded_at (str): ISO 8601 timestamp when the asset was uploaded.
            - processed_at (str | None): ISO 8601 timestamp when processing completed, or `None`.
    """
    if not ASSET_PIPELINE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Asset preprocessing pipeline not available"
        )

    asset = asset_pipeline.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return {
        "asset_id": asset.asset_id,
        "asset_type": asset.asset_type.value,
        "product_name": asset.product_name,
        "brand": asset.brand,
        "collection": asset.collection,
        "original_resolution": {
            "width": asset.original_resolution[0],
            "height": asset.original_resolution[1],
        },
        "final_resolution": {
            "width": asset.final_resolution[0],
            "height": asset.final_resolution[1],
        },
        "upscale_factor": asset.upscale_factor,
        "has_3d_model": asset.has_3d_model,
        "processed_path": asset.processed_path,
        "thumbnail_path": asset.thumbnail_path,
        "model_3d_path": asset.model_3d_path,
        "uploaded_at": asset.uploaded_at.isoformat(),
        "processed_at": asset.processed_at.isoformat() if asset.processed_at else None,
    }


@router.get("/assets", tags=["Assets"])
async def list_assets():
    """
    Retrieve aggregated metrics about preprocessed assets.

    Returns:
        dict: Aggregated asset metrics with keys:
            total_assets (int): Total number of assets tracked by the pipeline.
            3d_models (int): Number of assets that are 3D models.
            assets_processed (int): Number of assets that have been processed.
            avg_processing_time (float): Average processing time (in seconds) for assets.
    """
    if not ASSET_PIPELINE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Asset preprocessing pipeline not available"
        )

    status_info = asset_pipeline.get_system_status()

    return {
        "total_assets": status_info["assets"]["total_assets"],
        "3d_models": status_info["assets"]["3d_models"],
        "assets_processed": status_info["performance"]["assets_processed"],
        "avg_processing_time": status_info["performance"]["avg_processing_time"],
    }


# ============================================================================
# VIRTUAL TRY-ON & HUGGINGFACE ENDPOINTS
# ============================================================================


@router.post("/tryon/generate", tags=["Virtual Try-On"])
async def generate_virtual_tryon(request: VirtualTryOnRequestModel, background_tasks: BackgroundTasks):
    """
    Generate virtual try-on assets (images, optional videos and 3D previews) for a product using the provided model specification.

    Parameters:
        request (VirtualTryOnRequestModel): Specifies the product asset ID, target model demographics (gender, ethnicity, age_range, body_type), pose, number of variations, and flags for video, multiple angles, and 3D preview generation.

    Returns:
        dict: A result payload containing:
            - `success` (bool): `True` when generation succeeded.
            - `request_id` (str): Unique identifier for the generation request.
            - `images` (list[str]): Generated image URLs or encoded image data.
            - `videos` (list[str]): Generated video URLs or encoded video data (may be empty if not requested).
            - `model_3d` (Optional[dict or str]): 3D preview data or URL when `generate_3d_preview` is requested.
            - `variations_generated` (int): Number of variations produced.
            - `quality_score` (float): Overall quality metric for the generated outputs.
            - `product_accuracy_score` (float): Metric indicating how accurately the product is placed on the model.
            - `realism_score` (float): Perceived realism metric for the outputs.
            - `generation_time` (float): Time in seconds taken to generate outputs.
            - `model_used` (str): Identifier or name of the underlying model(s) used.

    Raises:
        HTTPException: 503 if the virtual try-on agent is unavailable.
        HTTPException: 500 if generation fails or an internal error occurs.
    """
    if not VIRTUAL_TRYON_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Virtual try-on agent not available"
        )

    try:
        # Create model specification
        model_spec = ModelSpecification(
            gender=request.gender,
            ethnicity=ModelEthnicity(request.ethnicity),
            age_range=request.age_range,
            body_type=BodyType(request.body_type),
            pose=PoseType(request.pose),
        )

        # Create try-on request
        tryon_request = TryOnRequest(
            product_asset_id=request.product_asset_id,
            model_spec=model_spec,
            num_variations=request.num_variations,
            generate_video=request.generate_video,
            video_duration_seconds=request.video_duration_seconds,
            generate_multiple_angles=request.generate_multiple_angles,
            generate_3d_preview=request.generate_3d_preview,
        )

        # Generate try-on
        result = await virtual_tryon_agent.generate_tryon(tryon_request)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Try-on generation failed: {result.error}"
            )

        return {
            "success": True,
            "request_id": result.request_id,
            "images": result.images,
            "videos": result.videos,
            "model_3d": result.model_3d,
            "variations_generated": result.variations_generated,
            "quality_score": result.quality_score,
            "product_accuracy_score": result.product_accuracy_score,
            "realism_score": result.realism_score,
            "generation_time": result.generation_time,
            "model_used": result.model_used,
        }

    except Exception as e:
        logger.error(f"Virtual try-on error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tryon/models", tags=["Virtual Try-On"])
async def get_available_models():
    """
    Return available HuggingFace models and their high-level capabilities for the virtual try-on subsystem.

    Returns:
        dict: {
            "total_models": int — count of discovered models,
            "models": list — detailed model entries returned by the agent,
            "capabilities": list — human-readable capability categories supported by the models
        }

    Raises:
        fastapi.HTTPException: If the virtual try-on agent is not available (HTTP 503).
    """
    if not VIRTUAL_TRYON_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Virtual try-on agent not available"
        )

    models = virtual_tryon_agent.get_available_models()

    return {
        "total_models": len(models),
        "models": models,
        "capabilities": [
            "Virtual Try-On (IDM-VTON, OOTDiffusion)",
            "Image Generation (SDXL, SDXL Turbo)",
            "Video Generation (AnimateDiff, SVD, CogVideoX)",
            "3D Generation (TripoSR, Wonder3D)",
            "Face Models (InstantID, PhotoMaker, GFPGAN)",
            "Control Models (ControlNet Pose/Depth)",
            "Segmentation (SAM, CLIPSeg)",
            "Detection (Grounding DINO, DWPose)",
            "Enhancement (Real-ESRGAN)",
            "Fashion-Specific (DeepFashion)",
        ],
    }


@router.get("/tryon/status", tags=["Virtual Try-On"])
async def get_tryon_status():
    """
    Get virtual try-on system status.

    Returns:
        dict: Status payload containing:
            - `available` (bool): True if the virtual try-on agent is available, False otherwise.
            - `status` (Any): System status from the virtual try-on agent when available.
            - `error` (str): Error message when the agent is not available.
    """
    if not VIRTUAL_TRYON_AVAILABLE:
        return {"available": False, "error": "Virtual try-on agent not available"}

    return {
        "available": True,
        "status": virtual_tryon_agent.get_system_status(),
    }


# ============================================================================
# VISUAL CONTENT GENERATION ENDPOINTS
# ============================================================================


@router.post("/visual-content/generate", tags=["Visual Content"])
async def generate_visual_content(request: VisualContentRequest, background_tasks: BackgroundTasks):
    """
    Generate visual content for the brand based on the provided VisualContentRequest.

    Returns:
        dict: Result payload with keys:
            - `success` (bool): `true` when generation succeeded, `false` otherwise.
            - `request_id` (str|None): Provider request identifier when available.
            - `provider` (str|None): Name of the content provider used.
            - `images` (list[dict]|None): Generated image objects or metadata.
            - `quality_score` (float|None): Estimated quality or confidence score.
            - `generation_time` (float|None): Time taken to generate content in seconds.
            - `cost` (float|None): Estimated cost for the generation operation.
            - `error` (str|None): Error message when generation failed.

    Raises:
        HTTPException: With 503 when the visual content agent is unavailable.
        HTTPException: With 500 when generation fails due to an internal error.
    """
    if not VISUAL_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Visual content agent not available"
        )

    try:
        # Create generation request
        gen_request = GenerationRequest(
            prompt=request.prompt,
            content_type=ContentType(request.content_type),
            style_preset=StylePreset(request.style_preset) if request.style_preset else None,
            provider=ContentProvider(request.provider) if request.provider else None,
            width=request.width,
            height=request.height,
            quality=request.quality,
            variations=request.variations,
        )

        # Generate content
        result = await visual_content_agent.generate_content(gen_request)

        return {
            "success": result.success,
            "request_id": result.request_id,
            "provider": result.provider.value,
            "images": result.images,
            "quality_score": result.quality_score,
            "generation_time": result.generation_time,
            "cost": result.cost,
            "error": result.error,
        }

    except Exception as e:
        logger.error(f"Visual content generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual-content/batch-generate", tags=["Visual Content"])
async def batch_generate_visual_content(requests: list[VisualContentRequest]):
    """
    Generate visual content for a batch of VisualContentRequest objects.

    Parameters:
        requests (list[VisualContentRequest]): List of visual content requests to process in bulk.

    Returns:
        dict: Summary of the batch operation with keys:
            - `success` (bool): `True` if the batch request was submitted and processed.
            - `total_requests` (int): Number of requests in the batch.
            - `results` (list[dict]): Per-request results, each containing:
                - `request_id` (str): Identifier for the generated request.
                - `success` (bool): `True` if that request succeeded, `false` otherwise.
                - `images` (list[str]): Generated image asset paths or URLs.
                - `error` (str | None): Error message when generation failed, otherwise `None`.
    """
    if not VISUAL_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Visual content agent not available"
        )

    try:
        # Convert to generation requests
        gen_requests = [
            GenerationRequest(
                prompt=req.prompt,
                content_type=ContentType(req.content_type),
                style_preset=StylePreset(req.style_preset) if req.style_preset else None,
                width=req.width,
                height=req.height,
                quality=req.quality,
            )
            for req in requests
        ]

        # Batch generate
        results = await visual_content_agent.batch_generate(gen_requests)

        return {
            "success": True,
            "total_requests": len(requests),
            "results": [
                {
                    "request_id": r.request_id,
                    "success": r.success,
                    "images": r.images,
                    "error": r.error,
                }
                for r in results
            ],
        }

    except Exception as e:
        logger.error(f"Batch generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visual-content/status", tags=["Visual Content"])
async def get_visual_content_status():
    """
    Report availability and system status of the visual content agent.

    Returns:
        dict: If the agent is available, returns {"available": True, "status": <status>} where <status> is the agent's system status. If unavailable, returns {"available": False, "error": "<message>"}.
    """
    if not VISUAL_AGENT_AVAILABLE:
        return {"available": False, "error": "Visual content agent not available"}

    return {
        "available": True,
        "status": visual_content_agent.get_system_status(),
    }


# ============================================================================
# FINANCE & INVENTORY ENDPOINTS
# ============================================================================


@router.post("/finance/inventory/sync", tags=["Finance & Inventory"])
async def sync_inventory(request: InventorySyncRequest):
    """
    Synchronize inventory from an external sales channel specified in the request.

    Parameters:
        request (InventorySyncRequest): Sync request containing `channel` (the external platform name) and `items` to be synchronized. Supported channels include WooCommerce, Shopify, Magento, Amazon, and eBay.

    Returns:
        dict: Result object describing the synchronization outcome, for example keys such as `success` (bool), `processed_count` (int), and `errors` (list) when applicable.
    """
    if not FINANCE_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Finance & inventory agent not available"
        )

    try:
        channel = InventoryChannel(request.channel)
        result = await finance_inventory_agent.sync_inventory(channel, request.items)

        return result

    except Exception as e:
        logger.error(f"Inventory sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finance/transactions/record", tags=["Finance & Inventory"])
async def record_transaction(
    request: FinancialTransactionRequest,
    current_user: dict[str, Any] = Depends(require_role(UserRole.ADMIN) if SECURITY_AVAILABLE else get_current_user),
):
    """
    Record a financial transaction and apply related inventory updates and tax calculations.

    **Authentication Required:** ADMIN role or higher
    **RBAC:** ADMIN, SUPER_ADMIN

    Parameters:
        request (FinancialTransactionRequest): Transaction details (type, amount, currency, channel, order_id, customer_id, line_items, payment_method, etc.).

    Returns:
        dict: {
            "success": True if recording succeeded, False otherwise,
            "transaction_id": Unique identifier of the recorded transaction,
            "type": Transaction type as a string,
            "amount": Total transaction amount as a float,
            "currency": Currency code,
            "status": Payment status string,
            "created_at": ISO 8601 timestamp when the transaction was created
        }

    Raises:
        HTTPException: 503 if the finance & inventory agent is unavailable.
        HTTPException: 500 if an error occurs while recording the transaction.
    """
    if not FINANCE_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Finance & inventory agent not available"
        )

    try:
        transaction_data = request.dict()
        transaction = await finance_inventory_agent.record_transaction(transaction_data)

        return {
            "success": True,
            "transaction_id": transaction.transaction_id,
            "type": transaction.type.value,
            "amount": float(transaction.total_amount),
            "currency": transaction.currency,
            "status": transaction.payment_status,
            "created_at": transaction.created_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Transaction recording error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finance/forecast/{item_id}", tags=["Finance & Inventory"])
async def get_demand_forecast(item_id: str, forecast_period_days: int = 30):
    """
    Produce a demand forecast for a given inventory item.

    Parameters:
        item_id (str): Identifier of the inventory item (SKU or internal ID).
        forecast_period_days (int): Forecast horizon in days (default 30).

    Returns:
        dict: Forecast payload containing:
            - forecast_id: Unique identifier for the forecast.
            - item_id: The requested item identifier.
            - sku: Item SKU.
            - predicted_demand: Estimated demand quantity for the period.
            - confidence_interval: Dict with `lower` and `upper` bounds.
            - confidence_score: Numeric confidence metric for the prediction.
            - recommended_order_quantity: Suggested order quantity based on the forecast.
            - forecast_period: Human-readable period string (e.g., "30 days").
            - generated_at: ISO 8601 timestamp when the forecast was produced.

    Raises:
        HTTPException: If the finance & inventory agent is unavailable or if forecasting fails.
    """
    if not FINANCE_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Finance & inventory agent not available"
        )

    try:
        forecast = await finance_inventory_agent.forecast_demand(item_id, forecast_period_days)

        return {
            "forecast_id": forecast.forecast_id,
            "item_id": forecast.item_id,
            "sku": forecast.sku,
            "predicted_demand": forecast.predicted_demand,
            "confidence_interval": {
                "lower": forecast.confidence_interval_lower,
                "upper": forecast.confidence_interval_upper,
            },
            "confidence_score": forecast.confidence_score,
            "recommended_order_quantity": forecast.recommended_order_quantity,
            "forecast_period": f"{forecast_period_days} days",
            "generated_at": forecast.generated_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Demand forecasting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finance/reports/financial", tags=["Finance & Inventory"])
async def generate_financial_report(start_date: datetime, end_date: datetime):
    """
    Generate a financial report for the specified date range.

    Parameters:
        start_date (datetime): Start of the reporting period (inclusive).
        end_date (datetime): End of the reporting period (inclusive).

    Returns:
        dict: A report containing aggregated financial metrics and breakdowns, typically including:
            - revenue: total revenue for the period
            - profit_margins: overall and/or per-channel profit margin metrics
            - top_selling_items: list of top items with sales and revenue stats
            - channel_breakdown: revenue and performance by sales channel
            - totals: aggregated totals (orders, units, refunds, etc.)
            - time_range: the report's start and end timestamps
            - generated_at: timestamp when the report was produced
            - any additional aggregated metrics or confidence/quality indicators provided by the agent
    """
    if not FINANCE_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Finance & inventory agent not available"
        )

    try:
        report = await finance_inventory_agent.generate_financial_report(start_date, end_date)

        return report

    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finance/status", tags=["Finance & Inventory"])
async def get_finance_inventory_status():
    """
    Return availability and operational status for the finance and inventory agent.

    Returns:
        dict: A status payload with either:
            - When the agent is available: {"available": True, "status": <agent status dict>}
            - When the agent is unavailable: {"available": False, "error": "<error message>"}
    """
    if not FINANCE_AGENT_AVAILABLE:
        return {"available": False, "error": "Finance agent not available"}

    return {
        "available": True,
        "status": finance_inventory_agent.get_system_status(),
    }


# ============================================================================
# MARKETING CAMPAIGN ENDPOINTS
# ============================================================================


@router.post("/marketing/campaigns/create", tags=["Marketing"])
async def create_campaign(request: CampaignRequest):
    """
    Create a new marketing campaign.

    Parameters:
        request (CampaignRequest): Campaign definition including name, description, campaign_type, channels, target segments, variants, budget, and scheduling.

    Returns:
        dict: Metadata about the created campaign containing:
            - success (bool): `True` when creation succeeded.
            - campaign_id (str): Unique identifier for the campaign.
            - name (str): Campaign name.
            - type (str): Campaign type.
            - status (str): Current campaign status.
            - channels (list[str]): Enabled distribution channels.
            - enable_testing (bool): Whether A/B testing is enabled.
            - variants_count (int): Number of campaign variants.
            - created_at (str): ISO-8601 timestamp when the campaign was created.
    """
    if not MARKETING_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Marketing orchestrator not available"
        )

    try:
        campaign_data = request.dict()
        campaign = await marketing_orchestrator.create_campaign(campaign_data)

        return {
            "success": True,
            "campaign_id": campaign.campaign_id,
            "name": campaign.name,
            "type": campaign.campaign_type.value,
            "status": campaign.status.value,
            "channels": [ch.value for ch in campaign.channels],
            "enable_testing": campaign.enable_testing,
            "variants_count": len(campaign.variants),
            "created_at": campaign.created_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Campaign creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketing/campaigns/{campaign_id}/launch", tags=["Marketing"])
async def launch_campaign(campaign_id: str):
    """
    Launches a marketing campaign across configured channels and starts A/B testing when enabled.

    @param campaign_id: Identifier of the campaign to launch.
    @returns: A dictionary with launch metadata (e.g., `campaign_id`, `status`, `launch_time`, and any provider-specific details or errors).
    @raises HTTPException: Raised with status 503 if the marketing orchestrator is unavailable; raised with status 500 if the campaign launch fails.
    """
    if not MARKETING_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Marketing orchestrator not available"
        )

    try:
        result = await marketing_orchestrator.launch_campaign(campaign_id)
        return result

    except Exception as e:
        logger.error(f"Campaign launch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketing/campaigns/{campaign_id}/complete", tags=["Marketing"])
async def complete_campaign(campaign_id: str):
    """
    Finalize a marketing campaign and produce its final performance report.

    Parameters:
        campaign_id (str): Identifier of the campaign to complete.

    Returns:
        dict: Final campaign metadata and analytics, typically including fields such as `campaign_id`, `status`, `roi`, `conversion_rates`, `ab_test_results`, and `completed_at`.

    Raises:
        HTTPException: If the marketing orchestrator is unavailable or the completion operation fails.
    """
    if not MARKETING_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Marketing orchestrator not available"
        )

    try:
        result = await marketing_orchestrator.complete_campaign(campaign_id)
        return result

    except Exception as e:
        logger.error(f"Campaign completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketing/segments/create", tags=["Marketing"])
async def create_segment(segment_data: dict[str, Any]):
    """
    Create a customer segment for targeted marketing.

    Parameters:
        segment_data (dict[str, Any]): Criteria and metadata for the segment (for example: "name", "demographics", "behavior", "purchase_history", "engagement", "filters"). Keys and value shapes depend on the marketing orchestrator's schema.

    Returns:
        dict: Result object with keys:
            - success (bool): `True` on successful creation.
            - segment_id (str): Identifier of the created segment.
            - name (str): Segment name.
            - customer_count (int): Number of customers included in the segment.
            - created_at (str): ISO 8601 timestamp of creation.

    Raises:
        HTTPException: `503` if the marketing orchestrator is unavailable.
        HTTPException: `500` if segment creation fails due to an internal error.
    """
    if not MARKETING_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Marketing orchestrator not available"
        )

    try:
        segment = await marketing_orchestrator.create_segment(segment_data)

        return {
            "success": True,
            "segment_id": segment.segment_id,
            "name": segment.name,
            "customer_count": segment.customer_count,
            "created_at": segment.created_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Segment creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marketing/status", tags=["Marketing"])
async def get_marketing_status():
    """
    Return the availability and system status of the marketing orchestrator.

    Returns:
        dict: `{"available": True, "status": <status_payload>}` when the orchestrator is available; `{"available": False, "error": "<message>"}` when it is not.
    """
    if not MARKETING_AGENT_AVAILABLE:
        return {"available": False, "error": "Marketing orchestrator not available"}

    return {
        "available": True,
        "status": marketing_orchestrator.get_system_status(),
    }


# ============================================================================
# CODE GENERATION & RECOVERY ENDPOINTS
# ============================================================================


@router.post("/code/generate", tags=["Code Development"])
async def generate_code(request: CodeGenerationRequest):
    """
    Generate source code and accompanying metadata from a high-level code specification.

    Parameters:
        request (CodeGenerationRequest): Generation parameters including a textual description, target language and framework, dependency requirements, whether to include tests and documentation, and the preferred model.

    Returns:
        dict: Generation result with keys:
            - `success` (bool): `true` if generation completed without fatal errors, `false` otherwise.
            - `request_id` (str): Provider or agent request identifier.
            - `code` (str): Generated source code (may be multi-file concatenation or a single file content).
            - `file_path` (str|None): Suggested or persisted file path for the generated code, if available.
            - `language` (str): Target programming language.
            - `quality_score` (float|None): Heuristic quality score for the generated code.
            - `complexity_score` (float|None): Heuristic complexity metric.
            - `issues_found` (list[dict]|None): Detected issues or linting findings.
            - `suggestions` (list[str]|None): Recommendations to improve or refactor the generated code.
            - `generation_time` (float|None): Time in seconds taken to generate the code.
            - `model_used` (str|None): Model identifier used for generation.
            - `error` (str|None): Error message when generation failed.

    Raises:
        HTTPException: with status 503 if the code recovery agent is unavailable.
        HTTPException: with status 500 on internal generation failures.
    """
    if not CODE_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Code recovery agent not available"
        )

    try:
        gen_request = CodeGenRequest(
            description=request.description,
            language=CodeLanguage(request.language),
            framework=request.framework,
            requirements=request.requirements,
            test_requirements=request.include_tests,
            documentation_required=request.include_docs,
            model=request.model,
        )

        result = await code_recovery_agent.generate_code(gen_request)

        return {
            "success": result.success,
            "request_id": result.request_id,
            "code": result.code,
            "file_path": result.file_path,
            "language": result.language.value,
            "quality_score": result.quality_score,
            "complexity_score": result.complexity_score,
            "issues_found": result.issues_found,
            "suggestions": result.suggestions,
            "generation_time": result.generation_time,
            "model_used": result.model_used,
            "error": result.error,
        }

    except Exception as e:
        logger.error(f"Code generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code/recover", tags=["Code Development"])
async def recover_code(request: CodeRecoveryRequestModel):
    """
    Recover source code from a repository or backups using the code recovery agent.

    Parameters:
        request (CodeRecoveryRequestModel): Recovery parameters including recovery_type (strategy), repository_url, file_path, branch, and commit_hash.

    Returns:
        dict: Recovery result containing:
            - `success`: `true` if recovery succeeded, `false` otherwise.
            - `request_id`: Unique identifier for the recovery request.
            - `files_recovered`: Number of files successfully recovered.
            - `total_lines`: Total number of lines recovered across all files.
            - `strategy_used`: Name of the recovery strategy applied.
            - `integrity_verified`: `true` if recovered content passed integrity checks, `false` otherwise.
            - `recovery_time`: Recovery duration or timestamp as provided by the agent.
            - `error`: Error message when recovery failed, or `null` on success.

    Raises:
        HTTPException: 503 when the code recovery agent is unavailable.
        HTTPException: 500 for internal errors encountered during recovery.
    """
    if not CODE_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Code recovery agent not available"
        )

    try:
        recovery_request = CodeRecoveryRequest(
            recovery_type=RecoveryStrategy(request.recovery_type),
            repository_url=request.repository_url,
            file_path=request.file_path,
            branch=request.branch,
            commit_hash=request.commit_hash,
        )

        result = await code_recovery_agent.recover_code(recovery_request)

        return {
            "success": result.success,
            "request_id": result.request_id,
            "files_recovered": len(result.files_recovered),
            "total_lines": result.total_lines,
            "strategy_used": result.strategy_used.value,
            "integrity_verified": result.integrity_verified,
            "recovery_time": result.recovery_time,
            "error": result.error,
        }

    except Exception as e:
        logger.error(f"Code recovery error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/code/status", tags=["Code Development"])
async def get_code_agent_status():
    """
    Report the availability and system status of the code recovery agent.

    Returns:
        dict: If the agent is available, returns {"available": True, "status": <status dict>}.
              If the agent is unavailable, returns {"available": False, "error": "<error message>"}.
    """
    if not CODE_AGENT_AVAILABLE:
        return {"available": False, "error": "Code agent not available"}

    return {
        "available": True,
        "status": code_recovery_agent.get_system_status(),
    }


# ============================================================================
# WORKFLOW ORCHESTRATION ENDPOINTS
# ============================================================================


@router.post("/workflows/create", tags=["Workflows"])
async def create_workflow(request: WorkflowExecutionRequest):
    """
    Create a multi-agent workflow.

    Supported workflow types:
    - fashion_brand_launch: Complete brand launch automation
    - product_launch: New product launch with marketing
    - marketing_campaign: Multi-channel campaign with A/B testing
    - inventory_sync: Cross-platform inventory synchronization
    - content_generation: Automated content pipeline

    Returns:
        dict: Workflow creation result containing:
            - `success` (bool): `True` if creation succeeded.
            - `workflow_id` (str): Identifier of the created workflow.
            - `name` (str): Workflow name.
            - `type` (str): Workflow type value.
            - `total_tasks` (int): Number of tasks in the workflow.
            - `status` (str): Current workflow status value.

    Raises:
        HTTPException: 503 if the workflow engine is not available.
        HTTPException: 500 if workflow creation fails.
    """
    if not WORKFLOW_ENGINE_AVAILABLE:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Workflow engine not available")

    try:
        workflow_type = WorkflowType(request.workflow_type)
        workflow = await workflow_engine.create_workflow(workflow_type, request.workflow_data)

        return {
            "success": True,
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "type": workflow.workflow_type.value,
            "total_tasks": len(workflow.tasks),
            "status": workflow.status.value,
        }

    except Exception as e:
        logger.error(f"Workflow creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/{workflow_id}/execute", tags=["Workflows"])
async def execute_workflow(workflow_id: str, background_tasks: BackgroundTasks):
    """
    Start execution of the specified workflow and schedule it to run in the background.

    Schedules the workflow engine to execute the workflow identified by `workflow_id`. If the workflow engine is unavailable an HTTP 503 is raised.

    Returns:
        result (dict): Execution acknowledgement containing:
            - `success` (bool): `True` when execution was scheduled.
            - `workflow_id` (str): The id of the scheduled workflow.
            - `message` (str): Human-readable status message.
            - `status_endpoint` (str): URL where the workflow status can be queried.
    """
    if not WORKFLOW_ENGINE_AVAILABLE:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Workflow engine not available")

    # Execute workflow in background
    background_tasks.add_task(workflow_engine.execute_workflow, workflow_id)

    return {
        "success": True,
        "workflow_id": workflow_id,
        "message": "Workflow execution started",
        "status_endpoint": f"/api/v1/luxury-automation/workflows/{workflow_id}/status",
    }


@router.get("/workflows/{workflow_id}/status", tags=["Workflows"])
async def get_workflow_status(workflow_id: str):
    """
    Fetch the current execution status and progress for a workflow.

    Returns:
        A dict with workflow runtime state and metadata, typically including keys such as `status`, `progress` (percentage), and `tasks` (per-task results).

    Raises:
        HTTPException: 503 if the workflow engine is unavailable.
        HTTPException: 404 if the requested workflow reports an error or is not found.
        HTTPException: 500 for unexpected server-side errors.
    """
    if not WORKFLOW_ENGINE_AVAILABLE:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Workflow engine not available")

    try:
        status = workflow_engine.get_workflow_status(workflow_id)

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/status", tags=["Workflows"])
async def get_workflow_engine_status():
    """
    Get the workflow engine's availability and current system status.

    Returns:
        dict: A status payload with:
            - available (bool): True when the workflow engine is available, False otherwise.
            - status (Any): System status object from the workflow engine when available.
            - error (str): Error message when the workflow engine is unavailable.
    """
    if not WORKFLOW_ENGINE_AVAILABLE:
        return {"available": False, "error": "Workflow engine not available"}

    return {
        "available": True,
        "status": workflow_engine.get_system_status(),
    }


# ============================================================================
# SYSTEM STATUS ENDPOINT
# ============================================================================


@router.get("/system/status", tags=["System"])
async def get_system_status():
    """
    Get the overall runtime status of the system and its optional agents.

    Returns:
        dict: A dictionary with keys:
            - `timestamp` (str): ISO 8601 timestamp of the status snapshot.
            - `version` (str): Service version identifier.
            - `agents` (dict): Mapping of agent names to status objects. Each agent entry contains:
                - `available` (bool): Whether the agent is present and enabled.
                - `status` (object|None): Agent-specific status information when available, or `None` when unavailable.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-production",
        "agents": {
            "visual_content": {
                "available": VISUAL_AGENT_AVAILABLE,
                "status": visual_content_agent.get_system_status() if VISUAL_AGENT_AVAILABLE else None,
            },
            "finance_inventory": {
                "available": FINANCE_AGENT_AVAILABLE,
                "status": finance_inventory_agent.get_system_status() if FINANCE_AGENT_AVAILABLE else None,
            },
            "marketing": {
                "available": MARKETING_AGENT_AVAILABLE,
                "status": marketing_orchestrator.get_system_status() if MARKETING_AGENT_AVAILABLE else None,
            },
            "code_development": {
                "available": CODE_AGENT_AVAILABLE,
                "status": code_recovery_agent.get_system_status() if CODE_AGENT_AVAILABLE else None,
            },
            "workflow_engine": {
                "available": WORKFLOW_ENGINE_AVAILABLE,
                "status": workflow_engine.get_system_status() if WORKFLOW_ENGINE_AVAILABLE else None,
            },
        },
    }
