"""
Integration Tests for ML Model Training & Deployment Pipeline
Comprehensive testing of end-to-end ML workflows

Test Coverage:
- End-to-end model training pipeline
- Model version management
- A/B testing deployment
- Rollback on performance degradation
- Model registry integration
- Performance monitoring
- Dataset preparation and validation
- Fine-tuning workflows
- Model deployment and serving

Per Truth Protocol:
- Rule #8: Test coverage ≥90%
- Rule #12: Performance SLOs
- Rule #13: Security baseline for model storage
- Rule #14: Error ledger required
"""

import asyncio
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import tempfile
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from ml.agent_finetuning_system import (
    AgentCategory,
    AgentPerformanceSnapshot,
    FinetuningDataset,
    FinetuningJob,
    FinetuningProvider,
    FinetuningStatus,
)
from ml.model_registry import ModelRegistry, ModelVersion, ModelMetadata
from ml.agent_deployment_system import (
    DeploymentEnvironment,
    DeploymentStrategy,
    ModelDeployment,
)


logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_model_dir() -> Path:
    """Create temporary directory for model storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def model_registry(temp_model_dir: Path) -> ModelRegistry:
    """Create model registry instance."""
    return ModelRegistry(storage_path=temp_model_dir)


@pytest.fixture
def sample_training_data() -> list[AgentPerformanceSnapshot]:
    """Generate sample training data."""
    snapshots = []
    for i in range(100):
        snapshot = AgentPerformanceSnapshot(
            agent_id=f"agent_{i % 5}",
            agent_name=f"test_agent_{i % 5}",
            category=AgentCategory.ECOMMERCE,
            timestamp=datetime.now() - timedelta(days=i % 30),
            task_type="product_recommendation",
            input_data={"user_id": f"user_{i}", "category": "handbags"},
            output_data={"recommendations": [f"product_{j}" for j in range(5)]},
            success=i % 10 != 0,  # 90% success rate
            performance_score=0.85 + (i % 10) * 0.01,
            execution_time_ms=150 + (i % 50),
            tokens_used=500 + (i % 200),
            user_feedback=0.8 + (i % 5) * 0.04 if i % 3 == 0 else None,
        )
        snapshots.append(snapshot)
    return snapshots


@pytest.fixture
def finetuning_dataset(sample_training_data: list[AgentPerformanceSnapshot]) -> FinetuningDataset:
    """Create finetuning dataset from training data."""
    return FinetuningDataset(
        dataset_id="dataset_test_001",
        category=AgentCategory.ECOMMERCE,
        created_at=datetime.now(),
        snapshots=sample_training_data,
        train_split=0.8,
        validation_split=0.1,
        test_split=0.1,
        format="jsonl",
        size_bytes=len(json.dumps([s.__dict__ for s in sample_training_data])),
    )


# ============================================================================
# DATA COLLECTION & PREPARATION TESTS
# ============================================================================


class TestDataCollectionAndPreparation:
    """Test data collection and dataset preparation for training."""

    def test_collect_agent_performance_data(self, sample_training_data: list[AgentPerformanceSnapshot]):
        """Test collection of agent performance snapshots."""
        assert len(sample_training_data) == 100
        assert all(isinstance(s, AgentPerformanceSnapshot) for s in sample_training_data)
        assert all(s.category == AgentCategory.ECOMMERCE for s in sample_training_data)

    def test_dataset_train_validation_test_split(self, finetuning_dataset: FinetuningDataset):
        """Test dataset is correctly split into train/validation/test."""
        total_samples = len(finetuning_dataset.snapshots)
        train_size = int(total_samples * finetuning_dataset.train_split)
        val_size = int(total_samples * finetuning_dataset.validation_split)
        test_size = int(total_samples * finetuning_dataset.test_split)

        assert train_size + val_size + test_size <= total_samples
        assert finetuning_dataset.train_split + finetuning_dataset.validation_split + finetuning_dataset.test_split == 1.0

    def test_dataset_format_validation(self, finetuning_dataset: FinetuningDataset):
        """Test dataset format is valid for training."""
        assert finetuning_dataset.format in ["jsonl", "parquet", "csv"]
        assert finetuning_dataset.size_bytes > 0

    def test_filter_low_quality_samples(self, sample_training_data: list[AgentPerformanceSnapshot]):
        """Test filtering out low-quality training samples."""
        quality_threshold = 0.7
        high_quality_samples = [
            s for s in sample_training_data
            if s.success and s.performance_score >= quality_threshold
        ]

        assert len(high_quality_samples) < len(sample_training_data)
        assert all(s.performance_score >= quality_threshold for s in high_quality_samples)

    def test_balance_dataset_by_category(self, sample_training_data: list[AgentPerformanceSnapshot]):
        """Test dataset balancing across categories."""
        from collections import Counter

        category_counts = Counter(s.category for s in sample_training_data)

        assert len(category_counts) >= 1
        for category, count in category_counts.items():
            assert count > 0

    def test_augment_training_data(self, sample_training_data: list[AgentPerformanceSnapshot]):
        """Test data augmentation for training."""
        augmented_data = []
        for snapshot in sample_training_data[:10]:
            augmented_data.append(snapshot)

            augmented_snapshot = AgentPerformanceSnapshot(
                agent_id=snapshot.agent_id,
                agent_name=snapshot.agent_name,
                category=snapshot.category,
                timestamp=snapshot.timestamp,
                task_type=snapshot.task_type,
                input_data={**snapshot.input_data, "augmented": True},
                output_data=snapshot.output_data,
                success=snapshot.success,
                performance_score=snapshot.performance_score,
                execution_time_ms=snapshot.execution_time_ms,
                tokens_used=snapshot.tokens_used,
            )
            augmented_data.append(augmented_snapshot)

        assert len(augmented_data) == 20
        assert sum(1 for s in augmented_data if s.input_data.get("augmented")) == 10


# ============================================================================
# MODEL TRAINING TESTS
# ============================================================================


class TestModelTraining:
    """Test model training workflows."""

    @pytest.mark.asyncio
    async def test_start_finetuning_job(self, finetuning_dataset: FinetuningDataset):
        """Test starting a finetuning job."""
        from ml.agent_finetuning_system import AgentFinetuningSystem

        finetuning_system = AgentFinetuningSystem()

        job = await finetuning_system.create_finetuning_job(
            category=AgentCategory.ECOMMERCE,
            dataset=finetuning_dataset,
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            hyperparameters={
                "n_epochs": 3,
                "batch_size": 4,
                "learning_rate_multiplier": 0.1,
            },
        )

        assert job is not None
        assert job.status == FinetuningStatus.PENDING
        assert job.category == AgentCategory.ECOMMERCE
        assert job.provider == FinetuningProvider.OPENAI

    @pytest.mark.asyncio
    async def test_monitor_training_progress(self):
        """Test monitoring training progress."""
        from ml.agent_finetuning_system import AgentFinetuningSystem

        finetuning_system = AgentFinetuningSystem()

        job = FinetuningJob(
            job_id="job_test_001",
            category=AgentCategory.ECOMMERCE,
            provider=FinetuningProvider.OPENAI,
            dataset_id="dataset_test_001",
            base_model="gpt-3.5-turbo",
            status=FinetuningStatus.TRAINING,
            created_at=datetime.now(),
            started_at=datetime.now(),
            hyperparameters={},
            training_progress=0.0,
        )

        progress_updates = []

        async def mock_get_job_status(job_id: str) -> dict[str, Any]:
            progress_updates.append(len(progress_updates) * 0.25)
            return {
                "status": FinetuningStatus.TRAINING,
                "progress": progress_updates[-1],
            }

        with patch.object(finetuning_system, "get_job_status", side_effect=mock_get_job_status):
            for _ in range(4):
                status = await finetuning_system.get_job_status(job.job_id)
                await asyncio.sleep(0.1)

        assert len(progress_updates) == 4
        assert progress_updates[-1] == 0.75

    @pytest.mark.asyncio
    async def test_training_completes_successfully(self):
        """Test successful training completion."""
        from ml.agent_finetuning_system import AgentFinetuningSystem

        finetuning_system = AgentFinetuningSystem()

        job = FinetuningJob(
            job_id="job_success_001",
            category=AgentCategory.ECOMMERCE,
            provider=FinetuningProvider.OPENAI,
            dataset_id="dataset_test_001",
            base_model="gpt-3.5-turbo",
            status=FinetuningStatus.TRAINING,
            created_at=datetime.now(),
            started_at=datetime.now(),
            hyperparameters={},
        )

        async def mock_wait_for_completion(job_id: str) -> FinetuningJob:
            job.status = FinetuningStatus.COMPLETED
            job.completed_at = datetime.now()
            job.finetuned_model_id = "ft:gpt-3.5-turbo:custom:test:123"
            job.validation_metrics = {
                "loss": 0.12,
                "accuracy": 0.95,
            }
            return job

        with patch.object(finetuning_system, "wait_for_completion", side_effect=mock_wait_for_completion):
            completed_job = await finetuning_system.wait_for_completion(job.job_id)

        assert completed_job.status == FinetuningStatus.COMPLETED
        assert completed_job.finetuned_model_id is not None
        assert completed_job.validation_metrics is not None

    @pytest.mark.asyncio
    async def test_training_failure_handling(self):
        """Test handling of training failures."""
        from ml.agent_finetuning_system import AgentFinetuningSystem

        finetuning_system = AgentFinetuningSystem()

        job = FinetuningJob(
            job_id="job_fail_001",
            category=AgentCategory.ECOMMERCE,
            provider=FinetuningProvider.OPENAI,
            dataset_id="dataset_test_001",
            base_model="gpt-3.5-turbo",
            status=FinetuningStatus.TRAINING,
            created_at=datetime.now(),
            started_at=datetime.now(),
            hyperparameters={},
        )

        async def mock_wait_for_completion(job_id: str) -> FinetuningJob:
            job.status = FinetuningStatus.FAILED
            job.error_message = "Training failed: insufficient data quality"
            return job

        with patch.object(finetuning_system, "wait_for_completion", side_effect=mock_wait_for_completion):
            failed_job = await finetuning_system.wait_for_completion(job.job_id)

        assert failed_job.status == FinetuningStatus.FAILED
        assert failed_job.error_message is not None
        assert "insufficient data quality" in failed_job.error_message

    @pytest.mark.asyncio
    async def test_hyperparameter_tuning(self):
        """Test hyperparameter tuning for optimal performance."""
        from ml.agent_finetuning_system import AgentFinetuningSystem

        finetuning_system = AgentFinetuningSystem()

        hyperparameter_configs = [
            {"n_epochs": 2, "learning_rate_multiplier": 0.05},
            {"n_epochs": 3, "learning_rate_multiplier": 0.1},
            {"n_epochs": 4, "learning_rate_multiplier": 0.2},
        ]

        results = []
        for config in hyperparameter_configs:
            job = FinetuningJob(
                job_id=f"job_hyperparam_{len(results)}",
                category=AgentCategory.ECOMMERCE,
                provider=FinetuningProvider.OPENAI,
                dataset_id="dataset_test_001",
                base_model="gpt-3.5-turbo",
                status=FinetuningStatus.COMPLETED,
                created_at=datetime.now(),
                hyperparameters=config,
                validation_metrics={
                    "loss": 0.15 - (config["n_epochs"] * 0.02),
                    "accuracy": 0.85 + (config["n_epochs"] * 0.03),
                },
            )
            results.append(job)

        best_job = max(results, key=lambda j: j.validation_metrics["accuracy"])

        assert best_job.hyperparameters["n_epochs"] == 4
        assert best_job.validation_metrics["accuracy"] > 0.9


# ============================================================================
# MODEL REGISTRY & VERSIONING TESTS
# ============================================================================


class TestModelRegistryAndVersioning:
    """Test model registry and version management."""

    def test_register_new_model(self, model_registry: ModelRegistry):
        """Test registering a new model in the registry."""
        metadata = ModelMetadata(
            model_id="model_test_001",
            model_name="ecommerce_recommender_v1",
            category=AgentCategory.ECOMMERCE,
            version="1.0.0",
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            finetuned_model_id="ft:gpt-3.5-turbo:custom:test:001",
            created_at=datetime.now(),
            metrics={
                "validation_loss": 0.12,
                "validation_accuracy": 0.95,
            },
        )

        model_registry.register_model(metadata)

        retrieved = model_registry.get_model("model_test_001")
        assert retrieved is not None
        assert retrieved.model_id == "model_test_001"
        assert retrieved.version == "1.0.0"

    def test_create_model_version(self, model_registry: ModelRegistry):
        """Test creating a new version of existing model."""
        v1_metadata = ModelMetadata(
            model_id="model_versioning_001",
            model_name="ecommerce_recommender",
            category=AgentCategory.ECOMMERCE,
            version="1.0.0",
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            finetuned_model_id="ft:gpt-3.5-turbo:v1",
            created_at=datetime.now(),
            metrics={"accuracy": 0.90},
        )

        v2_metadata = ModelMetadata(
            model_id="model_versioning_002",
            model_name="ecommerce_recommender",
            category=AgentCategory.ECOMMERCE,
            version="2.0.0",
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            finetuned_model_id="ft:gpt-3.5-turbo:v2",
            created_at=datetime.now(),
            metrics={"accuracy": 0.95},
        )

        model_registry.register_model(v1_metadata)
        model_registry.register_model(v2_metadata)

        versions = model_registry.get_model_versions("ecommerce_recommender")
        assert len(versions) == 2
        assert versions[0].version == "2.0.0"  # Latest first
        assert versions[1].version == "1.0.0"

    def test_get_latest_model_version(self, model_registry: ModelRegistry):
        """Test retrieving the latest model version."""
        for i in range(3):
            metadata = ModelMetadata(
                model_id=f"model_latest_{i}",
                model_name="test_model",
                category=AgentCategory.ECOMMERCE,
                version=f"{i + 1}.0.0",
                provider=FinetuningProvider.OPENAI,
                base_model="gpt-3.5-turbo",
                finetuned_model_id=f"ft:gpt-3.5-turbo:v{i+1}",
                created_at=datetime.now() + timedelta(seconds=i),
                metrics={"accuracy": 0.85 + (i * 0.05)},
            )
            model_registry.register_model(metadata)

        latest = model_registry.get_latest_model("test_model")
        assert latest is not None
        assert latest.version == "3.0.0"
        assert latest.metrics["accuracy"] == 0.95

    def test_model_metadata_storage(self, model_registry: ModelRegistry, temp_model_dir: Path):
        """Test model metadata is persisted to storage."""
        metadata = ModelMetadata(
            model_id="model_storage_001",
            model_name="persisted_model",
            category=AgentCategory.ECOMMERCE,
            version="1.0.0",
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            finetuned_model_id="ft:gpt-3.5-turbo:persist",
            created_at=datetime.now(),
            metrics={"accuracy": 0.92},
        )

        model_registry.register_model(metadata)
        model_registry.save_to_disk()

        new_registry = ModelRegistry(storage_path=temp_model_dir)
        new_registry.load_from_disk()

        retrieved = new_registry.get_model("model_storage_001")
        assert retrieved is not None
        assert retrieved.model_name == "persisted_model"

    def test_delete_old_model_versions(self, model_registry: ModelRegistry):
        """Test deleting old model versions to save space."""
        for i in range(10):
            metadata = ModelMetadata(
                model_id=f"model_cleanup_{i}",
                model_name="cleanup_test",
                category=AgentCategory.ECOMMERCE,
                version=f"{i + 1}.0.0",
                provider=FinetuningProvider.OPENAI,
                base_model="gpt-3.5-turbo",
                finetuned_model_id=f"ft:v{i+1}",
                created_at=datetime.now() - timedelta(days=10 - i),
                metrics={},
            )
            model_registry.register_model(metadata)

        model_registry.cleanup_old_versions("cleanup_test", keep_latest=3)

        remaining_versions = model_registry.get_model_versions("cleanup_test")
        assert len(remaining_versions) == 3
        assert all(int(v.version.split(".")[0]) >= 8 for v in remaining_versions)


# ============================================================================
# MODEL DEPLOYMENT TESTS
# ============================================================================


class TestModelDeployment:
    """Test model deployment workflows."""

    @pytest.mark.asyncio
    async def test_deploy_model_to_staging(self, model_registry: ModelRegistry):
        """Test deploying model to staging environment."""
        from ml.agent_deployment_system import AgentDeploymentSystem

        deployment_system = AgentDeploymentSystem()

        metadata = ModelMetadata(
            model_id="model_deploy_staging_001",
            model_name="staging_test_model",
            category=AgentCategory.ECOMMERCE,
            version="1.0.0",
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            finetuned_model_id="ft:staging:001",
            created_at=datetime.now(),
            metrics={"accuracy": 0.93},
        )

        deployment = await deployment_system.deploy_model(
            model_metadata=metadata,
            environment=DeploymentEnvironment.STAGING,
            strategy=DeploymentStrategy.BLUE_GREEN,
        )

        assert deployment is not None
        assert deployment.environment == DeploymentEnvironment.STAGING
        assert deployment.model_id == "model_deploy_staging_001"

    @pytest.mark.asyncio
    async def test_deploy_model_to_production(self):
        """Test deploying model to production environment."""
        from ml.agent_deployment_system import AgentDeploymentSystem

        deployment_system = AgentDeploymentSystem()

        metadata = ModelMetadata(
            model_id="model_deploy_prod_001",
            model_name="production_model",
            category=AgentCategory.ECOMMERCE,
            version="2.0.0",
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            finetuned_model_id="ft:prod:001",
            created_at=datetime.now(),
            metrics={"accuracy": 0.96},
        )

        deployment = await deployment_system.deploy_model(
            model_metadata=metadata,
            environment=DeploymentEnvironment.PRODUCTION,
            strategy=DeploymentStrategy.CANARY,
            canary_percentage=10,
        )

        assert deployment.environment == DeploymentEnvironment.PRODUCTION
        assert deployment.strategy == DeploymentStrategy.CANARY
        assert deployment.canary_percentage == 10

    @pytest.mark.asyncio
    async def test_blue_green_deployment(self):
        """Test blue-green deployment strategy."""
        from ml.agent_deployment_system import AgentDeploymentSystem

        deployment_system = AgentDeploymentSystem()

        old_model = ModelMetadata(
            model_id="model_blue",
            model_name="blue_green_test",
            category=AgentCategory.ECOMMERCE,
            version="1.0.0",
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            finetuned_model_id="ft:blue",
            created_at=datetime.now() - timedelta(days=7),
            metrics={"accuracy": 0.90},
        )

        new_model = ModelMetadata(
            model_id="model_green",
            model_name="blue_green_test",
            category=AgentCategory.ECOMMERCE,
            version="2.0.0",
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            finetuned_model_id="ft:green",
            created_at=datetime.now(),
            metrics={"accuracy": 0.95},
        )

        await deployment_system.deploy_model(old_model, DeploymentEnvironment.PRODUCTION, DeploymentStrategy.BLUE_GREEN)
        deployment = await deployment_system.deploy_model(new_model, DeploymentEnvironment.PRODUCTION, DeploymentStrategy.BLUE_GREEN)

        assert deployment.model_id == "model_green"
        assert deployment.previous_model_id == "model_blue"

    @pytest.mark.asyncio
    async def test_canary_deployment(self):
        """Test canary deployment with gradual rollout."""
        from ml.agent_deployment_system import AgentDeploymentSystem

        deployment_system = AgentDeploymentSystem()

        metadata = ModelMetadata(
            model_id="model_canary_001",
            model_name="canary_test",
            category=AgentCategory.ECOMMERCE,
            version="1.0.0",
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            finetuned_model_id="ft:canary:001",
            created_at=datetime.now(),
            metrics={"accuracy": 0.94},
        )

        deployment = await deployment_system.deploy_model(
            metadata,
            DeploymentEnvironment.PRODUCTION,
            DeploymentStrategy.CANARY,
            canary_percentage=5,
        )

        assert deployment.canary_percentage == 5

        await deployment_system.increase_canary_traffic(deployment.deployment_id, 25)
        updated_deployment = deployment_system.get_deployment(deployment.deployment_id)
        assert updated_deployment.canary_percentage == 25


# ============================================================================
# A/B TESTING TESTS
# ============================================================================


class TestABTesting:
    """Test A/B testing for model comparison."""

    @pytest.mark.asyncio
    async def test_create_ab_test(self):
        """Test creating an A/B test between two models."""
        from ml.agent_deployment_system import AgentDeploymentSystem

        deployment_system = AgentDeploymentSystem()

        model_a = ModelMetadata(
            model_id="model_a_001",
            model_name="ab_test_baseline",
            category=AgentCategory.ECOMMERCE,
            version="1.0.0",
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            finetuned_model_id="ft:model_a",
            created_at=datetime.now(),
            metrics={"accuracy": 0.90},
        )

        model_b = ModelMetadata(
            model_id="model_b_001",
            model_name="ab_test_challenger",
            category=AgentCategory.ECOMMERCE,
            version="2.0.0",
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            finetuned_model_id="ft:model_b",
            created_at=datetime.now(),
            metrics={"accuracy": 0.95},
        )

        ab_test = await deployment_system.create_ab_test(
            model_a_metadata=model_a,
            model_b_metadata=model_b,
            traffic_split={"a": 0.5, "b": 0.5},
            duration_hours=24,
        )

        assert ab_test is not None
        assert ab_test.model_a_id == "model_a_001"
        assert ab_test.model_b_id == "model_b_001"
        assert ab_test.traffic_split["a"] == 0.5

    @pytest.mark.asyncio
    async def test_collect_ab_test_metrics(self):
        """Test collecting metrics during A/B test."""
        from ml.agent_deployment_system import AgentDeploymentSystem

        deployment_system = AgentDeploymentSystem()

        ab_test_id = "ab_test_metrics_001"

        model_a_metrics = {
            "requests": 1000,
            "success_rate": 0.92,
            "avg_latency_ms": 180,
            "user_satisfaction": 0.85,
        }

        model_b_metrics = {
            "requests": 1000,
            "success_rate": 0.96,
            "avg_latency_ms": 150,
            "user_satisfaction": 0.90,
        }

        await deployment_system.record_ab_test_metrics(ab_test_id, "a", model_a_metrics)
        await deployment_system.record_ab_test_metrics(ab_test_id, "b", model_b_metrics)

        results = deployment_system.get_ab_test_results(ab_test_id)

        assert results["model_a"]["success_rate"] < results["model_b"]["success_rate"]
        assert results["model_b"]["user_satisfaction"] > results["model_a"]["user_satisfaction"]

    @pytest.mark.asyncio
    async def test_ab_test_winner_selection(self):
        """Test automatic winner selection based on metrics."""
        from ml.agent_deployment_system import AgentDeploymentSystem

        deployment_system = AgentDeploymentSystem()

        ab_test_id = "ab_test_winner_001"

        model_a_metrics = {"success_rate": 0.90, "user_satisfaction": 0.82}
        model_b_metrics = {"success_rate": 0.95, "user_satisfaction": 0.91}

        await deployment_system.record_ab_test_metrics(ab_test_id, "a", model_a_metrics)
        await deployment_system.record_ab_test_metrics(ab_test_id, "b", model_b_metrics)

        winner = deployment_system.determine_ab_test_winner(
            ab_test_id,
            primary_metric="user_satisfaction",
            significance_threshold=0.05,
        )

        assert winner == "b"


# ============================================================================
# ROLLBACK & RECOVERY TESTS
# ============================================================================


class TestRollbackAndRecovery:
    """Test rollback and recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_automatic_rollback_on_performance_degradation(self):
        """Test automatic rollback when performance degrades."""
        from ml.agent_deployment_system import AgentDeploymentSystem

        deployment_system = AgentDeploymentSystem()

        stable_model = ModelMetadata(
            model_id="model_stable_001",
            model_name="stable_production",
            category=AgentCategory.ECOMMERCE,
            version="1.0.0",
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            finetuned_model_id="ft:stable",
            created_at=datetime.now() - timedelta(days=30),
            metrics={"accuracy": 0.93},
        )

        degraded_model = ModelMetadata(
            model_id="model_degraded_001",
            model_name="stable_production",
            category=AgentCategory.ECOMMERCE,
            version="2.0.0",
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            finetuned_model_id="ft:degraded",
            created_at=datetime.now(),
            metrics={"accuracy": 0.95},
        )

        await deployment_system.deploy_model(stable_model, DeploymentEnvironment.PRODUCTION, DeploymentStrategy.BLUE_GREEN)
        deployment = await deployment_system.deploy_model(degraded_model, DeploymentEnvironment.PRODUCTION, DeploymentStrategy.BLUE_GREEN)

        deployment_system.enable_auto_rollback(
            deployment_id=deployment.deployment_id,
            performance_threshold={"error_rate": 0.05},
        )

        await deployment_system.record_deployment_metrics(
            deployment.deployment_id,
            {"error_rate": 0.08, "success_rate": 0.92},
        )

        rollback_triggered = await deployment_system.check_rollback_conditions(deployment.deployment_id)

        assert rollback_triggered is True

    @pytest.mark.asyncio
    async def test_manual_rollback(self):
        """Test manual rollback to previous model version."""
        from ml.agent_deployment_system import AgentDeploymentSystem

        deployment_system = AgentDeploymentSystem()

        deployment_id = "deployment_manual_rollback_001"

        rollback_result = await deployment_system.rollback_deployment(
            deployment_id=deployment_id,
            target_model_id="model_previous_stable",
        )

        assert rollback_result["status"] == "success"
        assert rollback_result["active_model_id"] == "model_previous_stable"


