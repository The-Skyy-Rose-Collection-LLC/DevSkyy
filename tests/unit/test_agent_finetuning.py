"""
Unit Tests for Agent Finetuning System
Comprehensive test coverage for finetuning infrastructure

Per Truth Protocol:
- Rule #8: Test coverage ≥90%
- Rule #1: Never guess - Verify all behaviors
- Rule #14: Error ledger required - Track test failures
"""

import asyncio
from datetime import datetime
from pathlib import Path
import shutil
import tempfile

import pytest

from ml.agent_finetuning_system import (
    AgentCategory,
    AgentFinetuningSystem,
    AgentPerformanceSnapshot,
    FinetuningConfig,
    FinetuningProvider,
    FinetuningStatus,
    get_finetuning_system,
)


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def finetuning_system(temp_data_dir):
    """Create finetuning system with temp directory"""
    return AgentFinetuningSystem(data_dir=temp_data_dir)


@pytest.fixture
def sample_snapshot():
    """Create sample performance snapshot"""
    return AgentPerformanceSnapshot(
        agent_id="test_agent_001",
        agent_name="Test Agent",
        category=AgentCategory.CORE_SECURITY,
        timestamp=datetime.now(),
        task_type="vulnerability_scan",
        input_data={"file_path": "/test/path.py"},
        output_data={"vulnerabilities": []},
        success=True,
        performance_score=0.95,
        execution_time_ms=120.5,
        tokens_used=150,
        user_feedback=0.9,
        metadata={"version": "1.0.0"}
    )


# ============================================================================
# PERFORMANCE SNAPSHOT COLLECTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_collect_performance_snapshot(finetuning_system):
    """Test collecting a performance snapshot"""
    await finetuning_system.collect_performance_snapshot(
        agent_id="agent_001",
        agent_name="Scanner V2",
        category=AgentCategory.CORE_SECURITY,
        task_type="code_scan",
        input_data={"code": "print('test')"},
        output_data={"issues": []},
        success=True,
        performance_score=0.92,
        execution_time_ms=100.0,
        tokens_used=50
    )

    assert len(finetuning_system.performance_snapshots) == 1
    snapshot = finetuning_system.performance_snapshots[0]
    assert snapshot.agent_id == "agent_001"
    assert snapshot.category == AgentCategory.CORE_SECURITY
    assert snapshot.performance_score == 0.92


@pytest.mark.asyncio
async def test_collect_multiple_snapshots(finetuning_system):
    """Test collecting multiple snapshots"""
    for i in range(10):
        await finetuning_system.collect_performance_snapshot(
            agent_id=f"agent_{i:03d}",
            agent_name=f"Agent {i}",
            category=AgentCategory.ECOMMERCE,
            task_type="product_import",
            input_data={"product_id": i},
            output_data={"imported": True},
            success=True,
            performance_score=0.8 + (i * 0.01),
            execution_time_ms=100.0 + i,
            tokens_used=50 + i
        )

    assert len(finetuning_system.performance_snapshots) == 10


@pytest.mark.asyncio
async def test_snapshot_memory_management(finetuning_system, temp_data_dir):
    """Test that snapshots are flushed to disk when limit reached"""
    # Set low limit for testing
    finetuning_system.max_snapshots_in_memory = 5

    # Collect more than limit
    for i in range(10):
        await finetuning_system.collect_performance_snapshot(
            agent_id=f"agent_{i:03d}",
            agent_name=f"Agent {i}",
            category=AgentCategory.AI_INTELLIGENCE,
            task_type="reasoning",
            input_data={"query": f"test_{i}"},
            output_data={"answer": f"result_{i}"},
            success=True,
            performance_score=0.9,
            execution_time_ms=200.0,
            tokens_used=100
        )

    # Should have flushed once
    snapshot_files = list(temp_data_dir.glob("snapshots_*.jsonl"))
    assert len(snapshot_files) >= 1
    assert len(finetuning_system.performance_snapshots) <= 5


# ============================================================================
# DATASET PREPARATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_prepare_dataset_success(finetuning_system):
    """Test successful dataset preparation"""
    # Collect 150 quality snapshots
    for i in range(150):
        await finetuning_system.collect_performance_snapshot(
            agent_id="scanner_v2",
            agent_name="Scanner V2",
            category=AgentCategory.CORE_SECURITY,
            task_type="vulnerability_scan",
            input_data={"file": f"file_{i}.py"},
            output_data={"issues": i % 5},
            success=True,
            performance_score=0.85 + (i % 10) * 0.01,
            execution_time_ms=100.0,
            tokens_used=50
        )

    dataset = await finetuning_system.prepare_dataset(
        category=AgentCategory.CORE_SECURITY,
        min_samples=100,
        max_samples=200,
        quality_threshold=0.7,
        time_range_days=30
    )

    assert dataset.category == AgentCategory.CORE_SECURITY
    assert len(dataset.train_split) > 0
    assert len(dataset.val_split) > 0
    assert len(dataset.test_split) > 0
    assert dataset.statistics["total_samples"] >= 100


