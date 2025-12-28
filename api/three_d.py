"""
3D Pipeline API Endpoints
=========================

Real 3D generation endpoints using:
- HuggingFace 3D Models (Hunyuan3D-2, TripoSR, InstantMesh, LGM, SHAP-E, POINT-E)
- TRELLIS (Microsoft) - HuggingFace Gradio API (free, high quality)
- Tripo3D - Commercial API (fast, production)

Supports two modes:
- Direct: Pick a single provider for generation
- Round Table: All providers compete, A/B test top 2, select winner

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import logging
import os
import shutil
import time
import uuid
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

three_d_router = APIRouter(tags=["3D Pipeline"])


# =============================================================================
# Configuration
# =============================================================================

OUTPUT_DIR = Path(os.getenv("THREE_D_OUTPUT_DIR", "./assets/3d-models-generated"))
UPLOAD_DIR = Path(os.getenv("THREE_D_UPLOAD_DIR", "./assets/3d-uploads"))

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Enums & Models
# =============================================================================


class ModelProvider(str, Enum):
    """3D generation provider."""

    # Direct providers
    TRELLIS = "trellis"  # Microsoft TRELLIS via HuggingFace (free)
    TRIPO = "tripo"  # Tripo3D commercial API

    # HuggingFace Round Table providers
    HUNYUAN3D = "hunyuan3d"  # Hunyuan3D-2 (high quality)
    TRIPOSR = "triposr"  # TripoSR (fast)
    INSTANTMESH = "instantmesh"  # InstantMesh
    LGM = "lgm"  # LGM
    SHAP_E = "shap_e"  # SHAP-E (text-to-3D)
    POINT_E = "point_e"  # POINT-E

    # Competition mode
    ROUND_TABLE = "round_table"  # All compete, A/B test winner


class JobStatus(str, Enum):
    """Generation job status."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerateTextRequest(BaseModel):
    """Request to generate 3D from text."""

    prompt: str = Field(..., min_length=1, max_length=2000)
    product_name: str = Field(..., min_length=1, max_length=200)
    collection: str = Field(default="SIGNATURE")
    garment_type: str = Field(default="tee")
    provider: ModelProvider = Field(default=ModelProvider.TRIPO)
    output_format: str = Field(default="glb")


class GenerateImageRequest(BaseModel):
    """Request to generate 3D from image URL."""

    image_url: str = Field(..., min_length=1)
    product_name: str = Field(default="")
    provider: ModelProvider = Field(default=ModelProvider.TRELLIS)
    texture_size: int = Field(default=1024, ge=512, le=2048)


class JobResponse(BaseModel):
    """Response for a generation job."""

    job_id: str
    status: JobStatus
    provider: str
    product_name: str
    created_at: str
    completed_at: str | None = None
    model_url: str | None = None
    model_path: str | None = None
    preview_url: str | None = None
    error: str | None = None
    progress: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineStatus(BaseModel):
    """Pipeline status response."""

    status: str
    providers: list[dict[str, Any]]
    queue_length: int
    processing_time_avg: float
    last_generated: str | None
    total_generated: int


class ProviderInfo(BaseModel):
    """Provider information."""

    name: str
    display_name: str
    description: str
    status: str
    avg_time_seconds: float
    cost_per_model: float
    supported_inputs: list[str]


# =============================================================================
# In-Memory Job Store
# =============================================================================


