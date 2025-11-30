"""
Clothing Asset Pipeline Orchestrator

Coordinates the end-to-end workflow for 3D clothing asset generation:
1. 3D Model Generation (Tripo3D)
2. Virtual Try-On (FASHN)
3. WordPress Upload

Brand: SkyyRose - Oakland luxury streetwear, "where love meets luxury"
Collections: BLACK_ROSE, LOVE_HURTS, SIGNATURE

Truth Protocol Compliance:
- Rule #1: All APIs verified from official documentation
- Rule #5: All credentials via environment variables
- Rule #9: Fully documented with type hints
- Rule #10: Error handling with continue policy
- Rule #12: Performance tracking for SLO compliance
- Rule #14: Errors recorded to error ledger
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Any

from agent.modules.clothing.clients.fashn_client import FASHNClient, FASHNError
from agent.modules.clothing.clients.tripo3d_client import Tripo3DClient, Tripo3DError
from agent.modules.clothing.clients.wordpress_media import WordPressMediaClient, WordPressError
from agent.modules.clothing.schemas.schemas import (
    BatchPipelineRequest,
    BatchPipelineResult,
    ClothingItem,
    Model3DFormat,
    Model3DResult,
    PipelineResult,
    PipelineStage,
    TryOnModel,
    TryOnResult,
    WordPressUploadResult,
)
from core.enterprise_error_handler import record_error

logger = logging.getLogger(__name__)


class ClothingAssetPipeline:
    """
    Orchestrates the complete 3D clothing asset generation pipeline.

    This pipeline processes clothing items through:
    1. 3D Model Generation using Tripo3D
    2. Virtual Try-On using FASHN
    3. Upload to WordPress/WooCommerce

    Example:
        pipeline = ClothingAssetPipeline()
        await pipeline.initialize()

        item = ClothingItem(
            item_id="hoodie-001",
            name="Black Rose Hoodie",
            description="Luxury black hoodie with embroidered rose pattern",
            collection=ClothingCollection.BLACK_ROSE,
            category=ClothingCategory.HOODIE,
            color="black",
            price=149.99,
            sku="SR-BR-H001"
        )

        result = await pipeline.process_item(item)
        print(f"3D Model: {result.model_3d.model_url}")
        print(f"Try-On Images: {len(result.try_on_results)}")

    Attributes:
        tripo3d: Tripo3D client for 3D generation
        fashn: FASHN client for virtual try-on
        wordpress: WordPress client for uploads
    """

    def __init__(
        self,
        tripo3d_client: Tripo3DClient | None = None,
        fashn_client: FASHNClient | None = None,
        wordpress_client: WordPressMediaClient | None = None,
        enable_3d: bool = True,
        enable_tryon: bool = True,
        enable_upload: bool = True,
        tryon_models: list[TryOnModel] | None = None,
        model_format: Model3DFormat = Model3DFormat.GLB,
    ):
        """
        Initialize the pipeline.

        Args:
            tripo3d_client: Custom Tripo3D client (or creates new)
            fashn_client: Custom FASHN client (or creates new)
            wordpress_client: Custom WordPress client (or creates new)
            enable_3d: Enable 3D model generation
            enable_tryon: Enable virtual try-on
            enable_upload: Enable WordPress upload
            tryon_models: Model types for try-on
            model_format: 3D model output format
        """
        self.tripo3d = tripo3d_client or Tripo3DClient()
        self.fashn = fashn_client or FASHNClient()
        self.wordpress = wordpress_client or WordPressMediaClient()

        self.enable_3d = enable_3d
        self.enable_tryon = enable_tryon
        self.enable_upload = enable_upload
        self.tryon_models = tryon_models or [TryOnModel.FEMALE, TryOnModel.MALE]
        self.model_format = model_format

        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize all pipeline clients.

        Returns:
            True if all enabled clients initialized successfully
        """
        try:
            init_tasks = []

            if self.enable_3d:
                init_tasks.append(self.tripo3d.initialize())
            if self.enable_tryon:
                init_tasks.append(self.fashn.initialize())
            if self.enable_upload:
                init_tasks.append(self.wordpress.initialize())

            if init_tasks:
                results = await asyncio.gather(*init_tasks, return_exceptions=True)

                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.warning(f"Client initialization warning: {result}")

            self._initialized = True
            logger.info("ClothingAssetPipeline initialized successfully")
            return True

        except Exception as e:
            record_error(
                error_type="PipelineInitializationError",
                message=f"Failed to initialize pipeline: {e}",
                severity="HIGH",
                component="agent.modules.clothing.pipeline",
                exception=e,
                action="continue",
            )
            raise

    async def close(self) -> None:
        """Close all pipeline clients."""
        close_tasks = []

        if self.enable_3d:
            close_tasks.append(self.tripo3d.close())
        if self.enable_tryon:
            close_tasks.append(self.fashn.close())
        if self.enable_upload:
            close_tasks.append(self.wordpress.close())

        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)

        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure pipeline is initialized."""
        if not self._initialized:
            await self.initialize()

    async def process_item(
        self,
        item: ClothingItem,
        generate_3d: bool | None = None,
        generate_tryon: bool | None = None,
        upload: bool | None = None,
    ) -> PipelineResult:
        """
        Process a single clothing item through the pipeline.

        Executes enabled pipeline stages in sequence:
        1. Generate 3D model from item description
        2. Create virtual try-on images
        3. Upload all assets to WordPress

        Args:
            item: ClothingItem to process
            generate_3d: Override for 3D generation (uses default if None)
            generate_tryon: Override for try-on (uses default if None)
            upload: Override for upload (uses default if None)

        Returns:
            PipelineResult with all generated assets and metadata

        Example:
            result = await pipeline.process_item(item)
            if result.success:
                print(f"Generated {result.try_on_count} try-on images")
        """
        await self._ensure_initialized()

        start_time = time.time()

        # Use overrides or defaults
        do_3d = generate_3d if generate_3d is not None else self.enable_3d
        do_tryon = generate_tryon if generate_tryon is not None else self.enable_tryon
        do_upload = upload if upload is not None else self.enable_upload

        result = PipelineResult(
            item_id=item.item_id,
            item_name=item.name,
            stage=PipelineStage.PENDING,
            started_at=datetime.now(),
        )

        logger.info(f"Processing item: {item.name} ({item.item_id})")

        try:
            # Stage 1: 3D Model Generation
            if do_3d:
                result.stage = PipelineStage.GENERATING_3D
                result.model_3d = await self._generate_3d_model(item)

                if result.model_3d.status != "success":
                    result.errors.append(f"3D generation failed: {result.model_3d.metadata.get('error', 'Unknown')}")

            # Stage 2: Virtual Try-On
            if do_tryon:
                result.stage = PipelineStage.VIRTUAL_TRYON
                result.try_on_results = await self._generate_tryon(item, result.model_3d)

                failed_tryons = [r for r in result.try_on_results if r.status != "completed"]
                if failed_tryons:
                    result.errors.append(f"{len(failed_tryons)} try-on generation(s) failed")

            # Stage 3: WordPress Upload
            if do_upload:
                result.stage = PipelineStage.UPLOADING
                result.wordpress_uploads = await self._upload_assets(item, result)

            # Finalize
            result.stage = PipelineStage.COMPLETED
            result.success = len(result.errors) == 0
            result.completed_at = datetime.now()
            result.total_processing_time_seconds = time.time() - start_time

            logger.info(
                f"Completed processing {item.name}: "
                f"3D={result.has_3d_model}, "
                f"TryOns={result.try_on_count}, "
                f"Uploads={result.upload_count}, "
                f"Time={result.total_processing_time_seconds:.1f}s"
            )

        except Exception as e:
            result.stage = PipelineStage.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.now()
            result.total_processing_time_seconds = time.time() - start_time

            record_error(
                error_type="PipelineProcessingError",
                message=f"Failed to process item {item.item_id}: {e}",
                severity="HIGH",
                component="agent.modules.clothing.pipeline",
                context={"item_id": item.item_id, "item_name": item.name},
                exception=e,
                action="continue",
            )

        return result

    async def _generate_3d_model(self, item: ClothingItem) -> Model3DResult:
        """
        Generate 3D model for a clothing item.

        Uses image-to-3D if reference image available, otherwise text-to-3D.

        Args:
            item: ClothingItem to generate model for

        Returns:
            Model3DResult with generation status
        """
        logger.info(f"Generating 3D model for {item.name}")

        try:
            if item.reference_image_url or item.reference_image_path:
                # Image-to-3D generation
                result = await self.tripo3d.image_to_3d(
                    image_url=item.reference_image_url,
                    image_path=item.reference_image_path,
                    output_format=self.model_format,
                    wait_for_completion=True,
                )
            else:
                # Text-to-3D generation using optimized prompt
                result = await self.tripo3d.text_to_3d(
                    prompt=item.prompt_for_3d,
                    output_format=self.model_format,
                    wait_for_completion=True,
                )

            return result

        except Tripo3DError as e:
            record_error(
                error_type="3DGenerationError",
                message=f"3D generation failed for {item.item_id}: {e}",
                severity="MEDIUM",
                component="agent.modules.clothing.pipeline",
                context={"item_id": item.item_id},
                exception=e,
                action="continue",
            )

            return Model3DResult(
                task_id="error",
                status="failed",
                model_format=self.model_format,
                metadata={"error": str(e)},
            )

    async def _generate_tryon(
        self,
        item: ClothingItem,
        model_3d: Model3DResult | None,
    ) -> list[TryOnResult]:
        """
        Generate virtual try-on images for a clothing item.

        Uses the reference image if available, or the 3D model thumbnail.

        Args:
            item: ClothingItem to generate try-ons for
            model_3d: 3D model result (for thumbnail fallback)

        Returns:
            List of TryOnResult for each model type
        """
        logger.info(f"Generating try-on images for {item.name}")

        # Determine garment image to use
        garment_image_url = item.reference_image_url
        garment_image_path = item.reference_image_path

        # Fall back to 3D model thumbnail if no reference image
        if not garment_image_url and not garment_image_path:
            if model_3d and model_3d.thumbnail_url:
                garment_image_url = model_3d.thumbnail_url
            else:
                logger.warning(f"No image available for try-on: {item.item_id}")
                return []

        try:
            # Determine category for FASHN
            category_map = {
                "hoodie": "tops",
                "t_shirt": "tops",
                "jacket": "tops",
                "sweater": "tops",
                "tank_top": "tops",
                "coat": "tops",
                "pants": "bottoms",
                "shorts": "bottoms",
                "skirt": "bottoms",
                "dress": "one-pieces",
            }
            category = category_map.get(item.category.value, "tops")

            if garment_image_url:
                results = await self.fashn.batch_tryon(
                    garment_image_url=garment_image_url,
                    model_types=self.tryon_models,
                    category=category,
                )
            else:
                # Process each model type with local image
                results = []
                for model_type in self.tryon_models:
                    result = await self.fashn.virtual_tryon(
                        garment_image_path=garment_image_path,
                        model_type=model_type,
                        category=category,
                    )
                    results.append(result)

            return results

        except FASHNError as e:
            record_error(
                error_type="TryOnGenerationError",
                message=f"Try-on generation failed for {item.item_id}: {e}",
                severity="MEDIUM",
                component="agent.modules.clothing.pipeline",
                context={"item_id": item.item_id},
                exception=e,
                action="continue",
            )

            return []

    async def _upload_assets(
        self,
        item: ClothingItem,
        result: PipelineResult,
    ) -> list[WordPressUploadResult]:
        """
        Upload generated assets to WordPress.

        Uploads 3D model and try-on images to WooCommerce media library.

        Args:
            item: ClothingItem metadata for titles/descriptions
            result: PipelineResult with generated assets

        Returns:
            List of WordPressUploadResult for each upload
        """
        logger.info(f"Uploading assets for {item.name}")

        uploads: list[WordPressUploadResult] = []
        upload_tasks: list[dict[str, Any]] = []

        # Prepare 3D model upload
        if result.model_3d and result.model_3d.local_path:
            upload_tasks.append({
                "path": result.model_3d.local_path,
                "title": f"{item.name} - 3D Model",
                "alt_text": f"3D model of {item.name} from SkyyRose {item.collection.value.replace('_', ' ').title()} collection",
                "description": item.description,
            })

        # Prepare try-on image uploads
        for tryon in result.try_on_results:
            if tryon.status == "completed" and tryon.local_path:
                upload_tasks.append({
                    "path": tryon.local_path,
                    "title": f"{item.name} - Virtual Try-On ({tryon.model_type.value.title()})",
                    "alt_text": f"Virtual try-on of {item.name} on {tryon.model_type.value} model",
                })

        if not upload_tasks:
            logger.warning(f"No assets to upload for {item.item_id}")
            return []

        try:
            uploads = await self.wordpress.batch_upload(
                files=upload_tasks,
                max_concurrent=3,
            )
            return uploads

        except WordPressError as e:
            record_error(
                error_type="WordPressUploadError",
                message=f"Upload failed for {item.item_id}: {e}",
                severity="MEDIUM",
                component="agent.modules.clothing.pipeline",
                context={"item_id": item.item_id},
                exception=e,
                action="continue",
            )
            return []

    async def process_batch(
        self,
        request: BatchPipelineRequest,
    ) -> BatchPipelineResult:
        """
        Process multiple clothing items in a batch.

        Processes items in parallel for efficiency, respecting
        the max_concurrent limit.

        Args:
            request: BatchPipelineRequest with items and options

        Returns:
            BatchPipelineResult with all item results

        Example:
            request = BatchPipelineRequest(
                items=[item1, item2, item3],
                generate_3d=True,
                generate_tryon=True,
                upload_to_wordpress=True,
                max_concurrent=5
            )
            result = await pipeline.process_batch(request)
            print(f"Processed {result.successful}/{result.total_items} items")
        """
        await self._ensure_initialized()

        start_time = time.time()
        batch_id = str(uuid.uuid4())[:8]

        logger.info(f"Starting batch {batch_id} with {len(request.items)} items")

        batch_result = BatchPipelineResult(
            batch_id=batch_id,
            total_items=len(request.items),
            started_at=datetime.now(),
        )

        # Configure pipeline settings from request
        self.enable_3d = request.generate_3d
        self.enable_tryon = request.generate_tryon
        self.enable_upload = request.upload_to_wordpress
        self.tryon_models = request.tryon_models
        self.model_format = request.model_format

        if request.parallel_processing:
            # Process in parallel with semaphore
            semaphore = asyncio.Semaphore(request.max_concurrent)

            async def process_with_limit(item: ClothingItem) -> PipelineResult:
                async with semaphore:
                    return await self.process_item(item)

            results = await asyncio.gather(
                *[process_with_limit(item) for item in request.items],
                return_exceptions=True,
            )
        else:
            # Process sequentially
            results = []
            for item in request.items:
                try:
                    result = await self.process_item(item)
                    results.append(result)
                except Exception as e:
                    results.append(e)

        # Aggregate results
        for result in results:
            if isinstance(result, Exception):
                batch_result.failed += 1
                batch_result.results.append(
                    PipelineResult(
                        item_id="error",
                        item_name="error",
                        stage=PipelineStage.FAILED,
                        errors=[str(result)],
                    )
                )
            elif isinstance(result, PipelineResult):
                batch_result.results.append(result)
                if result.success:
                    batch_result.successful += 1
                else:
                    batch_result.failed += 1

        batch_result.completed_at = datetime.now()
        batch_result.total_processing_time_seconds = time.time() - start_time

        logger.info(
            f"Batch {batch_id} completed: "
            f"{batch_result.successful}/{batch_result.total_items} successful "
            f"({batch_result.success_rate:.1f}%) in {batch_result.total_processing_time_seconds:.1f}s"
        )

        return batch_result

    async def __aenter__(self) -> "ClothingAssetPipeline":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