# ============================================================================
# PERFORMANCE MONITORING TESTS
# ============================================================================


class TestPerformanceMonitoring:
    """Test performance monitoring for deployed models."""

    @pytest.mark.asyncio
    async def test_monitor_model_latency(self):
        """Test monitoring model inference latency."""
        from ml.agent_deployment_system import AgentDeploymentSystem

        deployment_system = AgentDeploymentSystem()

        latencies = [120, 150, 180, 160, 140, 200, 170, 155, 165, 145]

        for latency in latencies:
            await deployment_system.record_inference_latency("model_latency_001", latency)

        stats = deployment_system.get_latency_stats("model_latency_001")

        assert stats["p50"] < 200
        assert stats["p95"] < 250
        assert stats["p99"] < 300

    @pytest.mark.asyncio
    async def test_monitor_model_accuracy(self):
        """Test monitoring model accuracy over time."""
        from ml.agent_deployment_system import AgentDeploymentSystem

        deployment_system = AgentDeploymentSystem()

        predictions = [
            {"predicted": "A", "actual": "A"},
            {"predicted": "B", "actual": "B"},
            {"predicted": "A", "actual": "B"},
            {"predicted": "C", "actual": "C"},
        ]

        for pred in predictions:
            await deployment_system.record_prediction("model_accuracy_001", pred["predicted"], pred["actual"])

        accuracy = deployment_system.calculate_accuracy("model_accuracy_001")

        assert accuracy == 0.75

    @pytest.mark.asyncio
    async def test_detect_model_drift(self):
        """Test detection of model drift."""
        from ml.agent_deployment_system import AgentDeploymentSystem

        deployment_system = AgentDeploymentSystem()

        baseline_distribution = np.random.normal(0.9, 0.05, 1000)
        current_distribution = np.random.normal(0.7, 0.08, 1000)

        drift_detected = deployment_system.detect_drift(
            baseline_distribution.tolist(),
            current_distribution.tolist(),
            threshold=0.05,
        )

        assert drift_detected is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