class JobStore:
    """In-memory job storage."""

    def __init__(self):
        self._jobs: dict[str, JobResponse] = {}
        self._total_generated = 0
        self._total_time_ms = 0.0

    def create(
        self,
        provider: ModelProvider,
        product_name: str,
        metadata: dict[str, Any] | None = None,
    ) -> JobResponse:
        """Create a new job."""
        job_id = f"3d_{uuid.uuid4().hex[:12]}"
        job = JobResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            provider=provider.value,
            product_name=product_name,
            created_at=datetime.now(UTC).isoformat(),
            metadata=metadata or {},
        )
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> JobResponse | None:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs) -> JobResponse | None:
        """Update job fields."""
        job = self._jobs.get(job_id)
        if job:
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
        return job

    def complete(
        self,
        job_id: str,
        model_url: str,
        model_path: str,
        duration_ms: float,
    ) -> JobResponse | None:
        """Mark job as completed."""
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.model_url = model_url
            job.model_path = model_path
            job.completed_at = datetime.now(UTC).isoformat()
            job.progress = 1.0
            self._total_generated += 1
            self._total_time_ms += duration_ms
        return job

    def fail(self, job_id: str, error: str) -> JobResponse | None:
        """Mark job as failed."""
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error = error
            job.completed_at = datetime.now(UTC).isoformat()
        return job

    def list_jobs(self, limit: int = 20) -> list[JobResponse]:
        """List recent jobs."""
        jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    @property
    def queue_length(self) -> int:
        """Get number of queued/processing jobs."""
        return sum(
            1 for j in self._jobs.values() if j.status in (JobStatus.QUEUED, JobStatus.PROCESSING)
        )

    @property
    def avg_time_seconds(self) -> float:
        """Get average generation time."""
        if self._total_generated == 0:
            return 10.0  # Default estimate
        return (self._total_time_ms / self._total_generated) / 1000

    @property
    def total_generated(self) -> int:
        """Get total generated count."""
        return self._total_generated

    @property
    def last_generated(self) -> str | None:
        """Get timestamp of last completed job."""
        completed = [j for j in self._jobs.values() if j.status == JobStatus.COMPLETED]
        if completed:
            completed.sort(key=lambda j: j.completed_at or "", reverse=True)
            return completed[0].completed_at
        return None


job_store = JobStore()


# =============================================================================
# Background Task Runners
# =============================================================================


async def run_trellis_generation(
    job_id: str,
    image_path: str,
    output_dir: Path,
    texture_size: int = 1024,
):
    """Run TRELLIS generation in background."""
    start_time = time.time()

    try:
        job_store.update(job_id, status=JobStatus.PROCESSING, progress=0.1)

        # Import gradio client
        try:
            from gradio_client import Client, handle_file
        except ImportError:
            job_store.fail(job_id, "gradio_client not installed. Run: pip install gradio_client")
            return

        # Connect to TRELLIS HuggingFace Space
        job_store.update(job_id, progress=0.2)
        client = Client("JeffreyXiang/TRELLIS")

        job_store.update(job_id, progress=0.3)

        # Call TRELLIS API
        result = client.predict(
            image=handle_file(image_path),
            multiimages=[],
            seed=42,
            ss_guidance_strength=7.5,
            ss_sampling_steps=12,
            slat_guidance_strength=3,
            slat_sampling_steps=12,
            multiimage_algo="stochastic",
            mesh_simplify=0.95,
            texture_size=texture_size,
            api_name="/generate_and_extract_glb",
        )

        job_store.update(job_id, progress=0.8)

        # Extract GLB path
        video_info, glb_path, download_path = result

        if glb_path and os.path.exists(glb_path):
            # Copy to output directory
            job = job_store.get(job_id)
            output_name = f"{job.product_name or 'model'}_{job_id}.glb".replace(" ", "_")
            output_path = output_dir / output_name
            shutil.copy2(glb_path, output_path)

            duration_ms = (time.time() - start_time) * 1000
            job_store.complete(
                job_id,
                model_url=f"/assets/3d-models-generated/{output_name}",
                model_path=str(output_path),
                duration_ms=duration_ms,
            )
            logger.info(f"TRELLIS generation completed: {job_id}")
        else:
            job_store.fail(job_id, "No GLB file returned from TRELLIS")

    except Exception as e:
        logger.exception(f"TRELLIS generation failed: {e}")
        job_store.fail(job_id, str(e))


