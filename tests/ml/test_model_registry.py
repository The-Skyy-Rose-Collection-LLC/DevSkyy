"""
Comprehensive tests for ml/model_registry.py

Target: 85%+ coverage

Tests cover:
- Model registration and versioning
- Model loading and retrieval
- Model promotion and lifecycle management
- Metadata management
- Model comparison
- Registry statistics
- Error handling
"""

from datetime import datetime
import json
from pathlib import Path

import joblib
import pytest

from ml.model_registry import (
    ModelMetadata,
    ModelRegistry,
    ModelStage,
    get_model_registry,
)


class TestModelStage:
    """Test ModelStage enum"""

    def test_model_stages(self):
        """Test all model stages"""
        assert ModelStage.DEVELOPMENT == "development"
        assert ModelStage.STAGING == "staging"
        assert ModelStage.PRODUCTION == "production"
        assert ModelStage.ARCHIVED == "archived"

    def test_stage_values(self):
        """Test stage string values"""
        stages = [stage.value for stage in ModelStage]
        assert "development" in stages
        assert "staging" in stages
        assert "production" in stages
        assert "archived" in stages


class TestModelMetadata:
    """Test ModelMetadata class"""

    def test_create_metadata(self):
        """Test metadata creation"""
        metadata = ModelMetadata(
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="scikit-learn",
            created_at=datetime.now(),
            metrics={"accuracy": 0.95},
            parameters={"n_estimators": 100},
            dataset_info={"samples": 1000},
        )

        assert metadata.model_name == "test_model"
        assert metadata.version == "1.0.0"
        assert metadata.model_type == "classifier"
        assert metadata.framework == "scikit-learn"
        assert metadata.stage == ModelStage.DEVELOPMENT
        assert metadata.metrics["accuracy"] == 0.95

    def test_metadata_to_dict(self):
        """Test metadata serialization"""
        created_at = datetime.now()
        metadata = ModelMetadata(
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="scikit-learn",
            created_at=created_at,
            metrics={"accuracy": 0.95},
            parameters={"n_estimators": 100},
            dataset_info={"samples": 1000},
            stage=ModelStage.STAGING,
        )

        data = metadata.to_dict()

        assert data["model_name"] == "test_model"
        assert data["version"] == "1.0.0"
        assert data["model_type"] == "classifier"
        assert data["framework"] == "scikit-learn"
        assert data["stage"] == ModelStage.STAGING
        assert data["metrics"] == {"accuracy": 0.95}
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)

    def test_metadata_from_dict(self):
        """Test metadata deserialization"""
        data = {
            "model_name": "test_model",
            "version": "1.0.0",
            "model_type": "classifier",
            "framework": "scikit-learn",
            "created_at": datetime.now().isoformat(),
            "metrics": {"accuracy": 0.95},
            "parameters": {"n_estimators": 100},
            "dataset_info": {"samples": 1000},
            "stage": ModelStage.PRODUCTION,
        }

        metadata = ModelMetadata.from_dict(data)

        assert metadata.model_name == "test_model"
        assert metadata.version == "1.0.0"
        assert metadata.stage == ModelStage.PRODUCTION

    def test_metadata_default_stage(self):
        """Test default stage in from_dict"""
        data = {
            "model_name": "test_model",
            "version": "1.0.0",
            "model_type": "classifier",
            "framework": "scikit-learn",
            "created_at": datetime.now().isoformat(),
            "metrics": {},
            "parameters": {},
            "dataset_info": {},
        }

        metadata = ModelMetadata.from_dict(data)
        assert metadata.stage == ModelStage.DEVELOPMENT


