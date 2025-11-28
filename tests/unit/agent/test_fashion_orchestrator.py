"""
Unit Tests for Fashion Orchestrator

Tests the FashionOrchestrator class including AI model selection,
task creation, workflow execution, and fashion-specific operations.

Truth Protocol Compliance:
- Rule #8: Test Coverage ≥90%
- Rule #9: Document All (Google-style docstrings)
- Rule #10: No-Skip Rule (all errors logged and handled)
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, mock_open, patch

import pytest

from agent.fashion_orchestrator import (
    AIModelConfig,
    AIModelProvider,
    Asset3D,
    AvatarModel,
    FashionAssetType,
    FashionOrchestrator,
    ProductDescription,
)
from agent.unified_orchestrator import ExecutionPriority, Task, TaskStatus


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_fashion_config():
    """Provide mock fashion configuration data."""
    return {
        "version": "3.0.0-fashion",
        "metadata": {
            "name": "DevSkyy Fashion MCP Configuration",
            "brand": "The Skyy Rose Collection LLC",
        },
        "ai_model_selection": {
            "models": {
                "product_description": {
                    "primary": {
                        "provider": "anthropic",
                        "model": "claude-3-5-sonnet-20241022",
                        "reason": "Superior creative writing",
                        "verified_source": "https://www.anthropic.com/claude",
                        "features": ["creative_writing", "brand_voice"],
                    },
                    "fallback": {
                        "provider": "openai",
                        "model": "gpt-4-turbo-preview",
                        "reason": "Alternative for high-quality content",
                    },
                },
                "3d_generation": {
                    "primary": {
                        "provider": "openai",
                        "model": "shap-e",
                        "reason": "3D object generation from text/images",
                        "verified_source": "https://github.com/openai/shap-e",
                    },
                    "alternative": {
                        "provider": "meshy",
                        "model": "meshy-3",
                        "reason": "Text-to-3D for fashion assets",
                        "verified_source": "https://www.meshy.ai/",
                    },
                },
                "avatar_generation": {
                    "primary": {
                        "provider": "readyplayerme",
                        "model": "rpm-avatar-creator",
                        "reason": "Customizable 3D avatars",
                        "verified_source": "https://docs.readyplayer.me/",
                        "features": ["full_body", "rigged"],
                    },
                },
                "virtual_try_on": {
                    "primary": {
                        "provider": "huggingface",
                        "model": "yisol/IDM-VTON",
                        "reason": "State-of-the-art virtual try-on",
                        "verified_source": "https://huggingface.co/yisol/IDM-VTON",
                    },
                },
            },
            "selection_rules": {
                "product_description": {
                    "preferred_models": ["claude-3-5-sonnet-20241022", "gpt-4-turbo-preview"],
                },
                "3d_generation": {
                    "preferred_models": ["shap-e", "meshy-3"],
                },
            },
        },
        "brand_configuration": {
            "brand_name": "The Skyy Rose Collection",
            "product_categories": ["handbags", "shoes", "jewelry"],
            "brand_identity": {
                "brand_voice": {
                    "keywords": ["luxury", "elegant", "timeless"],
                    "avoid": ["cheap", "basic"],
                },
                "color_palette": {
                    "primary": ["#000000", "#C0A080", "#8B7355"],
                },
            },
        },
        "verifiable_sources": {
            "ai_models": {
                "claude": {
                    "official_site": "https://www.anthropic.com/claude",
                    "documentation": "https://docs.anthropic.com/",
                },
            },
        },
    }


@pytest.fixture
def mock_config_file(mock_fashion_config, tmp_path):
    """Create a temporary config file."""
    config_path = tmp_path / "fashion_config.json"
    config_path.write_text(json.dumps(mock_fashion_config))
    return str(config_path)


# =============================================================================
# Enum Tests
# =============================================================================


class TestFashionAssetType:
    """Tests for FashionAssetType enum."""

    def test_asset_type_values(self):
        """Test FashionAssetType enum values are correct."""
        # Arrange & Act & Assert
        assert FashionAssetType.HANDBAG.value == "handbag"
        assert FashionAssetType.SHOES.value == "shoes"
        assert FashionAssetType.JEWELRY.value == "jewelry"
        assert FashionAssetType.ACCESSORY.value == "accessory"
        assert FashionAssetType.GARMENT.value == "garment"
        assert FashionAssetType.DRESS.value == "dress"
        assert FashionAssetType.OUTERWEAR.value == "outerwear"

    def test_asset_type_count(self):
        """Test that FashionAssetType has expected number of values."""
        # Arrange & Act
        asset_types = list(FashionAssetType)

        # Assert
        assert len(asset_types) == 7


class TestAIModelProvider:
    """Tests for AIModelProvider enum."""

    def test_provider_values(self):
        """Test AIModelProvider enum values are correct."""
        # Arrange & Act & Assert
        assert AIModelProvider.ANTHROPIC.value == "anthropic"
        assert AIModelProvider.OPENAI.value == "openai"
        assert AIModelProvider.STABILITY.value == "stability"
        assert AIModelProvider.REPLICATE.value == "replicate"
        assert AIModelProvider.HUGGINGFACE.value == "huggingface"
        assert AIModelProvider.READY_PLAYER_ME.value == "readyplayerme"
        assert AIModelProvider.MESHCAPADE.value == "meshcapade"
        assert AIModelProvider.CLO3D.value == "clo3d"
        assert AIModelProvider.MESHY.value == "meshy"

    def test_provider_count(self):
        """Test that AIModelProvider has expected number of values."""
        # Arrange & Act
        providers = list(AIModelProvider)

        # Assert
        assert len(providers) == 9


# =============================================================================
# Dataclass Tests
# =============================================================================


class TestAIModelConfig:
    """Tests for AIModelConfig dataclass."""

    def test_create_ai_model_config(self):
        """Test creating an AI model configuration."""
        # Arrange & Act
        config = AIModelConfig(
            provider=AIModelProvider.ANTHROPIC,
            model_name="claude-3-5-sonnet-20241022",
            reason="Superior creative writing",
            verified_source="https://www.anthropic.com/claude",
            capabilities=["creative_writing"],
            features=["brand_voice"],
            cost_per_request=0.015,
        )

        # Assert
        assert config.provider == AIModelProvider.ANTHROPIC
        assert config.model_name == "claude-3-5-sonnet-20241022"
        assert config.reason == "Superior creative writing"
        assert config.verified_source == "https://www.anthropic.com/claude"
        assert config.capabilities == ["creative_writing"]
        assert config.features == ["brand_voice"]
        assert config.cost_per_request == 0.015

    def test_ai_model_config_defaults(self):
        """Test AI model configuration default values."""
        # Arrange & Act
        config = AIModelConfig(
            provider=AIModelProvider.OPENAI,
            model_name="gpt-4",
            reason="Test model",
            verified_source="https://openai.com",
        )

        # Assert
        assert config.capabilities == []
        assert config.features == []
        assert config.cost_per_request is None


class TestProductDescription:
    """Tests for ProductDescription dataclass."""

    def test_create_product_description(self):
        """Test creating a product description."""
        # Arrange & Act
        desc = ProductDescription(
            title="Luxury Handbag",
            short_description="Elegant Italian leather handbag",
            long_description="Crafted from the finest Italian leather...",
            features_list=["Italian leather", "Gold hardware"],
            care_instructions="Wipe with soft cloth",
            styling_suggestions=["Pair with evening wear"],
            seo_keywords=["luxury", "handbag", "italian leather"],
            brand_story_integration="The Skyy Rose Collection tradition...",
        )

        # Assert
        assert desc.title == "Luxury Handbag"
        assert desc.short_description == "Elegant Italian leather handbag"
        assert len(desc.features_list) == 2
        assert "luxury" in desc.seo_keywords


class TestAsset3D:
    """Tests for Asset3D dataclass."""

    def test_create_3d_asset(self):
        """Test creating a 3D asset."""
        # Arrange & Act
        asset = Asset3D(
            model_url="https://example.com/model.glb",
            format="glb",
            polycount=50000,
            texture_maps={"albedo": "texture_albedo.png", "normal": "texture_normal.png"},
            bounding_box={"min": [0, 0, 0], "max": [10, 10, 10]},
            file_size_mb=12.5,
        )

        # Assert
        assert asset.model_url == "https://example.com/model.glb"
        assert asset.format == "glb"
        assert asset.polycount == 50000
        assert "albedo" in asset.texture_maps
        assert asset.file_size_mb == 12.5


class TestAvatarModel:
    """Tests for AvatarModel dataclass."""

    def test_create_avatar_model(self):
        """Test creating an avatar model."""
        # Arrange & Act
        avatar = AvatarModel(
            avatar_url="https://example.com/avatar.glb",
            avatar_id="avatar_123",
            format="glb",
            rigged=True,
            bone_count=65,
            measurements={"height_cm": 175, "bust_cm": 86},
            texture_url="https://example.com/texture.png",
            lod_variants=["lod0", "lod1", "lod2"],
        )

        # Assert
        assert avatar.avatar_id == "avatar_123"
        assert avatar.rigged is True
        assert avatar.bone_count == 65
        assert len(avatar.lod_variants) == 3


# =============================================================================
# FashionOrchestrator Initialization Tests
# =============================================================================


class TestFashionOrchestratorInit:
    """Tests for FashionOrchestrator initialization."""

    @patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__")
    @patch("builtins.open", new_callable=mock_open)
    def test_init_with_valid_config(
        self, mock_file, mock_super_init, mock_fashion_config, mock_config_file
    ):
        """Test initialization with valid configuration."""
        # Arrange
        mock_file.return_value.read.return_value = json.dumps(mock_fashion_config)
        mock_super_init.return_value = None

        # Act
        with patch("json.load", return_value=mock_fashion_config):
            orchestrator = FashionOrchestrator(
                config_path=mock_config_file, max_concurrent_tasks=50
            )

        # Assert
        assert orchestrator.fashion_config == mock_fashion_config
        assert orchestrator.brand_config == mock_fashion_config["brand_configuration"]
        assert len(orchestrator.ai_models) > 0
        mock_super_init.assert_called_once()

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_init_with_missing_config(self, mock_file):
        """Test initialization with missing configuration file."""
        # Arrange & Act & Assert
        with pytest.raises(FileNotFoundError):
            FashionOrchestrator(config_path="/nonexistent/config.json")

    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    @patch("json.load", side_effect=json.JSONDecodeError("error", "doc", 0))
    def test_init_with_invalid_json(self, mock_json, mock_file):
        """Test initialization with invalid JSON configuration."""
        # Arrange & Act & Assert
        with pytest.raises(json.JSONDecodeError):
            FashionOrchestrator(config_path="/path/to/config.json")


# =============================================================================
# Configuration Loading Tests
# =============================================================================


class TestConfigurationLoading:
    """Tests for configuration loading methods."""

    @patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_fashion_config_success(
        self, mock_file, mock_super_init, mock_fashion_config, mock_config_file
    ):
        """Test successful fashion configuration loading."""
        # Arrange
        mock_super_init.return_value = None

        # Act
        with patch("json.load", return_value=mock_fashion_config):
            orchestrator = FashionOrchestrator(config_path=mock_config_file)

        # Assert
        assert orchestrator.fashion_config == mock_fashion_config
        assert orchestrator.brand_config["brand_name"] == "The Skyy Rose Collection"

    @patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__")
    @patch("builtins.open", new_callable=mock_open)
    def test_initialize_ai_models(
        self, mock_file, mock_super_init, mock_fashion_config, mock_config_file
    ):
        """Test AI model initialization from configuration."""
        # Arrange
        mock_super_init.return_value = None

        # Act
        with patch("json.load", return_value=mock_fashion_config):
            orchestrator = FashionOrchestrator(config_path=mock_config_file)

        # Assert
        assert "product_description_primary" in orchestrator.ai_models
        assert "3d_generation_primary" in orchestrator.ai_models
        assert orchestrator.ai_models["product_description_primary"].provider == AIModelProvider.ANTHROPIC

    @patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__")
    @patch("builtins.open", new_callable=mock_open)
    def test_initialize_ai_models_with_unknown_provider(
        self, mock_file, mock_super_init, mock_config_file
    ):
        """Test AI model initialization skips unknown providers."""
        # Arrange
        mock_super_init.return_value = None
        config_with_unknown = {
            "ai_model_selection": {
                "models": {
                    "test_task": {
                        "primary": {
                            "provider": "unknown_provider",
                            "model": "test-model",
                            "reason": "Testing",
                            "verified_source": "https://example.com",
                        }
                    }
                }
            },
            "brand_configuration": {},
        }

        # Act
        with patch("json.load", return_value=config_with_unknown):
            orchestrator = FashionOrchestrator(config_path=mock_config_file)

        # Assert
        assert "test_task_primary" not in orchestrator.ai_models


# =============================================================================
# AI Model Selection Tests
# =============================================================================


class TestAIModelSelection:
    """Tests for AI model selection logic."""

    @patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__")
    @patch("builtins.open", new_callable=mock_open)
    def test_select_primary_model(
        self, mock_file, mock_super_init, mock_fashion_config, mock_config_file
    ):
        """Test selecting primary AI model for a task."""
        # Arrange
        mock_super_init.return_value = None

        with patch("json.load", return_value=mock_fashion_config):
            orchestrator = FashionOrchestrator(config_path=mock_config_file)

        # Act
        model = orchestrator.select_ai_model("product_description")

        # Assert
        assert model is not None
        assert model.provider == AIModelProvider.ANTHROPIC
        assert model.model_name == "claude-3-5-sonnet-20241022"

    @patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__")
    @patch("builtins.open", new_callable=mock_open)
    def test_select_model_with_provider_preference(
        self, mock_file, mock_super_init, mock_fashion_config, mock_config_file
    ):
        """Test selecting AI model with provider preference."""
        # Arrange
        mock_super_init.return_value = None

        with patch("json.load", return_value=mock_fashion_config):
            orchestrator = FashionOrchestrator(config_path=mock_config_file)

        # Act
        model = orchestrator.select_ai_model(
            "product_description", prefer_provider=AIModelProvider.ANTHROPIC
        )

        # Assert
        assert model is not None
        assert model.provider == AIModelProvider.ANTHROPIC

    @patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__")
    @patch("builtins.open", new_callable=mock_open)
    def test_select_alternative_model(
        self, mock_file, mock_super_init, mock_fashion_config, mock_config_file
    ):
        """Test selecting alternative AI model when primary doesn't match preference."""
        # Arrange
        mock_super_init.return_value = None

        with patch("json.load", return_value=mock_fashion_config):
            orchestrator = FashionOrchestrator(config_path=mock_config_file)

        # Act
        model = orchestrator.select_ai_model("3d_generation")

        # Assert
        assert model is not None
        assert model.provider in [AIModelProvider.OPENAI, AIModelProvider.MESHY]

    @patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__")
    @patch("builtins.open", new_callable=mock_open)
    def test_select_model_not_found(
        self, mock_file, mock_super_init, mock_fashion_config, mock_config_file
    ):
        """Test selecting AI model returns None when not found."""
        # Arrange
        mock_super_init.return_value = None

        with patch("json.load", return_value=mock_fashion_config):
            orchestrator = FashionOrchestrator(config_path=mock_config_file)

        # Act
        model = orchestrator.select_ai_model("nonexistent_task")

        # Assert
        assert model is None


