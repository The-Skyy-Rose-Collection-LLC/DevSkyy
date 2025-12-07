"""
Comprehensive tests for ml/agent_finetuning_system.py

Target: 70%+ coverage

Tests cover:
- Agent categories and enums
- Performance snapshot collection
- Dataset preparation and splitting
- Finetuning job creation and execution
- Provider-specific finetuning (OpenAI, Anthropic)
- Statistics and status tracking
- Error handling
"""

import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path

import numpy as np
import pytest

from ml.agent_finetuning_system import (
    AgentCategory,
    AgentFinetuningSystem,
    AgentPerformanceSnapshot,
    FinetuningConfig,
    FinetuningDataset,
    FinetuningJob,
    FinetuningProvider,
    FinetuningStatus,
    get_finetuning_system,
)


class TestAgentCategory:
    """Test AgentCategory enum"""

    def test_agent_categories(self):
        """Test all agent categories"""
        assert AgentCategory.CORE_SECURITY == "core_security"
        assert AgentCategory.AI_INTELLIGENCE == "ai_intelligence"
        assert AgentCategory.ECOMMERCE == "ecommerce"
        assert AgentCategory.MARKETING_BRAND == "marketing_brand"
        assert AgentCategory.WORDPRESS_CMS == "wordpress_cms"
        assert AgentCategory.CUSTOMER_SERVICE == "customer_service"
        assert AgentCategory.SPECIALIZED == "specialized"

    def test_category_values(self):
        """Test category string values"""
        categories = [cat.value for cat in AgentCategory]
        assert len(categories) == 7


class TestFinetuningProvider:
    """Test FinetuningProvider enum"""

    def test_providers(self):
        """Test all providers"""
        assert FinetuningProvider.OPENAI == "openai"
        assert FinetuningProvider.ANTHROPIC == "anthropic"
        assert FinetuningProvider.CUSTOM == "custom"
        assert FinetuningProvider.HUGGINGFACE == "huggingface"


class TestFinetuningStatus:
    """Test FinetuningStatus enum"""

    def test_statuses(self):
        """Test all statuses"""
        assert FinetuningStatus.PENDING == "pending"
        assert FinetuningStatus.COLLECTING_DATA == "collecting_data"
        assert FinetuningStatus.PREPARING_DATASET == "preparing_dataset"
        assert FinetuningStatus.TRAINING == "training"
        assert FinetuningStatus.VALIDATING == "validating"
        assert FinetuningStatus.COMPLETED == "completed"
        assert FinetuningStatus.FAILED == "failed"
        assert FinetuningStatus.CANCELLED == "cancelled"


class TestAgentPerformanceSnapshot:
    """Test AgentPerformanceSnapshot dataclass"""

    def test_create_snapshot(self):
        """Test creating performance snapshot"""
        snapshot = AgentPerformanceSnapshot(
            agent_id="agent_123",
            agent_name="test_agent",
            category=AgentCategory.CORE_SECURITY,
            timestamp=datetime.now(),
            task_type="code_scan",
            input_data={"code": "test"},
            output_data={"result": "clean"},
            success=True,
            performance_score=0.95,
            execution_time_ms=123.45,
            tokens_used=150,
        )

        assert snapshot.agent_id == "agent_123"
        assert snapshot.category == AgentCategory.CORE_SECURITY
        assert snapshot.success is True
        assert snapshot.performance_score == 0.95

    def test_snapshot_with_feedback(self):
        """Test snapshot with user feedback"""
        snapshot = AgentPerformanceSnapshot(
            agent_id="agent_123",
            agent_name="test_agent",
            category=AgentCategory.ECOMMERCE,
            timestamp=datetime.now(),
            task_type="product_import",
            input_data={},
            output_data={},
            success=True,
            performance_score=0.9,
            execution_time_ms=100.0,
            tokens_used=100,
            user_feedback=0.85,
        )

        assert snapshot.user_feedback == 0.85

    def test_snapshot_with_metadata(self):
        """Test snapshot with metadata"""
        snapshot = AgentPerformanceSnapshot(
            agent_id="agent_123",
            agent_name="test_agent",
            category=AgentCategory.AI_INTELLIGENCE,
            timestamp=datetime.now(),
            task_type="model_comparison",
            input_data={},
            output_data={},
            success=True,
            performance_score=0.92,
            execution_time_ms=200.0,
            tokens_used=500,
            metadata={"version": "2.0", "model": "gpt-4"},
        )

        assert snapshot.metadata["version"] == "2.0"