async def run_tripo_generation(
    job_id: str,
    prompt: str,
    collection: str,
    garment_type: str,
    output_format: str,
):
    """Run Tripo3D generation in background."""
    start_time = time.time()

    try:
        job_store.update(job_id, status=JobStatus.PROCESSING, progress=0.1)

        # Import Tripo agent
        from agents.tripo_agent import TripoAssetAgent

        agent = TripoAssetAgent()
        job_store.update(job_id, progress=0.2)

        # Get product name from job
        job = job_store.get(job_id)
        product_name = job.product_name if job else "product"

        # Generate 3D model
        result = await agent._tool_generate_from_text(
            product_name=product_name,
            collection=collection,
            garment_type=garment_type,
            additional_details=prompt,
            output_format=output_format,
        )

        job_store.update(job_id, progress=0.9)

        if result and result.get("model_path"):
            duration_ms = (time.time() - start_time) * 1000
            job_store.complete(
                job_id,
                model_url=result.get("model_url", ""),
                model_path=result.get("model_path", ""),
                duration_ms=duration_ms,
            )
            logger.info(f"Tripo3D generation completed: {job_id}")
        else:
            job_store.fail(job_id, "No model returned from Tripo3D")

        await agent.close()

    except Exception as e:
        logger.exception(f"Tripo3D generation failed: {e}")
        job_store.fail(job_id, str(e))


async def run_huggingface_text_generation(
    job_id: str,
    prompt: str,
    model: str,
):
    """Run HuggingFace text-to-3D generation in background."""
    start_time = time.time()

    try:
        job_store.update(job_id, status=JobStatus.PROCESSING, progress=0.1)

        # Import HuggingFace client
        from orchestration.huggingface_3d_client import HF3DModel, HF3DQuality, HuggingFace3DClient

        client = HuggingFace3DClient()
        job_store.update(job_id, progress=0.2)

        # Map provider to model
        model_map = {
            "shap_e": HF3DModel.SHAP_E_TEXT,
            "point_e": HF3DModel.POINT_E,
            "hunyuan3d": HF3DModel.HUNYUAN3D_2,
        }
        hf_model = model_map.get(model, HF3DModel.SHAP_E_TEXT)

        try:
            result = await client.generate_from_text(
                prompt=prompt,
                model=hf_model,
                quality=HF3DQuality.PRODUCTION,
            )

            job_store.update(job_id, progress=0.9)

            if result.status == "success" and result.output_path:
                duration_ms = (time.time() - start_time) * 1000
                job_store.complete(
                    job_id,
                    model_url=result.output_url or "",
                    model_path=result.output_path,
                    duration_ms=duration_ms,
                )
                logger.info(f"HuggingFace text-to-3D completed: {job_id}, model: {model}")
            else:
                job_store.fail(job_id, result.error_message or "No output from HuggingFace")

        finally:
            await client.close()

    except Exception as e:
        logger.exception(f"HuggingFace text generation failed: {e}")
        job_store.fail(job_id, str(e))


async def run_huggingface_image_generation(
    job_id: str,
    image_path: str,
    model: str,
):
    """Run HuggingFace image-to-3D generation in background."""
    start_time = time.time()

    try:
        job_store.update(job_id, status=JobStatus.PROCESSING, progress=0.1)

        # Import HuggingFace client
        from orchestration.huggingface_3d_client import HF3DModel, HF3DQuality, HuggingFace3DClient

        client = HuggingFace3DClient()
        job_store.update(job_id, progress=0.2)

        # Map provider to model
        model_map = {
            "triposr": HF3DModel.TRIPOSR,
            "instantmesh": HF3DModel.INSTANTMESH,
            "lgm": HF3DModel.LGM,
            "hunyuan3d": HF3DModel.HUNYUAN3D_2,
        }
        hf_model = model_map.get(model, HF3DModel.TRIPOSR)

        try:
            result = await client.generate_from_image(
                image_path=image_path,
                model=hf_model,
                quality=HF3DQuality.PRODUCTION,
            )

            job_store.update(job_id, progress=0.9)

            if result.status == "success" and result.output_path:
                duration_ms = (time.time() - start_time) * 1000
                job_store.complete(
                    job_id,
                    model_url=result.output_url or "",
                    model_path=result.output_path,
                    duration_ms=duration_ms,
                )
                logger.info(f"HuggingFace image-to-3D completed: {job_id}, model: {model}")
            else:
                job_store.fail(job_id, result.error_message or "No output from HuggingFace")

        finally:
            await client.close()

    except Exception as e:
        logger.exception(f"HuggingFace image generation failed: {e}")
        job_store.fail(job_id, str(e))


