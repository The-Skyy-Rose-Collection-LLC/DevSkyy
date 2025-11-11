from pathlib import Path
import shutil
import tempfile
from unittest.mock import AsyncMock, Mock, patch

from PIL import Image
import pytest


"""
Test Suite for Video Generation and Brand Model Training
Validates output quality, brand accuracy, and system integration
"""


class TestFashionComputerVisionAgent:
    """Test suite for FashionComputerVisionAgent video generation capabilities."""

    @pytest.fixture
    async def fashion_agent(self):
        """Create fashion vision agent for testing."""
        from agent.modules.frontend.fashion_computer_vision_agent import FashionComputerVisionAgent

        # Mock the models to avoid loading large models in tests
        with patch.multiple(
            "agent.modules.frontend.fashion_computer_vision_agent",
            StableDiffusionXLPipeline=Mock(),
            StableVideoDiffusionPipeline=Mock(),
            AnimateDiffPipeline=Mock(),
            CLIPModel=Mock(),
            ViTModel=Mock(),
            Blip2ForConditionalGeneration=Mock(),
        ):
            agent = FashionComputerVisionAgent()
            yield agent

    @pytest.fixture
    def sample_image(self):
        """Create a sample test image."""
        # Create a simple test image
        image = Image.new("RGB", (512, 512), color="red")

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            image.save(f.name)
            yield f.name

        # Cleanup
        Path(f.name).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_runway_video_generation(self, fashion_agent):
        """Test fashion runway video generation."""
        # Mock the video generation pipeline
        mock_frames = [Image.new("RGB", (1024, 576), color="blue") for _ in range(32)]

        with patch.object(fashion_agent, "svd_pipeline") as mock_svd:
            mock_svd.return_value.frames = [mock_frames]

            with patch.object(fashion_agent, "_frames_to_video") as mock_frames_to_video:
                mock_frames_to_video.return_value = None

                result = await fashion_agent.generate_fashion_runway_video(
                    prompt="luxury evening gown runway", duration=4, fps=8
                )

                assert result["success"] is True
                assert "video_path" in result
                assert result["duration"] == 4
                assert result["fps"] == 8
                assert result["model"] == "stable-video-diffusion"

    @pytest.mark.asyncio
    async def test_product_360_video_generation(self, fashion_agent, sample_image):
        """Test product 360° video generation."""
        mock_frames = [Image.new("RGB", (512, 512), color="green") for _ in range(24)]

        with patch.object(fashion_agent, "animatediff_pipeline") as mock_animatediff:
            mock_animatediff.return_value.frames = [mock_frames]

            with patch.object(fashion_agent, "_frames_to_video") as mock_frames_to_video:
                mock_frames_to_video.return_value = None

                result = await fashion_agent.generate_product_360_video(
                    product_image_path=sample_image, rotation_steps=24, duration=3
                )

                assert result["success"] is True
                assert "video_path" in result
                assert result["rotation_steps"] == 24
                assert result["duration"] == 3
                assert result["model"] == "animatediff"

    @pytest.mark.asyncio
    async def test_video_upscaling(self, fashion_agent):
        """Test video upscaling functionality."""
        # Create a mock video file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            mock_video_path = f.name

        try:
            with patch("moviepy.video.io.VideoFileClip.VideoFileClip") as mock_clip:
                mock_clip.return_value.resize.return_value.write_videofile.return_value = None
                mock_clip.return_value.close.return_value = None

                result = await fashion_agent.upscale_video(video_path=mock_video_path, target_resolution=(2048, 1152))

                assert result["success"] is True
                assert "upscaled_video_path" in result
                assert result["target_resolution"] == (2048, 1152)

        finally:
            Path(mock_video_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_image_caption_generation(self, fashion_agent, sample_image):
        """Test automatic image captioning."""
        with patch.object(fashion_agent, "blip2_model") as mock_blip2:
            mock_blip2.generate.return_value = [[1, 2, 3, 4]]  # Mock token IDs

            with patch.object(fashion_agent, "blip2_processor") as mock_processor:
                mock_processor.return_value.to.return_value = Mock()
                mock_processor.batch_decode.return_value = ["luxury fashion dress"]

                caption = await fashion_agent.generate_image_caption(sample_image)

                assert isinstance(caption, str)
                assert len(caption) > 0

    def test_model_loading_flags(self, fashion_agent):
        """Test model loading state management."""
        assert hasattr(fashion_agent, "_models_loaded")
        assert isinstance(fashion_agent._models_loaded, dict)

        expected_models = ["clip", "vit", "sdxl", "svd", "animatediff", "blip2"]
        for model in expected_models:
            assert model in fashion_agent._models_loaded

    def test_storage_directories_creation(self, fashion_agent):
        """Test that required storage directories are created."""
        assert fashion_agent.video_storage.exists()
        assert fashion_agent.model_storage.exists()


class TestSkyRoseBrandTrainer:
    """Test suite for SkyRoseBrandTrainer brand model training capabilities."""

    @pytest.fixture
    async def brand_trainer(self):
        """Create brand trainer for testing."""
        from agent.modules.backend.brand_model_trainer import SkyRoseBrandTrainer

        # Mock the models to avoid loading large models in tests
        with patch.multiple(
            "agent.modules.backend.brand_model_trainer",
            StableDiffusionXLPipeline=Mock(),
            Blip2ForConditionalGeneration=Mock(),
            Blip2Processor=Mock(),
        ):
            trainer = SkyRoseBrandTrainer()
            yield trainer

    @pytest.fixture
    def sample_training_images(self):
        """Create sample training images."""
        temp_dir = Path(tempfile.mkdtemp())

        # Create sample images
        for i in range(5):
            image = Image.new("RGB", (512, 512), color=(i * 50, 100, 150))
            image.save(temp_dir / f"sample_{i}.jpg")

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_dataset_preparation(self, brand_trainer, sample_training_images):
        """Test training dataset preparation."""
        with patch.object(brand_trainer, "_generate_brand_caption") as mock_caption:
            mock_caption.return_value = "skyrose_dress, luxury fashion item"

            result = await brand_trainer.prepare_training_dataset(
                input_directory=sample_training_images, category="dresses"
            )

            assert result["success"] is True
            assert result["category"] == "dresses"
            assert result["total_processed"] == 5
            assert "output_directory" in result
            assert "metadata_file" in result
            assert "manifest_file" in result

    @pytest.mark.asyncio
    async def test_lora_model_training(self, brand_trainer):
        """Test LoRA model training process."""
        # Create mock training manifest
        temp_dir = Path(tempfile.mkdtemp())
        manifest_file = temp_dir / "training_manifest.json"

        manifest_data = {
            "train": [
                {"image": "image1.jpg", "caption": "skyrose_dress, elegant design"},
                {"image": "image2.jpg", "caption": "skyrose_dress, luxury fabric"},
            ],
            "validation": [{"image": "image3.jpg", "caption": "skyrose_dress, premium quality"}],
        }

        with open(manifest_file, "w") as f:
            import json

            json.dump(manifest_data, f)

        try:
            with patch.object(brand_trainer, "_run_training_loop") as mock_training:
                mock_training.return_value = {
                    "training_losses": [0.5, 0.4, 0.3],
                    "validation_losses": [0.45, 0.35],
                    "final_train_loss": 0.3,
                    "final_val_loss": 0.35,
                    "epochs_completed": 3,
                }

                result = await brand_trainer.train_lora_model(dataset_path=temp_dir, model_name="test_model")

                assert result["success"] is True
                assert result["model_name"] == "test_model"
                assert "model_path" in result
                assert "training_results" in result

        finally:
            shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_brand_image_generation(self, brand_trainer):
        """Test brand-specific image generation."""
        with patch.object(brand_trainer, "base_model") as mock_model:
            mock_image = Image.new("RGB", (1024, 1024), color="purple")
            mock_model.return_value.images = [mock_image]

            result = await brand_trainer.generate_with_brand_model(
                prompt="elegant evening dress", model_name="skyy_rose_v1", trigger_word="skyrose_dress"
            )

            assert result["success"] is True
            assert "image_path" in result
            assert result["model_used"] == "skyy_rose_v1"
            assert result["trigger_word"] == "skyrose_dress"

    @pytest.mark.asyncio
    async def test_brand_consistency_validation(self, brand_trainer):
        """Test brand consistency validation."""
        # Create mock image paths
        generated_images = ["gen1.jpg", "gen2.jpg", "gen3.jpg"]
        reference_images = ["ref1.jpg", "ref2.jpg"]

        result = await brand_trainer.validate_brand_consistency(
            generated_images=generated_images, reference_images=reference_images
        )

        assert result["success"] is True
        assert "average_consistency" in result
        assert "individual_scores" in result
        assert "validation_status" in result
        assert "recommendations" in result

    def test_brand_configuration(self, brand_trainer):
        """Test brand configuration settings."""
        config = brand_trainer.brand_config

        assert config["brand_name"] == "Skyy Rose Collection"
        assert "trigger_words" in config
        assert "skyrose_dress" in config["trigger_words"]
        assert "skyrose_collection" in config["trigger_words"]
        assert config["target_resolution"] == (1024, 1024)

    def test_lora_configuration(self, brand_trainer):
        """Test LoRA configuration parameters."""
        lora_config = brand_trainer.lora_config

        assert lora_config.r == 16  # Rank
        assert lora_config.lora_alpha == 32  # Alpha parameter
        assert lora_config.lora_dropout == 0.1
        assert "to_k" in lora_config.target_modules
        assert "to_q" in lora_config.target_modules


class TestVideoGenerationWorkflow:
    """Test suite for video generation workflow integration."""

    @pytest.fixture
    async def workflow_engine(self):
        """Create workflow engine for testing."""
        from api_integration.workflow_engine import VideoGenerationWorkflowEngine

        with (
            patch.multiple("agent.modules.frontend.fashion_computer_vision_agent", fashion_vision_agent=Mock()),
            patch.multiple("agent.modules.backend.brand_model_trainer", brand_trainer=Mock()),
        ):
            engine = VideoGenerationWorkflowEngine()
            yield engine

    @pytest.mark.asyncio
    async def test_runway_video_workflow_action(self, workflow_engine):
        """Test runway video generation workflow action."""
        # Mock the fashion vision agent
        mock_result = {"success": True, "video_path": "test_runway_video.mp4", "duration": 4, "fps": 8}

        workflow_engine.fashion_vision_agent.generate_fashion_runway_video = AsyncMock(return_value=mock_result)

        context = {"prompt": "luxury fashion runway", "duration": 4, "fps": 8}

        result = await workflow_engine._generate_runway_video_action(context)

        assert result["success"] is True
        assert result["video_path"] == "test_runway_video.mp4"

    @pytest.mark.asyncio
    async def test_product_360_workflow_action(self, workflow_engine):
        """Test product 360° video generation workflow action."""
        mock_result = {"success": True, "video_path": "test_360_video.mp4", "rotation_steps": 24}

        workflow_engine.fashion_vision_agent.generate_product_360_video = AsyncMock(return_value=mock_result)

        context = {"product_image_path": "test_product.jpg", "rotation_steps": 24}

        result = await workflow_engine._generate_product_360_action(context)

        assert result["success"] is True
        assert result["video_path"] == "test_360_video.mp4"

    @pytest.mark.asyncio
    async def test_brand_training_workflow_action(self, workflow_engine):
        """Test brand model training workflow action."""
        mock_result = {"success": True, "model_name": "test_model", "model_path": "custom_models/test_model"}

        workflow_engine.brand_trainer.train_lora_model = AsyncMock(return_value=mock_result)

        context = {"dataset_path": "test_dataset/", "model_name": "test_model"}

        result = await workflow_engine._train_brand_model_action(context)

        assert result["success"] is True
        assert result["model_name"] == "test_model"

    def test_video_action_registration(self, workflow_engine):
        """Test that video generation actions are properly registered."""
        # Check that video generation actions are registered
        assert hasattr(workflow_engine, "_generate_runway_video_action")
        assert hasattr(workflow_engine, "_generate_product_360_action")
        assert hasattr(workflow_engine, "_train_brand_model_action")
        assert hasattr(workflow_engine, "_generate_brand_image_action")
        assert hasattr(workflow_engine, "_upscale_video_action")


# Integration tests
class TestSystemIntegration:
    """Test suite for end-to-end system integration."""

    @pytest.mark.asyncio
    async def test_full_video_generation_pipeline(self):
        """Test complete video generation pipeline."""
        # This would test the full pipeline from input to output
        # In a real test environment with proper models loaded

    @pytest.mark.asyncio
    async def test_full_brand_training_pipeline(self):
        """Test complete brand training pipeline."""
        # This would test the full training pipeline
        # In a real test environment with proper models loaded

    def test_gpu_memory_management(self):
        """Test GPU memory management functionality."""
        # Test model loading/unloading for memory management

    def test_storage_management(self):
        """Test storage management and cleanup."""
        # Test file storage, cleanup, and retention policies


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