class TestFinetuningConfig:
    """Test FinetuningConfig model"""

    def test_create_config(self):
        """Test creating finetuning config"""
        config = FinetuningConfig(
            category=AgentCategory.CORE_SECURITY,
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-4o-mini",
        )

        assert config.category == AgentCategory.CORE_SECURITY
        assert config.provider == FinetuningProvider.OPENAI
        assert config.n_epochs == 3  # default
        assert config.batch_size == 32  # default

    def test_config_with_hyperparameters(self):
        """Test config with custom hyperparameters"""
        config = FinetuningConfig(
            category=AgentCategory.ECOMMERCE,
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-3.5-turbo",
            n_epochs=5,
            batch_size=64,
            learning_rate=0.001,
        )

        assert config.n_epochs == 5
        assert config.batch_size == 64
        assert config.learning_rate == 0.001

    def test_config_validation(self):
        """Test config validation"""
        with pytest.raises(Exception):  # Pydantic validation error
            FinetuningConfig(
                category=AgentCategory.CORE_SECURITY,
                provider=FinetuningProvider.OPENAI,
                base_model="gpt-4",
                n_epochs=0,  # Invalid: must be >= 1
            )


class TestFinetuningJob:
    """Test FinetuningJob model"""

    def test_create_job(self):
        """Test creating finetuning job"""
        config = FinetuningConfig(
            category=AgentCategory.CORE_SECURITY,
            provider=FinetuningProvider.OPENAI,
            base_model="gpt-4o-mini",
        )

        job = FinetuningJob(
            job_id="job_123",
            category=AgentCategory.CORE_SECURITY,
            config=config,
            status=FinetuningStatus.PENDING,
            created_at=datetime.now(),
        )

        assert job.job_id == "job_123"
        assert job.status == FinetuningStatus.PENDING
        assert job.training_samples == 0