# =============================================================================
# Task Creation Tests
# =============================================================================


class TestTaskCreation:
    """Tests for fashion-specific task creation methods."""

    @pytest.fixture
    def orchestrator(self, mock_fashion_config, mock_config_file):
        """Create a FashionOrchestrator instance for testing."""
        with patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__", return_value=None):
            with patch("builtins.open", new_callable=mock_open):
                with patch("json.load", return_value=mock_fashion_config):
                    orch = FashionOrchestrator(config_path=mock_config_file)
                    return orch

    @pytest.mark.asyncio
    async def test_create_product_description_task(self, orchestrator):
        """Test creating a product description task."""
        # Arrange
        orchestrator.create_task = AsyncMock(
            return_value=Task(
                name="Generate product description: Test Product",
                tool_name="product_description_writer",
                task_type="product_description",
                priority=ExecutionPriority.HIGH,
            )
        )

        # Act
        task = await orchestrator.create_product_description_task(
            product_name="Test Product",
            product_type="handbag",
            materials=["leather"],
            colors=["black"],
            price_point="luxury",
            unique_features=["detachable strap"],
            tone="elegant",
            length="medium",
        )

        # Assert
        assert task is not None
        assert task.name == "Generate product description: Test Product"
        assert task.tool_name == "product_description_writer"
        assert task.task_type == "product_description"
        assert task.priority == ExecutionPriority.HIGH
        orchestrator.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_product_description_task_no_ai_model(self, orchestrator):
        """Test creating product description task fails when no AI model available."""
        # Arrange
        orchestrator.ai_models = {}

        # Act & Assert
        with pytest.raises(ValueError, match="No AI model available for product description"):
            await orchestrator.create_product_description_task(
                product_name="Test",
                product_type="handbag",
                materials=["leather"],
                colors=["black"],
            )

    @pytest.mark.asyncio
    async def test_create_3d_asset_task(self, orchestrator):
        """Test creating a 3D asset generation task."""
        # Arrange
        orchestrator.create_task = AsyncMock(
            return_value=Task(
                name=f"Generate 3D asset: {FashionAssetType.HANDBAG.value}",
                tool_name="3d_fashion_asset_generator",
                task_type="3d_asset_creation",
                priority=ExecutionPriority.MEDIUM,
            )
        )

        # Act
        task = await orchestrator.create_3d_asset_task(
            asset_type=FashionAssetType.HANDBAG,
            style_reference="Luxury designer handbag",
            dimensions={"width_cm": 30, "height_cm": 20},
            output_format="glb",
            polycount="high",
            texture_resolution=2048,
        )

        # Assert
        assert task is not None
        assert task.name == f"Generate 3D asset: {FashionAssetType.HANDBAG.value}"
        assert task.tool_name == "3d_fashion_asset_generator"
        assert task.priority == ExecutionPriority.MEDIUM

    @pytest.mark.asyncio
    async def test_create_3d_asset_task_no_ai_model(self, orchestrator):
        """Test creating 3D asset task fails when no AI model available."""
        # Arrange
        orchestrator.ai_models = {}

        # Act & Assert
        with pytest.raises(ValueError, match="No AI model available for 3D generation"):
            await orchestrator.create_3d_asset_task(
                asset_type=FashionAssetType.HANDBAG,
                style_reference="Test style",
            )

    @pytest.mark.asyncio
    async def test_create_avatar_task(self, orchestrator):
        """Test creating an avatar generation task."""
        # Arrange
        orchestrator.create_task = AsyncMock(
            return_value=Task(
                name="Generate avatar: female realistic",
                tool_name="avatar_creator",
                task_type="avatar_generation",
                priority=ExecutionPriority.MEDIUM,
            )
        )

        # Act
        task = await orchestrator.create_avatar_task(
            gender="female",
            body_measurements={"height_cm": 175, "bust_cm": 86},
            avatar_type="realistic",
            customization={"hair_color": "brown"},
            output_format="glb",
            rigging=True,
        )

        # Assert
        assert task is not None
        assert task.name == "Generate avatar: female realistic"
        assert task.tool_name == "avatar_creator"

    @pytest.mark.asyncio
    async def test_create_avatar_task_no_ai_model(self, orchestrator):
        """Test creating avatar task fails when no AI model available."""
        # Arrange
        orchestrator.ai_models = {}

        # Act & Assert
        with pytest.raises(ValueError, match="No AI model available for avatar generation"):
            await orchestrator.create_avatar_task(
                gender="female", body_measurements={"height_cm": 175}
            )

    @pytest.mark.asyncio
    async def test_create_virtual_try_on_task(self, orchestrator):
        """Test creating a virtual try-on task."""
        # Arrange
        orchestrator.create_task = AsyncMock(
            return_value=Task(
                name="Virtual try-on",
                tool_name="virtual_try_on",
                task_type="virtual_try_on",
                priority=ExecutionPriority.HIGH,
            )
        )

        # Act
        task = await orchestrator.create_virtual_try_on_task(
            person_image="https://example.com/person.jpg",
            garment_image="https://example.com/garment.jpg",
            garment_type="dress",
            resolution=1024,
        )

        # Assert
        assert task is not None
        assert task.name == "Virtual try-on"
        assert task.tool_name == "virtual_try_on"
        assert task.priority == ExecutionPriority.HIGH

    @pytest.mark.asyncio
    async def test_create_virtual_try_on_task_no_ai_model(self, orchestrator):
        """Test creating virtual try-on task fails when no AI model available."""
        # Arrange
        orchestrator.ai_models = {}

        # Act & Assert
        with pytest.raises(ValueError, match="No AI model available for virtual try-on"):
            await orchestrator.create_virtual_try_on_task(
                person_image="test.jpg", garment_image="garment.jpg", garment_type="dress"
            )

    @pytest.mark.asyncio
    async def test_create_3d_garment_simulation_task(self, orchestrator):
        """Test creating a 3D garment simulation task."""
        # Arrange
        orchestrator.create_task = AsyncMock(
            return_value=Task(
                name="3D garment simulation",
                tool_name="3d_garment_simulator",
                task_type="3d_simulation",
                priority=ExecutionPriority.MEDIUM,
            )
        )

        # Act
        task = await orchestrator.create_3d_garment_simulation_task(
            garment_3d_model="https://example.com/garment.glb",
            avatar_3d_model="https://example.com/avatar.glb",
            fabric_properties={"material_type": "silk", "weight_gsm": 100},
            animation={"enabled": True},
        )

        # Assert
        assert task is not None
        assert task.name == "3D garment simulation"
        assert task.tool_name == "3d_garment_simulator"

    @pytest.mark.asyncio
    async def test_create_3d_garment_simulation_task_with_defaults(self, orchestrator):
        """Test creating 3D garment simulation task uses default values."""
        # Arrange
        orchestrator.create_task = AsyncMock(return_value=Task())

        # Act
        task = await orchestrator.create_3d_garment_simulation_task(
            garment_3d_model="garment.glb",
            avatar_3d_model="avatar.glb",
        )

        # Assert
        call_args = orchestrator.create_task.call_args
        input_data = call_args.kwargs["input_data"]
        assert "fabric_properties" in input_data
        assert input_data["fabric_properties"]["material_type"] == "silk"
        assert input_data["simulation_quality"] == "preview"

    @pytest.mark.asyncio
    async def test_create_brand_fine_tuning_task(self, orchestrator):
        """Test creating a brand model fine-tuning task."""
        # Arrange
        orchestrator.create_task = AsyncMock(
            return_value=Task(
                name="Fine-tune text_generation model",
                tool_name="brand_fine_tuner",
                task_type="model_training",
                priority=ExecutionPriority.CRITICAL,
            )
        )

        # Act
        task = await orchestrator.create_brand_fine_tuning_task(
            model_type="text_generation",
            base_model="gpt-4",
            training_data_path="/data/training.jsonl",
            epochs=10,
            learning_rate=0.0001,
            lora_rank=16,
        )

        # Assert
        assert task is not None
        assert task.name == "Fine-tune text_generation model"
        assert task.priority == ExecutionPriority.CRITICAL
        call_args = orchestrator.create_task.call_args
        input_data = call_args.kwargs["input_data"]
        assert input_data["training_config"]["epochs"] == 10
        assert input_data["training_config"]["learning_rate"] == 0.0001