async def run_round_table_generation(
    job_id: str,
    image_path: str | None,
    prompt: str | None,
    is_text: bool = False,
):
    """Run 3D Round Table competition in background."""
    start_time = time.time()

    try:
        job_store.update(job_id, status=JobStatus.PROCESSING, progress=0.1)

        # Import ThreeDRoundTable
        try:
            from orchestration.threed_round_table import HF3DQuality, ThreeDRoundTable
        except ImportError:
            job_store.fail(job_id, "ThreeDRoundTable not available. Check orchestration module.")
            return

        round_table = ThreeDRoundTable(
            output_dir=str(OUTPUT_DIR),
            enable_tripo3d=bool(os.getenv("TRIPO_API_KEY")),
        )

        job_store.update(job_id, progress=0.2)

        try:
            if is_text and prompt:
                result = await round_table.compete_text_to_3d(
                    prompt=prompt,
                    quality=HF3DQuality.PRODUCTION,
                    task_id=job_id,
                )
            elif image_path:
                result = await round_table.compete_image_to_3d(
                    image_path=image_path,
                    quality=HF3DQuality.PRODUCTION,
                    task_id=job_id,
                )
            else:
                job_store.fail(job_id, "Either prompt or image_path required")
                return

            job_store.update(job_id, progress=0.9)

            if result.winner and result.winner.response.success:
                duration_ms = (time.time() - start_time) * 1000
                winner = result.winner

                # Store competition details in metadata
                job = job_store.get(job_id)
                if job:
                    job.metadata.update(
                        {
                            "competition_id": result.id,
                            "winner_provider": winner.provider.value,
                            "winner_score": winner.total_score,
                            "competitors": len(result.entries),
                            "ab_test": {
                                "reasoning": result.ab_test.reasoning if result.ab_test else None,
                                "confidence": result.ab_test.confidence if result.ab_test else None,
                            },
                        }
                    )

                job_store.complete(
                    job_id,
                    model_url=winner.response.output_url or "",
                    model_path=winner.response.output_path or "",
                    duration_ms=duration_ms,
                )
                logger.info(
                    f"Round Table completed: {job_id}, winner: {winner.provider.value}, "
                    f"score: {winner.total_score:.1f}"
                )
            else:
                job_store.fail(job_id, f"Round Table failed: {result.status.value}")

        finally:
            await round_table.close()

    except Exception as e:
        logger.exception(f"Round Table generation failed: {e}")
        job_store.fail(job_id, str(e))


# =============================================================================
# Endpoints
# =============================================================================


@three_d_router.get("/3d/status", response_model=PipelineStatus)
async def get_pipeline_status() -> PipelineStatus:
    """Get 3D pipeline status."""
    # Check provider availability
    tripo_available = bool(os.getenv("TRIPO_API_KEY"))

    providers = [
        {
            "name": "trellis",
            "display_name": "TRELLIS (Microsoft)",
            "status": "available",
            "type": "huggingface",
        },
        {
            "name": "tripo",
            "display_name": "Tripo3D",
            "status": "available" if tripo_available else "requires_api_key",
            "type": "commercial",
        },
    ]

    return PipelineStatus(
        status="operational",
        providers=providers,
        queue_length=job_store.queue_length,
        processing_time_avg=job_store.avg_time_seconds,
        last_generated=job_store.last_generated,
        total_generated=job_store.total_generated,
    )


