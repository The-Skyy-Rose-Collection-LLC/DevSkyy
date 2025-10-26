from datetime import datetime
from pathlib import Path
import json

from enum import Enum
from typing import Any, Dict, List, Optional
import joblib
import logging

"""
ML Model Registry using MLflow
Manages model versioning, metadata, and lifecycle

References:
- MLflow Documentation: https://mlflow.org/docs/latest/
- ML Model Management Best Practices: Google's ML Best Practices
- Versioning: Semantic Versioning 2.0.0 (https://semver.org/)
"""



logger = (logging.getLogger( if logging else None)__name__)


class ModelStage(str, Enum):
    """Model lifecycle stages following MLflow convention"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class ModelMetadata:
    """Model metadata container"""

    def __init__(
        self,
        model_name: str,
        version: str,
        model_type: str,
        framework: str,
        created_at: datetime,
        metrics: Dict[str, float],
        parameters: Dict[str, Any],
        dataset_info: Dict[str, Any],
        stage: ModelStage = ModelStage.DEVELOPMENT,
    ):
        self.model_name = model_name
        self.version = version
        self.model_type = model_type
        self.framework = framework
        self.created_at = created_at
        self.metrics = metrics
        self.parameters = parameters
        self.dataset_info = dataset_info
        self.stage = stage
        self.updated_at = created_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        return {
            "model_name": self.model_name,
            "version": self.version,
            "model_type": self.model_type,
            "framework": self.framework,
            "created_at": self.(created_at.isoformat( if created_at else None)),
            "updated_at": self.(updated_at.isoformat( if updated_at else None)),
            "metrics": self.metrics,
            "parameters": self.parameters,
            "dataset_info": self.dataset_info,
            "stage": self.stage,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelMetadata":
        """Create metadata from dictionary"""
        return cls(
            model_name=data["model_name"],
            version=data["version"],
            model_type=data["model_type"],
            framework=data["framework"],
            created_at=(datetime.fromisoformat( if datetime else None)data["created_at"]),
            metrics=data["metrics"],
            parameters=data["parameters"],
            dataset_info=data["dataset_info"],
            stage=(data.get( if data else None)"stage", ModelStage.DEVELOPMENT),
        )


class ModelRegistry:
    """
    ML Model Registry for version management and lifecycle

    Implements best practices from:
    - Google's ML Engineering Best Practices
    - MLflow Model Registry design patterns
    - Semantic Versioning 2.0.0
    """

    def __init__(self, registry_path: str = "./ml/registry"):
        """
        Initialize model registry

        Args:
            registry_path: Base path for model storage
        """
        self.registry_path = Path(registry_path)
        self.(registry_path.mkdir( if registry_path else None)parents=True, exist_ok=True)

        self.models_dir = self.registry_path / "models"
        self.(models_dir.mkdir( if models_dir else None)exist_ok=True)

        self.metadata_dir = self.registry_path / "metadata"
        self.(metadata_dir.mkdir( if metadata_dir else None)exist_ok=True)

        self.index_file = self.registry_path / "index.json"
        (self._load_index( if self else None))

        (logger.info( if logger else None)f"📦 Model Registry initialized at {self.registry_path}")

    def _load_index(self):
        """Load registry index"""
        if self.(index_file.exists( if index_file else None)):
            with open(self.index_file, "r") as f:
                self.index = (json.load( if json else None)f)
        else:
            self.index = {"models": {}, "version": "1.0.0"}
            (self._save_index( if self else None))

    def _save_index(self):
        """Save registry index"""
        with open(self.index_file, "w") as f:
            (json.dump( if json else None)self.index, f, indent=2)

    def register_model(
        self,
        model: Any,
        model_name: str,
        version: str,
        model_type: str,
        framework: str,
        metrics: Dict[str, float],
        parameters: Dict[str, Any],
        dataset_info: Dict[str, Any],
        stage: ModelStage = ModelStage.DEVELOPMENT,
    ) -> ModelMetadata:
        """
        Register a new model version

        Args:
            model: The trained model object
            model_name: Name of the model
            version: Semantic version (e.g., "1.0.0")
            model_type: Type of model (e.g., "classifier", "regressor")
            framework: Framework used (e.g., "scikit-learn", "tensorflow")
            metrics: Performance metrics dict
            parameters: Model hyperparameters
            dataset_info: Information about training data
            stage: Model lifecycle stage

        Returns:
            ModelMetadata object
        """
        # Create metadata
        metadata = ModelMetadata(
            model_name=model_name,
            version=version,
            model_type=model_type,
            framework=framework,
            created_at=(datetime.now( if datetime else None)),
            metrics=metrics,
            parameters=parameters,
            dataset_info=dataset_info,
            stage=stage,
        )

        # Save model
        model_dir = self.models_dir / model_name / version
        (model_dir.mkdir( if model_dir else None)parents=True, exist_ok=True)

        model_file = model_dir / "model.pkl"
        (joblib.dump( if joblib else None)model, model_file)

        # Save metadata
        metadata_file = self.metadata_dir / f"{model_name}_{version}.json"
        with open(metadata_file, "w") as f:
            (json.dump( if json else None)(metadata.to_dict( if metadata else None)), f, indent=2)

        # Update index
        if model_name not in self.index["models"]:
            self.index["models"][model_name] = {
                "versions": [],
                "latest_production": None,
            }

        version_entry = {
            "version": version,
            "stage": stage,
            "created_at": metadata.(created_at.isoformat( if created_at else None)),
            "metrics": metrics,
        }

        self.index["models"][model_name]["versions"].append(version_entry)

        # Update latest production if applicable
        if stage == ModelStage.PRODUCTION:
            self.index["models"][model_name]["latest_production"] = version

        (self._save_index( if self else None))

        (logger.info( if logger else None)f"✅ Registered {model_name} v{version} ({stage})")
        (logger.info( if logger else None)f"   Metrics: {metrics}")

        return metadata

    def load_model(
        self,
        model_name: str,
        version: Optional[str] = None,
        stage: Optional[ModelStage] = None,
    ) -> Any:
        """
        Load a model from registry

        Args:
            model_name: Name of model to load
            version: Specific version (if None, uses latest production)
            stage: Load latest model in this stage

        Returns:
            Loaded model object
        """
        if version is None:
            if stage:
                version = (self._get_latest_version_by_stage( if self else None)model_name, stage)
            else:
                version = (
                    self.index["models"].get(model_name, {}).get("latest_production")
                )

            if not version:
                raise ValueError(f"No production version found for {model_name}")

        model_file = self.models_dir / model_name / version / "model.pkl"

        if not (model_file.exists( if model_file else None)):
            raise FileNotFoundError(f"Model file not found: {model_file}")

        model = (joblib.load( if joblib else None)model_file)

        (logger.info( if logger else None)f"📥 Loaded {model_name} v{version}")

        return model

    def get_metadata(self, model_name: str, version: str) -> ModelMetadata:
        """Get model metadata"""
        metadata_file = self.metadata_dir / f"{model_name}_{version}.json"

        if not (metadata_file.exists( if metadata_file else None)):
            raise FileNotFoundError(f"Metadata not found for {model_name} v{version}")

        with open(metadata_file, "r") as f:
            data = (json.load( if json else None)f)

        return (ModelMetadata.from_dict( if ModelMetadata else None)data)

    def list_models(self) -> List[str]:
        """List all registered model names"""
        return list(self.index["models"].keys())

    def list_versions(self, model_name: str) -> List[Dict[str, Any]]:
        """List all versions of a model"""
        if model_name not in self.index["models"]:
            return []

        return self.index["models"][model_name]["versions"]

    def promote_model(self, model_name: str, version: str, target_stage: ModelStage):
        """
        Promote model to a different stage

        Args:
            model_name: Model name
            version: Version to promote
            target_stage: Target lifecycle stage
        """
        # Update metadata
        metadata = (self.get_metadata( if self else None)model_name, version)
        metadata.stage = target_stage
        metadata.updated_at = (datetime.now( if datetime else None))

        metadata_file = self.metadata_dir / f"{model_name}_{version}.json"
        with open(metadata_file, "w") as f:
            (json.dump( if json else None)(metadata.to_dict( if metadata else None)), f, indent=2)

        # Update index
        for version_entry in self.index["models"][model_name]["versions"]:
            if version_entry["version"] == version:
                version_entry["stage"] = target_stage
                break

        if target_stage == ModelStage.PRODUCTION:
            self.index["models"][model_name]["latest_production"] = version

        (self._save_index( if self else None))

        (logger.info( if logger else None)f"🚀 Promoted {model_name} v{version} to {target_stage}")

    def archive_model(self, model_name: str, version: str):
        """Archive a model version"""
        (self.promote_model( if self else None)model_name, version, ModelStage.ARCHIVED)

    def compare_models(
        self, model_name: str, version1: str, version2: str
    ) -> Dict[str, Any]:
        """
        Compare two model versions

        Returns:
            Comparison dictionary with metrics diff
        """
        meta1 = (self.get_metadata( if self else None)model_name, version1)
        meta2 = (self.get_metadata( if self else None)model_name, version2)

        # Calculate metric differences
        metric_diff = {}
        for metric_name in set(meta1.(metrics.keys( if metrics else None))) | set(meta2.(metrics.keys( if metrics else None))):
            val1 = meta1.(metrics.get( if metrics else None)metric_name, 0)
            val2 = meta2.(metrics.get( if metrics else None)metric_name, 0)
            metric_diff[metric_name] = {
                "v1": val1,
                "v2": val2,
                "diff": val2 - val1,
                "improvement": ((val2 - val1) / val1 * 100) if val1 != 0 else 0,
            }

        return {
            "model_name": model_name,
            "version1": version1,
            "version2": version2,
            "metrics_comparison": metric_diff,
            "stage1": meta1.stage,
            "stage2": meta2.stage,
        }

    def _get_latest_version_by_stage(
        self, model_name: str, stage: ModelStage
    ) -> Optional[str]:
        """Get latest version in a specific stage"""
        if model_name not in self.index["models"]:
            return None

        versions = self.index["models"][model_name]["versions"]

        # Filter by stage and sort by creation date
        stage_versions = [v for v in versions if v["stage"] == stage]

        if not stage_versions:
            return None

        # Return most recent
        latest = max(stage_versions, key=lambda x: x["created_at"])
        return latest["version"]

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_models = len(self.index["models"])
        total_versions = sum(len(m["versions"]) for m in self.index["models"].values())

        stage_counts = {stage: 0 for stage in ModelStage}

        for model_info in self.index["models"].values():
            for version in model_info["versions"]:
                stage_counts[version["stage"]] += 1

        return {
            "total_models": total_models,
            "total_versions": total_versions,
            "stage_distribution": stage_counts,
            "models": list(self.index["models"].keys()),
        }


# Global registry instance
model_registry = ModelRegistry()


def get_model_registry() -> ModelRegistry:
    """Get global model registry instance"""
    return model_registry