# =============================================================================
# Workflow Execution Tests
# =============================================================================


class TestWorkflowExecution:
    """Tests for high-level fashion workflow execution."""

    @pytest.fixture
    def orchestrator(self, mock_fashion_config, mock_config_file):
        """Create a FashionOrchestrator instance for testing."""
        with patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__", return_value=None):
            with patch("builtins.open", new_callable=mock_open):
                with patch("json.load", return_value=mock_fashion_config):
                    orch = FashionOrchestrator(config_path=mock_config_file)
                    return orch

    @pytest.mark.asyncio
    async def test_execute_complete_product_pipeline(self, orchestrator):
        """Test executing complete product pipeline workflow."""
        # Arrange
        orchestrator.execute_workflow = AsyncMock(
            return_value={
                "description": "Product description generated",
                "3d_asset": "Asset created",
                "avatar": "Avatar generated",
            }
        )
        product_details = {
            "name": "Luxury Handbag",
            "type": "handbag",
            "materials": ["leather"],
        }
        avatar_specs = {"gender": "female", "height_cm": 175}

        # Act
        result = await orchestrator.execute_complete_product_pipeline(
            product_details=product_details, avatar_specifications=avatar_specs
        )

        # Assert
        assert result is not None
        assert result["workflow"] == "complete_product_pipeline"
        assert "results" in result
        assert "timestamp" in result
        orchestrator.execute_workflow.assert_called_once_with(
            "complete_product_pipeline",
            {"product": product_details, "avatar": avatar_specs},
        )

    @pytest.mark.asyncio
    async def test_execute_virtual_try_on_workflow(self, orchestrator):
        """Test executing virtual try-on workflow."""
        # Arrange
        orchestrator.execute_workflow = AsyncMock(
            return_value={"try_on_image": "https://example.com/result.jpg"}
        )

        # Act
        result = await orchestrator.execute_virtual_try_on_workflow(
            customer_photo="customer.jpg",
            product_image="product.jpg",
            product_3d_model="model.glb",
        )

        # Assert
        assert result is not None
        assert result["workflow"] == "virtual_try_on_workflow"
        assert "results" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_execute_collection_launch(self, orchestrator):
        """Test executing collection launch pipeline."""
        # Arrange
        orchestrator.execute_workflow = AsyncMock(
            return_value={
                "models_fine_tuned": 2,
                "descriptions_generated": 10,
                "assets_created": 10,
            }
        )
        products = [
            {"name": "Product 1", "type": "handbag"},
            {"name": "Product 2", "type": "shoes"},
        ]
        models = [{"type": "text_generation", "base": "gpt-4"}]

        # Act
        result = await orchestrator.execute_collection_launch(
            collection_products=products,
            training_data_path="/data/training.jsonl",
            model_specifications=models,
        )

        # Assert
        assert result is not None
        assert result["workflow"] == "collection_launch_pipeline"
        assert result["collection_size"] == 2
        assert "results" in result
        assert "timestamp" in result