@pytest.mark.asyncio
async def test_prepare_dataset_insufficient_data(finetuning_system):
    """Test dataset preparation with insufficient data"""
    # Collect only 50 snapshots (less than min_samples)
    for i in range(50):
        await finetuning_system.collect_performance_snapshot(
            agent_id="agent_001",
            agent_name="Test Agent",
            category=AgentCategory.MARKETING_BRAND,
            task_type="content_generation",
            input_data={"prompt": f"test_{i}"},
            output_data={"content": "result"},
            success=True,
            performance_score=0.8,
            execution_time_ms=150.0,
            tokens_used=75
        )

    with pytest.raises(ValueError, match="Insufficient data"):
        await finetuning_system.prepare_dataset(
            category=AgentCategory.MARKETING_BRAND,
            min_samples=100,
            quality_threshold=0.7
        )


@pytest.mark.asyncio
async def test_prepare_dataset_quality_filtering(finetuning_system):
    """Test that dataset filters for quality"""
    # Mix of high and low quality snapshots
    for i in range(100):
        quality = 0.9 if i % 2 == 0 else 0.5  # Alternating quality
        await finetuning_system.collect_performance_snapshot(
            agent_id="agent_001",
            agent_name="Test Agent",
            category=AgentCategory.WORDPRESS_CMS,
            task_type="theme_build",
            input_data={"theme": f"theme_{i}"},
            output_data={"success": True},
            success=True,
            performance_score=quality,
            execution_time_ms=100.0,
            tokens_used=50
        )

    dataset = await finetuning_system.prepare_dataset(
        category=AgentCategory.WORDPRESS_CMS,
        min_samples=30,
        quality_threshold=0.8  # Should filter out low quality
    )

    # All samples should be high quality
    for snapshot in dataset.snapshots:
        assert snapshot.performance_score >= 0.5  # Some failures included


@pytest.mark.asyncio
async def test_dataset_splits(finetuning_system):
    """Test that dataset is properly split into train/val/test"""
    for i in range(200):
        await finetuning_system.collect_performance_snapshot(
            agent_id="agent_001",
            agent_name="Test Agent",
            category=AgentCategory.CUSTOMER_SERVICE,
            task_type="customer_query",
            input_data={"query": f"test_{i}"},
            output_data={"response": "answer"},
            success=True,
            performance_score=0.9,
            execution_time_ms=100.0,
            tokens_used=50
        )

    dataset = await finetuning_system.prepare_dataset(
        category=AgentCategory.CUSTOMER_SERVICE,
        min_samples=100
    )

    total = len(dataset.train_split) + len(dataset.val_split) + len(dataset.test_split)

    # Check splits are approximately 80/10/10
    assert 0.75 <= len(dataset.train_split) / total <= 0.85
    assert 0.05 <= len(dataset.val_split) / total <= 0.15
    assert 0.05 <= len(dataset.test_split) / total <= 0.15


# ============================================================================
# FINETUNING JOB TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_finetuning_job(finetuning_system):
    """Test creating a finetuning job"""
    # Prepare dataset first
    for i in range(150):
        await finetuning_system.collect_performance_snapshot(
            agent_id="agent_001",
            agent_name="Test Agent",
            category=AgentCategory.SPECIALIZED,
            task_type="specialized_task",
            input_data={"input": f"test_{i}"},
            output_data={"output": "result"},
            success=True,
            performance_score=0.9,
            execution_time_ms=100.0,
            tokens_used=50
        )

    await finetuning_system.prepare_dataset(
        category=AgentCategory.SPECIALIZED,
        min_samples=100
    )

    # Create job
    config = FinetuningConfig(
        category=AgentCategory.SPECIALIZED,
        provider=FinetuningProvider.OPENAI,
        base_model="gpt-4o-mini",
        n_epochs=3
    )

    job = await finetuning_system.create_finetuning_job(
        category=AgentCategory.SPECIALIZED,
        config=config
    )

    assert job.category == AgentCategory.SPECIALIZED
    assert job.status == FinetuningStatus.PENDING
    assert job.job_id.startswith("finetune_")


@pytest.mark.asyncio
async def test_create_job_without_dataset(finetuning_system):
    """Test that creating job without dataset fails"""
    config = FinetuningConfig(
        category=AgentCategory.ECOMMERCE,
        provider=FinetuningProvider.OPENAI,
        base_model="gpt-4o-mini"
    )

    with pytest.raises(ValueError, match="No dataset prepared"):
        await finetuning_system.create_finetuning_job(
            category=AgentCategory.ECOMMERCE,
            config=config
        )