@three_d_router.get("/3d/providers", response_model=list[ProviderInfo])
async def list_providers() -> list[ProviderInfo]:
    """List available 3D generation providers."""
    tripo_available = bool(os.getenv("TRIPO_API_KEY"))

    return [
        # Round Table - Competition mode
        ProviderInfo(
            name="round_table",
            display_name="🏆 Round Table",
            description="All HuggingFace models compete. A/B test top 2. Returns best quality.",
            status="available",
            avg_time_seconds=120.0,  # Multiple models in parallel
            cost_per_model=0.03 if tripo_available else 0.0,
            supported_inputs=["text", "image"],
        ),
        # Direct Providers
        ProviderInfo(
            name="hunyuan3d",
            display_name="Hunyuan3D-2",
            description="High-quality text/image to 3D. Best geometry quality.",
            status="available",
            avg_time_seconds=60.0,
            cost_per_model=0.0,
            supported_inputs=["text", "image"],
        ),
        ProviderInfo(
            name="trellis",
            display_name="TRELLIS (Microsoft)",
            description="High-quality 3D via HuggingFace Gradio API. Free, ~30-60s per model.",
            status="available",
            avg_time_seconds=45.0,
            cost_per_model=0.0,
            supported_inputs=["image"],
        ),
        ProviderInfo(
            name="triposr",
            display_name="TripoSR",
            description="Fast image-to-3D with good quality.",
            status="available",
            avg_time_seconds=30.0,
            cost_per_model=0.0,
            supported_inputs=["image"],
        ),
        ProviderInfo(
            name="instantmesh",
            display_name="InstantMesh",
            description="Multi-view image to 3D mesh generation.",
            status="available",
            avg_time_seconds=45.0,
            cost_per_model=0.0,
            supported_inputs=["image"],
        ),
        ProviderInfo(
            name="tripo",
            display_name="Tripo3D",
            description="Commercial 3D API. Fast production quality, ~10s per model.",
            status="available" if tripo_available else "requires_api_key",
            avg_time_seconds=10.0,
            cost_per_model=0.03,
            supported_inputs=["text", "image"],
        ),
        ProviderInfo(
            name="shap_e",
            display_name="SHAP-E",
            description="OpenAI's text-to-3D model. Good for simple shapes.",
            status="available",
            avg_time_seconds=30.0,
            cost_per_model=0.0,
            supported_inputs=["text"],
        ),
    ]


@three_d_router.get("/3d/jobs", response_model=list[JobResponse])
async def list_jobs(limit: int = 20) -> list[JobResponse]:
    """List recent generation jobs."""
    return job_store.list_jobs(limit)


