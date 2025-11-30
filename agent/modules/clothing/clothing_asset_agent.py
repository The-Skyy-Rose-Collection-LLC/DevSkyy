"""
Clothing Asset Agent for DevSkyy

Enterprise-grade AI agent for 3D clothing asset automation.
Integrates with SkyyRose luxury streetwear brand operations.

Features:
- 3D model generation via Tripo3D
- Virtual try-on via FASHN
- WordPress/WooCommerce upload
- Self-healing and error recovery
- ML-powered anomaly detection
- Performance monitoring

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

import logging
from typing import Any

from agent.modules.base_agent import BaseAgent
from agent.modules.clothing.schemas.schemas import (
    BatchPipelineRequest,
    BatchPipelineResult,
    ClothingCategory,
    ClothingCollection,
    ClothingItem,
    Model3DFormat,
    PipelineResult,
    TryOnModel,
)
from agent.modules.clothing.pipeline import ClothingAssetPipeline
from core.enterprise_error_handler import record_error

logger = logging.getLogger(__name__)


class ClothingAssetAgent(BaseAgent):
    """
    AI Agent for 3D clothing asset automation.

    This agent extends BaseAgent to provide:
    - Self-healing capabilities for API failures
    - ML-powered anomaly detection on processing times
    - Performance metrics collection
    - Circuit breaker protection

    The agent orchestrates the full pipeline:
    1. 3D Model Generation (Tripo3D)
    2. Virtual Try-On (FASHN)
    3. WordPress/WooCommerce Upload

    Example:
        agent = ClothingAssetAgent()
        await agent.initialize()

        result = await agent.process_clothing_item(
            item_id="hoodie-001",
            name="Black Rose Hoodie",
            description="Luxury black hoodie with embroidered rose pattern",
            collection="black_rose",
            category="hoodie",
            color="black",
            price=149.99,
            sku="SR-BR-H001"
        )

        print(f"Success: {result['success']}")
        print(f"3D Model URL: {result['model_3d_url']}")

    Attributes:
        pipeline: ClothingAssetPipeline for orchestration
        default_format: Default 3D model format
        default_tryon_models: Default try-on model types
    """

    def __init__(
        self,
        agent_name: str = "ClothingAssetAgent",
        version: str = "1.0.0",
        enable_3d: bool = True,
        enable_tryon: bool = True,
        enable_upload: bool = True,
        default_format: Model3DFormat = Model3DFormat.GLB,
        tryon_models: list[TryOnModel] | None = None,
    ):
        """
        Initialize the Clothing Asset Agent.

        Args:
            agent_name: Name for this agent instance
            version: Agent version
            enable_3d: Enable 3D model generation by default
            enable_tryon: Enable virtual try-on by default
            enable_upload: Enable WordPress upload by default
            default_format: Default 3D model output format
            tryon_models: Default model types for virtual try-on
        """
        super().__init__(agent_name=agent_name, version=version)

        self.enable_3d = enable_3d
        self.enable_tryon = enable_tryon
        self.enable_upload = enable_upload
        self.default_format = default_format
        self.default_tryon_models = tryon_models or [TryOnModel.FEMALE, TryOnModel.MALE]

        self.pipeline: ClothingAssetPipeline | None = None

    async def initialize(self) -> bool:
        """
        Initialize the agent and its pipeline.

        Sets up the ClothingAssetPipeline with all required clients.
        Verifies API access and prepares for processing.

        Returns:
            True if initialization successful
        """
        logger.info(f"Initializing {self.agent_name} v{self.version}")

        try:
            self.pipeline = ClothingAssetPipeline(
                enable_3d=self.enable_3d,
                enable_tryon=self.enable_tryon,
                enable_upload=self.enable_upload,
                model_format=self.default_format,
                tryon_models=self.default_tryon_models,
            )

            await self.pipeline.initialize()

            self.status = self.status.__class__.HEALTHY
            logger.info(f"{self.agent_name} initialized successfully")
            return True

        except Exception as e:
            self.status = self.status.__class__.FAILED
            record_error(
                error_type="AgentInitializationError",
                message=f"Failed to initialize {self.agent_name}: {e}",
                severity="HIGH",
                component="agent.modules.clothing.clothing_asset_agent",
                exception=e,
                action="continue",
            )
            raise

    async def execute_core_function(self, **kwargs: Any) -> dict[str, Any]:
        """
        Execute the core agent function.

        This is the main entry point for agent operations.
        Supports single item processing and batch processing.

        Args:
            **kwargs: Operation parameters including:
                - operation: "process_item" or "process_batch"
                - item: ClothingItem dict for single processing
                - items: List of ClothingItem dicts for batch
                - Additional processing options

        Returns:
            dict with operation results

        Example:
            result = await agent.execute_core_function(
                operation="process_item",
                item={
                    "item_id": "hoodie-001",
                    "name": "Black Rose Hoodie",
                    "description": "Luxury hoodie",
                    "collection": "black_rose",
                    "category": "hoodie",
                    "color": "black",
                    "price": 149.99,
                    "sku": "SR-BR-H001"
                }
            )
        """
        operation = kwargs.get("operation", "process_item")

        if operation == "process_item":
            return await self._execute_process_item(kwargs)
        elif operation == "process_batch":
            return await self._execute_process_batch(kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}",
                "available_operations": ["process_item", "process_batch"],
            }

    async def _execute_process_item(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Execute single item processing."""
        item_data = kwargs.get("item", {})

        if not item_data:
            return {"success": False, "error": "No item data provided"}

        # Create ClothingItem from dict
        try:
            item = ClothingItem(
                item_id=item_data.get("item_id", ""),
                name=item_data.get("name", ""),
                description=item_data.get("description", ""),
                collection=ClothingCollection(item_data.get("collection", "signature")),
                category=ClothingCategory(item_data.get("category", "t_shirt")),
                color=item_data.get("color", "black"),
                reference_image_url=item_data.get("reference_image_url"),
                reference_image_path=item_data.get("reference_image_path"),
                price=item_data.get("price", 0.0),
                sku=item_data.get("sku", ""),
                tags=item_data.get("tags", []),
            )
        except Exception as e:
            return {"success": False, "error": f"Invalid item data: {e}"}

        result = await self.process_clothing_item_obj(
            item=item,
            generate_3d=kwargs.get("generate_3d"),
            generate_tryon=kwargs.get("generate_tryon"),
            upload=kwargs.get("upload"),
        )

        return self._pipeline_result_to_dict(result)

    async def _execute_process_batch(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Execute batch processing."""
        items_data = kwargs.get("items", [])

        if not items_data:
            return {"success": False, "error": "No items provided"}

        # Create ClothingItems from dicts
        items = []
        for item_data in items_data:
            try:
                item = ClothingItem(
                    item_id=item_data.get("item_id", ""),
                    name=item_data.get("name", ""),
                    description=item_data.get("description", ""),
                    collection=ClothingCollection(item_data.get("collection", "signature")),
                    category=ClothingCategory(item_data.get("category", "t_shirt")),
                    color=item_data.get("color", "black"),
                    reference_image_url=item_data.get("reference_image_url"),
                    reference_image_path=item_data.get("reference_image_path"),
                    price=item_data.get("price", 0.0),
                    sku=item_data.get("sku", ""),
                    tags=item_data.get("tags", []),
                )
                items.append(item)
            except Exception as e:
                logger.warning(f"Skipping invalid item: {e}")

        if not items:
            return {"success": False, "error": "No valid items to process"}

        # Create batch request
        request = BatchPipelineRequest(
            items=items,
            generate_3d=kwargs.get("generate_3d", True),
            generate_tryon=kwargs.get("generate_tryon", True),
            upload_to_wordpress=kwargs.get("upload", True),
            tryon_models=kwargs.get("tryon_models", self.default_tryon_models),
            model_format=kwargs.get("model_format", self.default_format),
            parallel_processing=kwargs.get("parallel", True),
            max_concurrent=kwargs.get("max_concurrent", 5),
        )

        result = await self.process_batch(request)
        return self._batch_result_to_dict(result)

    @property
    def _wrapped_process_item(self):
        """Get wrapped process item method with self-healing."""
        return self.with_healing(self._process_item_internal)

    async def process_clothing_item(
        self,
        item_id: str,
        name: str,
        description: str,
        collection: str,
        category: str,
        color: str,
        price: float,
        sku: str,
        reference_image_url: str | None = None,
        reference_image_path: str | None = None,
        tags: list[str] | None = None,
        generate_3d: bool | None = None,
        generate_tryon: bool | None = None,
        upload: bool | None = None,
    ) -> dict[str, Any]:
        """
        Process a single clothing item through the pipeline.

        Convenient method that accepts individual parameters instead of
        a ClothingItem object.

        Args:
            item_id: Unique item identifier
            name: Product name
            description: Product description for 3D generation
            collection: SkyyRose collection (black_rose, love_hurts, signature)
            category: Clothing category (hoodie, t_shirt, etc.)
            color: Primary color
            price: Price in USD
            sku: Stock Keeping Unit
            reference_image_url: URL to reference image (optional)
            reference_image_path: Local path to reference image (optional)
            tags: Product tags (optional)
            generate_3d: Override 3D generation setting
            generate_tryon: Override try-on setting
            upload: Override upload setting

        Returns:
            dict with processing results

        Example:
            result = await agent.process_clothing_item(
                item_id="hoodie-001",
                name="Black Rose Hoodie",
                description="Luxury black hoodie with embroidered rose pattern",
                collection="black_rose",
                category="hoodie",
                color="black",
                price=149.99,
                sku="SR-BR-H001"
            )
        """
        item = ClothingItem(
            item_id=item_id,
            name=name,
            description=description,
            collection=ClothingCollection(collection),
            category=ClothingCategory(category),
            color=color,
            price=price,
            sku=sku,
            reference_image_url=reference_image_url,
            reference_image_path=reference_image_path,
            tags=tags or [],
        )

        result = await self.process_clothing_item_obj(
            item=item,
            generate_3d=generate_3d,
            generate_tryon=generate_tryon,
            upload=upload,
        )

        return self._pipeline_result_to_dict(result)

    async def process_clothing_item_obj(
        self,
        item: ClothingItem,
        generate_3d: bool | None = None,
        generate_tryon: bool | None = None,
        upload: bool | None = None,
    ) -> PipelineResult:
        """
        Process a ClothingItem object through the pipeline.

        Args:
            item: ClothingItem to process
            generate_3d: Override 3D generation setting
            generate_tryon: Override try-on setting
            upload: Override upload setting

        Returns:
            PipelineResult with all generated assets
        """
        if not self.pipeline:
            await self.initialize()

        # Use self-healing wrapper
        wrapped = self.with_healing(self._process_item_internal)
        return await wrapped(item, generate_3d, generate_tryon, upload)

    async def _process_item_internal(
        self,
        item: ClothingItem,
        generate_3d: bool | None,
        generate_tryon: bool | None,
        upload: bool | None,
    ) -> PipelineResult:
        """Internal processing method wrapped with self-healing."""
        return await self.pipeline.process_item(
            item=item,
            generate_3d=generate_3d,
            generate_tryon=generate_tryon,
            upload=upload,
        )

    async def process_batch(self, request: BatchPipelineRequest) -> BatchPipelineResult:
        """
        Process a batch of clothing items.

        Args:
            request: BatchPipelineRequest with items and options

        Returns:
            BatchPipelineResult with all item results
        """
        if not self.pipeline:
            await self.initialize()

        return await self.pipeline.process_batch(request)

    def _pipeline_result_to_dict(self, result: PipelineResult) -> dict[str, Any]:
        """Convert PipelineResult to dict for API response."""
        return {
            "success": result.success,
            "item_id": result.item_id,
            "item_name": result.item_name,
            "stage": result.stage.value,
            "model_3d": {
                "task_id": result.model_3d.task_id if result.model_3d else None,
                "status": result.model_3d.status if result.model_3d else None,
                "model_url": result.model_3d.model_url if result.model_3d else None,
                "local_path": result.model_3d.local_path if result.model_3d else None,
                "thumbnail_url": result.model_3d.thumbnail_url if result.model_3d else None,
                "generation_time_seconds": result.model_3d.generation_time_seconds if result.model_3d else None,
            } if result.model_3d else None,
            "try_on_results": [
                {
                    "task_id": tryon.task_id,
                    "status": tryon.status,
                    "image_url": tryon.image_url,
                    "local_path": tryon.local_path,
                    "model_type": tryon.model_type.value,
                    "processing_time_seconds": tryon.processing_time_seconds,
                }
                for tryon in result.try_on_results
            ],
            "wordpress_uploads": [
                {
                    "media_id": upload.media_id,
                    "source_url": upload.source_url,
                    "title": upload.title,
                    "mime_type": upload.mime_type,
                }
                for upload in result.wordpress_uploads
            ],
            "errors": result.errors,
            "total_processing_time_seconds": result.total_processing_time_seconds,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
        }

    def _batch_result_to_dict(self, result: BatchPipelineResult) -> dict[str, Any]:
        """Convert BatchPipelineResult to dict for API response."""
        return {
            "success": result.failed == 0,
            "batch_id": result.batch_id,
            "total_items": result.total_items,
            "successful": result.successful,
            "failed": result.failed,
            "success_rate": result.success_rate,
            "results": [
                self._pipeline_result_to_dict(r) for r in result.results
            ],
            "total_processing_time_seconds": result.total_processing_time_seconds,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown the agent and its pipeline."""
        logger.info(f"Shutting down {self.agent_name}")

        if self.pipeline:
            await self.pipeline.close()
            self.pipeline = None

        await super().shutdown()