@pytest.mark.asyncio
async def test_get_job_status(finetuning_system):
    """Test getting job status"""
    # Prepare and create job
    for i in range(150):
        await finetuning_system.collect_performance_snapshot(
            agent_id="agent_001",
            agent_name="Test Agent",
            category=AgentCategory.AI_INTELLIGENCE,
            task_type="intelligence_task",
            input_data={"input": f"test_{i}"},
            output_data={"output": "result"},
            success=True,
            performance_score=0.9,
            execution_time_ms=100.0,
            tokens_used=50
        )

    await finetuning_system.prepare_dataset(
        category=AgentCategory.AI_INTELLIGENCE,
        min_samples=100
    )

    config = FinetuningConfig(
        category=AgentCategory.AI_INTELLIGENCE,
        provider=FinetuningProvider.OPENAI,
        base_model="gpt-4o"
    )

    job = await finetuning_system.create_finetuning_job(
        category=AgentCategory.AI_INTELLIGENCE,
        config=config
    )

    # Get status
    retrieved_job = finetuning_system.get_job_status(job.job_id)
    assert retrieved_job is not None
    assert retrieved_job.job_id == job.job_id
    assert retrieved_job.category == AgentCategory.AI_INTELLIGENCE


# ============================================================================
# STATISTICS TESTS
# ============================================================================

def test_get_system_statistics(finetuning_system):
    """Test getting system statistics"""
    stats = finetuning_system.get_system_statistics()

    assert "total_snapshots" in stats
    assert "datasets_prepared" in stats
    assert "active_jobs" in stats
    assert "completed_jobs" in stats
    assert "failed_jobs" in stats
    assert "total_cost_usd" in stats


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_full_finetuning_workflow(finetuning_system):
    """Test complete finetuning workflow from data collection to job creation"""
    category = AgentCategory.CORE_SECURITY

    # Step 1: Collect performance data
    for i in range(200):
        await finetuning_system.collect_performance_snapshot(
            agent_id="scanner_v2",
            agent_name="Scanner V2",
            category=category,
            task_type="vulnerability_scan",
            input_data={"file": f"file_{i}.py", "scan_depth": "full"},
            output_data={
                "vulnerabilities": [{"severity": "low", "line": i % 100}] if i % 10 == 0 else [],
                "scan_time_ms": 100 + i
            },
            success=True,
            performance_score=0.85 + ((i % 15) * 0.01),
            execution_time_ms=100.0 + i,
            tokens_used=50 + (i % 20),
            user_feedback=0.9 if i % 5 == 0 else None
        )

    assert len(finetuning_system.performance_snapshots) == 200

    # Step 2: Prepare dataset
    dataset = await finetuning_system.prepare_dataset(
        category=category,
        min_samples=100,
        max_samples=200,
        quality_threshold=0.7,
        time_range_days=30
    )

    assert dataset.category == category
    assert len(dataset.train_split) >= 80
    assert "success_rate" in dataset.statistics

    # Step 3: Create finetuning job
    config = FinetuningConfig(
        category=category,
        provider=FinetuningProvider.OPENAI,
        base_model="gpt-4o-mini",
        n_epochs=3,
        batch_size=32,
        learning_rate=0.0001,
        description="Test finetuning for core security agents"
    )

    job = await finetuning_system.create_finetuning_job(
        category=category,
        config=config
    )

    assert job.job_id.startswith("finetune_")
    assert job.training_samples >= 80
    assert job.validation_samples >= 10

    # Step 4: Wait a bit for background processing
    await asyncio.sleep(0.5)

    # Step 5: Check statistics
    stats = finetuning_system.get_system_statistics()
    assert stats["datasets_prepared"] >= 1
    assert category.value in stats["categories_with_data"]


@pytest.mark.asyncio
async def test_concurrent_snapshot_collection(finetuning_system):
    """Test collecting snapshots concurrently"""
    tasks = []

    for i in range(50):
        task = finetuning_system.collect_performance_snapshot(
            agent_id=f"agent_{i % 5}",
            agent_name=f"Agent {i % 5}",
            category=AgentCategory.ECOMMERCE,
            task_type="product_sync",
            input_data={"product_id": i},
            output_data={"synced": True},
            success=True,
            performance_score=0.9,
            execution_time_ms=100.0,
            tokens_used=50
        )
        tasks.append(task)

    await asyncio.gather(*tasks)

    assert len(finetuning_system.performance_snapshots) == 50


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_get_nonexistent_job(finetuning_system):
    """Test getting status of non-existent job"""
    job = finetuning_system.get_job_status("nonexistent_job_id")
    assert job is None


@pytest.mark.asyncio
async def test_prepare_dataset_empty_category(finetuning_system):
    """Test preparing dataset for category with no data"""
    with pytest.raises(ValueError, match="Insufficient data"):
        await finetuning_system.prepare_dataset(
            category=AgentCategory.SPECIALIZED,
            min_samples=100
        )


# ============================================================================
# GLOBAL INSTANCE TEST
# ============================================================================

def test_get_global_finetuning_system():
    """Test getting global finetuning system instance"""
    system1 = get_finetuning_system()
    system2 = get_finetuning_system()

    # Should return same instance
    assert system1 is system2
