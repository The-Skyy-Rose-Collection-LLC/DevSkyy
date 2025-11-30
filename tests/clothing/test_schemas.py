"""
Tests for Clothing Asset Pydantic Schemas

Tests validation, serialization, and computed properties
for all data models used in the clothing automation pipeline.

Truth Protocol Rule #8: Test coverage ≥90%
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from agent.modules.clothing.schemas.schemas import (
    BatchPipelineRequest,
    BatchPipelineResult,
    ClothingCategory,
    ClothingCollection,
    ClothingItem,
    Model3DFormat,
    Model3DResult,
    PipelineResult,
    PipelineStage,
    TryOnModel,
    TryOnResult,
    WordPressUploadResult,
)


class TestClothingItem:
    """Tests for ClothingItem schema."""

    def test_valid_clothing_item(self) -> None:
        """Test creating a valid clothing item."""
        item = ClothingItem(
            item_id="hoodie-001",
            name="Black Rose Hoodie",
            description="Luxury black hoodie with embroidered rose pattern, premium cotton blend",
            collection=ClothingCollection.BLACK_ROSE,
            category=ClothingCategory.HOODIE,
            color="black",
            price=149.99,
            sku="SR-BR-H001",
        )

        assert item.item_id == "hoodie-001"
        assert item.name == "Black Rose Hoodie"
        assert item.collection == ClothingCollection.BLACK_ROSE
        assert item.category == ClothingCategory.HOODIE
        assert item.price == 149.99

    def test_clothing_item_with_reference_image(self) -> None:
        """Test clothing item with reference image URL."""
        item = ClothingItem(
            item_id="tee-001",
            name="Love Hurts Tee",
            description="Premium cotton t-shirt with emotional expression design",
            collection=ClothingCollection.LOVE_HURTS,
            category=ClothingCategory.T_SHIRT,
            color="white",
            price=79.99,
            sku="SR-LH-T001",
            reference_image_url="https://skyyrose.co/images/tee.png",
        )

        assert item.reference_image_url == "https://skyyrose.co/images/tee.png"

    def test_invalid_reference_url(self) -> None:
        """Test that invalid URLs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ClothingItem(
                item_id="tee-001",
                name="Test Tee",
                description="Test description for validation",
                collection=ClothingCollection.SIGNATURE,
                category=ClothingCategory.T_SHIRT,
                color="black",
                price=50.0,
                sku="TEST-001",
                reference_image_url="not-a-valid-url",
            )

        assert "reference_image_url" in str(exc_info.value)

    def test_invalid_price(self) -> None:
        """Test that non-positive prices are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ClothingItem(
                item_id="test-001",
                name="Test Item",
                description="Test description for validation",
                collection=ClothingCollection.SIGNATURE,
                category=ClothingCategory.T_SHIRT,
                color="black",
                price=-10.0,
                sku="TEST-001",
            )

        assert "price" in str(exc_info.value).lower()

    def test_prompt_for_3d_black_rose(self) -> None:
        """Test 3D prompt generation for BLACK_ROSE collection."""
        item = ClothingItem(
            item_id="hoodie-001",
            name="Black Rose Hoodie",
            description="Embroidered rose pattern on chest",
            collection=ClothingCollection.BLACK_ROSE,
            category=ClothingCategory.HOODIE,
            color="black",
            price=149.99,
            sku="SR-BR-H001",
        )

        prompt = item.prompt_for_3d

        assert "black" in prompt.lower()
        assert "hoodie" in prompt.lower()
        assert "dark elegant" in prompt.lower()
        assert "rose" in prompt.lower()

    def test_prompt_for_3d_love_hurts(self) -> None:
        """Test 3D prompt generation for LOVE_HURTS collection."""
        item = ClothingItem(
            item_id="tee-001",
            name="Heartbreak Tee",
            description="Heart design with artistic elements",
            collection=ClothingCollection.LOVE_HURTS,
            category=ClothingCategory.T_SHIRT,
            color="red",
            price=79.99,
            sku="SR-LH-T001",
        )

        prompt = item.prompt_for_3d

        assert "emotional" in prompt.lower()
        assert "heart" in prompt.lower()

    def test_clothing_item_tags(self) -> None:
        """Test clothing item with tags."""
        item = ClothingItem(
            item_id="hoodie-001",
            name="Black Rose Hoodie",
            description="Luxury hoodie with detailed description",
            collection=ClothingCollection.BLACK_ROSE,
            category=ClothingCategory.HOODIE,
            color="black",
            price=149.99,
            sku="SR-BR-H001",
            tags=["luxury", "streetwear", "limited-edition"],
        )

        assert len(item.tags) == 3
        assert "luxury" in item.tags


class TestModel3DResult:
    """Tests for Model3DResult schema."""

    def test_successful_model_result(self) -> None:
        """Test successful 3D model result."""
        result = Model3DResult(
            task_id="task_abc123",
            status="success",
            model_url="https://api.tripo3d.ai/models/abc123.glb",
            model_format=Model3DFormat.GLB,
            local_path="/tmp/models/abc123.glb",
            thumbnail_url="https://api.tripo3d.ai/thumbnails/abc123.png",
            generation_time_seconds=45.5,
        )

        assert result.task_id == "task_abc123"
        assert result.status == "success"
        assert result.model_format == Model3DFormat.GLB
        assert result.generation_time_seconds == 45.5

    def test_failed_model_result(self) -> None:
        """Test failed 3D model result."""
        result = Model3DResult(
            task_id="task_failed",
            status="failed",
            model_format=Model3DFormat.GLB,
            metadata={"error": "Generation timeout"},
        )

        assert result.status == "failed"
        assert result.model_url is None
        assert "error" in result.metadata


class TestTryOnResult:
    """Tests for TryOnResult schema."""

    def test_completed_tryon_result(self) -> None:
        """Test completed try-on result."""
        result = TryOnResult(
            task_id="tryon_xyz789",
            status="completed",
            image_url="https://api.fashn.ai/results/xyz789.png",
            local_path="/tmp/tryon/xyz789.png",
            model_type=TryOnModel.FEMALE,
            processing_time_seconds=12.3,
        )

        assert result.task_id == "tryon_xyz789"
        assert result.status == "completed"
        assert result.model_type == TryOnModel.FEMALE
        assert result.resolution == (576, 864)

    def test_tryon_default_resolution(self) -> None:
        """Test try-on default resolution."""
        result = TryOnResult(
            task_id="tryon_test",
            status="processing",
        )

        assert result.resolution == (576, 864)


class TestWordPressUploadResult:
    """Tests for WordPressUploadResult schema."""

    def test_successful_upload_result(self) -> None:
        """Test successful WordPress upload result."""
        result = WordPressUploadResult(
            media_id=12345,
            source_url="https://skyyrose.co/wp-content/uploads/2025/01/hoodie.glb",
            mime_type="model/gltf-binary",
            title="Black Rose Hoodie 3D Model",
            alt_text="3D model of SkyyRose Black Rose Hoodie",
            file_size_bytes=2048000,
        )

        assert result.media_id == 12345
        assert result.mime_type == "model/gltf-binary"
        assert result.file_size_bytes == 2048000


class TestPipelineResult:
    """Tests for PipelineResult schema."""

    def test_successful_pipeline_result(self) -> None:
        """Test successful pipeline result."""
        model_3d = Model3DResult(
            task_id="task_123",
            status="success",
            model_format=Model3DFormat.GLB,
        )

        tryon = TryOnResult(
            task_id="tryon_456",
            status="completed",
            model_type=TryOnModel.FEMALE,
        )

        result = PipelineResult(
            item_id="hoodie-001",
            item_name="Black Rose Hoodie",
            stage=PipelineStage.COMPLETED,
            success=True,
            model_3d=model_3d,
            try_on_results=[tryon],
            total_processing_time_seconds=120.5,
        )

        assert result.success is True
        assert result.has_3d_model is True
        assert result.try_on_count == 1

    def test_pipeline_result_computed_properties(self) -> None:
        """Test PipelineResult computed properties."""
        result = PipelineResult(
            item_id="test-001",
            item_name="Test Item",
            stage=PipelineStage.FAILED,
            success=False,
            errors=["3D generation failed", "Try-on failed"],
        )

        assert result.has_3d_model is False
        assert result.try_on_count == 0
        assert result.upload_count == 0
        assert len(result.errors) == 2


class TestBatchPipelineRequest:
    """Tests for BatchPipelineRequest schema."""

    def test_valid_batch_request(self) -> None:
        """Test valid batch request."""
        items = [
            ClothingItem(
                item_id=f"item-{i}",
                name=f"Test Item {i}",
                description="Test description for validation",
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
            max_concurrent=5,
        )

        assert len(request.items) == 3
        assert request.generate_3d is True
        assert request.max_concurrent == 5

    def test_batch_request_tryon_models(self) -> None:
        """Test batch request with custom try-on models."""
        item = ClothingItem(
            item_id="item-001",
            name="Test Item",
            description="Test description for validation",
            collection=ClothingCollection.SIGNATURE,
            category=ClothingCategory.T_SHIRT,
            color="black",
            price=50.0,
            sku="TEST-001",
        )

        request = BatchPipelineRequest(
            items=[item],
            tryon_models=[TryOnModel.FEMALE, TryOnModel.MALE, TryOnModel.UNISEX],
        )

        assert len(request.tryon_models) == 3
        assert TryOnModel.UNISEX in request.tryon_models

    def test_batch_request_max_items_validation(self) -> None:
        """Test batch request max items validation."""
        # Create 101 items (should fail with max 100)
        items = [
            ClothingItem(
                item_id=f"item-{i}",
                name=f"Test Item {i}",
                description="Test description for validation",
                collection=ClothingCollection.SIGNATURE,
                category=ClothingCategory.T_SHIRT,
                color="black",
                price=50.0,
                sku=f"TEST-{i:03d}",
            )
            for i in range(101)
        ]

        with pytest.raises(ValidationError):
            BatchPipelineRequest(items=items)


class TestBatchPipelineResult:
    """Tests for BatchPipelineResult schema."""

    def test_batch_result_success_rate(self) -> None:
        """Test batch result success rate calculation."""
        result = BatchPipelineResult(
            batch_id="batch_abc",
            total_items=10,
            successful=8,
            failed=2,
        )

        assert result.success_rate == 80.0

    def test_batch_result_zero_items(self) -> None:
        """Test batch result with zero items."""
        result = BatchPipelineResult(
            batch_id="batch_empty",
            total_items=0,
        )

        assert result.success_rate == 0.0


class TestEnums:
    """Tests for enum values."""

    def test_clothing_collections(self) -> None:
        """Test all clothing collections are defined."""
        assert ClothingCollection.BLACK_ROSE.value == "black_rose"
        assert ClothingCollection.LOVE_HURTS.value == "love_hurts"
        assert ClothingCollection.SIGNATURE.value == "signature"

    def test_clothing_categories(self) -> None:
        """Test all clothing categories are defined."""
        categories = [
            ClothingCategory.HOODIE,
            ClothingCategory.T_SHIRT,
            ClothingCategory.JACKET,
            ClothingCategory.PANTS,
            ClothingCategory.SHORTS,
            ClothingCategory.DRESS,
            ClothingCategory.SKIRT,
            ClothingCategory.SWEATER,
            ClothingCategory.TANK_TOP,
            ClothingCategory.COAT,
        ]
        assert len(categories) == 10

    def test_model_formats(self) -> None:
        """Test all 3D model formats are defined."""
        assert Model3DFormat.GLB.value == "glb"
        assert Model3DFormat.FBX.value == "fbx"
        assert Model3DFormat.OBJ.value == "obj"
        assert Model3DFormat.USDZ.value == "usdz"

    def test_tryon_models(self) -> None:
        """Test all try-on model types are defined."""
        assert TryOnModel.FEMALE.value == "female"
        assert TryOnModel.MALE.value == "male"
        assert TryOnModel.UNISEX.value == "unisex"

    def test_pipeline_stages(self) -> None:
        """Test all pipeline stages are defined."""
        stages = [
            PipelineStage.PENDING,
            PipelineStage.GENERATING_3D,
            PipelineStage.VIRTUAL_TRYON,
            PipelineStage.UPLOADING,
            PipelineStage.COMPLETED,
            PipelineStage.FAILED,
        ]
        assert len(stages) == 6