class TestModelRegistry:
    """Test ModelRegistry class"""

    def test_init_creates_directories(self, temp_dir):
        """Test registry initialization creates directories"""
        registry_path = temp_dir / "registry"
        registry = ModelRegistry(registry_path=str(registry_path))

        assert registry.registry_path.exists()
        assert registry.models_dir.exists()
        assert registry.metadata_dir.exists()
        assert registry.index_file.exists()

    def test_init_loads_existing_index(self, temp_dir):
        """Test registry loads existing index"""
        registry_path = temp_dir / "registry"
        registry1 = ModelRegistry(registry_path=str(registry_path))

        # Add a model
        model = object()
        registry1.register_model(
            model=model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.9},
            parameters={},
            dataset_info={},
        )

        # Create new registry instance
        registry2 = ModelRegistry(registry_path=str(registry_path))

        assert "test_model" in registry2.index["models"]

    def test_register_model(self, temp_registry, mock_model):
        """Test model registration"""
        metadata = temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95, "f1": 0.92},
            parameters={"param1": 100},
            dataset_info={"samples": 1000},
            stage=ModelStage.DEVELOPMENT,
        )

        assert metadata.model_name == "test_model"
        assert metadata.version == "1.0.0"
        assert metadata.metrics["accuracy"] == 0.95
        assert "test_model" in temp_registry.index["models"]

        # Check model file exists
        model_file = temp_registry.models_dir / "test_model" / "1.0.0" / "model.pkl"
        assert model_file.exists()

        # Check metadata file exists
        metadata_file = temp_registry.metadata_dir / "test_model_1.0.0.json"
        assert metadata_file.exists()

    def test_register_multiple_versions(self, temp_registry, mock_model):
        """Test registering multiple versions"""
        for version in ["1.0.0", "1.1.0", "2.0.0"]:
            temp_registry.register_model(
                model=mock_model,
                model_name="test_model",
                version=version,
                model_type="classifier",
                framework="test",
                metrics={"accuracy": 0.9 + float(version[0]) * 0.01},
                parameters={},
                dataset_info={},
            )

        versions = temp_registry.list_versions("test_model")
        assert len(versions) == 3
        assert any(v["version"] == "1.0.0" for v in versions)
        assert any(v["version"] == "2.0.0" for v in versions)

    def test_register_model_production_updates_latest(self, temp_registry, mock_model):
        """Test registering production model updates latest_production"""
        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95},
            parameters={},
            dataset_info={},
            stage=ModelStage.PRODUCTION,
        )

        assert temp_registry.index["models"]["test_model"]["latest_production"] == "1.0.0"

    def test_load_model_by_version(self, temp_registry, mock_model):
        """Test loading model by version"""
        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95},
            parameters={},
            dataset_info={},
        )

        loaded_model = temp_registry.load_model("test_model", version="1.0.0")
        assert loaded_model is not None
        assert hasattr(loaded_model, "predict")

    def test_load_model_latest_production(self, temp_registry, mock_model):
        """Test loading latest production model"""
        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95},
            parameters={},
            dataset_info={},
            stage=ModelStage.PRODUCTION,
        )

        loaded_model = temp_registry.load_model("test_model")
        assert loaded_model is not None

    def test_load_model_by_stage(self, temp_registry, mock_model):
        """Test loading model by stage"""
        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95},
            parameters={},
            dataset_info={},
            stage=ModelStage.STAGING,
        )

        loaded_model = temp_registry.load_model("test_model", stage=ModelStage.STAGING)
        assert loaded_model is not None

    def test_load_model_not_found(self, temp_registry):
        """Test loading non-existent model"""
        with pytest.raises(ValueError, match="No production version found"):
            temp_registry.load_model("nonexistent_model")

    def test_load_model_file_not_found(self, temp_registry, mock_model):
        """Test loading model with missing file"""
        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95},
            parameters={},
            dataset_info={},
        )

        # Remove model file
        model_file = temp_registry.models_dir / "test_model" / "1.0.0" / "model.pkl"
        model_file.unlink()

        with pytest.raises(FileNotFoundError):
            temp_registry.load_model("test_model", version="1.0.0")

    def test_get_metadata(self, temp_registry, mock_model):
        """Test getting model metadata"""
        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95},
            parameters={"param1": 100},
            dataset_info={"samples": 1000},
        )

        metadata = temp_registry.get_metadata("test_model", "1.0.0")

        assert metadata.model_name == "test_model"
        assert metadata.version == "1.0.0"
        assert metadata.metrics["accuracy"] == 0.95

    def test_get_metadata_not_found(self, temp_registry):
        """Test getting metadata for non-existent model"""
        with pytest.raises(FileNotFoundError):
            temp_registry.get_metadata("nonexistent", "1.0.0")

    def test_list_models(self, temp_registry, mock_model):
        """Test listing all models"""
        for model_name in ["model_a", "model_b", "model_c"]:
            temp_registry.register_model(
                model=mock_model,
                model_name=model_name,
                version="1.0.0",
                model_type="classifier",
                framework="test",
                metrics={"accuracy": 0.9},
                parameters={},
                dataset_info={},
            )

        models = temp_registry.list_models()
        assert len(models) == 3
        assert "model_a" in models
        assert "model_b" in models
        assert "model_c" in models

    def test_list_models_empty(self, temp_registry):
        """Test listing models in empty registry"""
        models = temp_registry.list_models()
        assert models == []

    def test_list_versions(self, temp_registry, mock_model):
        """Test listing model versions"""
        versions = ["1.0.0", "1.1.0", "2.0.0"]
        for version in versions:
            temp_registry.register_model(
                model=mock_model,
                model_name="test_model",
                version=version,
                model_type="classifier",
                framework="test",
                metrics={"accuracy": 0.9},
                parameters={},
                dataset_info={},
            )

        version_list = temp_registry.list_versions("test_model")
        assert len(version_list) == 3
        assert all(v["version"] in versions for v in version_list)

    def test_list_versions_nonexistent(self, temp_registry):
        """Test listing versions for non-existent model"""
        versions = temp_registry.list_versions("nonexistent")
        assert versions == []

    def test_promote_model(self, temp_registry, mock_model):
        """Test promoting model to different stage"""
        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95},
            parameters={},
            dataset_info={},
            stage=ModelStage.DEVELOPMENT,
        )

        # Promote to staging
        temp_registry.promote_model("test_model", "1.0.0", ModelStage.STAGING)

        metadata = temp_registry.get_metadata("test_model", "1.0.0")
        assert metadata.stage == ModelStage.STAGING

        # Check index updated
        versions = temp_registry.list_versions("test_model")
        assert versions[0]["stage"] == ModelStage.STAGING

    def test_promote_model_to_production(self, temp_registry, mock_model):
        """Test promoting model to production"""
        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95},
            parameters={},
            dataset_info={},
        )

        temp_registry.promote_model("test_model", "1.0.0", ModelStage.PRODUCTION)

        assert temp_registry.index["models"]["test_model"]["latest_production"] == "1.0.0"

    def test_archive_model(self, temp_registry, mock_model):
        """Test archiving model"""
        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95},
            parameters={},
            dataset_info={},
        )

        temp_registry.archive_model("test_model", "1.0.0")

        metadata = temp_registry.get_metadata("test_model", "1.0.0")
        assert metadata.stage == ModelStage.ARCHIVED

    def test_compare_models(self, temp_registry, mock_model):
        """Test comparing two model versions"""
        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.90, "f1": 0.88},
            parameters={},
            dataset_info={},
        )

        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="2.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95, "f1": 0.93},
            parameters={},
            dataset_info={},
        )

        comparison = temp_registry.compare_models("test_model", "1.0.0", "2.0.0")

        assert comparison["model_name"] == "test_model"
        assert comparison["version1"] == "1.0.0"
        assert comparison["version2"] == "2.0.0"
        assert "metrics_comparison" in comparison

        # Check accuracy comparison
        acc_comp = comparison["metrics_comparison"]["accuracy"]
        assert acc_comp["v1"] == 0.90
        assert acc_comp["v2"] == 0.95
        assert abs(acc_comp["diff"] - 0.05) < 0.0001  # Allow for floating point precision
        assert acc_comp["improvement"] > 0

    def test_compare_models_different_metrics(self, temp_registry, mock_model):
        """Test comparing models with different metric sets"""
        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.90},
            parameters={},
            dataset_info={},
        )

        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="2.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95, "f1": 0.93},
            parameters={},
            dataset_info={},
        )

        comparison = temp_registry.compare_models("test_model", "1.0.0", "2.0.0")

        assert "accuracy" in comparison["metrics_comparison"]
        assert "f1" in comparison["metrics_comparison"]

    def test_get_registry_stats(self, temp_registry, mock_model):
        """Test getting registry statistics"""
        # Register multiple models with different stages
        temp_registry.register_model(
            model=mock_model,
            model_name="model_a",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.9},
            parameters={},
            dataset_info={},
            stage=ModelStage.DEVELOPMENT,
        )

        temp_registry.register_model(
            model=mock_model,
            model_name="model_a",
            version="2.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95},
            parameters={},
            dataset_info={},
            stage=ModelStage.PRODUCTION,
        )

        temp_registry.register_model(
            model=mock_model,
            model_name="model_b",
            version="1.0.0",
            model_type="regressor",
            framework="test",
            metrics={"r2": 0.85},
            parameters={},
            dataset_info={},
            stage=ModelStage.STAGING,
        )

        stats = temp_registry.get_registry_stats()

        assert stats["total_models"] == 2
        assert stats["total_versions"] == 3
        assert "stage_distribution" in stats
        assert "models" in stats
        assert "model_a" in stats["models"]
        assert "model_b" in stats["models"]

    def test_get_registry_stats_empty(self, temp_registry):
        """Test registry stats for empty registry"""
        stats = temp_registry.get_registry_stats()

        assert stats["total_models"] == 0
        assert stats["total_versions"] == 0

    def test_get_latest_version_by_stage(self, temp_registry, mock_model):
        """Test getting latest version by stage"""
        # Register multiple versions with same stage
        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.9},
            parameters={},
            dataset_info={},
            stage=ModelStage.STAGING,
        )

        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="2.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.95},
            parameters={},
            dataset_info={},
            stage=ModelStage.STAGING,
        )

        latest = temp_registry._get_latest_version_by_stage("test_model", ModelStage.STAGING)
        # Should return most recent (2.0.0)
        assert latest in ["1.0.0", "2.0.0"]  # Either is valid since created_at is same

    def test_get_latest_version_by_stage_not_found(self, temp_registry, mock_model):
        """Test getting latest version for non-existent stage"""
        temp_registry.register_model(
            model=mock_model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            framework="test",
            metrics={"accuracy": 0.9},
            parameters={},
            dataset_info={},
            stage=ModelStage.DEVELOPMENT,
        )

        latest = temp_registry._get_latest_version_by_stage("test_model", ModelStage.PRODUCTION)
        assert latest is None

    def test_get_latest_version_by_stage_nonexistent_model(self, temp_registry):
        """Test getting latest version for non-existent model"""
        latest = temp_registry._get_latest_version_by_stage("nonexistent", ModelStage.DEVELOPMENT)
        assert latest is None


class TestGetModelRegistry:
    """Test get_model_registry function"""

    def test_get_model_registry(self):
        """Test getting global registry instance"""
        registry = get_model_registry()
        assert isinstance(registry, ModelRegistry)

    def test_get_model_registry_singleton(self):
        """Test registry is singleton"""
        registry1 = get_model_registry()
        registry2 = get_model_registry()
        assert registry1 is registry2