@three_d_router.get("/3d/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    """Get a specific job by ID."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@three_d_router.post("/3d/generate/text", response_model=JobResponse)
async def generate_from_text(
    request: GenerateTextRequest,
    background_tasks: BackgroundTasks,
) -> JobResponse:
    """Generate 3D model from text description."""
    # Validate provider for text-to-3D
    image_only_providers = [
        ModelProvider.TRELLIS,
        ModelProvider.TRIPOSR,
        ModelProvider.INSTANTMESH,
        ModelProvider.LGM,
    ]
    if request.provider in image_only_providers:
        raise HTTPException(
            status_code=400,
            detail=f"{request.provider.value} only supports image input. Use /3d/generate/image or select a text-to-3D provider.",
        )

    if request.provider == ModelProvider.TRIPO and not os.getenv("TRIPO_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="TRIPO_API_KEY not configured. Set environment variable to use Tripo3D.",
        )

    # Create job
    job = job_store.create(
        provider=request.provider,
        product_name=request.product_name,
        metadata={
            "prompt": request.prompt,
            "collection": request.collection,
            "garment_type": request.garment_type,
            "mode": "round_table" if request.provider == ModelProvider.ROUND_TABLE else "direct",
        },
    )

    # Schedule background task based on provider
    huggingface_text_providers = [
        ModelProvider.SHAP_E,
        ModelProvider.POINT_E,
        ModelProvider.HUNYUAN3D,
    ]

    if request.provider == ModelProvider.ROUND_TABLE:
        background_tasks.add_task(
            run_round_table_generation,
            job.job_id,
            None,  # No image for text-to-3D
            request.prompt,
            True,  # is_text = True
        )
    elif request.provider in huggingface_text_providers:
        background_tasks.add_task(
            run_huggingface_text_generation,
            job.job_id,
            request.prompt,
            request.provider.value,
        )
    else:
        # Tripo3D
        background_tasks.add_task(
            run_tripo_generation,
            job.job_id,
            request.prompt,
            request.collection,
            request.garment_type,
            request.output_format,
        )

    return job


@three_d_router.post("/3d/generate/image", response_model=JobResponse)
async def generate_from_image_url(
    request: GenerateImageRequest,
    background_tasks: BackgroundTasks,
) -> JobResponse:
    """Generate 3D model from image URL."""
    # Create job
    job = job_store.create(
        provider=request.provider,
        product_name=request.product_name or "uploaded_image",
        metadata={
            "image_url": request.image_url,
            "texture_size": request.texture_size,
        },
    )

    # Download image first
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(request.image_url)
            resp.raise_for_status()

            # Save to temp file
            ext = Path(request.image_url).suffix or ".png"
            temp_path = UPLOAD_DIR / f"{job.job_id}{ext}"
            temp_path.write_bytes(resp.content)

    except Exception as e:
        job_store.fail(job.job_id, f"Failed to download image: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to download image: {e}")

    # Schedule background task based on provider
    huggingface_image_providers = [
        ModelProvider.TRIPOSR,
        ModelProvider.INSTANTMESH,
        ModelProvider.LGM,
        ModelProvider.HUNYUAN3D,
    ]

    if request.provider == ModelProvider.ROUND_TABLE:
        background_tasks.add_task(
            run_round_table_generation,
            job.job_id,
            str(temp_path),
            None,  # No text prompt
            False,  # is_text = False
        )
    elif request.provider == ModelProvider.TRELLIS:
        background_tasks.add_task(
            run_trellis_generation,
            job.job_id,
            str(temp_path),
            OUTPUT_DIR,
            request.texture_size,
        )
    elif request.provider in huggingface_image_providers:
        background_tasks.add_task(
            run_huggingface_image_generation,
            job.job_id,
            str(temp_path),
            request.provider.value,
        )
    else:
        # Tripo3D
        background_tasks.add_task(
            run_tripo_generation,
            job.job_id,
            "3D model of clothing item from image",
            "SIGNATURE",
            "clothing",
            "glb",
        )

    return job


@three_d_router.post("/3d/generate/upload", response_model=JobResponse)
async def generate_from_upload(
    file: UploadFile = File(...),
    provider: ModelProvider = ModelProvider.TRELLIS,
    product_name: str = "",
    texture_size: int = 1024,
    background_tasks: BackgroundTasks = None,
) -> JobResponse:
    """Generate 3D model from uploaded image file."""
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Create job
    job = job_store.create(
        provider=provider,
        product_name=product_name or file.filename or "uploaded_image",
        metadata={
            "filename": file.filename,
            "content_type": file.content_type,
            "texture_size": texture_size,
        },
    )

    # Save uploaded file
    ext = Path(file.filename or "image.png").suffix or ".png"
    upload_path = UPLOAD_DIR / f"{job.job_id}{ext}"

    try:
        content = await file.read()
        upload_path.write_bytes(content)
    except Exception as e:
        job_store.fail(job.job_id, f"Failed to save upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

    # Schedule background task based on provider
    huggingface_image_providers = [
        ModelProvider.TRIPOSR,
        ModelProvider.INSTANTMESH,
        ModelProvider.LGM,
        ModelProvider.HUNYUAN3D,
    ]

    if provider == ModelProvider.ROUND_TABLE:
        background_tasks.add_task(
            run_round_table_generation,
            job.job_id,
            str(upload_path),
            None,  # No text prompt
            False,  # is_text = False
        )
    elif provider == ModelProvider.TRELLIS:
        background_tasks.add_task(
            run_trellis_generation,
            job.job_id,
            str(upload_path),
            OUTPUT_DIR,
            texture_size,
        )
    elif provider in huggingface_image_providers:
        background_tasks.add_task(
            run_huggingface_image_generation,
            job.job_id,
            str(upload_path),
            provider.value,
        )
    else:
        # Tripo3D
        background_tasks.add_task(
            run_tripo_generation,
            job.job_id,
            "3D model of clothing item from uploaded image",
            "SIGNATURE",
            "clothing",
            "glb",
        )

    return job
