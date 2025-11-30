"""
Tests for Clothing Asset Pipeline

Tests the orchestration pipeline that coordinates
3D generation, virtual try-on, and WordPress upload.

Truth Protocol Rule #8: Test coverage ≥90%
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.modules.clothing.clients.fashn_client import FASHNClient
from agent.modules.clothing.clients.tripo3d_client import Tripo3DClient
from agent.modules.clothing.clients.wordpress_media import WordPressMediaClient
from agent.modules.clothing.schemas.schemas import (
    BatchPipelineRequest,
    ClothingCategory,
    ClothingCollection,
    ClothingItem,
    Model3DFormat,
    Model3DResult,
    PipelineStage,
    TryOnModel,
    TryOnResult,
    WordPressUploadResult,
)
from agent.modules.clothing.pipeline import ClothingAssetPipeline


@pytest.fixture
def sample_item() -> ClothingItem:
    """Create a sample clothing item for testing."""
    return ClothingItem(
        item_id="hoodie-001",
        name="Black Rose Hoodie",
        description="Luxury black hoodie with embroidered rose pattern, premium cotton blend",
        collection=ClothingCollection.BLACK_ROSE,
        category=ClothingCategory.HOODIE,
        color="black",
        price=149.99,
        sku="SR-BR-H001",
        reference_image_url="https://skyyrose.co/images/hoodie.png",
    )


@pytest.fixture
def mock_tripo_client() -> MagicMock:
    """Create a mock Tripo3D client."""
    client = MagicMock(spec=Tripo3DClient)
    client.initialize = AsyncMock(return_value=True)
    client.close = AsyncMock()
    client.text_to_3d = AsyncMock(
        return_value=Model3DResult(
            task_id="task_123",
            status="success",
            model_url="https://api.tripo3d.ai/models/123.glb",
            model_format=Model3DFormat.GLB,
            local_path="/tmp/model.glb",
            thumbnail_url="https://api.tripo3d.ai/thumb/123.png",
            generation_time_seconds=45.0,
        )
    )
    client.image_to_3d = AsyncMock(
        return_value=Model3DResult(
            task_id="task_img_123",
            status="success",
            model_url="https://api.tripo3d.ai/models/img123.glb",
            model_format=Model3DFormat.GLB,
            local_path="/tmp/model_img.glb",
            generation_time_seconds=40.0,
        )
    )
    return client


@pytest.fixture
def mock_fashn_client() -> MagicMock:
    """Create a mock FASHN client."""
    client = MagicMock(spec=FASHNClient)
    client.initialize = AsyncMock(return_value=True)
    client.close = AsyncMock()
    client.batch_tryon = AsyncMock(
        return_value=[
            TryOnResult(
                task_id="tryon_f",
                status="completed",
                image_url="https://api.fashn.ai/results/f.png",
                local_path="/tmp/tryon_f.png",
                model_type=TryOnModel.FEMALE,
                processing_time_seconds=12.0,
            ),
            TryOnResult(
                task_id="tryon_m",
                status="completed",
                image_url="https://api.fashn.ai/results/m.png",
                local_path="/tmp/tryon_m.png",
                model_type=TryOnModel.MALE,
                processing_time_seconds=11.0,
            ),
        ]
    )
    return client


@pytest.fixture
def mock_wordpress_client() -> MagicMock:
    """Create a mock WordPress client."""
    client = MagicMock(spec=WordPressMediaClient)
    client.initialize = AsyncMock(return_value=True)
    client.close = AsyncMock()
    client.batch_upload = AsyncMock(
        return_value=[
            WordPressUploadResult(
                media_id=12345,
                source_url="https://skyyrose.co/uploads/model.glb",
                mime_type="model/gltf-binary",
                title="Black Rose Hoodie 3D Model",
            ),
            WordPressUploadResult(
                media_id=12346,
                source_url="https://skyyrose.co/uploads/tryon_f.png",
                mime_type="image/png",
                title="Try-On Female",
            ),
        ]
    )
    return client


class TestClothingAssetPipeline:
    """Tests for ClothingAssetPipeline."""

    @pytest.mark.asyncio
    async def test_initialize(
        self,
        mock_tripo_client: MagicMock,
        mock_fashn_client: MagicMock,
        mock_wordpress_client: MagicMock,
    ) -> None:
        """Test pipeline initialization."""
        pipeline = ClothingAssetPipeline(
            tripo3d_client=mock_tripo_client,
            fashn_client=mock_fashn_client,
            wordpress_client=mock_wordpress_client,
        )

        result = await pipeline.initialize()

        assert result is True
        assert pipeline._initialized is True
        mock_tripo_client.initialize.assert_called_once()
        mock_fashn_client.initialize.assert_called_once()
        mock_wordpress_client.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_item_full_pipeline(
        self,
        sample_item: ClothingItem,
        mock_tripo_client: MagicMock,
        mock_fashn_client: MagicMock,
        mock_wordpress_client: MagicMock,
    ) -> None:
        """Test full pipeline processing."""
        pipeline = ClothingAssetPipeline(
            tripo3d_client=mock_tripo_client,
            fashn_client=mock_fashn_client,
            wordpress_client=mock_wordpress_client,
        )
        await pipeline.initialize()

        result = await pipeline.process_item(sample_item)

        assert result.item_id == "hoodie-001"
        assert result.stage == PipelineStage.COMPLETED
        assert result.success is True
        assert result.has_3d_model is True
        assert result.try_on_count == 2
        assert result.upload_count == 2

    @pytest.mark.asyncio
    async def test_process_item_3d_only(
        self,
        sample_item: ClothingItem,
        mock_tripo_client: MagicMock,
        mock_fashn_client: MagicMock,
        mock_wordpress_client: MagicMock,
    ) -> None:
        """Test pipeline with only 3D generation."""
        pipeline = ClothingAssetPipeline(
            tripo3d_client=mock_tripo_client,
            fashn_client=mock_fashn_client,
            wordpress_client=mock_wordpress_client,
            enable_3d=True,
            enable_tryon=False,
            enable_upload=False,
        )
        await pipeline.initialize()

        result = await pipeline.process_item(sample_item)

        assert result.has_3d_model is True
        assert result.try_on_count == 0
        assert result.upload_count == 0
        mock_fashn_client.batch_tryon.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_item_with_reference_image(
        self,
        mock_tripo_client: MagicMock,
        mock_fashn_client: MagicMock,
        mock_wordpress_client: MagicMock,
    ) -> None:
        """Test pipeline uses image-to-3D when reference image provided."""
        item = ClothingItem(
            item_id="tee-001",
            name="Test Tee",
            description="Test description for the t-shirt",
            collection=ClothingCollection.SIGNATURE,
            category=ClothingCategory.T_SHIRT,
            color="white",
            price=50.0,
            sku="TEST-001",
            reference_image_url="https://example.com/ref.png",
        )

        pipeline = ClothingAssetPipeline(
            tripo3d_client=mock_tripo_client,
            fashn_client=mock_fashn_client,
            wordpress_client=mock_wordpress_client,
            enable_tryon=False,
            enable_upload=False,
        )
        await pipeline.initialize()

        await pipeline.process_item(item)

        mock_tripo_client.image_to_3d.assert_called_once()
        mock_tripo_client.text_to_3d.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_item_text_to_3d(
        self,
        mock_tripo_client: MagicMock,
        mock_fashn_client: MagicMock,
        mock_wordpress_client: MagicMock,
    ) -> None:
        """Test pipeline uses text-to-3D when no reference image."""
        item = ClothingItem(
            item_id="tee-002",
            name="Test Tee",
            description="Test description for the t-shirt",
            collection=ClothingCollection.SIGNATURE,
            category=ClothingCategory.T_SHIRT,
            color="black",
            price=50.0,
            sku="TEST-002",
        )

        pipeline = ClothingAssetPipeline(
            tripo3d_client=mock_tripo_client,
            fashn_client=mock_fashn_client,
            wordpress_client=mock_wordpress_client,
            enable_tryon=False,
            enable_upload=False,
        )
        await pipeline.initialize()

        await pipeline.process_item(item)

        mock_tripo_client.text_to_3d.assert_called_once()
        mock_tripo_client.image_to_3d.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_item_3d_failure(
        self,
        sample_item: ClothingItem,
        mock_tripo_client: MagicMock,
        mock_fashn_client: MagicMock,
        mock_wordpress_client: MagicMock,
    ) -> None:
        """Test pipeline handles 3D generation failure."""
        mock_tripo_client.image_to_3d.return_value = Model3DResult(
            task_id="task_fail",
            status="failed",
            model_format=Model3DFormat.GLB,
            metadata={"error": "Generation timeout"},
        )

        pipeline = ClothingAssetPipeline(
            tripo3d_client=mock_tripo_client,
            fashn_client=mock_fashn_client,
            wordpress_client=mock_wordpress_client,
        )
        await pipeline.initialize()

        result = await pipeline.process_item(sample_item)

        assert result.has_3d_model is False
        assert len(result.errors) > 0
        assert "3D generation failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_process_batch(
        self,
        mock_tripo_client: MagicMock,
        mock_fashn_client: MagicMock,
        mock_wordpress_client: MagicMock,
    ) -> None:
        """Test batch processing."""
        items = [
            ClothingItem(
                item_id=f"item-{i}",
                name=f"Test Item {i}",
                description="Test description for batch processing",
                collection=ClothingCollection.SIGNATURE,
                category=ClothingCategory.T_SHIRT,
                color="black",
                price=50.0,
                sku=f"TEST-{i:03d}",
            )
            for i in range(3)
        ]

        request = BatchPipelineRequest(
            items=items,
            generate_3d=True,
            generate_tryon=True,
            upload_to_wordpress=True,
            max_concurrent=2,
        )

        pipeline = ClothingAssetPipeline(
            tripo3d_client=mock_tripo_client,
            fashn_client=mock_fashn_client,
            wordpress_client=mock_wordpress_client,
        )
        await pipeline.initialize()

        result = await pipeline.process_batch(request)

        assert result.total_items == 3
        assert result.successful == 3
        assert result.failed == 0
        assert result.success_rate == 100.0

    @pytest.mark.asyncio
    async def test_process_batch_partial_failure(
        self,
        mock_tripo_client: MagicMock,
        mock_fashn_client: MagicMock,
        mock_wordpress_client: MagicMock,
    ) -> None:
        """Test batch processing with partial failure."""
        # Make second call fail
        mock_tripo_client.text_to_3d.side_effect = [
            Model3DResult(
                task_id="task_1",
                status="success",
                model_format=Model3DFormat.GLB,
                local_path="/tmp/model1.glb",
            ),
            Model3DResult(
                task_id="task_2",
                status="failed",
                model_format=Model3DFormat.GLB,
                metadata={"error": "Failed"},
            ),
        ]

        items = [
            ClothingItem(
                item_id=f"item-{i}",
                name=f"Test Item {i}",
                description="Test description for batch processing",
                collection=ClothingCollection.SIGNATURE,
                category=ClothingCategory.T_SHIRT,
                color="black",
                price=50.0,
                sku=f"TEST-{i:03d}",
            )
            for i in range(2)
        ]

        request = BatchPipelineRequest(
            items=items,
            generate_3d=True,
            generate_tryon=False,
            upload_to_wordpress=False,
            parallel_processing=False,
        )

        pipeline = ClothingAssetPipeline(
            tripo3d_client=mock_tripo_client,
            fashn_client=mock_fashn_client,
            wordpress_client=mock_wordpress_client,
        )
        await pipeline.initialize()

        result = await pipeline.process_batch(request)

        assert result.total_items == 2
        assert result.successful >= 1  # At least one succeeded

    @pytest.mark.asyncio
    async def test_context_manager(
        self,
        mock_tripo_client: MagicMock,
        mock_fashn_client: MagicMock,
        mock_wordpress_client: MagicMock,
    ) -> None:
        """Test pipeline as async context manager."""
        async with ClothingAssetPipeline(
            tripo3d_client=mock_tripo_client,
            fashn_client=mock_fashn_client,
            wordpress_client=mock_wordpress_client,
        ) as pipeline:
            assert pipeline._initialized is True

        mock_tripo_client.close.assert_called_once()
        mock_fashn_client.close.assert_called_once()
        mock_wordpress_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(
        self,
        mock_tripo_client: MagicMock,
        mock_fashn_client: MagicMock,
        mock_wordpress_client: MagicMock,
    ) -> None:
        """Test pipeline close."""
        pipeline = ClothingAssetPipeline(
            tripo3d_client=mock_tripo_client,
            fashn_client=mock_fashn_client,
            wordpress_client=mock_wordpress_client,
        )
        await pipeline.initialize()
        await pipeline.close()

        assert pipeline._initialized is False
        mock_tripo_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_category_mapping(
        self,
        mock_tripo_client: MagicMock,
        mock_fashn_client: MagicMock,
        mock_wordpress_client: MagicMock,
    ) -> None:
        """Test clothing category to FASHN category mapping."""
        # Test different categories
        for category, expected_fashn in [
            (ClothingCategory.HOODIE, "tops"),
            (ClothingCategory.T_SHIRT, "tops"),
            (ClothingCategory.PANTS, "bottoms"),
            (ClothingCategory.DRESS, "one-pieces"),
        ]:
            item = ClothingItem(
                item_id="test-cat",
                name="Test",
                description="Test description for category testing",
                collection=ClothingCollection.SIGNATURE,
                category=category,
                color="black",
                price=50.0,
                sku="TEST-CAT",
                reference_image_url="https://example.com/img.png",
            )

            pipeline = ClothingAssetPipeline(
                tripo3d_client=mock_tripo_client,
                fashn_client=mock_fashn_client,
                wordpress_client=mock_wordpress_client,
                enable_3d=False,
                enable_upload=False,
            )
            await pipeline.initialize()

            await pipeline.process_item(item)

            # Verify category mapping in call
            call_args = mock_fashn_client.batch_tryon.call_args
            assert call_args is not None
            assert call_args.kwargs.get("category") == expected_fashn

            mock_fashn_client.reset_mock()