# =============================================================================
# Utility Method Tests
# =============================================================================


class TestUtilityMethods:
    """Tests for utility methods."""

    @pytest.fixture
    def orchestrator(self, mock_fashion_config, mock_config_file):
        """Create a FashionOrchestrator instance for testing."""
        with patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__", return_value=None):
            with patch("builtins.open", new_callable=mock_open):
                with patch("json.load", return_value=mock_fashion_config):
                    orch = FashionOrchestrator(config_path=mock_config_file)
                    return orch

    def test_get_brand_info(self, orchestrator):
        """Test retrieving brand configuration."""
        # Arrange & Act
        brand_info = orchestrator.get_brand_info()

        # Assert
        assert brand_info is not None
        assert brand_info["brand_name"] == "The Skyy Rose Collection"
        assert "product_categories" in brand_info

    def test_get_available_ai_models(self, orchestrator):
        """Test retrieving available AI models."""
        # Arrange & Act
        models = orchestrator.get_available_ai_models()

        # Assert
        assert models is not None
        assert isinstance(models, dict)
        assert len(models) > 0

    def test_get_verifiable_sources(self, orchestrator):
        """Test retrieving verifiable sources."""
        # Arrange & Act
        sources = orchestrator.get_verifiable_sources()

        # Assert
        assert sources is not None
        assert isinstance(sources, dict)


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def orchestrator(self, mock_fashion_config, mock_config_file):
        """Create a FashionOrchestrator instance for testing."""
        with patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__", return_value=None):
            with patch("builtins.open", new_callable=mock_open):
                with patch("json.load", return_value=mock_fashion_config):
                    orch = FashionOrchestrator(config_path=mock_config_file)
                    return orch

    @pytest.mark.asyncio
    async def test_create_task_with_empty_features(self, orchestrator):
        """Test creating task with empty unique features list."""
        # Arrange
        orchestrator.create_task = AsyncMock(return_value=Task())

        # Act
        task = await orchestrator.create_product_description_task(
            product_name="Test",
            product_type="handbag",
            materials=["leather"],
            colors=["black"],
            unique_features=None,
        )

        # Assert
        call_args = orchestrator.create_task.call_args
        assert call_args.kwargs["input_data"]["unique_features"] == []

    @pytest.mark.asyncio
    async def test_create_task_with_empty_dimensions(self, orchestrator):
        """Test creating 3D asset task with no dimensions."""
        # Arrange
        orchestrator.create_task = AsyncMock(return_value=Task())

        # Act
        task = await orchestrator.create_3d_asset_task(
            asset_type=FashionAssetType.SHOES,
            style_reference="Athletic shoes",
            dimensions=None,
        )

        # Assert
        call_args = orchestrator.create_task.call_args
        assert call_args.kwargs["input_data"]["dimensions"] == {}

    @pytest.mark.asyncio
    async def test_create_avatar_task_with_empty_customization(self, orchestrator):
        """Test creating avatar task with no customization."""
        # Arrange
        orchestrator.create_task = AsyncMock(return_value=Task())

        # Act
        task = await orchestrator.create_avatar_task(
            gender="male",
            body_measurements={"height_cm": 180},
            customization=None,
        )

        # Assert
        call_args = orchestrator.create_task.call_args
        assert call_args.kwargs["input_data"]["customization"] == {}

    def test_select_model_with_multiple_alternatives(self, orchestrator):
        """Test model selection tries alternatives in order."""
        # Arrange
        orchestrator.ai_models = {
            "test_task_fashion_specific": AIModelConfig(
                provider=AIModelProvider.MESHY,
                model_name="meshy-3",
                reason="Fashion specific",
                verified_source="https://meshy.ai",
            ),
            "test_task_alternative": AIModelConfig(
                provider=AIModelProvider.OPENAI,
                model_name="shap-e",
                reason="Alternative",
                verified_source="https://github.com/openai/shap-e",
            ),
        }

        # Act
        model = orchestrator.select_ai_model("test_task")

        # Assert
        assert model is not None
        # Should select fashion_specific first
        assert model.provider == AIModelProvider.MESHY

    def test_empty_brand_config(self):
        """Test orchestrator handles empty brand configuration."""
        # Arrange
        minimal_config = {
            "ai_model_selection": {"models": {}},
            "brand_configuration": {},
        }

        # Act
        with patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__", return_value=None):
            with patch("builtins.open", new_callable=mock_open):
                with patch("json.load", return_value=minimal_config):
                    orchestrator = FashionOrchestrator(config_path="/test/config.json")

        # Assert
        assert orchestrator.brand_config == {}
        assert orchestrator.get_brand_info() == {}


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for FashionOrchestrator."""

    @pytest.mark.asyncio
    @patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__")
    @patch("builtins.open", new_callable=mock_open)
    async def test_full_task_creation_flow(
        self, mock_file, mock_super_init, mock_fashion_config
    ):
        """Test full flow of creating multiple tasks."""
        # Arrange
        mock_super_init.return_value = None

        with patch("json.load", return_value=mock_fashion_config):
            orchestrator = FashionOrchestrator(config_path="/test/config.json")
            orchestrator.create_task = AsyncMock(return_value=Task())

        # Act - Create multiple tasks
        desc_task = await orchestrator.create_product_description_task(
            product_name="Test Handbag",
            product_type="handbag",
            materials=["leather"],
            colors=["black"],
        )

        asset_task = await orchestrator.create_3d_asset_task(
            asset_type=FashionAssetType.HANDBAG,
            style_reference="Luxury handbag",
        )

        avatar_task = await orchestrator.create_avatar_task(
            gender="female",
            body_measurements={"height_cm": 175},
        )

        # Assert
        assert orchestrator.create_task.call_count == 3
        assert all(task is not None for task in [desc_task, asset_task, avatar_task])

    def test_model_config_persistence(self, mock_fashion_config):
        """Test AI model configurations persist correctly."""
        # Arrange & Act
        with patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__", return_value=None):
            with patch("builtins.open", new_callable=mock_open):
                with patch("json.load", return_value=mock_fashion_config):
                    orchestrator = FashionOrchestrator(config_path="/test/config.json")

        # Assert
        model = orchestrator.select_ai_model("product_description")
        assert model is not None
        assert model.verified_source == "https://www.anthropic.com/claude"
        assert "creative_writing" in model.features


# =============================================================================
# Performance and Validation Tests
# =============================================================================


class TestPerformanceAndValidation:
    """Tests for performance characteristics and data validation."""

    @pytest.fixture
    def orchestrator(self, mock_fashion_config, mock_config_file):
        """Create a FashionOrchestrator instance for testing."""
        with patch("agent.fashion_orchestrator.UnifiedMCPOrchestrator.__init__", return_value=None):
            with patch("builtins.open", new_callable=mock_open):
                with patch("json.load", return_value=mock_fashion_config):
                    orch = FashionOrchestrator(config_path=mock_config_file)
                    return orch

    def test_model_selection_performance(self, orchestrator):
        """Test model selection executes quickly."""
        # Arrange
        import time

        # Act
        start = time.time()
        for _ in range(100):
            orchestrator.select_ai_model("product_description")
        duration = time.time() - start

        # Assert - Should complete 100 selections in under 100ms
        assert duration < 0.1

    def test_enum_values_are_strings(self):
        """Test all enum values are strings."""
        # Arrange & Act & Assert
        for asset_type in FashionAssetType:
            assert isinstance(asset_type.value, str)

        for provider in AIModelProvider:
            assert isinstance(provider.value, str)

    @pytest.mark.asyncio
    async def test_task_creation_with_all_parameters(self, orchestrator):
        """Test task creation with all possible parameters."""
        # Arrange
        orchestrator.create_task = AsyncMock(return_value=Task())

        # Act
        task = await orchestrator.create_product_description_task(
            product_name="Complete Test Product",
            product_type="handbag",
            materials=["Italian leather", "gold hardware"],
            colors=["black", "gold"],
            price_point="luxury",
            unique_features=["feature1", "feature2", "feature3"],
            tone="elegant",
            length="long",
        )

        # Assert
        assert task is not None
        call_args = orchestrator.create_task.call_args
        input_data = call_args.kwargs["input_data"]
        assert len(input_data["materials"]) == 2
        assert len(input_data["colors"]) == 2
        assert len(input_data["unique_features"]) == 3
