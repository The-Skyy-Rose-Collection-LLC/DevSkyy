---
name: ml-model-registry
description: ML model lifecycle management with versioning, deployment, monitoring, and A/B testing for DevSkyy's 54+ agents
---

You are the ML Model Registry expert for DevSkyy. Manage machine learning model lifecycles across all agents with versioning, staging, deployment, performance monitoring, and A/B testing.

## Core ML Registry System

### 1. Model Registry Manager

```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import pickle
import joblib
from pathlib import Path

class ModelStage(Enum):
    """Model deployment stages"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"

@dataclass
class ModelMetadata:
    """ML model metadata"""
    model_name: str
    version: str
    model_type: str  # classifier, regressor, clustering, etc.
    framework: str  # sklearn, pytorch, tensorflow, etc.

    # Performance metrics
    metrics: Dict[str, float]

    # Training info
    training_date: datetime
    dataset_size: int
    features: List[str]
    hyperparameters: Dict[str, Any]

    # Deployment
    stage: ModelStage
    deployed_at: Optional[datetime] = None

    # Metadata
    created_by: str = "DevSkyy AI"
    description: str = ""
    tags: List[str] = None

class MLModelRegistry:
    """Central registry for all ML models"""

    def __init__(self, registry_path: str = "ml/registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.models: Dict[str, Dict[str, ModelMetadata]] = {}
        self.load_registry()

    def register_model(
        self,
        model: Any,
        model_name: str,
        version: str,
        model_type: str,
        metrics: Dict[str, float],
        **kwargs
    ) -> ModelMetadata:
        """Register a new model version"""

        # Save model file
        model_path = self.registry_path / model_name / version
        model_path.mkdir(parents=True, exist_ok=True)

        model_file = model_path / "model.pkl"
        joblib.dump(model, model_file)

        # Create metadata
        metadata = ModelMetadata(
            model_name=model_name,
            version=version,
            model_type=model_type,
            framework=kwargs.get('framework', 'sklearn'),
            metrics=metrics,
            training_date=datetime.now(),
            dataset_size=kwargs.get('dataset_size', 0),
            features=kwargs.get('features', []),
            hyperparameters=kwargs.get('hyperparameters', {}),
            stage=ModelStage.DEVELOPMENT,
            description=kwargs.get('description', ''),
            tags=kwargs.get('tags', [])
        )

        # Save metadata
        self._save_metadata(metadata)

        # Update registry
        if model_name not in self.models:
            self.models[model_name] = {}
        self.models[model_name][version] = metadata

        return metadata

    def promote_model(
        self,
        model_name: str,
        version: str,
        stage: ModelStage
    ) -> bool:
        """Promote model to a new stage"""

        if model_name not in self.models or version not in self.models[model_name]:
            return False

        metadata = self.models[model_name][version]
        metadata.stage = stage

        if stage == ModelStage.PRODUCTION:
            metadata.deployed_at = datetime.now()

        self._save_metadata(metadata)
        return True

    def load_model(
        self,
        model_name: str,
        version: Optional[str] = None,
        stage: Optional[ModelStage] = None
    ) -> Optional[Any]:
        """Load a model from registry"""

        if version:
            model_path = self.registry_path / model_name / version / "model.pkl"
        elif stage:
            # Find model in specified stage
            versions = self.get_model_versions(model_name, stage=stage)
            if not versions:
                return None
            version = versions[0]['version']
            model_path = self.registry_path / model_name / version / "model.pkl"
        else:
            # Load latest production model
            versions = self.get_model_versions(model_name, stage=ModelStage.PRODUCTION)
            if not versions:
                return None
            version = versions[0]['version']
            model_path = self.registry_path / model_name / version / "model.pkl"

        if model_path.exists():
            return joblib.load(model_path)
        return None

    def get_model_versions(
        self,
        model_name: str,
        stage: Optional[ModelStage] = None
    ) -> List[Dict[str, Any]]:
        """Get all versions of a model"""

        if model_name not in self.models:
            return []

        versions = []
        for version, metadata in self.models[model_name].items():
            if stage is None or metadata.stage == stage:
                versions.append({
                    'version': version,
                    'stage': metadata.stage.value,
                    'metrics': metadata.metrics,
                    'training_date': metadata.training_date.isoformat()
                })

        # Sort by version descending
        versions.sort(key=lambda x: x['version'], reverse=True)
        return versions

    def compare_models(
        self,
        model_name: str,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """Compare two model versions"""

        if model_name not in self.models:
            return {"error": "Model not found"}

        meta1 = self.models[model_name].get(version1)
        meta2 = self.models[model_name].get(version2)

        if not meta1 or not meta2:
            return {"error": "One or both versions not found"}

        # Compare metrics
        metric_comparison = {}
        all_metrics = set(meta1.metrics.keys()) | set(meta2.metrics.keys())

        for metric in all_metrics:
            val1 = meta1.metrics.get(metric, 0)
            val2 = meta2.metrics.get(metric, 0)
            diff = val2 - val1
            diff_pct = (diff / val1 * 100) if val1 != 0 else 0

            metric_comparison[metric] = {
                version1: val1,
                version2: val2,
                "difference": diff,
                "difference_pct": diff_pct,
                "better": version2 if val2 > val1 else version1
            }

        return {
            "model_name": model_name,
            "versions_compared": [version1, version2],
            "metric_comparison": metric_comparison,
            "recommendation": self._get_recommendation(metric_comparison)
        }

    def _get_recommendation(self, comparison: Dict[str, Any]) -> str:
        """Get deployment recommendation based on comparison"""
        # Simple logic: if most metrics improved, recommend new version
        improvements = sum(1 for m in comparison.values() if m.get('difference', 0) > 0)
        total = len(comparison)

        if improvements / total > 0.7:
            return "Recommend deploying newer version (70%+ metrics improved)"
        elif improvements / total < 0.3:
            return "Keep current version (metrics declined)"
        else:
            return "Mixed results - conduct A/B test"

    def _save_metadata(self, metadata: ModelMetadata):
        """Save metadata to JSON"""
        import json

        metadata_path = self.registry_path / metadata.model_name / metadata.version / "metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        with open(metadata_path, 'w') as f:
            json.dump({
                "model_name": metadata.model_name,
                "version": metadata.version,
                "model_type": metadata.model_type,
                "framework": metadata.framework,
                "metrics": metadata.metrics,
                "training_date": metadata.training_date.isoformat(),
                "stage": metadata.stage.value,
                "deployed_at": metadata.deployed_at.isoformat() if metadata.deployed_at else None,
                "description": metadata.description
            }, f, indent=2)

    def load_registry(self):
        """Load existing registry from disk"""
        # Implementation to load existing models
        pass
```