class TestAgentFinetuningSystem:
    """Test AgentFinetuningSystem"""

    def test_init(self, temp_dir):
        """Test system initialization"""
        system = AgentFinetuningSystem(data_dir=temp_dir)

        assert system.data_dir.exists()
        assert len(system.datasets) == 0
        assert len(system.jobs) == 0
        assert len(system.performance_snapshots) == 0

    @pytest.mark.asyncio
    async def test_collect_performance_snapshot(self, finetuning_system):
        """Test collecting performance snapshot"""
        await finetuning_system.collect_performance_snapshot(
            agent_id="agent_123",
            agent_name="test_agent",
            category=AgentCategory.CORE_SECURITY,
            task_type="code_scan",
            input_data={"code": "print('hello')"},
            output_data={"issues": []},
            success=True,
            performance_score=0.95,
            execution_time_ms=123.45,
            tokens_used=150,
        )

        assert len(finetuning_system.performance_snapshots) == 1
        snapshot = finetuning_system.performance_snapshots[0]
        assert snapshot.agent_id == "agent_123"
        assert snapshot.success is True

    @pytest.mark.asyncio
    async def test_collect_snapshot_with_feedback(self, finetuning_system):
        """Test collecting snapshot with user feedback"""
        await finetuning_system.collect_performance_snapshot(
            agent_id="agent_123",
            agent_name="test_agent",
            category=AgentCategory.ECOMMERCE,
            task_type="product_import",
            input_data={},
            output_data={},
            success=True,
            performance_score=0.9,
            execution_time_ms=100.0,
            tokens_used=100,
            user_feedback=0.85,
        )

        snapshot = finetuning_system.performance_snapshots[0]
        assert snapshot.user_feedback == 0.85

    @pytest.mark.asyncio
    async def test_flush_snapshots_to_disk(self, finetuning_system):
        """Test flushing snapshots to disk"""
        # Add multiple snapshots
        for i in range(20):
            await finetuning_system.collect_performance_snapshot(
                agent_id=f"agent_{i}",
                agent_name=f"agent_{i}",
                category=AgentCategory.CORE_SECURITY,
                task_type="test",
                input_data={},
                output_data={},
                success=True,
                performance_score=0.9,
                execution_time_ms=100.0,
                tokens_used=100,
            )

        # Flush to disk
        await finetuning_system._flush_snapshots_to_disk()

        # Check file created
        files = list(finetuning_system.data_dir.glob("snapshots_*.jsonl"))
        assert len(files) > 0

        # Check snapshots cleared
        assert len(finetuning_system.performance_snapshots) == 0

    @pytest.mark.asyncio
    async def test_auto_flush_on_max_snapshots(self, finetuning_system):
        """Test auto-flush when max snapshots reached"""
        finetuning_system.max_snapshots_in_memory = 10

        # Add more than max
        for i in range(15):
            await finetuning_system.collect_performance_snapshot(
                agent_id=f"agent_{i}",
                agent_name=f"agent_{i}",
                category=AgentCategory.CORE_SECURITY,
                task_type="test",
                input_data={},
                output_data={},
                success=True,
                performance_score=0.9,
                execution_time_ms=100.0,
                tokens_used=100,
            )

        # Should have flushed
        files = list(finetuning_system.data_dir.glob("snapshots_*.jsonl"))
        assert len(files) > 0

    @pytest.mark.asyncio
    async def test_prepare_dataset(self, finetuning_system, agent_category):
        """Test dataset preparation"""
        # Collect sufficient snapshots
        for i in range(150):
            await finetuning_system.collect_performance_snapshot(
                agent_id="agent_1",
                agent_name="test_agent",
                category=agent_category,
                task_type=["task_a", "task_b", "task_c"][i % 3],
                input_data={"input": i},
                output_data={"output": i},
                success=i % 10 != 0,  # 90% success rate
                performance_score=0.7 + (i % 30) / 100.0,
                execution_time_ms=100.0,
                tokens_used=100,
            )

        dataset = await finetuning_system.prepare_dataset(
            category=agent_category,
            min_samples=100,
            max_samples=200,
            quality_threshold=0.7,
        )

        assert dataset.category == agent_category
        assert len(dataset.train_split) > 0
        assert len(dataset.val_split) > 0
        assert len(dataset.test_split) > 0
        assert dataset.statistics["total_samples"] > 0

    @pytest.mark.asyncio
    async def test_prepare_dataset_insufficient_data(self, finetuning_system):
        """Test dataset preparation with insufficient data"""
        # Collect few snapshots
        for i in range(10):
            await finetuning_system.collect_performance_snapshot(
                agent_id="agent_1",
                agent_name="test_agent",
                category=AgentCategory.CORE_SECURITY,
                task_type="test",
                input_data={},
                output_data={},
                success=True,
                performance_score=0.9,
                execution_time_ms=100.0,
                tokens_used=100,
            )

        with pytest.raises(ValueError, match="Insufficient data"):
            await finetuning_system.prepare_dataset(
                category=AgentCategory.CORE_SECURITY,
                min_samples=100,
            )

    @pytest.mark.asyncio
    async def test_prepare_dataset_with_failures(self, finetuning_system):
        """Test dataset includes failure examples"""
        # Collect snapshots with mix of success/failure
        for i in range(150):
            await finetuning_system.collect_performance_snapshot(
                agent_id="agent_1",
                agent_name="test_agent",
                category=AgentCategory.ECOMMERCE,
                task_type="test",
                input_data={},
                output_data={},
                success=i % 5 != 0,  # 80% success rate
                performance_score=0.8,
                execution_time_ms=100.0,
                tokens_used=100,
            )

        dataset = await finetuning_system.prepare_dataset(
            category=AgentCategory.ECOMMERCE,
            min_samples=100,
        )

        # Should include some failures (up to 10%)
        failure_count = sum(1 for s in dataset.snapshots if not s.success)
        assert failure_count > 0

    @pytest.mark.asyncio
    async def test_dataset_train_val_test_split(self, finetuning_system):
        """Test dataset split ratios"""
        # Collect snapshots
        for i in range(200):
            await finetuning_system.collect_performance_snapshot(
                agent_id="agent_1",
                agent_name="test_agent",
                category=AgentCategory.AI_INTELLIGENCE,
                task_type="test",
                input_data={},
                output_data={},
                success=True,
                performance_score=0.9,
                execution_time_ms=100.0,
                tokens_used=100,
            )

        dataset = await finetuning_system.prepare_dataset(
            category=AgentCategory.AI_INTELLIGENCE,
        )

        total = len(dataset.train_split) + len(dataset.val_split) + len(dataset.test_split)

        # Check approximate split ratios (80/10/10)
        assert len(dataset.train_split) / total > 0.75
        assert len(dataset.train_split) / total < 0.85
        assert len(dataset.val_split) / total > 0.05
        assert len(dataset.test_split) / total > 0.05

    @pytest.mark.asyncio
    async def test_calculate_dataset_stats(self, finetuning_system):
        """Test dataset statistics calculation"""
        # Prepare dataset
        for i in range(150):
            await finetuning_system.collect_performance_snapshot(
                agent_id="agent_1",
                agent_name="test_agent",
                category=AgentCategory.MARKETING_BRAND,
                task_type=["seo", "content"][i % 2],
                input_data={},
                output_data={},
                success=i % 10 != 0,
                performance_score=0.8 + (i % 20) / 100.0,
                execution_time_ms=50.0 + i,
                tokens_used=100 + i * 10,
            )

        dataset = await finetuning_system.prepare_dataset(
            category=AgentCategory.MARKETING_BRAND,
        )

        stats = dataset.statistics

        assert "total_samples" in stats
        assert "train_samples" in stats
        assert "val_samples" in stats
        assert "test_samples" in stats
        assert "success_rate" in stats
        assert "avg_performance_score" in stats
        assert "avg_execution_time_ms" in stats
        assert "task_type_distribution" in stats
        assert "date_range" in stats

    @pytest.mark.asyncio
    async def test_create_finetuning_job(self, finetuning_system, sample_finetuning_config):
        """Test creating finetuning job"""
        # Prepare dataset first
        for i in range(150):
            await finetuning_system.collect_performance_snapshot(
                agent_id="agent_1",
                agent_name="test_agent",
                category=AgentCategory.CORE_SECURITY,
                task_type="test",
                input_data={},
                output_data={},
                success=True,
                performance_score=0.9,
                execution_time_ms=100.0,
                tokens_used=100,
            )

        await finetuning_system.prepare_dataset(category=AgentCategory.CORE_SECURITY)

        job = await finetuning_system.create_finetuning_job(
            category=AgentCategory.CORE_SECURITY,
            config=sample_finetuning_config,
        )

        assert job.job_id in finetuning_system.jobs
        assert job.status == FinetuningStatus.PENDING
        assert job.training_samples > 0

    @pytest.mark.asyncio
    async def test_create_job_without_dataset(self, finetuning_system, sample_finetuning_config):
        """Test creating job without dataset raises error"""
        with pytest.raises(ValueError, match="No dataset prepared"):
            await finetuning_system.create_finetuning_job(
                category=AgentCategory.CORE_SECURITY,
                config=sample_finetuning_config,
            )

    @pytest.mark.asyncio
    async def test_prepare_openai_dataset(self, finetuning_system):
        """Test preparing OpenAI-format dataset"""
        # Create dataset
        snapshots = []
        for i in range(10):
            snapshots.append(
                AgentPerformanceSnapshot(
                    agent_id="agent_1",
                    agent_name="test_agent",
                    category=AgentCategory.CORE_SECURITY,
                    timestamp=datetime.now(),
                    task_type="test",
                    input_data={"input": f"test {i}"},
                    output_data={"output": f"result {i}"},
                    success=True,
                    performance_score=0.9,
                    execution_time_ms=100.0,
                    tokens_used=100,
                )
            )

        dataset = FinetuningDataset(
            dataset_id="test_dataset",
            category=AgentCategory.CORE_SECURITY,
            created_at=datetime.now(),
            snapshots=snapshots,
            train_split=snapshots,
            val_split=[],
            test_split=[],
        )

        output_file = await finetuning_system._prepare_openai_dataset(dataset)

        # Check file exists
        assert Path(output_file).exists()

        # Check format
        with open(output_file) as f:
            lines = f.readlines()
            assert len(lines) == 10

            # Check JSON format
            example = json.loads(lines[0])
            assert "messages" in example
            assert len(example["messages"]) == 3  # system, user, assistant

    @pytest.mark.asyncio
    async def test_get_job_status(self, finetuning_system, sample_finetuning_config):
        """Test getting job status"""
        # Prepare dataset
        for i in range(150):
            await finetuning_system.collect_performance_snapshot(
                agent_id="agent_1",
                agent_name="test_agent",
                category=AgentCategory.CORE_SECURITY,
                task_type="test",
                input_data={},
                output_data={},
                success=True,
                performance_score=0.9,
                execution_time_ms=100.0,
                tokens_used=100,
            )

        await finetuning_system.prepare_dataset(category=AgentCategory.CORE_SECURITY)

        job = await finetuning_system.create_finetuning_job(
            category=AgentCategory.CORE_SECURITY,
            config=sample_finetuning_config,
        )

        # Get status
        status = finetuning_system.get_job_status(job.job_id)

        assert status is not None
        assert status.job_id == job.job_id

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, finetuning_system):
        """Test getting status for non-existent job"""
        status = finetuning_system.get_job_status("nonexistent_job")
        assert status is None

    @pytest.mark.asyncio
    async def test_get_category_jobs(self, finetuning_system, sample_finetuning_config):
        """Test getting jobs by category"""
        # Prepare datasets for multiple categories
        for category in [AgentCategory.CORE_SECURITY, AgentCategory.ECOMMERCE]:
            for i in range(150):
                await finetuning_system.collect_performance_snapshot(
                    agent_id="agent_1",
                    agent_name="test_agent",
                    category=category,
                    task_type="test",
                    input_data={},
                    output_data={},
                    success=True,
                    performance_score=0.9,
                    execution_time_ms=100.0,
                    tokens_used=100,
                )

            await finetuning_system.prepare_dataset(category=category)

            config = FinetuningConfig(
                category=category,
                provider=FinetuningProvider.OPENAI,
                base_model="gpt-4o-mini",
            )

            await finetuning_system.create_finetuning_job(category=category, config=config)

        # Get jobs for specific category
        security_jobs = finetuning_system.get_category_jobs(AgentCategory.CORE_SECURITY)
        assert len(security_jobs) == 1
        assert security_jobs[0].category == AgentCategory.CORE_SECURITY

    @pytest.mark.asyncio
    async def test_get_system_statistics(self, finetuning_system):
        """Test getting system statistics"""
        # Collect some snapshots
        for i in range(50):
            await finetuning_system.collect_performance_snapshot(
                agent_id="agent_1",
                agent_name="test_agent",
                category=AgentCategory.CORE_SECURITY,
                task_type="test",
                input_data={},
                output_data={},
                success=True,
                performance_score=0.9,
                execution_time_ms=100.0,
                tokens_used=100,
            )

        stats = finetuning_system.get_system_statistics()

        assert "total_snapshots" in stats
        assert "datasets_prepared" in stats
        assert "active_jobs" in stats
        assert "completed_jobs" in stats
        assert "failed_jobs" in stats
        assert "total_cost_usd" in stats

    @pytest.mark.asyncio
    async def test_load_snapshots_from_disk(self, finetuning_system):
        """Test loading snapshots from disk files"""
        # Create and flush snapshots
        for i in range(50):
            await finetuning_system.collect_performance_snapshot(
                agent_id="agent_1",
                agent_name="test_agent",
                category=AgentCategory.CORE_SECURITY,
                task_type="test",
                input_data={"test": i},
                output_data={"result": i},
                success=True,
                performance_score=0.9,
                execution_time_ms=100.0,
                tokens_used=100,
            )

        await finetuning_system._flush_snapshots_to_disk()

        # Load from disk
        loaded = await finetuning_system._load_snapshots_for_category(
            AgentCategory.CORE_SECURITY,
            time_range_days=30,
        )

        assert len(loaded) > 0

    @pytest.mark.asyncio
    async def test_load_snapshots_time_filter(self, finetuning_system):
        """Test loading snapshots filters by time range"""
        # Create old and new snapshots
        old_snapshot = AgentPerformanceSnapshot(
            agent_id="agent_1",
            agent_name="test_agent",
            category=AgentCategory.CORE_SECURITY,
            timestamp=datetime.now() - timedelta(days=60),  # 60 days old
            task_type="test",
            input_data={},
            output_data={},
            success=True,
            performance_score=0.9,
            execution_time_ms=100.0,
            tokens_used=100,
        )

        finetuning_system.performance_snapshots.append(old_snapshot)

        # Load with 30-day filter
        loaded = await finetuning_system._load_snapshots_for_category(
            AgentCategory.CORE_SECURITY,
            time_range_days=30,
        )

        # Old snapshot should be filtered out
        assert all(s.timestamp > datetime.now() - timedelta(days=30) for s in loaded)


class TestGetFinetuningSystem:
    """Test get_finetuning_system function"""

    def test_get_finetuning_system(self):
        """Test getting global finetuning system"""
        system = get_finetuning_system()
        assert isinstance(system, AgentFinetuningSystem)

    def test_get_finetuning_system_singleton(self):
        """Test system is singleton"""
        system1 = get_finetuning_system()
        system2 = get_finetuning_system()
        assert system1 is system2