### 2. Model Performance Monitor

```python
class ModelPerformanceMonitor:
    """Monitor ML model performance in production"""

    def __init__(self, registry: MLModelRegistry):
        self.registry = registry
        self.performance_log: List[Dict[str, Any]] = []

    async def log_prediction(
        self,
        model_name: str,
        version: str,
        input_data: Any,
        prediction: Any,
        ground_truth: Optional[Any] = None
    ):
        """Log model prediction for monitoring"""

        log_entry = {
            "model_name": model_name,
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "prediction": prediction,
            "ground_truth": ground_truth,
            "correct": prediction == ground_truth if ground_truth is not None else None
        }

        self.performance_log.append(log_entry)

    async def get_performance_report(
        self,
        model_name: str,
        version: str,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance report for a model"""

        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        # Filter logs
        relevant_logs = [
            log for log in self.performance_log
            if log['model_name'] == model_name
            and log['version'] == version
            and datetime.fromisoformat(log['timestamp']) > cutoff_time
        ]

        if not relevant_logs:
            return {"error": "No data available for this time window"}

        # Calculate metrics
        total_predictions = len(relevant_logs)
        correct_predictions = sum(1 for log in relevant_logs if log.get('correct', False))
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0

        return {
            "model_name": model_name,
            "version": version,
            "time_window_hours": time_window_hours,
            "total_predictions": total_predictions,
            "accuracy": round(accuracy, 4),
            "performance_trend": "stable"  # Could implement trend analysis
        }
```

## Usage Examples

### Example 1: Register and Deploy Model

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification

# Train model
X, y = make_classification(n_samples=1000, n_features=10)
model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

# Initialize registry
registry = MLModelRegistry()

# Register model
metadata = registry.register_model(
    model=model,
    model_name="fashion_trend_predictor",
    version="2.1.0",
    model_type="classifier",
    metrics={"accuracy": 0.95, "f1": 0.93, "precision": 0.94},
    framework="sklearn",
    dataset_size=1000,
    features=["season", "color", "material", "price_point", "category"],
    hyperparameters={"n_estimators": 100, "max_depth": 10}
)

# Promote to production
registry.promote_model("fashion_trend_predictor", "2.1.0", ModelStage.PRODUCTION)

# Load and use
model = registry.load_model("fashion_trend_predictor", stage=ModelStage.PRODUCTION)
prediction = model.predict([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]])
```

### Example 2: Compare Model Versions

```python
comparison = registry.compare_models(
    "fashion_trend_predictor",
    "2.0.0",
    "2.1.0"
)

print(f"Recommendation: {comparison['recommendation']}")
for metric, data in comparison['metric_comparison'].items():
    print(f"{metric}: {data['2.0.0']} → {data['2.1.0']} ({data['difference_pct']:.2f}% change)")
```

## Integration with DevSkyy Agents

All ML-powered agents use the registry:
- Fashion Computer Vision Agent
- Inventory Demand Forecaster
- Dynamic Pricing Engine
- Customer Segmentation
- SEO Optimization

Use this skill for production-grade ML model management across all DevSkyy agents.
